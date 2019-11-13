""" terminal reporting of the full testing process.

This is a good source for looking at the various reporting hooks.
"""
import argparse
import collections
import datetime
import platform
import sys
import time
from functools import partial
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Mapping
from typing import Optional
from typing import Set
from typing import Tuple

import attr
import pluggy
import py
from more_itertools import collapse

import pytest
from _pytest import nodes
from _pytest.config import Config
from _pytest.main import ExitCode
from _pytest.main import Session
from _pytest.reports import CollectReport
from _pytest.reports import TestReport

REPORT_COLLECTING_RESOLUTION = 0.5


class MoreQuietAction(argparse.Action):
    """
    a modified copy of the argparse count action which counts down and updates
    the legacy quiet attribute at the same time

    used to unify verbosity handling
    """

    def __init__(self, option_strings, dest, default=None, required=False, help=None):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            default=default,
            required=required,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        new_count = getattr(namespace, self.dest, 0) - 1
        setattr(namespace, self.dest, new_count)
        # todo Deprecate config.quiet
        namespace.quiet = getattr(namespace, "quiet", 0) + 1


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbose",
        help="increase verbosity.",
    ),
    group._addoption(
        "-q",
        "--quiet",
        action=MoreQuietAction,
        default=0,
        dest="verbose",
        help="decrease verbosity.",
    ),
    group._addoption(
        "--verbosity",
        dest="verbose",
        type=int,
        default=0,
        help="set verbosity. Default is 0.",
    )
    group._addoption(
        "-r",
        action="store",
        dest="reportchars",
        default="",
        metavar="chars",
        help="show extra test summary info as specified by chars: (f)ailed, "
        "(E)rror, (s)kipped, (x)failed, (X)passed, "
        "(p)assed, (P)assed with output, (a)ll except passed (p/P), or (A)ll. "
        "(w)arnings are enabled by default (see --disable-warnings).",
    )
    group._addoption(
        "--disable-warnings",
        "--disable-pytest-warnings",
        default=False,
        dest="disable_warnings",
        action="store_true",
        help="disable warnings summary",
    )
    group._addoption(
        "-l",
        "--showlocals",
        action="store_true",
        dest="showlocals",
        default=False,
        help="show locals in tracebacks (disabled by default).",
    )
    group._addoption(
        "--tb",
        metavar="style",
        action="store",
        dest="tbstyle",
        default="auto",
        choices=["auto", "long", "short", "no", "line", "native"],
        help="traceback print mode (auto/long/short/line/native/no).",
    )
    group._addoption(
        "--show-capture",
        action="store",
        dest="showcapture",
        choices=["no", "stdout", "stderr", "log", "all"],
        default="all",
        help="Controls how captured stdout/stderr/log is shown on failed tests. "
        "Default is 'all'.",
    )
    group._addoption(
        "--fulltrace",
        "--full-trace",
        action="store_true",
        default=False,
        help="don't cut any tracebacks (default is to cut).",
    )
    group._addoption(
        "--color",
        metavar="color",
        action="store",
        dest="color",
        default="auto",
        choices=["yes", "no", "auto"],
        help="color terminal output (yes/no/auto).",
    )

    parser.addini(
        "console_output_style",
        help='console output: "classic", or with additional progress information ("progress" (percentage) | "count").',
        default="progress",
    )


def pytest_configure(config: Config) -> None:
    reporter = TerminalReporter(config, sys.stdout)
    config.pluginmanager.register(reporter, "terminalreporter")
    if config.option.debug or config.option.traceconfig:

        def mywriter(tags, args):
            msg = " ".join(map(str, args))
            reporter.write_line("[traceconfig] " + msg)

        config.trace.root.setprocessor("pytest:config", mywriter)


def getreportopt(config: Config) -> str:
    reportopts = ""
    reportchars = config.option.reportchars
    if not config.option.disable_warnings and "w" not in reportchars:
        reportchars += "w"
    elif config.option.disable_warnings and "w" in reportchars:
        reportchars = reportchars.replace("w", "")
    for char in reportchars:
        if char == "a":
            reportopts = "sxXwEf"
        elif char == "A":
            reportopts = "PpsxXwEf"
            break
        elif char not in reportopts:
            reportopts += char
    return reportopts


