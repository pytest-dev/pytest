from io import StringIO
from pprint import pprint
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Union

import attr
import py

from _pytest._code.code import ExceptionChainRepr
from _pytest._code.code import ExceptionInfo
from _pytest._code.code import ReprEntry
from _pytest._code.code import ReprEntryNative
from _pytest._code.code import ReprExceptionInfo
from _pytest._code.code import ReprFileLocation
from _pytest._code.code import ReprFuncArgs
from _pytest._code.code import ReprLocals
from _pytest._code.code import ReprTraceback
from _pytest._code.code import TerminalRepr
from _pytest._io import TerminalWriter
from _pytest.compat import TYPE_CHECKING
from _pytest.config import Config
from _pytest.nodes import Collector
from _pytest.nodes import Item
from _pytest.outcomes import skip
from _pytest.pathlib import Path

if TYPE_CHECKING:
    from typing import NoReturn
    from typing_extensions import Type
    from typing_extensions import Literal

    from _pytest.runner import CallInfo


def getworkerinfoline(node):
    try:
        return node._workerinfocache
    except AttributeError:
        d = node.workerinfo
        ver = "%s.%s.%s" % d["version_info"][:3]
        node._workerinfocache = s = "[{}] {} -- Python {} {}".format(
            d["id"], d["sysplatform"], ver, d["executable"]
        )
        return s


_R = TypeVar("_R", bound="BaseReport")


class BaseReport:
    when = None  # type: Optional[str]
    location = None  # type: Optional[Tuple[str, Optional[int], str]]
    # TODO: Improve this Any.
    longrepr = None  # type: Optional[Any]
    sections = []  # type: List[Tuple[str, str]]
    nodeid = None  # type: str

    def __init__(self, **kw: Any) -> None:
        self.__dict__.update(kw)

    if TYPE_CHECKING:
        # Can have arbitrary fields given to __init__().
        def __getattr__(self, key: str) -> Any:
            raise NotImplementedError()

    def toterminal(self, out: TerminalWriter) -> None:
        if hasattr(self, "node"):
            out.line(getworkerinfoline(self.node))

        longrepr = self.longrepr
        if longrepr is None:
            return

        if hasattr(longrepr, "toterminal"):
            longrepr.toterminal(out)
        else:
            try:
                s = str(longrepr)
            except UnicodeEncodeError:
                s = "<unprintable longrepr>"
            out.line(s)

    def get_sections(self, prefix: str) -> Iterator[Tuple[str, str]]:
        for name, content in self.sections:
            if name.startswith(prefix):
                yield prefix, content

    @property
    def longreprtext(self) -> str:
        """
        Read-only property that returns the full string representation
        of ``longrepr``.

        .. versionadded:: 3.0
        """
        file = StringIO()
        tw = TerminalWriter(file)
        tw.hasmarkup = False
        self.toterminal(tw)
        exc = file.getvalue()
        return exc.strip()

    @property
    def caplog(self) -> str:
        """Return captured log lines, if log capturing is enabled

        .. versionadded:: 3.5
        """
        return "\n".join(
            content for (prefix, content) in self.get_sections("Captured log")
        )

    @property
    def capstdout(self) -> str:
        """Return captured text from stdout, if capturing is enabled

        .. versionadded:: 3.0
        """
        return "".join(
            content for (prefix, content) in self.get_sections("Captured stdout")
        )

    @property
    def capstderr(self) -> str:
        """Return captured text from stderr, if capturing is enabled

        .. versionadded:: 3.0
        """
        return "".join(
            content for (prefix, content) in self.get_sections("Captured stderr")
        )

    passed = property(lambda x: x.outcome == "passed")
    failed = property(lambda x: x.outcome == "failed")
    skipped = property(lambda x: x.outcome == "skipped")

    @property
    def fspath(self) -> str:
        return self.nodeid.split("::")[0]

    @property
    def count_towards_summary(self) -> bool:
        """
        **Experimental**

        ``True`` if this report should be counted towards the totals shown at the end of the
        test session: "1 passed, 1 failure, etc".

        .. note::

            This function is considered **experimental**, so beware that it is subject to changes
            even in patch releases.
        """
        return True

    @property
    def head_line(self) -> Optional[str]:
        """
        **Experimental**

        Returns the head line shown with longrepr output for this report, more commonly during
        traceback representation during failures::

            ________ Test.foo ________


        In the example above, the head_line is "Test.foo".

        .. note::

            This function is considered **experimental**, so beware that it is subject to changes
            even in patch releases.
        """
        if self.location is not None:
            fspath, lineno, domain = self.location
            return domain
        return None

    def _get_verbose_word(self, config: Config):
        _category, _short, verbose = config.hook.pytest_report_teststatus(
            report=self, config=config
        )
        return verbose

    def _to_json(self) -> Dict[str, Any]:
        """
        This was originally the serialize_report() function from xdist (ca03269).

        Returns the contents of this report as a dict of builtin entries, suitable for
        serialization.

        Experimental method.
        """
        return _report_to_json(self)

    @classmethod
    def _from_json(cls: "Type[_R]", reportdict: Dict[str, object]) -> _R:
        """
        This was originally the serialize_report() function from xdist (ca03269).

        Factory method that returns either a TestReport or CollectReport, depending on the calling
        class. It's the callers responsibility to know which class to pass here.

        Experimental method.
        """
        kwargs = _report_kwargs_from_json(reportdict)
        return cls(**kwargs)


