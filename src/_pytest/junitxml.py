# mypy: allow-untyped-defs
"""Report test results in JUnit-XML format, for use with Jenkins and build
integration servers.

Based on initial code from Ross Lawley.

Output conforms to
https://github.com/jenkinsci/xunit-plugin/blob/master/src/main/resources/org/jenkinsci/plugins/xunit/types/model/xsd/junit-10.xsd
"""

from __future__ import annotations

from collections.abc import Callable
import functools
import os
import platform
import re
from typing import Literal
import xml.etree.ElementTree as ET

from _pytest import nodes
from _pytest import timing
from _pytest._code.code import ExceptionRepr
from _pytest._code.code import ReprFileLocation
from _pytest.compat import assert_never
from _pytest.config import Config
from _pytest.config import filename_arg
from _pytest.config.argparsing import Parser
from _pytest.fixtures import FixtureRequest
from _pytest.nodeid import coerce_node_id
from _pytest.nodeid import NodeId
from _pytest.reports import BaseReport
from _pytest.reports import CollectReport
from _pytest.reports import TestReport
from _pytest.stash import StashKey
from _pytest.subtests import SubtestReport
from _pytest.terminal import TerminalReporter
import pytest


xml_key = StashKey["LogXML"]()

_JunitLogging = Literal["no", "log", "system-out", "system-err", "out-err", "all"]
_JunitDurationReport = Literal["total", "call"]
_JunitFamily = Literal["legacy", "xunit1", "xunit2"]


def bin_xml_escape(arg: object) -> str:
    r"""Visually escape invalid XML characters.

    For example, transforms
        'hello\aworld\b'
    into
        'hello#x07world#x08'
    Note that the #xABs are *not* XML escapes - missing the ampersand &#xAB.
    The idea is to escape visually for the user rather than for XML itself.
    """

    def repl(matchobj: re.Match[str]) -> str:
        i = ord(matchobj.group())
        if i <= 0xFF:
            return f"#x{i:02X}"
        else:
            return f"#x{i:04X}"

    # The spec range of valid chars is:
    # Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
    # For an unknown(?) reason, we disallow #x7F (DEL) as well.
    illegal_xml_re = "[^\u0009\u000a\u000d\u0020-\u007e\u0080-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]"
    return re.sub(illegal_xml_re, repl, str(arg))


# Budget for the ``message`` attribute of <failure> and <error> elements.
# The full report is always written as the element text.
MESSAGE_ATTR_BUDGET = 500


def shorten_message(msg: str, budget: int = MESSAGE_ATTR_BUDGET) -> str:
    """Shorten ``msg`` for use in a ``message`` attribute.

    Whole lines are kept while they fit in ``budget`` characters; a first
    line that is longer than ``budget`` on its own is cut. If anything was
    dropped, a final line points readers to the element text, which holds
    the full report.
    """
    lines = msg.splitlines() or [""]
    kept: list[str] = []
    size = 0
    for line in lines:
        if kept and size + len(line) + 1 > budget:
            break
        kept.append(line)
        size += len(line) + 1
    shortened = "\n".join(kept)
    first_line_cut = len(shortened) > budget
    if first_line_cut:
        shortened = shortened[:budget] + "..."
    remaining = len(lines) - len(kept)
    if remaining:
        note = f"+{remaining} more line{'s' if remaining > 1 else ''}"
    elif first_line_cut:
        note = "truncated"
    else:
        return msg
    return f"{shortened}\n[{note}; full report in element text]"


def merge_family(left, right) -> None:
    result = {}
    for kl, vl in left.items():
        for vr in right.values():
            if not isinstance(vl, list):
                raise TypeError(type(vl))
            result[kl] = vl + vr
    left.update(result)


families = {  # pylint: disable=dict-init-mutate
    "_base": {"testcase": ["classname", "name"]},
    "_base_legacy": {"testcase": ["file", "line", "url"]},
}
# xUnit 1.x inherits legacy attributes.
families["xunit1"] = families["_base"].copy()
merge_family(families["xunit1"], families["_base_legacy"])

