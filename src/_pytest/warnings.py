# mypy: allow-untyped-defs
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
import re
from typing import cast
from typing import Literal
import warnings

from _pytest.config import Config
from _pytest.config import parse_warning_filter
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.terminal import TerminalReporter
from _pytest.tracemalloc import tracemalloc_message
import pytest


# Entries of ``warnings.filters``: (action, message, category, module, lineno).
_WarningsFilter = tuple[
    str,
    "re.Pattern[str] | None",
    "type[Warning] | tuple[type[Warning], ...]",
    "re.Pattern[str] | None",
    int,
]


def _warnings_filter_key(filter_item: _WarningsFilter) -> tuple[object, ...]:
    """Return a hashable identity for an entry in ``warnings.filters``.

    The message and module parts are compiled regular expressions which do
    not compare equal across compilations, so their pattern text is used.
    """
    action, message, category, module, lineno = filter_item
    return (
        action,
        getattr(message, "pattern", message),
        category,
        getattr(module, "pattern", module),
        lineno,
    )


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
    # Whether filters installed inside the contained block are re-applied
    # after the warnings catch context restores the previous filter list.
    # This is enabled for the phases where user code is imported or
    # configured, so that e.g. a module-level ``warnings.filterwarnings()``
    # call in a test module or conftest keeps applying during the test run
    # (#13485). During "runtest", per-test isolation takes precedence and
    # filters stay confined to the item.
    persist_filters = when in ("config", "collect")
    installed_filters: list[_WarningsFilter] = []
    with config._catch_configured_warnings(record=record) as log:
        # apply filters from "filterwarnings" marks
        nodeid = "" if item is None else item.nodeid
        if item is not None:
            for mark in item.iter_markers(name="filterwarnings"):
                for arg in mark.args:
                    warnings.filterwarnings(*parse_warning_filter(arg, escape=False))

        baseline_keys = (
            {_warnings_filter_key(f) for f in warnings.filters}
            if persist_filters
            else set()
        )

        try:
            yield
        finally:
            if persist_filters:
                installed_filters = [
                    f
                    for f in warnings.filters
                    if _warnings_filter_key(f) not in baseline_keys
                ]
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

    if persist_filters:
        # ``warnings.filters`` is always a real list at runtime.
        cast("list[_WarningsFilter]", warnings.filters)[:0] = installed_filters


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
    config.addinivalue_line(
        "markers",
        "filterwarnings(warning): add a warning filter to the given test. "
        "see https://docs.pytest.org/en/stable/how-to/capture-warnings.html#pytest-mark-filterwarnings ",
    )