def _report_unserialization_failure(
    type_name: str, report_class: "Type[BaseReport]", reportdict
) -> "NoReturn":
    url = "https://github.com/pytest-dev/pytest/issues"
    stream = StringIO()
    pprint("-" * 100, stream=stream)
    pprint("INTERNALERROR: Unknown entry type returned: %s" % type_name, stream=stream)
    pprint("report_name: %s" % report_class, stream=stream)
    pprint(reportdict, stream=stream)
    pprint("Please report this bug at %s" % url, stream=stream)
    pprint("-" * 100, stream=stream)
    raise RuntimeError(stream.getvalue())


class TestReport(BaseReport):
    """ Basic test report object (also used for setup and teardown calls if
    they fail).
    """

    __test__ = False

    def __init__(
        self,
        nodeid: str,
        location: Tuple[str, Optional[int], str],
        keywords,
        outcome: "Literal['passed', 'failed', 'skipped']",
        longrepr,
        when: "Literal['setup', 'call', 'teardown']",
        sections: Iterable[Tuple[str, str]] = (),
        duration: float = 0,
        user_properties: Optional[Iterable[Tuple[str, object]]] = None,
        **extra
    ) -> None:
        #: normalized collection node id
        self.nodeid = nodeid

        #: a (filesystempath, lineno, domaininfo) tuple indicating the
        #: actual location of a test item - it might be different from the
        #: collected one e.g. if a method is inherited from a different module.
        self.location = location  # type: Tuple[str, Optional[int], str]

        #: a name -> value dictionary containing all keywords and
        #: markers associated with a test invocation.
        self.keywords = keywords

        #: test outcome, always one of "passed", "failed", "skipped".
        self.outcome = outcome

        #: None or a failure representation.
        self.longrepr = longrepr

        #: one of 'setup', 'call', 'teardown' to indicate runtest phase.
        self.when = when

        #: user properties is a list of tuples (name, value) that holds user
        #: defined properties of the test
        self.user_properties = list(user_properties or [])

        #: list of pairs ``(str, str)`` of extra information which needs to
        #: marshallable. Used by pytest to add captured text
        #: from ``stdout`` and ``stderr``, but may be used by other plugins
        #: to add arbitrary information to reports.
        self.sections = list(sections)

        #: time it took to run just the test
        self.duration = duration

        self.__dict__.update(extra)

    def __repr__(self) -> str:
        return "<{} {!r} when={!r} outcome={!r}>".format(
            self.__class__.__name__, self.nodeid, self.when, self.outcome
        )

    @classmethod
    def from_item_and_call(cls, item: Item, call: "CallInfo[None]") -> "TestReport":
        """
        Factory method to create and fill a TestReport with standard item and call info.
        """
        when = call.when
        # Remove "collect" from the Literal type -- only for collection calls.
        assert when != "collect"
        duration = call.duration
        keywords = {x: 1 for x in item.keywords}
        excinfo = call.excinfo
        sections = []
        if not call.excinfo:
            outcome = "passed"  # type: Literal["passed", "failed", "skipped"]
            # TODO: Improve this Any.
            longrepr = None  # type: Optional[Any]
        else:
            if not isinstance(excinfo, ExceptionInfo):
                outcome = "failed"
                longrepr = excinfo
            elif isinstance(excinfo.value, skip.Exception):
                outcome = "skipped"
                r = excinfo._getreprcrash()
                longrepr = (str(r.path), r.lineno, r.message)
            else:
                outcome = "failed"
                if call.when == "call":
                    longrepr = item.repr_failure(excinfo)
                else:  # exception in setup or teardown
                    longrepr = item._repr_failure_py(
                        excinfo, style=item.config.getoption("tbstyle", "auto")
                    )
        for rwhen, key, content in item._report_sections:
            sections.append(("Captured {} {}".format(key, rwhen), content))
        return cls(
            item.nodeid,
            item.location,
            keywords,
            outcome,
            longrepr,
            when,
            sections,
            duration,
            user_properties=item.user_properties,
        )