# xUnit 2.x uses strict base attributes.
families["xunit2"] = families["_base"]


class _NodeReporter:
    def __init__(self, node_id: NodeId, xml: LogXML) -> None:
        self.id = node_id
        self.xml = xml
        self.add_stats = self.xml.add_stats
        self.family = self.xml.family
        self.duration = 0.0
        self.properties: list[tuple[str, str]] = []
        self.nodes: list[ET.Element] = []
        self.attrs: dict[str, str] = {}

    def append(self, node: ET.Element) -> None:
        self.xml.add_stats(node.tag)
        self.nodes.append(node)

    def add_property(self, name: str, value: object) -> None:
        self.properties.append((bin_xml_escape(name), bin_xml_escape(value)))

    def add_attribute(self, name: str, value: object) -> None:
        self.attrs[bin_xml_escape(name)] = bin_xml_escape(value)

    def make_properties_node(self) -> ET.Element | None:
        """Return a Junit node containing custom properties, if any."""
        if self.properties:
            properties = ET.Element("properties")
            for name, value in self.properties:
                properties.append(ET.Element("property", name=name, value=value))
            return properties
        return None

    def record_testreport(self, testreport: TestReport | CollectReport) -> None:
        names = mangle_test_address(testreport.nodeid)
        existing_attrs = self.attrs
        classnames = names[:-1]
        if self.xml.prefix:
            classnames.insert(0, self.xml.prefix)
        location = testreport.location
        assert location is not None
        # The collected file, like the nodeid and classname; for an inherited
        # test location[0] is the module defining the function (#9388).
        collected = NodeId.parse(testreport.nodeid).path or location[0]
        attrs: dict[str, str] = {
            "classname": ".".join(classnames),
            "name": bin_xml_escape(names[-1]),
            "file": collected.replace(os.sep, nodes.SEP),
        }
        defined = location[0].replace(os.sep, nodes.SEP)
        if location[1] is not None and defined == attrs["file"]:
            # location line numbers are 0-based.
            attrs["line"] = str(location[1] + 1)
        if hasattr(testreport, "url"):
            attrs["url"] = testreport.url
        self.attrs = attrs
        self.attrs.update(existing_attrs)  # Restore any user-defined attributes.

        # Preserve legacy testcase behavior.
        if self.family == "xunit1":
            return

        # Filter out attributes not permitted by this test family.
        # Including custom attributes because they are not valid here.
        temp_attrs = {}
        for key in self.attrs:
            if key in families[self.family]["testcase"]:
                temp_attrs[key] = self.attrs[key]
        self.attrs = temp_attrs

    def to_xml(self) -> ET.Element:
        testcase = ET.Element("testcase", self.attrs, time=f"{self.duration:.3f}")
        properties = self.make_properties_node()
        if properties is not None:
            testcase.append(properties)
        testcase.extend(self.nodes)
        return testcase

    def _add_simple(self, tag: str, message: str, data: str | None = None) -> None:
        node = ET.Element(tag, message=message)
        node.text = bin_xml_escape(data)
        self.append(node)

    def write_captured_output(self, report: TestReport) -> None:
        content_out = report.capstdout
        content_log = report.caplog
        content_err = report.capstderr
        if self.xml.logging == "no":
            return
        content_all = ""
        if self.xml.logging in ["log", "all"]:
            content_all = self._prepare_content(content_log, " Captured Log ")
        if self.xml.logging in ["system-out", "out-err", "all"]:
            content_all += self._prepare_content(content_out, " Captured Out ")
            self._write_content(report, content_all, "system-out")
            content_all = ""
        if self.xml.logging in ["system-err", "out-err", "all"]:
            content_all += self._prepare_content(content_err, " Captured Err ")
            self._write_content(report, content_all, "system-err")
            content_all = ""
        if content_all:
            self._write_content(report, content_all, "system-out")

    def _prepare_content(self, content: str, header: str) -> str:
        return "\n".join([header.center(80, "-"), content, ""])

    def _write_content(self, report: TestReport, content: str, jheader: str) -> None:
        tag = ET.Element(jheader)
        tag.text = bin_xml_escape(content)
        self.append(tag)

    def append_pass(self, report: TestReport) -> None:
        self.add_stats("passed")

    def append_failure(self, report: TestReport) -> None:
        # msg = str(report.longrepr.reprtraceback.extraline)
        if hasattr(report, "wasxfail"):
            self._add_simple("skipped", "xfail-marked test passes unexpectedly")
        else:
            assert report.longrepr is not None
            reprcrash: ReprFileLocation | None = getattr(
                report.longrepr, "reprcrash", None
            )
            if reprcrash is not None:
                message = reprcrash.message
            else:
                message = str(report.longrepr)
            message = bin_xml_escape(shorten_message(message))
            self._add_simple("failure", message, str(report.longrepr))

    def append_collect_error(self, report: CollectReport) -> None:
        # msg = str(report.longrepr.reprtraceback.extraline)
        assert report.longrepr is not None
        self._add_simple("error", "collection failure", str(report.longrepr))

    def append_collect_skipped(self, report: CollectReport) -> None:
        self._add_simple("skipped", "collection skipped", str(report.longrepr))

    def append_error(self, report: TestReport) -> None:
        assert report.longrepr is not None
        reprcrash: ReprFileLocation | None = getattr(report.longrepr, "reprcrash", None)
        if reprcrash is not None:
            reason = reprcrash.message
        else:
            reason = str(report.longrepr)

        if report.when == "teardown":
            msg = f'failed on teardown with "{reason}"'
        else:
            msg = f'failed on setup with "{reason}"'
        self._add_simple(
            "error", bin_xml_escape(shorten_message(msg)), str(report.longrepr)
        )

    def append_skipped(self, report: TestReport) -> None:
        if hasattr(report, "wasxfail"):
            xfailreason = report.wasxfail
            xfailreason = xfailreason.removeprefix("reason: ")
            xfailreason = bin_xml_escape(xfailreason)
            skipped = ET.Element("skipped", type="pytest.xfail", message=xfailreason)
            self.append(skipped)
        else:
            assert isinstance(report.longrepr, tuple)
            filename, lineno, skipreason = report.longrepr
            skipreason = skipreason.removeprefix("Skipped: ")
            details = f"{filename}:{lineno}: {skipreason}"

            skipped = ET.Element(
                "skipped", type="pytest.skip", message=bin_xml_escape(skipreason)
            )
            skipped.text = bin_xml_escape(details)
            self.append(skipped)

    def finalize(self) -> None:
        data = self.to_xml()
        self.__dict__.clear()
        # Type ignored because mypy doesn't like overriding a method.
        # Also the return value doesn't match...
        self.to_xml = lambda: data  # type: ignore[method-assign]