@pytest.hookimpl(trylast=True)  # after _pytest.runner
def pytest_report_teststatus(report: TestReport) -> Tuple[str, str, str]:
    if report.passed:
        letter = "."
    elif report.skipped:
        letter = "s"
    elif report.failed:
        letter = "F"
        if report.when != "call":
            letter = "f"

    # Report failed CollectReports as "error" (in line with pytest_collectreport).
    outcome = report.outcome
    if report.when == "collect" and outcome == "failed":
        outcome = "error"

    return outcome, letter, outcome.upper()


@attr.s
class WarningReport:
    """
    Simple structure to hold warnings information captured by ``pytest_warning_captured``.

    :ivar str message: user friendly message about the warning
    :ivar str|None nodeid: node id that generated the warning (see ``get_location``).
    :ivar tuple|py.path.local fslocation:
        file system location of the source of the warning (see ``get_location``).
    """

    message = attr.ib(type=str)
    nodeid = attr.ib(type=Optional[str], default=None)
    fslocation = attr.ib(default=None)
    count_towards_summary = True

    def get_location(self, config):
        """
        Returns the more user-friendly information about the location
        of a warning, or None.
        """
        if self.nodeid:
            return self.nodeid
        if self.fslocation:
            if isinstance(self.fslocation, tuple) and len(self.fslocation) >= 2:
                filename, linenum = self.fslocation[:2]
                relpath = py.path.local(filename).relto(config.invocation_dir)
                if not relpath:
                    relpath = str(filename)
                return "{}:{}".format(relpath, linenum)
            else:
                return str(self.fslocation)
        return None


