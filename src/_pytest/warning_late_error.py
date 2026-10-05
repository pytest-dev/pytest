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

from collections.abc import Callable
from collections.abc import Iterator
import contextlib
import dataclasses
import re
import sys
import threading
from typing import Any
from typing import cast
from typing import Final
from typing import Literal
from typing import TextIO
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

    #: Warnings held over to the end of the session.
    collected: list[LateWarning] = dataclasses.field(default_factory=list)
    #: How many of ``collected`` have been written to the terminal.
    reported: int = 0
    #: Set once the session can no longer report; warnings after that point
    #: are shown the ordinary way instead of being collected and lost.
    closed: bool = False


late_warning_state_key: StashKey[LateWarningState] = StashKey()


# How the stdlib is made to decide ``error_later`` itself
# ---------------------------------------------------------
#
# An ``error_later`` filter is installed as a real ``always`` filter whose
# module field is a _WinProbe, immediately followed by a never-matching filter
# whose module field is a _LossProbe. The warnings module calls ``.match()`` on
# whatever object sits in the message and module fields of every filter it
# visits (Python/_warnings.c:check_matched, and ``mod.match(module)`` in the
# pure-Python warn_explicit), and stops at the first filter that matches. So
# for each warning:
#
# - the win probe sees the exact module name the stdlib matches against;
# - if its filter wins, the search stops and the warning is shown next, in
#   the same thread, before anything else can run;
# - if its filter loses on a later field (category and line are checked after
#   the module in C), the search goes on to the loss probe, which withdraws it.
#
# The verdict is handed over through a thread-local and consumed by pytest's
# recording log or showwarning wrapper. The win probe only records when one of
# those is where the warning will go, so a warning shown elsewhere (pytest.warns,
# a test's own catch_warnings, logging.captureWarnings) leaves nothing behind
# for the next warning to pick up.

_verdict = threading.local()

#: Python 3.14+: filters and the record log live in a context variable.
_CONTEXT_AWARE: Final = bool(getattr(sys.flags, "context_aware_warnings", False))


def _take_verdict() -> str | None:
    """The module name of a warning an ``error_later`` filter just won, once."""
    module: str | None = getattr(_verdict, "module", None)
    _verdict.module = None
    return module


class LateWarningLog(list[warnings.WarningMessage]):
    """A ``catch_warnings(record=True)`` log that knows which entries erred later.

    It records through the plain ``list.append`` until an ``error_later``
    filter is installed in its context; only then does it route through
    :meth:`_record`, so sessions without such a filter pay nothing.
    """

    def __init__(self) -> None:
        super().__init__()
        self._late: dict[int, str] = {}

    def _record(self, warning_message: warnings.WarningMessage) -> None:
        module = _take_verdict()
        if module is not None:
            self._late[id(warning_message)] = module
        self.append(warning_message)

    def is_late(self, warning_message: warnings.WarningMessage) -> bool:
        return id(warning_message) in self._late


class _ContextSink:
    """``_Context.log`` stand-in: 3.14 context-aware recording calls ``log.append``."""

    __slots__ = ("append", "log")

    def __init__(self, log: LateWarningLog) -> None:
        self.log = log
        self.append = log._record


def _route_recording_through_verdicts() -> None:
    if _CONTEXT_AWARE:
        context = warnings._get_context()  # type: ignore[attr-defined]
        if isinstance(context.log, LateWarningLog):
            context.log = _ContextSink(context.log)
    else:
        log = getattr(warnings._showwarnmsg_impl, "__self__", None)  # type: ignore[attr-defined]
        if isinstance(log, LateWarningLog):
            warnings._showwarnmsg_impl = log._record  # type: ignore[attr-defined]


def _pytest_receives_shown_warnings() -> bool:
    showwarning = warnings.showwarning
    if showwarning is not warnings._showwarning_orig:  # type: ignore[attr-defined]
        return getattr(showwarning, "_pytest_error_later_sink", False)
    if _CONTEXT_AWARE:
        import _py_warnings

        return warnings._showwarnmsg_impl is _py_warnings._showwarnmsg_impl and (  # type: ignore[attr-defined]
            isinstance(warnings._get_context().log, _ContextSink)  # type: ignore[attr-defined]
        )
    sink = getattr(warnings._showwarnmsg_impl, "__func__", None)  # type: ignore[attr-defined]
    return sink is LateWarningLog._record


class _WinProbe:
    __slots__ = ("_regex", "pattern")

    def __init__(self, module: str) -> None:
        #: Mirrors ``re.Pattern.pattern`` for code that inspects ``warnings.filters``.
        self.pattern = module
        self._regex = re.compile(module) if module else None

    def match(self, module: str) -> object:
        matched = True if self._regex is None else self._regex.match(module)
        if matched and _pytest_receives_shown_warnings():
            _verdict.module = module
        return matched

    def __repr__(self) -> str:
        return f"<error_later module={self.pattern!r}>"


class _LossProbe:
    __slots__ = ()
    pattern = None

    def match(self, module: str) -> None:
        _verdict.module = None

    def __repr__(self) -> str:
        return "<error_later lost>"


def _install_error_later(
    message: str, category: type[Warning], module: str, lineno: int
) -> None:
    # Not warnings.filterwarnings(): it insists on str patterns and compiles them.
    filters = cast(
        "list[Any]",
        warnings._get_filters()
        if hasattr(warnings, "_get_filters")
        else warnings.filters,
    )
    regex = re.compile(message, re.IGNORECASE) if message else None
    with getattr(warnings, "_lock", contextlib.nullcontext()):
        filters.insert(0, ("always", None, Warning, _LossProbe(), 0))
        filters.insert(0, ("always", regex, category, _WinProbe(module), lineno))
    warnings._filters_mutated()  # type: ignore[attr-defined]
    _route_recording_through_verdicts()


def install_warning_filter(filter_: WarningFilter) -> None:
    """Apply a parsed filter to the :mod:`warnings` module."""
    action, message, category, module, lineno = filter_
    if action == ERROR_LATER_ACTION:
        _install_error_later(message, category, module, lineno)
    else:
        warnings.filterwarnings(action, message, category, module, lineno)


@contextlib.contextmanager
def recording_warnings() -> Iterator[LateWarningLog]:
    """``catch_warnings(record=True)``, recording into a :class:`LateWarningLog`."""
    with warnings.catch_warnings(record=True):
        log = LateWarningLog()
        if _CONTEXT_AWARE:
            warnings._get_context().log = log  # type: ignore[attr-defined]
        else:
            warnings._showwarnmsg_impl = log.append  # type: ignore[attr-defined]
        yield log


def collect_or_show(
    state: LateWarningState, showwarning: Callable[..., object]
) -> Callable[..., None]:
    """``warnings.showwarning`` for contexts that do not record."""

    def show(
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: TextIO | None = None,
        line: str | None = None,
    ) -> None:
        if _take_verdict() is not None and not state.closed:
            warning_message = warnings.WarningMessage(
                message, category, filename, lineno, file, line
            )
            state.collected.append(to_late_warning(warning_message, nodeid=""))
        else:
            showwarning(message, category, filename, lineno, file, line)

    show._pytest_error_later_sink = True  # type: ignore[attr-defined]
    return show


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
    log: LateWarningLog, start: int, nodeid: str
) -> list[LateWarning]:
    """The warnings of ``log[start:]`` that an ``error_later`` filter won."""
    if not log._late:
        return []
    return [
        to_late_warning(warning_message, nodeid)
        for warning_message in log[start:]
        if log.is_late(warning_message)
    ]
