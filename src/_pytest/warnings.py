# mypy: allow-untyped-defs
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
import dataclasses
from typing import Literal
import warnings

from _pytest._code.code import ExceptionRepr
from _pytest.config import Config
from _pytest.config import ExitCode
from _pytest.config import parse_warning_filter
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.outcomes import fail
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.stash import StashKey
from _pytest.terminal import TerminalReporter
from _pytest.tracemalloc import tracemalloc_message
from _pytest.warning_late_error import install_warning_filter
from _pytest.warning_late_error import LATE_WARNING_ERRORS_STAT
from _pytest.warning_late_error import late_warning_state_key
from _pytest.warning_late_error import LateWarning
from _pytest.warning_late_error import LateWarningState
from _pytest.warning_late_error import select_late_warnings
import pytest


@contextmanager
def catch_warnings_for_item(
    config: Config,
    ihook,
    when: Literal["config", "collect", "runtest"],
    item: Item | None,
    *,
    record: bool = True,
) -> Generator[None]:
    """Context manager that catches warnings generated in the contained execution block.

    ``item`` can be None if we are not in the context of an item execution.

    Each warning captured triggers the ``pytest_warning_recorded`` hook.
    """
    with config._catch_configured_warnings(record=record) as log:
        # apply filters from "filterwarnings" marks
        nodeid = "" if item is None else item.nodeid
        state = config.stash.setdefault(late_warning_state_key, LateWarningState())
        if item is not None:
            for mark in item.iter_markers(name="filterwarnings"):
                for arg in mark.args:
                    parsed = parse_warning_filter(arg, escape=False)
                    install_warning_filter(parsed)
                    state.filters.append(parsed)

        # record=True means log is not None; mypy can't infer that.
        recording = _Recording(log=log, nodeid=nodeid) if log is not None else None
        recordings = config.stash.setdefault(_recordings_key, [])
        if recording is not None:
            recordings.append(recording)
        try:
            yield
        finally:
            if recording is not None:
                recordings.remove(recording)
                # Anything not already drained by a runtest phase boundary can
                # only be reported at the end of the session.
                state.collected.extend(_drain(config, recording))

            if record:
                # mypy can't infer that record=True means log is not None; help it.
                assert log is not None

                for warning_message in log:
                    ihook.pytest_warning_recorded.call_historic(
                        kwargs=dict(
                            warning_message=warning_message,
                            nodeid=nodeid,
                            when=when,
                            location=None,
                        )
                    )


@dataclasses.dataclass
class _Recording:
    """A live ``catch_warnings(record=True)`` log and how much of it was drained."""

    log: list[warnings.WarningMessage]
    nodeid: str
    cursor: int = 0


#: Active recordings, innermost last.
_recordings_key: StashKey[list[_Recording]] = StashKey()

#: Late warnings of a runtest phase that raised, keyed by phase, waiting for
#: that phase's report so they can be attached to its failure.
_phase_late_warnings_key: StashKey[dict[str, list[LateWarning]]] = StashKey()


def _drain(config: Config, recording: _Recording) -> list[LateWarning]:
    """Take the warnings recorded since the last drain that must error later."""
    state = config.stash[late_warning_state_key]
    late = select_late_warnings(
        recording.log[recording.cursor :], state.filters, recording.nodeid
    )
    recording.cursor = len(recording.log)
    return late


def _describe(late: list[LateWarning]) -> str:
    plural = "s" if len(late) > 1 else ""
    lines = "\n".join(w.format() for w in late)
    return f"{len(late)} warning{plural} matched an 'error_later' filter:\n{lines}"


def _late_warnings_phase(item: Item, when: str) -> Generator[None, object, object]:
    """Wrap a runtest phase so its late warnings are reported against it.

    Draining in a ``finally``-style wrapper rather than in a ``trylast`` hook
    makes sure a phase that raised is drained too; otherwise its warnings would
    leak into the next phase and be reported there a second time.
    """
    __tracebackhide__ = True
    config = item.config
    try:
        result = yield
    except BaseException:
        if late := _drain_innermost(config):
            # The phase already failed; pytest_runtest_makereport adds them to
            # that failure instead of failing a second time.
            item.stash.setdefault(_phase_late_warnings_key, {})[when] = late
        raise
    if late := _drain_innermost(config):
        # The warning's own location is in the message; the frames between
        # here and the emitting code are pytest's, so there is no traceback
        # worth showing.
        fail(_describe(late), pytrace=False)
    return result