class TerminalReporter:
    def __init__(self, config: Config, file=None) -> None:
        import _pytest.config

        self.config = config
        self._numcollected = 0
        self._session = None  # type: Optional[Session]
        self._showfspath = None

        self.stats = {}  # type: Dict[str, List[Any]]
        self.startdir = config.invocation_dir
        if file is None:
            file = sys.stdout
        self._tw = _pytest.config.create_terminal_writer(config, file)
        # self.writer will be deprecated in pytest-3.4
        self.writer = self._tw
        self._screen_width = self._tw.fullwidth
        self.currentfspath = None  # type: Any
        self.reportchars = getreportopt(config)
        self.hasmarkup = self._tw.hasmarkup
        self.isatty = file.isatty()
        self._progress_nodeids_reported = set()  # type: Set[str]
        self._show_progress_info = self._determine_show_progress_info()
        self._collect_report_last_write = None  # type: Optional[float]

    def _determine_show_progress_info(self):
        """Return True if we should display progress information based on the current config"""
        # do not show progress if we are not capturing output (#3038)
        if self.config.getoption("capture", "no") == "no":
            return False
        # do not show progress if we are showing fixture setup/teardown
        if self.config.getoption("setupshow", False):
            return False
        cfg = self.config.getini("console_output_style")
        if cfg in ("progress", "count"):
            return cfg
        return False

    @property
    def verbosity(self):
        return self.config.option.verbose

    @property
    def showheader(self):
        return self.verbosity >= 0

    @property
    def showfspath(self):
        if self._showfspath is None:
            return self.verbosity >= 0
        return self._showfspath

    @showfspath.setter
    def showfspath(self, value):
        self._showfspath = value

    @property
    def showlongtestinfo(self):
        return self.verbosity > 0

    def hasopt(self, char):
        char = {"xfailed": "x", "skipped": "s"}.get(char, char)
        return char in self.reportchars

    def write_fspath_result(self, nodeid, res, **markup):
        fspath = self.config.rootdir.join(nodeid.split("::")[0])
        # NOTE: explicitly check for None to work around py bug, and for less
        # overhead in general (https://github.com/pytest-dev/py/pull/207).
        if self.currentfspath is None or fspath != self.currentfspath:
            if self.currentfspath is not None and self._show_progress_info:
                self._write_progress_information_filling_space()
            self.currentfspath = fspath
            fspath = self.startdir.bestrelpath(fspath)
            self._tw.line()
            self._tw.write(fspath + " ")
        self._tw.write(res, **markup)

    def write_ensure_prefix(self, prefix, extra="", **kwargs):
        if self.currentfspath != prefix:
            self._tw.line()
            self.currentfspath = prefix
            self._tw.write(prefix)
        if extra:
            self._tw.write(extra, **kwargs)
            self.currentfspath = -2

    def ensure_newline(self):
        if self.currentfspath:
            self._tw.line()
            self.currentfspath = None

    def write(self, content, **markup):
        self._tw.write(content, **markup)

    def write_line(self, line, **markup):
        if not isinstance(line, str):
            line = str(line, errors="replace")
        self.ensure_newline()
        self._tw.line(line, **markup)

    def rewrite(self, line, **markup):
        """
        Rewinds the terminal cursor to the beginning and writes the given line.

        :kwarg erase: if True, will also add spaces until the full terminal width to ensure
            previous lines are properly erased.

        The rest of the keyword arguments are markup instructions.
        """
        erase = markup.pop("erase", False)
        if erase:
            fill_count = self._tw.fullwidth - len(line) - 1
            fill = " " * fill_count
        else:
            fill = ""
        line = str(line)
        self._tw.write("\r" + line + fill, **markup)

    def write_sep(self, sep, title=None, **markup):
        self.ensure_newline()
        self._tw.sep(sep, title, **markup)

    def section(self, title, sep="=", **kw):
        self._tw.sep(sep, title, **kw)

    def line(self, msg, **kw):
        self._tw.line(msg, **kw)

    def pytest_internalerror(self, excrepr):
        for line in str(excrepr).split("\n"):
            self.write_line("INTERNALERROR> " + line)
        return 1

    def pytest_warning_captured(self, warning_message, item):
        # from _pytest.nodes import get_fslocation_from_item
        from _pytest.warnings import warning_record_to_str

        warnings = self.stats.setdefault("warnings", [])
        fslocation = warning_message.filename, warning_message.lineno
        message = warning_record_to_str(warning_message)

        nodeid = item.nodeid if item is not None else ""
        warning_report = WarningReport(
            fslocation=fslocation, message=message, nodeid=nodeid
        )
        warnings.append(warning_report)

    def pytest_plugin_registered(self, plugin):
        if self.config.option.traceconfig:
            msg = "PLUGIN registered: {}".format(plugin)
            # XXX this event may happen during setup/teardown time
            #     which unfortunately captures our output here
            #     which garbles our output if we use self.write_line
            self.write_line(msg)

    def pytest_deselected(self, items):
        self.stats.setdefault("deselected", []).extend(items)

    def pytest_runtest_logstart(self, nodeid, location):
        # ensure that the path is printed before the
        # 1st test of a module starts running
        if self.showlongtestinfo:
            line = self._locationline(nodeid, *location)
            self.write_ensure_prefix(line, "")
        elif self.showfspath:
            fsid = nodeid.split("::")[0]
            self.write_fspath_result(fsid, "")

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        self._tests_ran = True
        rep = report
        res = self.config.hook.pytest_report_teststatus(report=rep, config=self.config)
        category, letter, word = res
        if isinstance(word, tuple):
            word, markup = word
        else:
            markup = None
        self.stats.setdefault(category, []).append(rep)
        if not letter and not word:
            # probably passed setup/teardown
            return
        running_xdist = hasattr(rep, "node")
        if markup is None:
            was_xfail = hasattr(report, "wasxfail")
            if rep.passed and not was_xfail:
                markup = {"green": True}
            elif rep.passed and was_xfail:
                markup = {"yellow": True}
            elif rep.failed:
                markup = {"red": True}
            elif rep.skipped:
                markup = {"yellow": True}
            else:
                markup = {}
        if self.verbosity <= 0:
            if not running_xdist and self.showfspath:
                self.write_fspath_result(rep.nodeid, letter, **markup)
            else:
                self._tw.write(letter, **markup)
        else:
            self._progress_nodeids_reported.add(rep.nodeid)
            line = self._locationline(rep.nodeid, *rep.location)
            if not running_xdist:
                self.write_ensure_prefix(line, word, **markup)
                if self._show_progress_info:
                    self._write_progress_information_filling_space()
            else:
                self.ensure_newline()
                self._tw.write("[%s]" % rep.node.gateway.id)  # type: ignore
                if self._show_progress_info:
                    self._tw.write(
                        self._get_progress_information_message() + " ", cyan=True
                    )
                else:
                    self._tw.write(" ")
                self._tw.write(word, **markup)
                self._tw.write(" " + line)
                self.currentfspath = -2

    def pytest_runtest_logfinish(self, nodeid):
        assert self._session
        if self.verbosity <= 0 and self._show_progress_info:
            if self._show_progress_info == "count":
                num_tests = self._session.testscollected
                progress_length = len(" [{}/{}]".format(str(num_tests), str(num_tests)))
            else:
                progress_length = len(" [100%]")

            main_color, _ = _get_main_color(self.stats)

            self._progress_nodeids_reported.add(nodeid)
            is_last_item = (
                len(self._progress_nodeids_reported) == self._session.testscollected
            )
            if is_last_item:
                self._write_progress_information_filling_space(color=main_color)
            else:
                w = self._width_of_current_line
                past_edge = w + progress_length + 1 >= self._screen_width
                if past_edge:
                    msg = self._get_progress_information_message()
                    self._tw.write(msg + "\n", **{main_color: True})

    def _get_progress_information_message(self) -> str:
        assert self._session
        collected = self._session.testscollected
        if self._show_progress_info == "count":
            if collected:
                progress = self._progress_nodeids_reported
                counter_format = "{{:{}d}}".format(len(str(collected)))
                format_string = " [{}/{{}}]".format(counter_format)
                return format_string.format(len(progress), collected)
            return " [ {} / {} ]".format(collected, collected)
        else:
            if collected:
                return " [{:3d}%]".format(
                    len(self._progress_nodeids_reported) * 100 // collected
                )
            return " [100%]"

    def _write_progress_information_filling_space(self, color=None):
        if not color:
            color, _ = _get_main_color(self.stats)
        msg = self._get_progress_information_message()
        w = self._width_of_current_line
        fill = self._tw.fullwidth - w - 1
        self.write(msg.rjust(fill), **{color: True})

    @property
    def _width_of_current_line(self):
        """Return the width of current line, using the superior implementation of py-1.6 when available"""
        try:
            return self._tw.width_of_current_line
        except AttributeError:
            # py < 1.6.0
            return self._tw.chars_on_current_line

    def pytest_collection(self):
        if self.isatty:
            if self.config.option.verbose >= 0:
                self.write("collecting ... ", bold=True)
                self._collect_report_last_write = time.time()
        elif self.config.option.verbose >= 1:
            self.write("collecting ... ", bold=True)

    def pytest_collectreport(self, report: CollectReport) -> None:
        if report.failed:
            self.stats.setdefault("error", []).append(report)
        elif report.skipped:
            self.stats.setdefault("skipped", []).append(report)
        items = [x for x in report.result if isinstance(x, pytest.Item)]
        self._numcollected += len(items)
        if self.isatty:
            self.report_collect()

    def report_collect(self, final=False):
        if self.config.option.verbose < 0:
            return

        if not final:
            # Only write "collecting" report every 0.5s.
            t = time.time()
            if (
                self._collect_report_last_write is not None
                and self._collect_report_last_write > t - REPORT_COLLECTING_RESOLUTION
            ):
                return
            self._collect_report_last_write = t

        errors = len(self.stats.get("error", []))
        skipped = len(self.stats.get("skipped", []))
        deselected = len(self.stats.get("deselected", []))
        selected = self._numcollected - errors - skipped - deselected
        if final:
            line = "collected "
        else:
            line = "collecting "
        line += (
            str(self._numcollected) + " item" + ("" if self._numcollected == 1 else "s")
        )
        if errors:
            line += " / %d error%s" % (errors, "s" if errors != 1 else "")
        if deselected:
            line += " / %d deselected" % deselected
        if skipped:
            line += " / %d skipped" % skipped
        if self._numcollected > selected > 0:
            line += " / %d selected" % selected
        if self.isatty:
            self.rewrite(line, bold=True, erase=True)
            if final:
                self.write("\n")
        else:
            self.write_line(line)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session: Session) -> None:
        self._session = session
        self._sessionstarttime = time.time()
        if not self.showheader:
            return
        self.write_sep("=", "test session starts", bold=True)
        verinfo = platform.python_version()
        msg = "platform {} -- Python {}".format(sys.platform, verinfo)
        pypy_version_info = getattr(sys, "pypy_version_info", None)
        if pypy_version_info:
            verinfo = ".".join(map(str, pypy_version_info[:3]))
            msg += "[pypy-{}-{}]".format(verinfo, pypy_version_info[3])
        msg += ", pytest-{}, py-{}, pluggy-{}".format(
            pytest.__version__, py.__version__, pluggy.__version__
        )
        if (
            self.verbosity > 0
            or self.config.option.debug
            or getattr(self.config.option, "pastebin", None)
        ):
            msg += " -- " + str(sys.executable)
        self.write_line(msg)
        lines = self.config.hook.pytest_report_header(
            config=self.config, startdir=self.startdir
        )
        self._write_report_lines_from_hooks(lines)

    def _write_report_lines_from_hooks(self, lines):
        lines.reverse()
        for line in collapse(lines):
            self.write_line(line)

    def pytest_report_header(self, config):
        line = "rootdir: %s" % config.rootdir

        if config.inifile:
            line += ", inifile: " + config.rootdir.bestrelpath(config.inifile)

        testpaths = config.getini("testpaths")
        if testpaths and config.args == testpaths:
            rel_paths = [config.rootdir.bestrelpath(x) for x in testpaths]
            line += ", testpaths: {}".format(", ".join(rel_paths))
        result = [line]

        plugininfo = config.pluginmanager.list_plugin_distinfo()
        if plugininfo:
            result.append("plugins: %s" % ", ".join(_plugin_nameversions(plugininfo)))
        return result

    def pytest_collection_finish(self, session):
        self.report_collect(True)

        if self.config.getoption("collectonly"):
            self._printcollecteditems(session.items)

        lines = self.config.hook.pytest_report_collectionfinish(
            config=self.config, startdir=self.startdir, items=session.items
        )
        self._write_report_lines_from_hooks(lines)

        if self.config.getoption("collectonly"):
            failed = self.stats.get("failed")
            if failed:
                self._tw.sep("!", "collection failures")
                for rep in failed:
                    rep.toterminal(self._tw)

    def _printcollecteditems(self, items):
        # to print out items and their parent collectors
        # we take care to leave out Instances aka ()
        # because later versions are going to get rid of them anyway
        if self.config.option.verbose < 0:
            if self.config.option.verbose < -1:
                counts = {}  # type: Dict[str, int]
                for item in items:
                    name = item.nodeid.split("::", 1)[0]
                    counts[name] = counts.get(name, 0) + 1
                for name, count in sorted(counts.items()):
                    self._tw.line("%s: %d" % (name, count))
            else:
                for item in items:
                    self._tw.line(item.nodeid)
            return
        stack = []
        indent = ""
        for item in items:
            needed_collectors = item.listchain()[1:]  # strip root node
            while stack:
                if stack == needed_collectors[: len(stack)]:
                    break
                stack.pop()
            for col in needed_collectors[len(stack) :]:
                stack.append(col)
                if col.name == "()":  # Skip Instances.
                    continue
                indent = (len(stack) - 1) * "  "
                self._tw.line("{}{}".format(indent, col))
                if self.config.option.verbose >= 1:
                    if hasattr(col, "_obj") and col._obj.__doc__:
                        for line in col._obj.__doc__.strip().splitlines():
                            self._tw.line("{}{}".format(indent + "  ", line.strip()))

    @pytest.hookimpl(hookwrapper=True)
    def pytest_sessionfinish(self, session: Session, exitstatus: ExitCode):
        outcome = yield
        outcome.get_result()
        self._tw.line("")
        summary_exit_codes = (
            ExitCode.OK,
            ExitCode.TESTS_FAILED,
            ExitCode.INTERRUPTED,
            ExitCode.USAGE_ERROR,
            ExitCode.NO_TESTS_COLLECTED,
        )
        if exitstatus in summary_exit_codes:
            self.config.hook.pytest_terminal_summary(
                terminalreporter=self, exitstatus=exitstatus, config=self.config
            )
        if session.shouldfail:
            self.write_sep("!", session.shouldfail, red=True)
        if exitstatus == ExitCode.INTERRUPTED:
            self._report_keyboardinterrupt()
            del self._keyboardinterrupt_memo
        elif session.shouldstop:
            self.write_sep("!", session.shouldstop, red=True)
        self.summary_stats()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_terminal_summary(self):
        self.summary_errors()
        self.summary_failures()
        self.summary_warnings()
        self.summary_passes()
        yield
        self.short_test_summary()
        # Display any extra warnings from teardown here (if any).
        self.summary_warnings()

    def pytest_keyboard_interrupt(self, excinfo):
        self._keyboardinterrupt_memo = excinfo.getrepr(funcargs=True)

    def pytest_unconfigure(self):
        if hasattr(self, "_keyboardinterrupt_memo"):
            self._report_keyboardinterrupt()

    def _report_keyboardinterrupt(self):
        excrepr = self._keyboardinterrupt_memo
        msg = excrepr.reprcrash.message
        self.write_sep("!", msg)
        if "KeyboardInterrupt" in msg:
            if self.config.option.fulltrace:
                excrepr.toterminal(self._tw)
            else:
                excrepr.reprcrash.toterminal(self._tw)
                self._tw.line(
                    "(to show a full traceback on KeyboardInterrupt use --full-trace)",
                    yellow=True,
                )

    def _locationline(self, nodeid, fspath, lineno, domain):
        def mkrel(nodeid):
            line = self.config.cwd_relative_nodeid(nodeid)
            if domain and line.endswith(domain):
                line = line[: -len(domain)]
                values = domain.split("[")
                values[0] = values[0].replace(".", "::")  # don't replace '.' in params
                line += "[".join(values)
            return line

        # collect_fspath comes from testid which has a "/"-normalized path

        if fspath:
            res = mkrel(nodeid)
            if self.verbosity >= 2 and nodeid.split("::")[0] != fspath.replace(
                "\\", nodes.SEP
            ):
                res += " <- " + self.startdir.bestrelpath(fspath)
        else:
            res = "[location]"
        return res + " "

    def _getfailureheadline(self, rep):
        head_line = rep.head_line
        if head_line:
            return head_line
        return "test session"  # XXX?

    def _getcrashline(self, rep):
        try:
            return str(rep.longrepr.reprcrash)
        except AttributeError:
            try:
                return str(rep.longrepr)[:50]
            except AttributeError:
                return ""

    #
    # summaries for sessionfinish
    #
    def getreports(self, name):
        values = []
        for x in self.stats.get(name, []):
            if not hasattr(x, "_pdbshown"):
                values.append(x)
        return values

    def summary_warnings(self):
        if self.hasopt("w"):
            all_warnings = self.stats.get(
                "warnings"
            )  # type: Optional[List[WarningReport]]
            if not all_warnings:
                return

            final = hasattr(self, "_already_displayed_warnings")
            if final:
                warning_reports = all_warnings[self._already_displayed_warnings :]
            else:
                warning_reports = all_warnings
            self._already_displayed_warnings = len(warning_reports)
            if not warning_reports:
                return

            reports_grouped_by_message = (
                collections.OrderedDict()
            )  # type: collections.OrderedDict[str, List[WarningReport]]
            for wr in warning_reports:
                reports_grouped_by_message.setdefault(wr.message, []).append(wr)

            title = "warnings summary (final)" if final else "warnings summary"
            self.write_sep("=", title, yellow=True, bold=False)
            for message, warning_reports in reports_grouped_by_message.items():
                has_any_location = False
                for w in warning_reports:
                    location = w.get_location(self.config)
                    if location:
                        self._tw.line(str(location))
                        has_any_location = True
                if has_any_location:
                    lines = message.splitlines()
                    indented = "\n".join("  " + x for x in lines)
                    message = indented.rstrip()
                else:
                    message = message.rstrip()
                self._tw.line(message)
                self._tw.line()
            self._tw.line("-- Docs: https://docs.pytest.org/en/latest/warnings.html")

    def summary_passes(self):
        if self.config.option.tbstyle != "no":
            if self.hasopt("P"):
                reports = self.getreports("passed")
                if not reports:
                    return
                self.write_sep("=", "PASSES")
                for rep in reports:
                    if rep.sections:
                        msg = self._getfailureheadline(rep)
                        self.write_sep("_", msg, green=True, bold=True)
                        self._outrep_summary(rep)

    def print_teardown_sections(self, rep):
        showcapture = self.config.option.showcapture
        if showcapture == "no":
            return
        for secname, content in rep.sections:
            if showcapture != "all" and showcapture not in secname:
                continue
            if "teardown" in secname:
                self._tw.sep("-", secname)
                if content[-1:] == "\n":
                    content = content[:-1]
                self._tw.line(content)

    def summary_failures(self):
        if self.config.option.tbstyle != "no":
            reports = self.getreports("failed")
            if not reports:
                return
            self.write_sep("=", "FAILURES")
            if self.config.option.tbstyle == "line":
                for rep in reports:
                    line = self._getcrashline(rep)
                    self.write_line(line)
            else:
                teardown_sections = {}
                for report in self.getreports(""):
                    if report.when == "teardown":
                        teardown_sections.setdefault(report.nodeid, []).append(report)

                for rep in reports:
                    msg = self._getfailureheadline(rep)
                    self.write_sep("_", msg, red=True, bold=True)
                    self._outrep_summary(rep)
                    for report in teardown_sections.get(rep.nodeid, []):
                        self.print_teardown_sections(report)

    def summary_errors(self):
        if self.config.option.tbstyle != "no":
            reports = self.getreports("error")
            if not reports:
                return
            self.write_sep("=", "ERRORS")
            for rep in self.stats["error"]:
                msg = self._getfailureheadline(rep)
                if rep.when == "collect":
                    msg = "ERROR collecting " + msg
                else:
                    msg = "ERROR at {} of {}".format(rep.when, msg)
                self.write_sep("_", msg, red=True, bold=True)
                self._outrep_summary(rep)

    def _outrep_summary(self, rep):
        rep.toterminal(self._tw)
        showcapture = self.config.option.showcapture
        if showcapture == "no":
            return
        for secname, content in rep.sections:
            if showcapture != "all" and showcapture not in secname:
                continue
            self._tw.sep("-", secname)
            if content[-1:] == "\n":
                content = content[:-1]
            self._tw.line(content)

    def summary_stats(self):
        if self.verbosity < -1:
            return

        session_duration = time.time() - self._sessionstarttime
        (parts, main_color) = build_summary_stats_line(self.stats)
        line_parts = []

        display_sep = self.verbosity >= 0
        if display_sep:
            fullwidth = self._tw.fullwidth
        for text, markup in parts:
            with_markup = self._tw.markup(text, **markup)
            if display_sep:
                fullwidth += len(with_markup) - len(text)
            line_parts.append(with_markup)
        msg = ", ".join(line_parts)

        main_markup = {main_color: True}
        duration = " in {}".format(format_session_duration(session_duration))
        duration_with_markup = self._tw.markup(duration, **main_markup)
        if display_sep:
            fullwidth += len(duration_with_markup) - len(duration)
        msg += duration_with_markup

        if display_sep:
            markup_for_end_sep = self._tw.markup("", **main_markup)
            if markup_for_end_sep.endswith("\x1b[0m"):
                markup_for_end_sep = markup_for_end_sep[:-4]
            fullwidth += len(markup_for_end_sep)
            msg += markup_for_end_sep

        if display_sep:
            self.write_sep("=", msg, fullwidth=fullwidth, **main_markup)
        else:
            self.write_line(msg, **main_markup)

    def short_test_summary(self) -> None:
        if not self.reportchars:
            return

        def show_simple(stat, lines: List[str]) -> None:
            failed = self.stats.get(stat, [])
            if not failed:
                return
            termwidth = self.writer.fullwidth
            config = self.config
            for rep in failed:
                line = _get_line_with_reprcrash_message(config, rep, termwidth)
                lines.append(line)

        def show_xfailed(lines: List[str]) -> None:
            xfailed = self.stats.get("xfailed", [])
            for rep in xfailed:
                verbose_word = rep._get_verbose_word(self.config)
                pos = _get_pos(self.config, rep)
                lines.append("{} {}".format(verbose_word, pos))
                reason = rep.wasxfail
                if reason:
                    lines.append("  " + str(reason))

        def show_xpassed(lines: List[str]) -> None:
            xpassed = self.stats.get("xpassed", [])
            for rep in xpassed:
                verbose_word = rep._get_verbose_word(self.config)
                pos = _get_pos(self.config, rep)
                reason = rep.wasxfail
                lines.append("{} {} {}".format(verbose_word, pos, reason))

        def show_skipped(lines: List[str]) -> None:
            skipped = self.stats.get("skipped", [])
            fskips = _folded_skips(skipped) if skipped else []
            if not fskips:
                return
            verbose_word = skipped[0]._get_verbose_word(self.config)
            for num, fspath, lineno, reason in fskips:
                if reason.startswith("Skipped: "):
                    reason = reason[9:]
                if lineno is not None:
                    lines.append(
                        "%s [%d] %s:%d: %s"
                        % (verbose_word, num, fspath, lineno, reason)
                    )
                else:
                    lines.append("%s [%d] %s: %s" % (verbose_word, num, fspath, reason))

        REPORTCHAR_ACTIONS = {
            "x": show_xfailed,
            "X": show_xpassed,
            "f": partial(show_simple, "failed"),
            "F": partial(show_simple, "failed"),
            "s": show_skipped,
            "S": show_skipped,
            "p": partial(show_simple, "passed"),
            "E": partial(show_simple, "error"),
        }  # type: Mapping[str, Callable[[List[str]], None]]

        lines = []  # type: List[str]
        for char in self.reportchars:
            action = REPORTCHAR_ACTIONS.get(char)
            if action:  # skipping e.g. "P" (passed with output) here.
                action(lines)

        if lines:
            self.write_sep("=", "short test summary info")
            for line in lines:
                self.write_line(line)


