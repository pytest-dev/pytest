# mypy: allow-untyped-defs
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from typing import Literal
import warnings

from _pytest.config import Config
from _pytest.config import parse_warning_filter
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.stash import StashKey
from _pytest.terminal import TerminalReporter
from _pytest.tracemalloc import tracemalloc_message
import pytest


# Filters that user code added while an earlier catching context was active
# (initial conftest import, collection). Re-applied in later catching contexts
# so module-level warnings.filterwarnings() is not discarded (#2430, #13485).
_persisted_filters_key = StashKey[list[Any]]()


def _copy_filters() -> list[Any]:
    return list(warnings.filters)


def _prepend_filters(filters: list[Any]) -> None:
    if filters:
        warnings.filters[:0] = filters


def _filters_added(before: list[Any], after: list[Any]) -> list[Any]:
    return [f for f in after if f not in before]


@contextmanager
def catch_warnings_for_item(
    config: Config,
    ihook,
    when: Literal["config", "collect", "runtest"],
    item: Item | None,
    *,
    record: bool = True,
    persist_new_filters: bool = False,
) -> Generator[None]:
    """Context manager that catches warnings generated in the contained execution block.

    ``item`` can be None if we are not in the context of an item execution.

    Each warning captured triggers the ``pytest_warning_recorded`` hook.

    If ``persist_new_filters`` is true, filters installed by the block (for
    example ``warnings.filterwarnings`` in a collected module) are kept and
    re-applied in later catching contexts.
    """
    added: list[Any] = []
    with config._catch_configured_warnings(record=record) as log:
        persisted = config.stash.get(_persisted_filters_key, None)
        if persisted:
            _prepend_filters(persisted)
        # apply filters from "filterwarnings" marks
        nodeid = "" if item is None else item.nodeid
        if item is not None:
            for mark in item.iter_markers(name="filterwarnings"):
                for arg in mark.args:
                    warnings.filterwarnings(*parse_warning_filter(arg, escape=False))

        before = _copy_filters() if persist_new_filters else []
        try:
            yield
        finally:
            if persist_new_filters:
                added = _filters_added(before, _copy_filters())
                if added:
                    prev = config.stash.get(_persisted_filters_key, [])
                    config.stash[_persisted_filters_key] = added + [
                        f for f in prev if f not in added
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
    # Promote newly added filters into the enclosing warnings context.
    _prepend_filters(added)


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
        config=config,
        ihook=config.hook,
        when="collect",
        item=None,
        persist_new_filters=True,
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
        config=early_config,
        ihook=early_config.hook,
        when="config",
        item=None,
        persist_new_filters=True,
    ):
        return (yield)


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers",
        "filterwarnings(warning): add a warning filter to the given test. "
        "see https://docs.pytest.org/en/stable/how-to/capture-warnings.html#pytest-mark-filterwarnings ",
    )