def _warn_incompatibility_with_xunit2(
    request: FixtureRequest, fixture_name: str
) -> None:
    """Emit a PytestWarning about the given fixture being incompatible with newer xunit revisions."""
    from _pytest.warning_types import PytestWarning

    xml = request.config.stash.get(xml_key, None)
    if xml is not None and xml.family not in ("xunit1", "legacy"):
        request.node.warn(
            PytestWarning(
                f"{fixture_name} is incompatible with junit_family '{xml.family}' (use 'legacy' or 'xunit1')"
            )
        )


@pytest.fixture
def record_property(request: FixtureRequest) -> Callable[[str, object], None]:
    """Add extra properties to the calling test.

    User properties become part of the test report and are available to the
    configured reporters, like JUnit XML.

    The fixture is callable with ``name, value``. The value is automatically
    XML-encoded.

    Example::

        def test_function(record_property):
            record_property("example_key", 1)
    """
    _warn_incompatibility_with_xunit2(request, "record_property")

    def append_property(name: str, value: object) -> None:
        request.node.user_properties.append((name, value))

    return append_property


@pytest.fixture
def record_xml_attribute(request: FixtureRequest) -> Callable[[str, object], None]:
    """Add extra xml attributes to the tag for the calling test.

    The fixture is callable with ``name, value``. The value is
    automatically XML-encoded.
    """
    from _pytest.warning_types import PytestExperimentalApiWarning

    request.node.warn(
        PytestExperimentalApiWarning("record_xml_attribute is an experimental feature")
    )

    _warn_incompatibility_with_xunit2(request, "record_xml_attribute")

    # Declare noop
    def add_attr_noop(name: str, value: object) -> None:
        pass

    attr_func = add_attr_noop

    xml = request.config.stash.get(xml_key, None)
    if xml is not None:
        node_reporter = xml.node_reporter(request.node.id)
        attr_func = node_reporter.add_attribute

    return attr_func