class CollectReport(BaseReport):
    """Collection report object."""

    when = "collect"

    def __init__(
        self,
        nodeid: str,
        outcome: "Literal['passed', 'skipped', 'failed']",
        longrepr,
        result: Optional[List[Union[Item, Collector]]],
        sections: Iterable[Tuple[str, str]] = (),
        **extra
    ) -> None:
        #: normalized collection node id
        self.nodeid = nodeid

        #: test outcome, always one of "passed", "failed", "skipped".
        self.outcome = outcome

        #: None or a failure representation.
        self.longrepr = longrepr

        #: The collected items and collection nodes.
        self.result = result or []

        #: list of pairs ``(str, str)`` of extra information which needs to
        #: marshallable. Used by pytest to add captured text
        #: from ``stdout`` and ``stderr``, but may be used by other plugins
        #: to add arbitrary information to reports.
        self.sections = list(sections)

        self.__dict__.update(extra)

    @property
    def location(self):
        return (self.fspath, None, self.fspath)

    def __repr__(self) -> str:
        return "<CollectReport {!r} lenresult={} outcome={!r}>".format(
            self.nodeid, len(self.result), self.outcome
        )


class CollectErrorRepr(TerminalRepr):
    def __init__(self, msg) -> None:
        self.longrepr = msg

    def toterminal(self, out: TerminalWriter) -> None:
        out.line(self.longrepr, red=True)


def pytest_report_to_serializable(
    report: Union[CollectReport, TestReport]
) -> Optional[Dict[str, Any]]:
    if isinstance(report, (TestReport, CollectReport)):
        data = report._to_json()
        data["$report_type"] = report.__class__.__name__
        return data
    return None


def pytest_report_from_serializable(
    data: Dict[str, Any],
) -> Optional[Union[CollectReport, TestReport]]:
    if "$report_type" in data:
        if data["$report_type"] == "TestReport":
            return TestReport._from_json(data)
        elif data["$report_type"] == "CollectReport":
            return CollectReport._from_json(data)
        assert False, "Unknown report_type unserialize data: {}".format(
            data["$report_type"]
        )
    return None