def _get_pos(config, rep):
    nodeid = config.cwd_relative_nodeid(rep.nodeid)
    return nodeid


def _get_line_with_reprcrash_message(config, rep, termwidth):
    """Get summary line for a report, trying to add reprcrash message."""
    from wcwidth import wcswidth

    verbose_word = rep._get_verbose_word(config)
    pos = _get_pos(config, rep)

    line = "{} {}".format(verbose_word, pos)
    len_line = wcswidth(line)
    ellipsis, len_ellipsis = "...", 3
    if len_line > termwidth - len_ellipsis:
        # No space for an additional message.
        return line

    try:
        msg = rep.longrepr.reprcrash.message
    except AttributeError:
        pass
    else:
        # Only use the first line.
        i = msg.find("\n")
        if i != -1:
            msg = msg[:i]
        len_msg = wcswidth(msg)

        sep, len_sep = " - ", 3
        max_len_msg = termwidth - len_line - len_sep
        if max_len_msg >= len_ellipsis:
            if len_msg > max_len_msg:
                max_len_msg -= len_ellipsis
                msg = msg[:max_len_msg]
                while wcswidth(msg) > max_len_msg:
                    msg = msg[:-1]
                msg += ellipsis
            line += sep + msg
    return line


def _folded_skips(skipped):
    d = {}
    for event in skipped:
        key = event.longrepr
        assert len(key) == 3, (event, key)
        keywords = getattr(event, "keywords", {})
        # folding reports with global pytestmark variable
        # this is workaround, because for now we cannot identify the scope of a skip marker
        # TODO: revisit after marks scope would be fixed
        if (
            event.when == "setup"
            and "skip" in keywords
            and "pytestmark" not in keywords
        ):
            key = (key[0], None, key[2])
        d.setdefault(key, []).append(event)
    values = []
    for key, events in d.items():
        values.append((len(events),) + key)
    return values


