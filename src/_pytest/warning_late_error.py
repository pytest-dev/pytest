"""Warnings that become errors after the fact.

The ``error`` warning filter raises at the ``warnings.warn()`` call site, which
aborts whatever the code under test was doing halfway through and reports the
failure at the frame that emitted the warning. The ``error_later`` action is
pytest's alternative: the warning still becomes an error, but it is recorded
first, the code under test runs to completion, and pytest raises afterwards at a
defined point.

This module holds the pieces both :mod:`_pytest.config` and :mod:`_pytest.warnings`
need, so that neither has to import the other.
"""

from __future__ import annotations

from collections.abc import Iterable
import dataclasses
import re
import sys
from typing import Final
from typing import Literal
import warnings

from _pytest.stash import StashKey


#: Filter action implemented by pytest rather than by the :mod:`warnings` module.
ERROR_LATER_ACTION: Final = "error_later"

#: Key of the terminal reporter's stats, and so of the final summary line.
LATE_WARNING_ERRORS_STAT: Final = "late warning errors"

#: A parsed warning filter: action, message regex, category, module regex, lineno.
WarningFilter = tuple[
    "warnings._ActionKind | Literal['error_later']", str, type[Warning], str, int
]


@dataclasses.dataclass(frozen=True)
class LateWarning:
    """A warning that matched an ``error_later`` filter, rendered down to plain data.

    Everything is pre-rendered so that no warning instance, and nothing the
    warning referenced, is kept alive until the report is written, and so that
    it can travel from a pytest-xdist worker to the controller.
    """

    message: str
    category: str
    filename: str
    lineno: int
    nodeid: str

    def format(self, *, with_nodeid: bool = False) -> str:
        location = f"{self.filename}:{self.lineno}"
        if with_nodeid and self.nodeid:
            location = f"{location} ({self.nodeid})"
        return f"{location}: {self.category}: {self.message}"


@dataclasses.dataclass
class LateWarningState:
    """Per-session state for the ``error_later`` action."""

    #: Filters pytest applied to the current ``catch_warnings`` context, in
    #: application order. Later entries take precedence, as in ``warnings.filters``.
    filters: list[WarningFilter] = dataclasses.field(default_factory=list)
    #: Warnings held over to the end of the session.
    collected: list[LateWarning] = dataclasses.field(default_factory=list)
    #: How many of ``collected`` have been written to the terminal.
    reported: int = 0
    #: Set once the session can no longer report; warnings after that point
    #: are shown the ordinary way instead of being collected and lost.
    closed: bool = False


late_warning_state_key: StashKey[LateWarningState] = StashKey()


def install_warning_filter(filter_: WarningFilter) -> None:
    """Apply a parsed filter to the :mod:`warnings` module.

    ``error_later`` is not an action the :mod:`warnings` module knows about; it is
    installed as ``always`` so that the warning is recorded rather than raised,
    and :func:`should_error_later` decides afterwards what to do with it.
    """
    action, message, category, module, lineno = filter_
    if action == ERROR_LATER_ACTION:
        warnings.filterwarnings("always", message, category, module, lineno)
    else:
        warnings.filterwarnings(action, message, category, module, lineno)


def _module_name(filename: str) -> str:
    """Best-effort ``__name__`` of the module a warning was emitted from.

    The :mod:`warnings` module matches the module field against the emitting
    frame's ``__name__``, which a recorded warning does not carry. Recover it
    from the loaded modules, and otherwise derive it from the filename the way
    :func:`warnings.warn_explicit` does when it is given no module.
    """
    for name, module in list(sys.modules.items()):
        if getattr(module, "__file__", None) == filename:
            return name
    name = filename or "<unknown>"
    if name[-3:].lower() == ".py":
        name = name[:-3]
    return name


def should_error_later(
    warning_message: warnings.WarningMessage, filters: list[WarningFilter]
) -> bool:
    """Whether a recorded warning matched an ``error_later`` filter.

    ``filters`` is in application order, so it is walked backwards: the last
    filter applied has the highest precedence, exactly as in ``warnings.filters``,
    and each field is matched the way :func:`warnings.filterwarnings` matches it.
    """
    text = str(warning_message.message)
    for action, message, category, module, lineno in reversed(filters):
        if not issubclass(warning_message.category, category):
            continue
        if message and not re.compile(message, re.IGNORECASE).match(text):
            continue
        if lineno and lineno != warning_message.lineno:
            continue
        if module and not re.compile(module).match(
            _module_name(warning_message.filename)
        ):
            continue
        return action == ERROR_LATER_ACTION
    return False


def to_late_warning(
    warning_message: warnings.WarningMessage, nodeid: str
) -> LateWarning:
    return LateWarning(
        message=str(warning_message.message),
        category=warning_message.category.__name__,
        filename=warning_message.filename,
        lineno=warning_message.lineno,
        nodeid=nodeid,
    )


def select_late_warnings(
    log: Iterable[warnings.WarningMessage],
    filters: list[WarningFilter],
    nodeid: str,
) -> list[LateWarning]:
    """The warnings of ``log`` that matched an ``error_later`` filter."""
    if not any(action == ERROR_LATER_ACTION for action, *_ in filters):
        return []
    return [
        to_late_warning(warning_message, nodeid)
        for warning_message in log
        if should_error_later(warning_message, filters)
    ]