def _report_to_json(report: BaseReport) -> Dict[str, Any]:
    """
    This was originally the serialize_report() function from xdist (ca03269).

    Returns the contents of this report as a dict of builtin entries, suitable for
    serialization.
    """

    def serialize_repr_entry(
        entry: Union[ReprEntry, ReprEntryNative]
    ) -> Dict[str, Any]:
        data = attr.asdict(entry)
        for key, value in data.items():
            if hasattr(value, "__dict__"):
                data[key] = attr.asdict(value)
        entry_data = {"type": type(entry).__name__, "data": data}
        return entry_data

    def serialize_repr_traceback(reprtraceback: ReprTraceback) -> Dict[str, Any]:
        result = attr.asdict(reprtraceback)
        result["reprentries"] = [
            serialize_repr_entry(x) for x in reprtraceback.reprentries
        ]
        return result

    def serialize_repr_crash(
        reprcrash: Optional[ReprFileLocation],
    ) -> Optional[Dict[str, Any]]:
        if reprcrash is not None:
            return attr.asdict(reprcrash)
        else:
            return None

    def serialize_longrepr(rep: BaseReport) -> Dict[str, Any]:
        assert rep.longrepr is not None
        result = {
            "reprcrash": serialize_repr_crash(rep.longrepr.reprcrash),
            "reprtraceback": serialize_repr_traceback(rep.longrepr.reprtraceback),
            "sections": rep.longrepr.sections,
        }  # type: Dict[str, Any]
        if isinstance(rep.longrepr, ExceptionChainRepr):
            result["chain"] = []
            for repr_traceback, repr_crash, description in rep.longrepr.chain:
                result["chain"].append(
                    (
                        serialize_repr_traceback(repr_traceback),
                        serialize_repr_crash(repr_crash),
                        description,
                    )
                )
        else:
            result["chain"] = None
        return result

    d = report.__dict__.copy()
    if hasattr(report.longrepr, "toterminal"):
        if hasattr(report.longrepr, "reprtraceback") and hasattr(
            report.longrepr, "reprcrash"
        ):
            d["longrepr"] = serialize_longrepr(report)
        else:
            d["longrepr"] = str(report.longrepr)
    else:
        d["longrepr"] = report.longrepr
    for name in d:
        if isinstance(d[name], (py.path.local, Path)):
            d[name] = str(d[name])
        elif name == "result":
            d[name] = None  # for now
    return d


def _report_kwargs_from_json(reportdict: Dict[str, Any]) -> Dict[str, Any]:
    """
    This was originally the serialize_report() function from xdist (ca03269).

    Returns **kwargs that can be used to construct a TestReport or CollectReport instance.
    """

    def deserialize_repr_entry(entry_data):
        data = entry_data["data"]
        entry_type = entry_data["type"]
        if entry_type == "ReprEntry":
            reprfuncargs = None
            reprfileloc = None
            reprlocals = None
            if data["reprfuncargs"]:
                reprfuncargs = ReprFuncArgs(**data["reprfuncargs"])
            if data["reprfileloc"]:
                reprfileloc = ReprFileLocation(**data["reprfileloc"])
            if data["reprlocals"]:
                reprlocals = ReprLocals(data["reprlocals"]["lines"])

            reprentry = ReprEntry(
                lines=data["lines"],
                reprfuncargs=reprfuncargs,
                reprlocals=reprlocals,
                reprfileloc=reprfileloc,
                style=data["style"],
            )  # type: Union[ReprEntry, ReprEntryNative]
        elif entry_type == "ReprEntryNative":
            reprentry = ReprEntryNative(data["lines"])
        else:
            _report_unserialization_failure(entry_type, TestReport, reportdict)
        return reprentry

    def deserialize_repr_traceback(repr_traceback_dict):
        repr_traceback_dict["reprentries"] = [
            deserialize_repr_entry(x) for x in repr_traceback_dict["reprentries"]
        ]
        return ReprTraceback(**repr_traceback_dict)

    def deserialize_repr_crash(repr_crash_dict: Optional[dict]):
        if repr_crash_dict is not None:
            return ReprFileLocation(**repr_crash_dict)
        else:
            return None

    if (
        reportdict["longrepr"]
        and "reprcrash" in reportdict["longrepr"]
        and "reprtraceback" in reportdict["longrepr"]
    ):

        reprtraceback = deserialize_repr_traceback(
            reportdict["longrepr"]["reprtraceback"]
        )
        reprcrash = deserialize_repr_crash(reportdict["longrepr"]["reprcrash"])
        if reportdict["longrepr"]["chain"]:
            chain = []
            for repr_traceback_data, repr_crash_data, description in reportdict[
                "longrepr"
            ]["chain"]:
                chain.append(
                    (
                        deserialize_repr_traceback(repr_traceback_data),
                        deserialize_repr_crash(repr_crash_data),
                        description,
                    )
                )
            exception_info = ExceptionChainRepr(
                chain
            )  # type: Union[ExceptionChainRepr,ReprExceptionInfo]
        else:
            exception_info = ReprExceptionInfo(reprtraceback, reprcrash)

        for section in reportdict["longrepr"]["sections"]:
            exception_info.addsection(*section)
        reportdict["longrepr"] = exception_info

    return reportdict