_color_for_type = {
    "failed": "red",
    "error": "red",
    "warnings": "yellow",
    "passed": "green",
}
_color_for_type_default = "yellow"


def _make_plural(count, noun):
    # No need to pluralize words such as `failed` or `passed`.
    if noun not in ["error", "warnings"]:
        return count, noun

    # The `warnings` key is plural. To avoid API breakage, we keep it that way but
    # set it to singular here so we can determine plurality in the same way as we do
    # for `error`.
    noun = noun.replace("warnings", "warning")

    return count, noun + "s" if count != 1 else noun


def _get_main_color(stats) -> Tuple[str, List[str]]:
    known_types = (
        "failed passed skipped deselected xfailed xpassed warnings error".split()
    )
    unknown_type_seen = False
    for found_type in stats:
        if found_type not in known_types:
            if found_type:  # setup/teardown reports have an empty key, ignore them
                known_types.append(found_type)
                unknown_type_seen = True

    # main color
    if "failed" in stats or "error" in stats:
        main_color = "red"
    elif "warnings" in stats or unknown_type_seen:
        main_color = "yellow"
    elif "passed" in stats:
        main_color = "green"
    else:
        main_color = "yellow"

    return main_color, known_types


def build_summary_stats_line(stats):
    main_color, known_types = _get_main_color(stats)

    parts = []
    for key in known_types:
        reports = stats.get(key, None)
        if reports:
            count = sum(
                1 for rep in reports if getattr(rep, "count_towards_summary", True)
            )
            color = _color_for_type.get(key, _color_for_type_default)
            markup = {color: True, "bold": color == main_color}
            parts.append(("%d %s" % _make_plural(count, key), markup))

    if not parts:
        parts = [("no tests ran", {_color_for_type_default: True})]

    return parts, main_color


def _plugin_nameversions(plugininfo) -> List[str]:
    values = []  # type: List[str]
    for plugin, dist in plugininfo:
        # gets us name and version!
        name = "{dist.project_name}-{dist.version}".format(dist=dist)
        # questionable convenience, but it keeps things short
        if name.startswith("pytest-"):
            name = name[7:]
        # we decided to print python package names
        # they can have more than one plugin
        if name not in values:
            values.append(name)
    return values


def format_session_duration(seconds: float) -> str:
    """Format the given seconds in a human readable manner to show in the final summary"""
    if seconds < 60:
        return "{:.2f}s".format(seconds)
    else:
        dt = datetime.timedelta(seconds=int(seconds))
        return "{:.2f}s ({})".format(seconds, dt)
