"""Builtin plugin that adds subtests support."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Mapping
from contextlib import AbstractContextManager
from contextlib import contextmanager
from contextlib import ExitStack
from contextlib import nullcontext
import dataclasses
import time
from types import TracebackType
from typing import Any
from typing import TYPE_CHECKING

import pluggy

from _pytest._code import ExceptionInfo
from _pytest._io.saferepr import saferepr
from _pytest.capture import CaptureFixture
from _pytest.capture import FDCapture
from _pytest.capture import SysCapture
from _pytest.config import Config
from _pytest.config import hookimpl
from _pytest.config.argparsing import Parser
from _pytest.deprecated import check_ispytest
from _pytest.fixtures import fixture
from _pytest.fixtures import SubRequest
from _pytest.logging import catching_logs
from _pytest.logging import LogCaptureHandler
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.runner import check_interactive_exception
from _pytest.stash import StashKey


if TYPE_CHECKING:
    from typing_extensions import Self


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("subtests")
    group.addoption(
        "--no-subtests-shortletter",
        action="store_true",
        dest="no_subtests_shortletter",
        default=False,
        help="Disables subtest output 'dots' in non-verbose mode (EXPERIMENTAL)",
    )
    group.addoption(
        "--no-subtests-reports",
        action="store_true",
        dest="no_subtests_reports",
        default=False,
        help="Disables subtest output unless it's a failed subtest (EXPERIMENTAL)",
    )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class SubtestContext:
    """The values passed to Subtests.test() that are included in the test report."""

    msg: str | None
    kwargs: Mapping[str, Any]

    def _to_json(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def _from_json(cls, d: dict[str, Any]) -> Self:
        return cls(msg=d["msg"], kwargs=d["kwargs"])


@dataclasses.dataclass(init=False)
class SubtestReport(TestReport):
    context: SubtestContext

    @property
    def head_line(self) -> str:
        _, _, domain = self.location
        return f"{domain} {self._sub_test_description()}"

    def _sub_test_description(self) -> str:
        parts = []
        if self.context.msg is not None:
            parts.append(f"[{self.context.msg}]")
        if self.context.kwargs:
            params_desc = ", ".join(
                f"{k}={saferepr(v)}" for (k, v) in self.context.kwargs.items()
            )
            parts.append(f"({params_desc})")
        return " ".join(parts) or "(<subtest>)"

    def _to_json(self) -> dict[str, Any]:
        data = super()._to_json()
        del data["context"]
        data["_report_type"] = "SubTestReport"
        data["_subtest.context"] = self.context._to_json()
        return data

    @classmethod
    def _from_json(cls, reportdict: dict[str, Any]) -> SubtestReport:
        report = super()._from_json(reportdict)
        report.context = SubtestContext._from_json(reportdict["_subtest.context"])
        return report

    @classmethod
    def _from_test_report(
        cls, test_report: TestReport, context: SubtestContext
    ) -> Self:
        result = super()._from_json(test_report._to_json())
        result.context = context
        return result


@fixture
def subtests(request: SubRequest) -> Subtests:
    """Provides subtests functionality."""
    capmam = request.node.config.pluginmanager.get_plugin("capturemanager")
    if capmam is not None:
        suspend_capture_ctx = capmam.global_and_fixture_disabled
    else:
        suspend_capture_ctx = nullcontext
    return Subtests(request.node.ihook, suspend_capture_ctx, request, _ispytest=True)


class Subtests:
    """Subtests fixture, enables declaring subtests inside test functions via the :meth:`test` method."""

    def __init__(
        self,
        ihook: pluggy.HookRelay,
        suspend_capture_ctx: Callable[[], AbstractContextManager[None]],
        request: SubRequest,
        *,
        _ispytest: bool = False,
    ) -> None:
        check_ispytest(_ispytest)
        self._ihook = ihook
        self._suspend_capture_ctx = suspend_capture_ctx
        self._request = request

    def test(
        self,
        msg: str | None = None,
        **kwargs: Any,
    ) -> _SubTestContextManager:
        """
        Context manager for subtests, capturing exceptions raised inside the subtest scope and
        reporting assertion failures and errors individually.

        Usage
        -----

        .. code-block:: python

            def test(subtests):
                for i in range(5):
                    with subtests.test("custom message", i=i):
                        assert i % 2 == 0

        :param msg:
            If given, the message will be shown in the test report in case of subtest failure.

        :param kwargs:
            Arbitrary values that are also added to the subtest report.
        """
        return _SubTestContextManager(
            self._ihook,
            msg,
            kwargs,
            request=self._request,
            suspend_capture_ctx=self._suspend_capture_ctx,
            config=self._request.config,
        )


@dataclasses.dataclass
class _SubTestContextManager:
    """
    Context manager for subtests, capturing exceptions raised inside the subtest scope and handling
    them through the pytest machinery.
    """

    # Note: initially the logic for this context manager was implemented directly
    # in Subtests.test() as a @contextmanager, however, it is not possible to control the output fully when
    # exiting from it due to an exception when in `--exitfirst` mode, so this was refactored into an
    # explicit context manager class (pytest-dev/pytest-subtests#134).

    ihook: pluggy.HookRelay
    msg: str | None
    kwargs: dict[str, Any]
    suspend_capture_ctx: Callable[[], AbstractContextManager[None]]
    request: SubRequest
    config: Config

    def __enter__(self) -> None:
        __tracebackhide__ = True

        self._start = time.time()
        self._precise_start = time.perf_counter()
        self._exc_info = None

        self._exit_stack = ExitStack()
        self._captured_output = self._exit_stack.enter_context(
            capturing_output(self.request)
        )
        self._captured_logs = self._exit_stack.enter_context(
            capturing_logs(self.request)
        )

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        __tracebackhide__ = True
        try:
            if exc_val is not None:
                exc_info = ExceptionInfo.from_exception(exc_val)
            else:
                exc_info = None
        finally:
            self._exit_stack.close()

        precise_stop = time.perf_counter()
        duration = precise_stop - self._precise_start
        stop = time.time()

        call_info = CallInfo[None](
            None,
            exc_info,
            start=self._start,
            stop=stop,
            duration=duration,
            when="call",
            _ispytest=True,
        )
        report = self.ihook.pytest_runtest_makereport(
            item=self.request.node, call=call_info
        )
        sub_report = SubtestReport._from_test_report(
            report, SubtestContext(msg=self.msg, kwargs=self.kwargs.copy())
        )

        if sub_report.failed:
            failed_subtests = self.config.stash[failed_subtests_key]
            failed_subtests[self.request.node.nodeid] += 1

        self._captured_output.update_report(sub_report)
        self._captured_logs.update_report(sub_report)

        with self.suspend_capture_ctx():
            self.ihook.pytest_runtest_logreport(report=sub_report)

        if check_interactive_exception(call_info, sub_report):
            self.ihook.pytest_exception_interact(
                node=self.request.node, call=call_info, report=sub_report
            )

        if exc_val is not None:
            if self.request.session.shouldfail:
                return False
        return True


@contextmanager
def capturing_output(request: SubRequest) -> Iterator[Captured]:
    option = request.config.getoption("capture", None)

    capman = request.config.pluginmanager.getplugin("capturemanager")
    if getattr(capman, "_capture_fixture", None):
        # capsys or capfd are active, subtest should not capture.
        fixture = None
    elif option == "sys":
        fixture = CaptureFixture(SysCapture, request, _ispytest=True)
    elif option == "fd":
        fixture = CaptureFixture(FDCapture, request, _ispytest=True)
    else:
        fixture = None

    if fixture is not None:
        fixture._start()

    captured = Captured()
    try:
        yield captured
    finally:
        if fixture is not None:
            out, err = fixture.readouterr()
            fixture.close()
            captured.out = out
            captured.err = err


@contextmanager
def capturing_logs(
    request: SubRequest,
) -> Iterator[CapturedLogs | NullCapturedLogs]:
    logging_plugin = request.config.pluginmanager.getplugin("logging-plugin")
    if logging_plugin is None:
        yield NullCapturedLogs()
    else:
        handler = LogCaptureHandler()
        handler.setFormatter(logging_plugin.formatter)

        captured_logs = CapturedLogs(handler)
        with catching_logs(handler):
            yield captured_logs


@dataclasses.dataclass
class Captured:
    out: str = ""
    err: str = ""

    def update_report(self, report: TestReport) -> None:
        if self.out:
            report.sections.append(("Captured stdout call", self.out))
        if self.err:
            report.sections.append(("Captured stderr call", self.err))


@dataclasses.dataclass
class CapturedLogs:
    handler: LogCaptureHandler

    def update_report(self, report: TestReport) -> None:
        captured_log = self.handler.stream.getvalue()
        if captured_log:
            report.sections.append(("Captured log call", captured_log))


class NullCapturedLogs:
    def update_report(self, report: TestReport) -> None:
        pass


def pytest_report_to_serializable(report: TestReport) -> dict[str, Any] | None:
    if isinstance(report, SubtestReport):
        return report._to_json()
    return None


def pytest_report_from_serializable(data: dict[str, Any]) -> SubtestReport | None:
    if data.get("_report_type") == "SubTestReport":
        return SubtestReport._from_json(data)
    return None


# Dict of nodeid -> number of failed subtests.
# Used to fail top-level tests that passed but contain failed subtests.
failed_subtests_key = StashKey[defaultdict[str, int]]()


def pytest_configure(config: Config) -> None:
    config.stash[failed_subtests_key] = defaultdict(lambda: 0)


@hookimpl(tryfirst=True)
def pytest_report_teststatus(
    report: TestReport,
    config: Config,
) -> tuple[str, str, str | Mapping[str, bool]] | None:
    if report.when != "call":
        return None

    if isinstance(report, SubtestReport):
        outcome = report.outcome
        description = report._sub_test_description()
        no_output = ("", "", "")

        if hasattr(report, "wasxfail"):
            if config.option.no_subtests_reports and outcome != "skipped":
                return no_output
            elif outcome == "skipped":
                category = "xfailed"
                short = "y"  # x letter is used for regular xfail, y for subtest xfail
                status = "SUBXFAIL"
            elif outcome == "passed":
                category = "xpassed"
                short = "Y"  # X letter is used for regular xpass, Y for subtest xpass
                status = "SUBXPASS"
            else:
                # This should not normally happen, unless some plugin is setting wasxfail without
                # the correct outcome. Pytest expects the call outcome to be either skipped or
                # passed in case of xfail.
                # Let's pass this report to the next hook.
                return None
            short = "" if config.option.no_subtests_shortletter else short
            return f"subtests {category}", short, f"{description} {status}"

        if config.option.no_subtests_reports and outcome != "failed":
            return no_output
        elif report.passed:
            short = "" if config.option.no_subtests_shortletter else ","
            return f"subtests {outcome}", short, f"{description} SUBPASSED"
        elif report.skipped:
            short = "" if config.option.no_subtests_shortletter else "-"
            return outcome, short, f"{description} SUBSKIPPED"
        elif outcome == "failed":
            short = "" if config.option.no_subtests_shortletter else "u"
            return outcome, short, f"{description} SUBFAILED"
    else:
        failed_subtests_count = config.stash[failed_subtests_key][report.nodeid]
        # Top-level test, fail it it contains failed subtests and it has passed.
        if report.passed and failed_subtests_count > 0:
            report.outcome = "failed"
            suffix = "s" if failed_subtests_count > 1 else ""
            report.longrepr = f"Contains {failed_subtests_count} failed subtest{suffix}"

    return None