def _check_record_param_type(param: str, v: str) -> None:
    """Used by record_testsuite_property to check that the given parameter name is of the proper
    type."""
    __tracebackhide__ = True
    if not isinstance(v, str):
        msg = "{param} parameter needs to be a string, but {g} given"  # type: ignore[unreachable]
        raise TypeError(msg.format(param=param, g=type(v).__name__))


@pytest.fixture(scope="session")
def record_testsuite_property(request: FixtureRequest) -> Callable[[str, object], None]:
    """Record a new ``<property>`` tag as child of the root ``<testsuite>``.

    This is suitable to writing global information regarding the entire test
    suite, and is compatible with ``xunit2`` JUnit family.

    This is a ``session``-scoped fixture which is called with ``(name, value)``. Example:

    .. code-block:: python

        def test_foo(record_testsuite_property):
            record_testsuite_property("ARCH", "PPC")
            record_testsuite_property("STORAGE_TYPE", "CEPH")

    :param name:
        The property name.
    :param value:
        The property value. Will be converted to a string.

    .. warning::

        Currently this fixture **does not work** with the
        `pytest-xdist <https://github.com/pytest-dev/pytest-xdist>`__ plugin. See
        :issue:`7767` for details.
    """
    __tracebackhide__ = True

    def record_func(name: str, value: object) -> None:
        """No-op function in case --junit-xml was not passed in the command-line."""
        __tracebackhide__ = True
        _check_record_param_type("name", name)

    xml = request.config.stash.get(xml_key, None)
    if xml is not None:
        record_func = xml.add_global_property
    return record_func


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("terminal reporting")
    group.addoption(
        "--junitxml",
        "--junit-xml",
        action="store",
        dest="xmlpath",
        metavar="path",
        type=functools.partial(filename_arg, optname="--junitxml"),
        default=None,
        help="Create junit-xml style report file at given path",
    )
    group.addoption(
        "--junitprefix",
        "--junit-prefix",
        action="store",
        metavar="str",
        default=None,
        help="Prepend prefix to classnames in junit-xml output",
    )
    parser.addini(
        "junit_suite_name", "Test suite name for JUnit report", default="pytest"
    )
    parser.addini(
        "junit_logging",
        "Write captured log messages to JUnit report",
        type=_JunitLogging,
        default="no",
    )
    parser.addini(
        "junit_log_passing_tests",
        "Capture log information for passing tests to JUnit report: ",
        type="bool",
        default=True,
    )
    parser.addini(
        "junit_duration_report",
        "Duration time to report",
        type=_JunitDurationReport,
        default="total",
    )
    parser.addini(
        "junit_family",
        "Emit XML for schema",
        type=_JunitFamily,
        default="xunit2",
    )


def pytest_configure(config: Config) -> None:
    xmlpath = config.option.xmlpath
    # Prevent opening xmllog on worker nodes (xdist).
    if xmlpath and not hasattr(config, "workerinput"):
        config.stash[xml_key] = LogXML(
            xmlpath,
            config.option.junitprefix,
            config.getini("junit_suite_name"),
            config.getini("junit_logging"),
            config.getini("junit_duration_report"),
            config.getini("junit_family"),
            config.getini("junit_log_passing_tests"),
        )
        config.pluginmanager.register(config.stash[xml_key])


def pytest_unconfigure(config: Config) -> None:
    xml = config.stash.get(xml_key, None)
    if xml:
        del config.stash[xml_key]
        config.pluginmanager.unregister(xml)


