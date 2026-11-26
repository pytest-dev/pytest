# mypy: allow-untyped-defs
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
import sys
from typing import Literal
import warnings

from _pytest.config import Config
from _pytest.config import parse_warning_filter
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.nodes import MarkerOrder
from _pytest.terminal import TerminalReporter
from _pytest.tracemalloc import tracemalloc_message
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

    Doctests compare the example's stdout with the expected text. A common
    pattern points ``sys.stderr`` at ``sys.stdout`` so the warning text is
    part of that comparison, which is what :mod:`doctest` does. Recording
    replaces the display function, so the text never arrives. For a doctest
    item, record the warning and also write it to ``sys.stderr``.
    """
    with config._catch_configured_warnings(record=record) as log:
        # Private stdlib hook. catch_warnings installs it, and the
        # public showwarning wrapper does not run while recording.
        # On Python 3.14+ with context-aware warnings, catch_warnings
        # restores a contextvar and leaves this global alone, so put it
        # back ourselves or the wrapper keeps writing later warnings.
        saved_showwarnmsg_impl = None
        if record and _item_is_doctest(item):
            record_impl = warnings._showwarnmsg_impl  # type: ignore[attr-defined]

            def _record_and_emit(msg, _record=record_impl):
                _record(msg)
                _write_warning(msg)

            warnings._showwarnmsg_impl = _record_and_emit  # type: ignore[attr-defined]
            saved_showwarnmsg_impl = record_impl
        # apply filters from "filterwarnings" marks
        nodeid = "" if item is None else item.nodeid
        if item is not None:
            # The filter applied last wins, so apply the closest one last.
            for _node, mark in item._iter_markers_with_node(
                name="filterwarnings", order=MarkerOrder.FARTHEST_FIRST
            ):
                for arg in mark.args:
                    warnings.filterwarnings(*parse_warning_filter(arg, escape=False))

        try:
            yield
        finally:
            if saved_showwarnmsg_impl is not None:
                warnings._showwarnmsg_impl = saved_showwarnmsg_impl  # type: ignore[attr-defined]
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


def _write_warning(msg: warnings.WarningMessage) -> None:
    """Write a warning the way :func:`warnings.showwarning` does."""
    file = msg.file
    if file is None:
        file = sys.stderr
    if file is None:
        return
    # formatwarning() builds a new WarningMessage and drops source, so the
    # tracemalloc line stdlib doctest prints never appears. _formatwarnmsg
    # formats the message the display hook actually received.
    text = warnings._formatwarnmsg(msg)  # type: ignore[attr-defined]
    try:
        file.write(text)
    except OSError:
        # The stream (usually stderr) can be closed. Match the stdlib and drop it.
        pass


def _item_is_doctest(item: Item | None) -> bool:
    if item is None:
        return False
    # Imported lazily: this module is loaded before the doctest plugin.
    from _pytest.doctest import DoctestItem

    return isinstance(item, DoctestItem)


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