def _drain_innermost(config: Config) -> list[LateWarning]:
    recordings = config.stash.get(_recordings_key, None)
    if not recordings:
        return []
    return _drain(config, recordings[-1])


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_setup(item: Item) -> Generator[None, object, object]:
    return (yield from _late_warnings_phase(item, "setup"))


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_call(item: Item) -> Generator[None, object, object]:
    return (yield from _late_warnings_phase(item, "call"))


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_teardown(item: Item) -> Generator[None, object, object]:
    return (yield from _late_warnings_phase(item, "teardown"))


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(
    item: Item, call: CallInfo[None]
) -> Generator[None, TestReport, TestReport]:
    report = yield
    late = item.stash.get(_phase_late_warnings_key, {}).pop(call.when, None)
    if late:
        if report.failed:
            _add_to_failure(report, _describe(late))
        else:
            # Skipped or xfailed: there is no failure to add them to, and
            # turning the outcome into one would defeat the marker.
            item.config.stash[late_warning_state_key].collected.extend(late)
    return report


def _add_to_failure(report: TestReport, text: str) -> None:
    longrepr = report.longrepr
    if isinstance(longrepr, ExceptionRepr):
        longrepr.addsection(LATE_WARNING_ERRORS_STAT, text)
    elif isinstance(longrepr, str):
        report.longrepr = f"{longrepr}\n\n{text}"
    else:
        report.sections.append((LATE_WARNING_ERRORS_STAT, text))


def warning_record_to_str(warning_message: warnings.WarningMessage) -> str:
    """Convert a warnings.WarningMessage to a string."""
    return warnings.formatwarning(
        str(warning_message.message),
        warning_message.category,
        warning_message.filename,
        warning_message.lineno,
        warning_message.line,
    ) + tracemalloc_message(warning_message.source)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_protocol(item: Item) -> Generator[None, object, object]:
    with catch_warnings_for_item(
        config=item.config, ihook=item.ihook, when="runtest", item=item
    ):
        return (yield)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_collection(session: Session) -> Generator[None, object, object]:
    config = session.config
    with catch_warnings_for_item(
        config=config, ihook=config.hook, when="collect", item=None
    ):
        return (yield)


@pytest.hookimpl(wrapper=True)
def pytest_terminal_summary(
    terminalreporter: TerminalReporter,
) -> Generator[None]:
    config = terminalreporter.config
    try:
        with catch_warnings_for_item(
            config=config, ihook=config.hook, when="config", item=None
        ):
            return (yield)
    finally:
        if terminalreporter._session is not None:
            _settle_late_warnings(terminalreporter._session)
        _write_late_warnings_section(terminalreporter)


@pytest.hookimpl(wrapper=True)
def pytest_sessionfinish(session: Session) -> Generator[None]:
    config = session.config
    state = config.stash.setdefault(late_warning_state_key, LateWarningState())
    try:
        # The context drains on exit, so it has to be closed before settling:
        # otherwise warnings from other pytest_sessionfinish hooks are lost.
        with catch_warnings_for_item(
            config=config, ihook=config.hook, when="config", item=None
        ):
            return (yield)
    finally:
        _settle_late_warnings(session)
        # From here on there is nothing left to report into, so warnings are
        # shown the ordinary way instead of being collected and dropped.
        state.closed = True


def _settle_late_warnings(session: Session) -> None:
    """Count the late warnings no test phase could fail for, and fail the run.

    Those are the ones emitted outside a test phase, such as during collection,
    and the ones of a test that was skipped.
    """
    config = session.config
    state = config.stash.get(late_warning_state_key, None)
    if state is None or not state.collected:
        return
    terminalreporter: TerminalReporter | None = config.pluginmanager.getplugin(
        "terminalreporter"
    )
    if terminalreporter is not None:
        counted = len(terminalreporter.stats.get(LATE_WARNING_ERRORS_STAT, []))
        if new := state.collected[counted:]:
            terminalreporter._add_stats(LATE_WARNING_ERRORS_STAT, new)
    if session.exitstatus == ExitCode.OK:
        session.exitstatus = ExitCode.LATE_WARNING_ERROR


def _write_late_warnings_section(terminalreporter: TerminalReporter) -> None:
    state = terminalreporter.config.stash.get(late_warning_state_key, None)
    if state is None or not state.collected[state.reported :]:
        return
    terminalreporter.write_sep("=", LATE_WARNING_ERRORS_STAT, red=True, bold=True)
    for late in state.collected[state.reported :]:
        terminalreporter.write_line(late.format(with_nodeid=True))
    state.reported = len(state.collected)


@pytest.hookimpl(wrapper=True)
def pytest_load_initial_conftests(
    early_config: Config,
) -> Generator[None]:
    with catch_warnings_for_item(
        config=early_config, ihook=early_config.hook, when="config", item=None
    ):
        return (yield)


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers",
        "filterwarnings(warning): add a warning filter to the given test. "
        "see https://docs.pytest.org/en/stable/how-to/capture-warnings.html#pytest-mark-filterwarnings ",
    )
