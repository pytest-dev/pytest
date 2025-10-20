# mypy: allow-untyped-defs
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextlib import ExitStack
import sys
from typing import Literal
import warnings

from _pytest.config import apply_warning_filters
from _pytest.config import Config
from _pytest.config import parse_warning_filter
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.stash import StashKey
from _pytest.terminal import TerminalReporter
from _pytest.tracemalloc import tracemalloc_message
import pytest


# StashKey for storing warning log on items
warning_captured_log_key = StashKey[list[warnings.WarningMessage]]()
# StashKey for tracking the index of the last dispatched warning
warning_last_dispatched_idx_key = StashKey[int]()


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
    config_filters = config.getini("filterwarnings")
    cmdline_filters = config.known_args_namespace.pythonwarnings or []
    with warnings.catch_warnings(record=record) as log:
        if not sys.warnoptions:
            # If user is not explicitly configuring warning filters, show deprecation warnings by default (#2908).
            warnings.filterwarnings("always", category=DeprecationWarning)
            warnings.filterwarnings("always", category=PendingDeprecationWarning)

        warnings.filterwarnings("error", category=pytest.PytestRemovedIn9Warning)

        apply_warning_filters(config_filters, cmdline_filters)

        # apply filters from "filterwarnings" marks
        nodeid = "" if item is None else item.nodeid
        if item is not None:
            for mark in item.iter_markers(name="filterwarnings"):
                for arg in mark.args:
                    warnings.filterwarnings(*parse_warning_filter(arg, escape=False))
            # Store the warning log on the item so it can be accessed during reporting
            if record and log is not None:
                item.stash[warning_captured_log_key] = log

        yield

        # For config and collect phases, dispatch warnings immediately.
        # For runtest phase, warnings are dispatched from pytest_runtest_makereport.
        if when != "runtest" and record:
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


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: Item, call: CallInfo[None]
) -> Generator[None, TestReport, None]:
    """Process warnings from stash and dispatch pytest_warning_recorded hooks."""
    outcome = yield
    report: TestReport = outcome.get_result()

    warning_log = item.stash.get(warning_captured_log_key, None)
    if warning_log:
        # Set has_warnings attribute on call phase for xdist compatibility and yellow coloring
        if report.when == "call":
            report.has_warnings = True  # type: ignore[attr-defined]

        # Only dispatch warnings that haven't been dispatched yet
        last_idx = item.stash.get(warning_last_dispatched_idx_key, -1)
        for idx in range(last_idx + 1, len(warning_log)):
            warning_message = warning_log[idx]
            item.ihook.pytest_warning_recorded.call_historic(
                kwargs=dict(
                    warning_message=warning_message,
                    nodeid=item.nodeid,
                    when="runtest",
                    location=None,
                )
            )
        # Update the last dispatched index
        item.stash[warning_last_dispatched_idx_key] = len(warning_log) - 1


@pytest.hookimpl(tryfirst=True)
def pytest_report_teststatus(report: TestReport, config: Config):
    """Provide yellow markup for passed tests that have warnings."""
    if report.passed and report.when == "call":
        if hasattr(report, "has_warnings") and report.has_warnings:
            # Return (category, shortletter, verbose_word) with yellow markup
            return "passed", ".", ("PASSED", {"yellow": True})


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
    with catch_warnings_for_item(
        config=config, ihook=config.hook, when="config", item=None
    ):
        return (yield)


@pytest.hookimpl(wrapper=True)
def pytest_sessionfinish(session: Session) -> Generator[None]:
    config = session.config
    with catch_warnings_for_item(
        config=config, ihook=config.hook, when="config", item=None
    ):
        return (yield)


@pytest.hookimpl(wrapper=True)
def pytest_load_initial_conftests(
    early_config: Config,
) -> Generator[None]:
    with catch_warnings_for_item(
        config=early_config, ihook=early_config.hook, when="config", item=None
    ):
        return (yield)


def pytest_configure(config: Config) -> None:
    with ExitStack() as stack:
        stack.enter_context(
            catch_warnings_for_item(
                config=config,
                ihook=config.hook,
                when="config",
                item=None,
                # this disables recording because the terminalreporter has
                # finished by the time it comes to reporting logged warnings
                # from the end of config cleanup. So for now, this is only
                # useful for setting a warning filter with an 'error' action.
                record=False,
            )
        )
        config.addinivalue_line(
            "markers",
            "filterwarnings(warning): add a warning filter to the given test. "
            "see https://docs.pytest.org/en/stable/how-to/capture-warnings.html#pytest-mark-filterwarnings ",
        )
        config.add_cleanup(stack.pop_all().close)
