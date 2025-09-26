from __future__ import annotations

from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterator
from collections.abc import Mapping
from contextlib import AbstractContextManager
from contextlib import contextmanager
from contextlib import ExitStack
from contextlib import nullcontext
import dataclasses
import time
from typing import Any
from typing import TYPE_CHECKING

import pluggy

from _pytest._code import ExceptionInfo
from _pytest.capture import CaptureFixture
from _pytest.capture import FDCapture
from _pytest.capture import SysCapture
from _pytest.config import Config
from _pytest.config import hookimpl
from _pytest.config.argparsing import Parser
from _pytest.fixtures import fixture
from _pytest.fixtures import SubRequest
from _pytest.logging import catching_logs
from _pytest.logging import LogCaptureHandler
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.runner import check_interactive_exception


if TYPE_CHECKING:
    from types import TracebackType
    from typing import Literal


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


@dataclasses.dataclass
class SubTestContext:
    """The values passed to SubTests.test() that are included in the test report."""

    msg: str | None
    kwargs: dict[str, Any]


@dataclasses.dataclass(init=False)
class SubTestReport(TestReport):
    context: SubTestContext

    @property
    def head_line(self) -> str:
        _, _, domain = self.location
        return f"{domain} {self.sub_test_description()}"

    def sub_test_description(self) -> str:
        parts = []
        if isinstance(self.context.msg, str):
            parts.append(f"[{self.context.msg}]")
        if self.context.kwargs:
            params_desc = ", ".join(
                f"{k}={v!r}" for (k, v) in sorted(self.context.kwargs.items())
            )
            parts.append(f"({params_desc})")
        return " ".join(parts) or "(<subtest>)"

    def _to_json(self) -> dict[str, Any]:
        data = super()._to_json()
        del data["context"]
        data["_report_type"] = "SubTestReport"
        data["_subtest.context"] = dataclasses.asdict(self.context)
        return data

    @classmethod
    def _from_json(cls, reportdict: dict[str, Any]) -> SubTestReport:
        report = super()._from_json(reportdict)
        context_data = reportdict["_subtest.context"]
        report.context = SubTestContext(
            msg=context_data["msg"], kwargs=context_data["kwargs"]
        )
        return report

    @classmethod
    def _from_test_report(cls, test_report: TestReport) -> SubTestReport:
        return super()._from_json(test_report._to_json())


@fixture
def subtests(request: SubRequest) -> Generator[SubTests, None, None]:
    """Provides subtests functionality."""
    capmam = request.node.config.pluginmanager.get_plugin("capturemanager")
    if capmam is not None:
        suspend_capture_ctx = capmam.global_and_fixture_disabled
    else:
        suspend_capture_ctx = nullcontext
    yield SubTests(request.node.ihook, suspend_capture_ctx, request)


# Note: cannot use a dataclass here because Sphinx insists on showing up the __init__ method in the documentation,
# even if we explicitly use :exclude-members: __init__.
class SubTests:
    """Subtests fixture, enables declaring subtests inside test functions via the :meth:`test` method."""

    def __init__(
        self,
        ihook: pluggy.HookRelay,
        suspend_capture_ctx: Callable[[], AbstractContextManager[None]],
        request: SubRequest,
    ) -> None:
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
                    with subtests.test(msg="custom message", i=i):
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
        )


@dataclasses.dataclass
class _SubTestContextManager:
    """
    Context manager for subtests, capturing exceptions raised inside the subtest scope and handling
    them through the pytest machinery.

    Note: initially this logic was implemented directly in SubTests.test() as a @contextmanager, however
    it is not possible to control the output fully when exiting from it due to an exception when
    in --exitfirst mode, so this was refactored into an explicit context manager class (pytest-dev/pytest-subtests#134).
    """

    ihook: pluggy.HookRelay
    msg: str | None
    kwargs: dict[str, Any]
    suspend_capture_ctx: Callable[[], AbstractContextManager[None]]
    request: SubRequest

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

        call_info = make_call_info(
            exc_info, start=self._start, stop=stop, duration=duration, when="call"
        )
        report = self.ihook.pytest_runtest_makereport(
            item=self.request.node, call=call_info
        )
        sub_report = SubTestReport._from_test_report(report)
        sub_report.context = SubTestContext(self.msg, self.kwargs.copy())

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


def make_call_info(
    exc_info: ExceptionInfo[BaseException] | None,
    *,
    start: float,
    stop: float,
    duration: float,
    when: Literal["collect", "setup", "call", "teardown"],
) -> CallInfo[Any]:
    return CallInfo(
        None,
        exc_info,
        start=start,
        stop=stop,
        duration=duration,
        when=when,
        _ispytest=True,
    )


@contextmanager
def capturing_output(request: SubRequest) -> Iterator[Captured]:
    option = request.config.getoption("capture", None)

    # capsys or capfd are active, subtest should not capture.
    capman = request.config.pluginmanager.getplugin("capturemanager")
    capture_fixture_active = getattr(capman, "_capture_fixture", None)

    if option == "sys" and not capture_fixture_active:
        fixture = CaptureFixture(SysCapture, request, _ispytest=True)
    elif option == "fd" and not capture_fixture_active:
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
        report.sections.append(("Captured log call", self.handler.stream.getvalue()))


class NullCapturedLogs:
    def update_report(self, report: TestReport) -> None:
        pass


def pytest_report_to_serializable(report: TestReport) -> dict[str, Any] | None:
    if isinstance(report, SubTestReport):
        return report._to_json()
    return None


def pytest_report_from_serializable(data: dict[str, Any]) -> SubTestReport | None:
    if data.get("_report_type") == "SubTestReport":
        return SubTestReport._from_json(data)
    return None


@hookimpl(tryfirst=True)
def pytest_report_teststatus(
    report: TestReport,
    config: Config,
) -> tuple[str, str, str | Mapping[str, bool]] | None:
    if report.when != "call" or not isinstance(report, SubTestReport):
        return None

    outcome = report.outcome
    description = report.sub_test_description()
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
            # the correct outcome. Pytest expects the call outcome to be either skipped or passed in case of xfail.
            # Let's pass this report to the next hook.
            return None
        short = "" if config.option.no_subtests_shortletter else short
        return f"subtests {category}", short, f"{description} {status}"

    if config.option.no_subtests_reports and outcome != "failed":
        return no_output
    elif report.passed:
        short = "" if config.option.no_subtests_shortletter else ","
        return f"subtests {outcome}", short, f"{description} SUBPASS"
    elif report.skipped:
        short = "" if config.option.no_subtests_shortletter else "-"
        return outcome, short, f"{description} SUBSKIP"
    elif outcome == "failed":
        short = "" if config.option.no_subtests_shortletter else "u"
        return outcome, short, f"{description} SUBFAIL"

    return None