def mangle_test_address(address: str) -> list[str]:
    oid = NodeId.parse(address)
    names = [oid.path, *oid.names]
    # Convert file path to dotted path.
    names[0] = names[0].replace(nodes.SEP, ".")
    names[0] = re.sub(r"\.py$", "", names[0])
    # Put any params back as one opaque bracket (the '-'-separated
    # param-call-boundary structure inside cannot be reliably recovered).
    if oid.params is not None:
        names[-1] += f"[{oid.params}]"
    return names


class LogXML:
    def __init__(
        self,
        logfile,
        prefix: str | None,
        suite_name: str = "pytest",
        logging: _JunitLogging = "no",
        report_duration: _JunitDurationReport = "total",
        family: _JunitFamily = "xunit1",
        log_passing_tests: bool = True,
    ) -> None:
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.prefix = prefix
        self.suite_name = suite_name
        self.logging = logging
        self.log_passing_tests = log_passing_tests
        self.report_duration = report_duration
        self.family = family
        self.stats: dict[str, int] = dict.fromkeys(
            ["error", "passed", "failure", "skipped"], 0
        )
        self.node_reporters: dict[tuple[NodeId, object], _NodeReporter] = {}
        self.node_reporters_ordered: list[_NodeReporter] = []
        self.global_properties: list[tuple[str, str]] = []

        # Reports of items whose teardown report has not arrived yet.
        self.pending_reports: dict[tuple[NodeId, object], list[TestReport]] = {}

        # Replaces convenience family with real family.
        if self.family == "legacy":
            self.family = "xunit1"

    def node_reporter(self, report: BaseReport | NodeId | str) -> _NodeReporter:
        match report:
            case NodeId():
                node_id = coerce_node_id(report)
            case str():
                node_id = coerce_node_id(report)
            case BaseReport():
                node_id = report.id
            case _:  # pragma: no cover
                assert_never(report)
        # Local hack to handle xdist report order.
        workernode = getattr(report, "node", None)

        key = node_id, workernode

        if key in self.node_reporters:
            # TODO: breaks for --dist=each
            return self.node_reporters[key]

        reporter = _NodeReporter(node_id, self)

        self.node_reporters[key] = reporter
        self.node_reporters_ordered.append(reporter)

        return reporter

    def add_stats(self, key: str) -> None:
        if key in self.stats:
            self.stats[key] += 1

    def _opentestcase(self, report: TestReport | CollectReport) -> _NodeReporter:
        reporter = self.node_reporter(report)
        reporter.record_testreport(report)
        return reporter

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """Collect the setup/call/teardown reports of one item and write its
        testcase element(s) once the teardown report arrives.

        Reports of different items may be interlaced (pytest-xdist), so they
        are buffered per (nodeid, worker node).  Deciding on the complete set
        of reports means the outcome of the whole item is known when choosing
        what to write, instead of deciding per phase.
        """
        key = report.id, getattr(report, "node", None)
        self.pending_reports.setdefault(key, []).append(report)
        if report.when == "teardown":
            self._write_item(key, self.pending_reports.pop(key))

    def _write_item(
        self, key: tuple[NodeId, object], reports: list[TestReport]
    ) -> None:
        subtests = [r for r in reports if isinstance(r, SubtestReport)]
        reports = [r for r in reports if not isinstance(r, SubtestReport)]
        teardown = reports[-1]
        call_failed = any(r.when == "call" and r.failed for r in reports)
        if call_failed and teardown.failed:
            # A call failure and a teardown error cannot be expressed in a
            # single schema-valid testcase, so they become two elements.
            groups = [reports[:-1], [teardown]]
        else:
            groups = [reports]
        for index, group in enumerate(groups):
            if index == 0:
                # May already exist, e.g. from record_xml_attribute.
                reporter = self.node_reporters.pop(key, None)
                if reporter is None:
                    reporter = _NodeReporter(teardown.id, self)
                    self.node_reporters_ordered.append(reporter)
            else:
                reporter = _NodeReporter(teardown.id, self)
                self.node_reporters_ordered.append(reporter)
            self._fill_testcase(reporter, group)
            if index == 0:
                # Each subtest is its own testcase, right after its parent.
                for number, subtest in enumerate(subtests, 1):
                    sub_reporter = _NodeReporter(subtest.id, self)
                    self.node_reporters_ordered.append(sub_reporter)
                    self._fill_testcase(
                        sub_reporter,
                        [subtest],
                        name_suffix=f" [subtest {number}] "
                        f"{subtest._sub_test_description()}",
                    )

    def _fill_testcase(
        self,
        reporter: _NodeReporter,
        reports: list[TestReport],
        name_suffix: str = "",
    ) -> None:
        for report in reports:
            if report.passed:
                if report.when == "call":
                    reporter.append_pass(report)
            elif report.failed:
                if report.when == "call":
                    reporter.append_failure(report)
                else:
                    reporter.append_error(report)
            else:
                reporter.append_skipped(report)
            if self.report_duration in {"total", report.when}:
                reporter.duration += getattr(report, "duration", 0.0)
        last = reports[-1]
        reporter.record_testreport(last)
        if name_suffix:
            reporter.attrs["name"] += bin_xml_escape(name_suffix)
        # The last report carries the captured sections of all earlier phases,
        # so output is written exactly once per testcase element.
        if self.log_passing_tests or not all(r.passed for r in reports):
            reporter.write_captured_output(last)
        for propname, propvalue in last.user_properties:
            reporter.add_property(propname, str(propvalue))
        reporter.finalize()

    def pytest_collectreport(self, report: CollectReport) -> None:
        if not report.passed:
            reporter = self._opentestcase(report)
            if report.failed:
                reporter.append_collect_error(report)
            else:
                reporter.append_collect_skipped(report)

    def pytest_internalerror(self, excrepr: ExceptionRepr) -> None:
        reporter = self.node_reporter("internal")
        reporter.attrs.update(classname="pytest", name="internal")
        reporter._add_simple("error", "internal error", str(excrepr))

    def pytest_sessionstart(self) -> None:
        self.suite_start = timing.Instant()

    def pytest_sessionfinish(self) -> None:
        dirname = os.path.dirname(os.path.abspath(self.logfile))
        # exist_ok avoids filesystem race conditions between checking path existence and requesting creation
        os.makedirs(dirname, exist_ok=True)

        with open(self.logfile, "w", encoding="utf-8") as logfile:
            duration = self.suite_start.elapsed()

            # One per testcase element: an item with a passing call and a
            # teardown error adds two stats but only one element (#3850).
            numtests = len(self.node_reporters_ordered)
            logfile.write('<?xml version="1.0" encoding="utf-8"?>')

            suite_node = ET.Element(
                "testsuite",
                name=self.suite_name,
                errors=str(self.stats["error"]),
                failures=str(self.stats["failure"]),
                skipped=str(self.stats["skipped"]),
                tests=str(numtests),
                time=f"{duration.seconds:.3f}",
                timestamp=self.suite_start.as_utc().astimezone().isoformat(),
                hostname=platform.node(),
            )
            global_properties = self._get_global_properties_node()
            if global_properties is not None:
                suite_node.append(global_properties)
            for node_reporter in self.node_reporters_ordered:
                suite_node.append(node_reporter.to_xml())
            testsuites = ET.Element("testsuites")
            testsuites.set("name", "pytest tests")
            testsuites.append(suite_node)
            logfile.write(ET.tostring(testsuites, encoding="unicode"))

    def pytest_terminal_summary(
        self, terminalreporter: TerminalReporter, config: pytest.Config
    ) -> None:
        if config.get_verbosity() >= 0:
            terminalreporter.write_sep("-", f"generated xml file: {self.logfile}")

    def add_global_property(self, name: str, value: object) -> None:
        __tracebackhide__ = True
        _check_record_param_type("name", name)
        self.global_properties.append((bin_xml_escape(name), bin_xml_escape(value)))

    def _get_global_properties_node(self) -> ET.Element | None:
        """Return a Junit node containing custom properties, if any."""
        if self.global_properties:
            properties = ET.Element("properties")
            for name, value in self.global_properties:
                properties.append(ET.Element("property", name=name, value=value))
            return properties
        return None
