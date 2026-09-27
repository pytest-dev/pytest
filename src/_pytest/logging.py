# mypy: allow-untyped-defs
"""Access and control log capturing."""

from __future__ import annotations

from collections.abc import Generator
from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from contextlib import contextmanager
from contextlib import nullcontext
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import io
from io import StringIO
import logging
from logging import LogRecord
import os
from pathlib import Path
import re
from threading import local
from types import TracebackType
from typing import final
from typing import Generic
from typing import Literal
from typing import TYPE_CHECKING
from typing import TypeVar
from weakref import WeakKeyDictionary

from _pytest import nodes
from _pytest._io import TerminalWriter
from _pytest.capture import CaptureManager
from _pytest.config import _strtobool
from _pytest.config import Config
from _pytest.config import create_terminal_writer
from _pytest.config import hookimpl
from _pytest.config import UsageError
from _pytest.config.argparsing import Parser
from _pytest.deprecated import check_ispytest
from _pytest.fixtures import fixture
from _pytest.fixtures import FixtureRequest
from _pytest.main import Session
from _pytest.stash import StashKey
from _pytest.terminal import TerminalReporter


if TYPE_CHECKING:
    logging_StreamHandler = logging.StreamHandler[StringIO]
else:
    logging_StreamHandler = logging.StreamHandler

DEFAULT_LOG_FORMAT = "%(levelname)-8s %(name)s:%(filename)s:%(lineno)d %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%H:%M:%S"
_ANSI_ESCAPE_SEQ = re.compile(r"\x1b\[[\d;]+m")
caplog_handler_key = StashKey["LogCaptureHandler"]()
caplog_records_key = StashKey[dict[str, list[logging.LogRecord]]]()


def _remove_ansi_escape_sequences(text: str) -> str:
    return _ANSI_ESCAPE_SEQ.sub("", text)


class DatetimeFormatter(logging.Formatter):
    """A logging formatter which formats record with
    :func:`datetime.datetime.strftime` formatter instead of
    :func:`time.strftime` in case of microseconds in format string.
    """

    def formatTime(self, record: LogRecord, datefmt: str | None = None) -> str:
        if datefmt and "%f" in datefmt:
            ct = self.converter(record.created)
            tz = timezone(timedelta(seconds=ct.tm_gmtoff), ct.tm_zone)
            # Construct `datetime.datetime` object from `struct_time`
            # and msecs information from `record`
            # Using int() instead of round() to avoid it exceeding 1_000_000 and causing a ValueError (#11861).
            dt = datetime(*ct[0:6], microsecond=int(record.msecs * 1000), tzinfo=tz)
            return dt.strftime(datefmt)
        # Use `logging.Formatter` for non-microsecond formats
        return super().formatTime(record, datefmt)


class ColoredLevelFormatter(DatetimeFormatter):
    """A logging formatter which colorizes the %(levelname)..s part of the
    log format passed to __init__."""

    LOGLEVEL_COLOROPTS: Mapping[int, AbstractSet[str]] = {
        logging.CRITICAL: {"red"},
        logging.ERROR: {"red", "bold"},
        logging.WARNING: {"yellow"},
        logging.INFO: {"green"},
        logging.DEBUG: {"purple"},
        logging.NOTSET: set(),
    }
    LEVELNAME_FMT_REGEX = re.compile(r"%\(levelname\)([+-.]?\d*(?:\.\d+)?s)")

    def __init__(self, terminalwriter: TerminalWriter, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._terminalwriter = terminalwriter
        self._original_fmt = self._style._fmt
        self._level_to_fmt_mapping: dict[int, str] = {}

        for level, color_opts in self.LOGLEVEL_COLOROPTS.items():
            self.add_color_level(level, *color_opts)

    def add_color_level(self, level: int, *color_opts: str) -> None:
        """Add or update color opts for a log level.

        :param level:
            Log level to apply a style to, e.g. ``logging.INFO``.
        :param color_opts:
            ANSI escape sequence color options. Capitalized colors indicates
            background color, i.e. ``'green', 'Yellow', 'bold'`` will give bold
            green text on yellow background.

        .. warning::
            This is an experimental API.
        """
        assert self._fmt is not None
        levelname_fmt_match = self.LEVELNAME_FMT_REGEX.search(self._fmt)
        if not levelname_fmt_match:
            return
        levelname_fmt = levelname_fmt_match.group()

        formatted_levelname = levelname_fmt % {"levelname": logging.getLevelName(level)}

        # add ANSI escape sequences around the formatted levelname
        color_kwargs = {name: True for name in color_opts}
        colorized_formatted_levelname = self._terminalwriter.markup(
            formatted_levelname, **color_kwargs
        )
        self._level_to_fmt_mapping[level] = self.LEVELNAME_FMT_REGEX.sub(
            colorized_formatted_levelname, self._fmt
        )

    def format(self, record: logging.LogRecord) -> str:
        fmt = self._level_to_fmt_mapping.get(record.levelno, self._original_fmt)
        self._style._fmt = fmt
        return super().format(record)


class PercentStyleMultiline(logging.PercentStyle):
    """A logging style with special support for multiline messages.

    If the message of a record consists of multiple lines, this style
    formats the message as if each line were logged separately.
    """

    def __init__(self, fmt: str, auto_indent: int | str | bool | None) -> None:
        super().__init__(fmt)
        self._auto_indent = self._get_auto_indent(auto_indent)

    @staticmethod
    def _get_auto_indent(auto_indent_option: int | str | bool | None) -> int:
        """Determine the current auto indentation setting.

        Specify auto indent behavior (on/off/fixed) by passing in
        extra={"auto_indent": [value]} to the call to logging.log() or
        using a --log-auto-indent [value] command line or the
        log_auto_indent [value] config option.

        Default behavior is auto-indent off.

        Using the string "True" or "on" or the boolean True as the value
        turns auto indent on, using the string "False" or "off" or the
        boolean False or the int 0 turns it off, and specifying a
        positive integer fixes the indentation position to the value
        specified.

        Any other values for the option are invalid, and will silently be
        converted to the default.

        :param None|bool|int|str auto_indent_option:
            User specified option for indentation from command line, config
            or extra kwarg. Accepts int, bool or str. str option accepts the
            same range of values as boolean config options, as well as
            positive integers represented in str form.

        :returns:
            Indentation value, which can be
            -1 (automatically determine indentation) or
            0 (auto-indent turned off) or
            >0 (explicitly set indentation position).
        """
        match auto_indent_option:
            case None | False:
                return 0
            case True:
                return -1
            case int():
                return max(auto_indent_option, 0)
            case str():
                try:
                    return max(int(auto_indent_option), 0)
                except ValueError:
                    pass
                try:
                    if _strtobool(auto_indent_option):
                        return -1
                except ValueError:
                    return 0
                return 0

    def format(self, record: logging.LogRecord) -> str:
        if "\n" in record.message:
            if hasattr(record, "auto_indent"):
                # Passed in from the "extra={}" kwarg on the call to logging.log().
                auto_indent = self._get_auto_indent(record.auto_indent)
            else:
                auto_indent = self._auto_indent

            if auto_indent:
                lines = record.message.splitlines()
                formatted = self._fmt % {**record.__dict__, "message": lines[0]}

                if auto_indent < 0:
                    indentation = _remove_ansi_escape_sequences(formatted).find(
                        lines[0]
                    )
                else:
                    # Optimizes logging by allowing a fixed indentation.
                    indentation = auto_indent
                lines[0] = formatted
                return ("\n" + " " * indentation).join(lines)
        return self._fmt % record.__dict__


def get_option_ini(config: Config, *names: str):
    for name in names:
        ret = config.getoption(name)  # 'default' arg won't work as expected
        if ret is None:
            ret = config.getini(name)
        if ret:
            return ret


def pytest_addoption(parser: Parser) -> None:
    """Add options to control log capturing."""
    group = parser.getgroup("logging")

    def add_option_ini(option, dest, default=None, type=None, **kwargs):
        parser.addini(
            dest, default=default, type=type, help="Default value for " + option
        )
        group.addoption(option, dest=dest, **kwargs)

    add_option_ini(
        "--log-level",
        dest="log_level",
        default=None,
        metavar="LEVEL",
        help=(
            "Level of messages to catch/display."
            " Not set by default, so it depends on the root/parent log handler's"
            ' effective level, where it is "WARNING" by default.'
        ),
    )
    add_option_ini(
        "--log-format",
        dest="log_format",
        default=DEFAULT_LOG_FORMAT,
        help="Log format used by the logging module",
    )
    add_option_ini(
        "--log-date-format",
        dest="log_date_format",
        default=DEFAULT_LOG_DATE_FORMAT,
        help="Log date format used by the logging module",
    )
    parser.addini(
        "log_cli",
        default=False,
        type="bool",
        help='Enable log display during test run (also known as "live logging")',
    )
    add_option_ini(
        "--log-cli-level", dest="log_cli_level", default=None, help="CLI logging level"
    )
    add_option_ini(
        "--log-cli-format",
        dest="log_cli_format",
        default=None,
        help="Log format used by the logging module",
    )
    add_option_ini(
        "--log-cli-date-format",
        dest="log_cli_date_format",
        default=None,
        help="Log date format used by the logging module",
    )
    add_option_ini(
        "--log-file",
        dest="log_file",
        default=None,
        help="Path to a file when logging will be written to",
    )
    add_option_ini(
        "--log-file-mode",
        dest="log_file_mode",
        default="w",
        choices=["w", "a"],
        help="Log file open mode",
    )
    add_option_ini(
        "--log-file-level",
        dest="log_file_level",
        default=None,
        help="Log file logging level",
    )
    add_option_ini(
        "--log-file-format",
        dest="log_file_format",
        default=None,
        help="Log format used by the logging module",
    )
    add_option_ini(
        "--log-file-date-format",
        dest="log_file_date_format",
        default=None,
        help="Log date format used by the logging module",
    )
    add_option_ini(
        "--log-auto-indent",
        dest="log_auto_indent",
        default=None,
        help="Auto-indent multiline messages passed to the logging module. Accepts true|on, false|off or an integer.",
    )
    group.addoption(
        "--log-disable",
        action="append",
        default=[],
        dest="logger_disable",
        help="Disable a logger by name. Can be passed multiple times.",
    )


_HandlerType = TypeVar("_HandlerType", bound=logging.Handler)


def _remove_handler_by_identity(
    logger: logging.Logger, handler: logging.Handler
) -> None:
    """Remove ``handler`` from ``logger.handlers`` comparing by identity.

    ``Logger.removeHandler()`` uses ``list.remove()``, i.e. ``__eq__``, so a
    user handler which compares equal to one of pytest's own would be removed
    in its place. Two loggers may also share a single ``handlers`` list, in
    which case the handler must come out of that one list exactly once.
    """
    handlers = logger.handlers
    for index, existing in enumerate(handlers):
        if existing is handler:
            del handlers[index]
            return


class _BoundProxyHandler(logging.Handler):
    """A proxy for a pytest capture handler, bound to one logger.

    The proxy forwards records to the real handler only while its logger
    currently does not propagate. This is attached (instead of the real
    handler) to loggers which were non-propagating when capture started, and
    to their ancestors, so that flipping ``Logger.propagate`` during a test
    neither duplicates the record (direct handler plus root handler) nor
    misses it (#15064, #3697).
    """

    __slots__ = (
        "_detached",
        "_proxied_filters",
        "_refcount",
        "_state",
        "logger",
        "real_handler",
    )

    def __init__(self, logger: logging.Logger, real_handler: logging.Handler) -> None:
        self.logger = logger
        self.real_handler = real_handler
        # Per-thread reentrancy guard: the proxy forwards into the real
        # handler, which may itself log and re-enter the same proxy.
        self._state = local()
        self._detached = False
        # Number of catching_logs scopes currently sharing this proxy. Overlapping
        # scopes (e.g. caplog + report handler nested per test phase, or two
        # contexts sharing one handler) must attach a single proxy, or the record
        # is forwarded once per scope and captured twice. Starts at 0: the
        # owning scope's ``__enter__`` accounts for the first reference.
        self._refcount = 0
        # Filters installed through this proxy (e.g. via ``logger.handlers``).
        # They are applied by the real handler, which the proxy forwards to, so
        # they are tracked here to be taken back off again on detach.
        self._proxied_filters: list[logging.Filter] = []
        # Deliberately skip ``logging.Handler.__init__``'s registration in the
        # global ``_handlerList``: a proxy is a short-lived internal object
        # which pytest detaches itself, it owns no stream, and it must never be
        # closed by ``logging.shutdown()`` (that would close the real handler
        # it forwards to). Everything else the base initialiser sets up is
        # replicated here.
        self._name = None
        self.formatter: logging.Formatter | None = None
        self._closed = False
        self.filters = []  # type: ignore[assignment]
        self.createLock()

    @property
    def level(self) -> int:
        # Always defer to the real handler, whose level may change after
        # attachment (e.g. via caplog.set_level()).
        return self.real_handler.level

    @level.setter
    def level(self, value: int) -> None:
        # Only assigned by logging.Handler.__init__(); the level is tracked
        # through the real handler instead.
        pass

    def addFilter(self, filter: logging.Filter) -> None:
        # Filters installed through ``logger.handlers`` (e.g. by
        # ``caplog.filtering()``) must keep affecting capture. ``handle()``
        # below forwards the record to the real handler, which is what applies
        # filters, so the filter is installed there too -- tracked so it can be
        # taken back off on detach. The real handler's own filters are left
        # untouched.
        super().addFilter(filter)
        self._proxied_filters.append(filter)
        real = self.real_handler
        if real is not None and not any(f is filter for f in real.filters):
            real.filters.append(filter)

    def removeFilter(self, filter: logging.Filter) -> None:  # type: ignore[override]
        # Removed from both, by identity, so a filter removed through the proxy
        # (as ``caplog.filtering()`` does on exit) does not stay active for the
        # next test.
        for existing_list in (self.filters, self._proxied_filters):
            for index, existing in enumerate(existing_list):
                if existing is filter:
                    del existing_list[index]
                    break
        real = self.real_handler
        if real is not None:
            for index, existing in enumerate(real.filters):
                if existing is filter:
                    del real.filters[index]
                    break

    def setFormatter(self, fmt: logging.Formatter | None) -> None:
        self.formatter = fmt
        if self.real_handler is not None:
            self.real_handler.setFormatter(fmt)

    def handle(self, record: logging.LogRecord) -> bool:
        """Forward to the real handler without holding the proxy's own lock.

        ``logging.Handler.handle()`` holds ``self.lock`` across ``emit()``.
        Calling ``real_handler.handle()`` from there would additionally take the
        real handler's lock, establishing a ``proxy -> real`` lock order that
        another thread can invert (``real -> proxy``) and deadlock on. Instead,
        take the real handler's lock directly, so only one lock is ever held.

        ``Logger.callHandlers()`` ignores the return value, so returning a
        falsy value here is safe; the stdlib's ``found`` bookkeeping is
        unaffected.
        """
        if self._is_detached:
            return False
        if self.logger.propagate:
            # The logger propagates now, so the record continues up the
            # hierarchy (to the real handler attached to root) -- do not
            # deliver it a second time.
            return False
        if any(h is self.real_handler for h in self.logger.handlers):
            # The real handler is attached to this logger directly (e.g. a
            # handler installed through ``logger.addHandler``), so this record
            # is already going to be handled by it on this same walk -- forward
            # and it would be captured twice.
            return False
        if getattr(self._state, "forwarding", False):
            # Re-entered from inside the real handler's own emit(); forwarding
            # again would recurse, so skip (the guard in ``emit()`` also covers
            # direct emit() calls).
            return False
        self._state.forwarding = True
        try:
            # Delegate whole-record handling (filters, level, lock, handleError)
            # to the real handler.
            return self.real_handler.handle(record)
        finally:
            self._state.forwarding = False

    def emit(self, record: logging.LogRecord) -> None:
        # Only reached when the handler is driven directly (``emit()`` by user
        # code); ``handle()`` forwards before acquiring this handler's lock.
        if (
            not self._is_detached
            and not self.logger.propagate
            and not getattr(self._state, "forwarding", False)
        ):
            self.handle(record)

    def close(self) -> None:
        # Detaching must not close the real handler, which pytest reuses across
        # phases; only mark the proxy detached so a retained proxy can neither
        # keep the capture handler alive nor forward records after the context
        # has ended. ``_detached`` rather than clearing the attributes, so that
        # any late call fails safe (no forwarding) instead of raising.
        self._detached = True
        # Filters installed through the proxy are also installed on the real
        # handler, so they must be taken back off on detach -- otherwise they
        # stay active for the next test and silently drop its records.
        real = self.real_handler
        if real is not None and self._proxied_filters:
            proxied = self._proxied_filters
            real.filters = [
                existing
                for existing in real.filters
                if not any(existing is f for f in proxied)
            ]
        self._proxied_filters.clear()
        super().close()

    @property
    def _is_detached(self) -> bool:
        return getattr(self, "_detached", False)


# Not using @contextmanager for performance reasons.
class catching_logs(Generic[_HandlerType]):
    """Context manager that prepares the whole logging machinery properly."""

    # Proxies are reused across the enclosing capture scope, so the set of
    # loggers needing one is cached per (manager, handler) and recomputed only
    # when a *new* non-propagating logger appears. pytest re-enters
    # ``catching_logs`` for every test phase, so this turns a per-entry
    # O(n^2) rescan into a single walk.
    __slots__ = (
        "attached_loggers",
        "attached_proxies",
        "handler",
        "level",
        "orig_level",
    )

    # Weakly keyed by the handler so the cache dies with it (pytest's handlers
    # live for the whole session, so this is bounded by a handful of entries).
    _target_cache: WeakKeyDictionary[object, tuple[logging.Logger, ...]] = (
        WeakKeyDictionary()
    )

    def __init__(self, handler: _HandlerType, level: int | None = None) -> None:
        self.handler = handler
        self.level = level
        self.attached_loggers: list[logging.Logger] = []
        self.attached_proxies: list[tuple[logging.Logger, _BoundProxyHandler]] = []

    def __enter__(self) -> _HandlerType:
        root_logger = logging.getLogger()
        if self.level is not None:
            self.handler.setLevel(self.level)
        # Attach to root logger.
        root_logger.addHandler(self.handler)
        self.attached_loggers.append(root_logger)
        # Attach bound proxy handlers to all non-propagating loggers
        # (their records won't reach root) and to their ancestors, so that
        # records which *do* reach root after a `propagate` change are only
        # handled once. The proxies consult the live `propagate` value per
        # record (#15064).
        # Note that this still misses loggers (outside those ancestor
        # chains) which *become* non-propagating after the `__enter__`.
        # Not worth the trouble for now.
        try:
            for logger in self._proxy_targets(root_logger, self.handler):
                # Reuse a proxy already bound to this (logger, handler) pair, so
                # that overlapping capturing_logs scopes -- pytest nests one per
                # handler and re-enters them for every test phase -- attach a
                # single proxy. Without reuse the same record is forwarded once
                # per scope and captured more than once.
                proxy: _BoundProxyHandler | None = None
                for existing in logger.handlers:
                    if (
                        isinstance(existing, _BoundProxyHandler)
                        and existing.real_handler is self.handler
                    ):
                        proxy = existing
                        break
                reused = proxy is not None
                if proxy is None:
                    proxy = _BoundProxyHandler(logger, self.handler)
                # ``Logger.addHandler`` refuses a handler that compares equal to
                # one already attached, so attach by identity and remember
                # exactly what we added -- otherwise a user handler which
                # compares equal would suppress the proxy *and* be removed in its
                # place on exit.
                if not reused and not any(h is proxy for h in logger.handlers):
                    logger.handlers.append(proxy)
                proxy._refcount += 1
                self.attached_proxies.append((logger, proxy))
        except BaseException:
            # Entry must be transactional: if anything above fails (e.g. an
            # unhashable Logger), undo the partial setup instead of leaving
            # pytest's handler attached to root with no owner to remove it.
            self._detach()
            raise
        if self.level is not None:
            # Non-propagating loggers still inherit the level (unless a logger
            # explicitly set level), so only do this on the root logger.
            self.orig_level = root_logger.level
            root_logger.setLevel(min(self.orig_level, self.level))
        return self.handler

    @classmethod
    def _proxy_targets(
        cls, root_logger: logging.Logger, handler: logging.Handler
    ) -> tuple[logging.Logger, ...]:
        """Loggers which need a bound proxy, in a stable order.

        Cached per handler and revalidated on every entry: the cache is only
        reused when the logger population is unchanged and every cached target
        is still registered and still non-propagating. Any logger which appears
        or flips ``propagate`` afterwards therefore forces a recompute, while
        the common case -- pytest re-entering the same scope for every test
        phase with nothing changed -- is an O(n) revalidation.

        Identity is used throughout: loggers are not guaranteed to be
        hashable (``Logger`` subclasses may set ``__hash__ = None``) and two
        distinct loggers can share one ``handlers`` list, so neither a dict
        keyed by logger nor a set is safe here.
        """
        manager = root_logger.manager
        current = manager.loggerDict
        cached = cls._target_cache.get(handler)
        if cached is not None and len(cached) == len(current):
            if all(
                any(existing is logger for existing in current.values())
                and not logger.propagate
                for logger in cached
            ):
                return cached

        root = current
        targets: list[logging.Logger] = []
        # Identity set: avoids hashing loggers and gives O(1) membership.
        seen: dict[int, logging.Logger] = {}
        for logger in list(root.values()):
            if (
                not isinstance(logger, logging.Logger)
                or logger is root_logger
                or logger.propagate
            ):
                continue
            if id(logger) not in seen:
                seen[id(logger)] = logger
                targets.append(logger)
            parent = logger.parent
            while parent is not None and parent is not root_logger:
                if id(parent) not in seen:
                    seen[id(parent)] = parent
                    targets.append(parent)
                parent = parent.parent
        result = tuple(targets)
        cls._target_cache[handler] = result
        return result

    def _detach(self) -> None:
        """Release everything this context attached, by identity.

        A proxy shared with an outer (still-active) scope is only released when
        the last owner lets go of it, so nested contexts over the same handler
        neither detach early nor double-forward.
        """
        for logger in self.attached_loggers:
            if any(h is self.handler for h in logger.handlers):
                _remove_handler_by_identity(logger, self.handler)
        self.attached_loggers.clear()
        for logger, proxy in self.attached_proxies:
            proxy._refcount -= 1
            if proxy._refcount > 0:
                # Still owned by an enclosing scope; leave it attached.
                continue
            if any(h is proxy for h in logger.handlers):
                _remove_handler_by_identity(logger, proxy)
            # Stop a retained proxy from forwarding (or keeping the capture
            # handler and logger alive) once capture is over.
            proxy.close()
        self.attached_proxies.clear()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        root_logger = logging.getLogger()
        if self.level is not None:
            root_logger.setLevel(self.orig_level)
        self._detach()


class LogCaptureHandler(logging_StreamHandler):
    """A logging handler that stores log records and the log text."""

    def __init__(self) -> None:
        """Create a new log handler."""
        super().__init__(StringIO())
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Keep the log records in a list in addition to the log text."""
        self.records.append(record)
        super().emit(record)

    def reset(self) -> None:
        self.records = []
        self.stream = StringIO()

    def clear(self) -> None:
        self.records.clear()
        self.stream = StringIO()

    def handleError(self, record: logging.LogRecord) -> None:
        if logging.raiseExceptions:
            # Fail the test if the log message is bad (emit failed).
            # The default behavior of logging is to print "Logging error"
            # to stderr with the call stack and some extra details.
            # pytest wants to make such mistakes visible during testing.
            raise  # noqa: PLE0704


@final
class LogCaptureFixture:
    """Provides access and control of log capturing."""

    def __init__(self, item: nodes.Node, *, _ispytest: bool = False) -> None:
        check_ispytest(_ispytest)
        self._item = item
        self._initial_handler_level: int | None = None
        # Dict of log name -> log level.
        self._initial_logger_levels: dict[str | None, int] = {}
        self._initial_disabled_logging_level: int | None = None

    def _finalize(self) -> None:
        """Finalize the fixture.

        This restores the log levels and the disabled logging levels changed by :meth:`set_level`.
        """
        # Restore log levels.
        if self._initial_handler_level is not None:
            self.handler.setLevel(self._initial_handler_level)
        for logger_name, level in self._initial_logger_levels.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
        # Disable logging at the original disabled logging level.
        if self._initial_disabled_logging_level is not None:
            logging.disable(self._initial_disabled_logging_level)
            self._initial_disabled_logging_level = None

    @property
    def handler(self) -> LogCaptureHandler:
        """Get the logging handler used by the fixture."""
        return self._item.stash[caplog_handler_key]

    def get_records(
        self, when: Literal["setup", "call", "teardown"]
    ) -> list[logging.LogRecord]:
        """Get the logging records for one of the possible test phases.

        :param when:
            Which test phase to obtain the records from.
            Valid values are: "setup", "call" and "teardown".

        :returns: The list of captured records at the given stage.

        .. versionadded:: 3.4
        """
        return self._item.stash[caplog_records_key].get(when, [])

    @property
    def text(self) -> str:
        """The formatted log text."""
        return _remove_ansi_escape_sequences(self.handler.stream.getvalue())

    @property
    def records(self) -> list[logging.LogRecord]:
        """The list of log records."""
        return self.handler.records

    @property
    def record_tuples(self) -> list[tuple[str, int, str]]:
        """A list of a stripped down version of log records intended
        for use in assertion comparison.

        The format of the tuple is:

            (logger_name, log_level, message)
        """
        return [(r.name, r.levelno, r.getMessage()) for r in self.records]

    @property
    def messages(self) -> list[str]:
        """A list of format-interpolated log messages.

        Unlike 'records', which contains the format string and parameters for
        interpolation, log messages in this list are all interpolated.

        Unlike 'text', which contains the output from the handler, log
        messages in this list are unadorned with levels, timestamps, etc,
        making exact comparisons more reliable.

        Note that traceback or stack info (from :func:`logging.exception` or
        the `exc_info` or `stack_info` arguments to the logging functions) is
        not included, as this is added by the formatter in the handler.

        .. versionadded:: 3.7
        """
        return [r.getMessage() for r in self.records]

    def clear(self) -> None:
        """Reset the list of log records and the captured log text."""
        self.handler.clear()

    def _force_enable_logging(
        self, level: int | str, logger_obj: logging.Logger
    ) -> int:
        """Enable the desired logging level if the global level was disabled via ``logging.disabled``.

        Only enables logging levels greater than or equal to the requested ``level``.

        Does nothing if the desired ``level`` wasn't disabled.

        :param level:
            The logger level caplog should capture.
            All logging is enabled if a non-standard logging level string is supplied.
            Valid level strings are in :data:`logging._nameToLevel`.
        :param logger_obj: The logger object to check.

        :return: The original disabled logging level.
        """
        original_disable_level: int = logger_obj.manager.disable

        if isinstance(level, str):
            # Try to translate the level string to an int for `logging.disable()`
            level = logging.getLevelName(level)  # type: ignore[deprecated]

        if not isinstance(level, int):
            # The level provided was not valid, so just un-disable all logging.
            logging.disable(logging.NOTSET)
        elif not logger_obj.isEnabledFor(level):
            # Each level is `10` away from other levels.
            # https://docs.python.org/3/library/logging.html#logging-levels
            disable_level = max(level - 10, logging.NOTSET)
            logging.disable(disable_level)

        return original_disable_level

    def set_level(self, level: int | str, logger: str | None = None) -> None:
        """Set the threshold level of a logger for the duration of a test.

        Logging messages which are less severe than this level will not be captured.

        .. versionchanged:: 3.4
            The levels of the loggers changed by this function will be
            restored to their initial values at the end of the test.

        Will enable the requested logging level if it was disabled via :func:`logging.disable`.

        :param level: The level.
        :param logger: The logger to update. If not given, the root logger.
        """
        logger_obj = logging.getLogger(logger)
        # Save the original log-level to restore it during teardown.
        self._initial_logger_levels.setdefault(logger, logger_obj.level)
        logger_obj.setLevel(level)
        if self._initial_handler_level is None:
            self._initial_handler_level = self.handler.level
        self.handler.setLevel(level)
        initial_disabled_logging_level = self._force_enable_logging(level, logger_obj)
        if self._initial_disabled_logging_level is None:
            self._initial_disabled_logging_level = initial_disabled_logging_level

    @contextmanager
    def at_level(self, level: int | str, logger: str | None = None) -> Generator[None]:
        """Context manager that sets the level for capturing of logs. After
        the end of the 'with' statement the level is restored to its original
        value.

        Will enable the requested logging level if it was disabled via :func:`logging.disable`.

        :param level: The level.
        :param logger: The logger to update. If not given, the root logger.
        """
        logger_obj = logging.getLogger(logger)
        orig_level = logger_obj.level
        logger_obj.setLevel(level)
        handler_orig_level = self.handler.level
        self.handler.setLevel(level)
        original_disable_level = self._force_enable_logging(level, logger_obj)
        try:
            yield
        finally:
            logger_obj.setLevel(orig_level)
            self.handler.setLevel(handler_orig_level)
            logging.disable(original_disable_level)

    @contextmanager
    def filtering(self, filter_: logging.Filter) -> Generator[None]:
        """Context manager that temporarily adds the given filter to the caplog's
        :meth:`handler` for the 'with' statement block, and removes that filter at the
        end of the block.

        :param filter_: A custom :class:`logging.Filter` object.

        .. versionadded:: 7.5
        """
        already_present = filter_ in self.handler.filters
        if already_present:
            yield
        else:
            try:
                self.handler.addFilter(filter_)
                yield
            finally:
                self.handler.removeFilter(filter_)


@fixture
def caplog(request: FixtureRequest) -> Generator[LogCaptureFixture]:
    """Access and control log capturing.

    Captured logs are available through the following properties/methods::

    * caplog.messages        -> list of format-interpolated log messages
    * caplog.text            -> string containing formatted log output
    * caplog.records         -> list of logging.LogRecord instances
    * caplog.record_tuples   -> list of (logger_name, level, message) tuples
    * caplog.clear()         -> clear captured records and formatted log output string
    """
    result = LogCaptureFixture(request.node, _ispytest=True)
    yield result
    result._finalize()


def get_log_level_for_setting(config: Config, *setting_names: str) -> int | None:
    for setting_name in setting_names:
        log_level = config.getoption(setting_name)
        if log_level is None:
            log_level = config.getini(setting_name)
        if log_level:
            break
    else:
        return None

    if isinstance(log_level, str):
        log_level = log_level.upper()
    try:
        return int(getattr(logging, log_level, log_level))
    except ValueError as e:
        # Python logging does not recognise this as a logging level
        raise UsageError(
            f"'{log_level}' is not recognized as a logging level name for "
            f"'{setting_name}'. Please consider passing the "
            "logging level num instead."
        ) from e


# run after terminalreporter/capturemanager are configured
@hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    config.pluginmanager.register(LoggingPlugin(config), "logging-plugin")


class LoggingPlugin:
    """Attaches to the logging module and captures log messages for each test."""

    def __init__(self, config: Config) -> None:
        """Create a new plugin to capture log messages.

        The formatter can be safely shared across all handlers so
        create a single one for the entire test session here.
        """
        self._config = config

        # Report logging.
        self.formatter = self._create_formatter(
            get_option_ini(config, "log_format"),
            get_option_ini(config, "log_date_format"),
            get_option_ini(config, "log_auto_indent"),
        )
        self.log_level = get_log_level_for_setting(config, "log_level")
        self.caplog_handler = LogCaptureHandler()
        self.caplog_handler.setFormatter(self.formatter)
        self.report_handler = LogCaptureHandler()
        self.report_handler.setFormatter(self.formatter)

        # File logging.
        self.log_file_level = get_log_level_for_setting(
            config, "log_file_level", "log_level"
        )
        log_file = get_option_ini(config, "log_file") or os.devnull
        if log_file != os.devnull:
            directory = os.path.dirname(os.path.abspath(log_file))
            if not os.path.isdir(directory):
                os.makedirs(directory)

        self.log_file_mode = get_option_ini(config, "log_file_mode") or "w"
        self.log_file_handler = _FileHandler(
            log_file, mode=self.log_file_mode, encoding="UTF-8"
        )
        log_file_format = get_option_ini(config, "log_file_format", "log_format")
        log_file_date_format = get_option_ini(
            config, "log_file_date_format", "log_date_format"
        )

        log_file_formatter = DatetimeFormatter(
            log_file_format, datefmt=log_file_date_format
        )
        self.log_file_handler.setFormatter(log_file_formatter)

        # CLI/live logging.
        self.log_cli_level = get_log_level_for_setting(
            config, "log_cli_level", "log_level"
        )
        if self._log_cli_enabled():
            terminal_reporter = config.pluginmanager.get_plugin("terminalreporter")
            # Guaranteed by `_log_cli_enabled()`.
            assert terminal_reporter is not None
            capture_manager = config.pluginmanager.get_plugin("capturemanager")
            # if capturemanager plugin is disabled, live logging still works.
            self.log_cli_handler: (
                _LiveLoggingStreamHandler | _LiveLoggingNullHandler
            ) = _LiveLoggingStreamHandler(terminal_reporter, capture_manager)
        else:
            self.log_cli_handler = _LiveLoggingNullHandler()
        log_cli_formatter = self._create_formatter(
            get_option_ini(config, "log_cli_format", "log_format"),
            get_option_ini(config, "log_cli_date_format", "log_date_format"),
            get_option_ini(config, "log_auto_indent"),
        )
        self.log_cli_handler.setFormatter(log_cli_formatter)
        self._disable_loggers(loggers_to_disable=config.option.logger_disable)

    def _disable_loggers(self, loggers_to_disable: list[str]) -> None:
        if not loggers_to_disable:
            return

        for name in loggers_to_disable:
            logger = logging.getLogger(name)
            logger.disabled = True

    def _create_formatter(self, log_format, log_date_format, auto_indent):
        # Color option doesn't exist if terminal plugin is disabled.
        color = getattr(self._config.option, "color", "no")
        if color != "no" and ColoredLevelFormatter.LEVELNAME_FMT_REGEX.search(
            log_format
        ):
            formatter: logging.Formatter = ColoredLevelFormatter(
                create_terminal_writer(self._config), log_format, log_date_format
            )
        else:
            formatter = DatetimeFormatter(log_format, log_date_format)

        formatter._style = PercentStyleMultiline(
            formatter._style._fmt, auto_indent=auto_indent
        )

        return formatter

    def set_log_path(self, fname: str) -> None:
        """Set the filename parameter for Logging.FileHandler().

        Creates parent directory if it does not exist.

        .. warning::
            This is an experimental API.
        """
        fpath = Path(fname)

        if not fpath.is_absolute():
            fpath = self._config.rootpath / fpath

        if not fpath.parent.exists():
            fpath.parent.mkdir(exist_ok=True, parents=True)

        # https://github.com/python/mypy/issues/11193
        stream: io.TextIOWrapper = fpath.open(mode=self.log_file_mode, encoding="UTF-8")  # type: ignore[assignment]
        old_stream = self.log_file_handler.setStream(stream)
        if old_stream:
            old_stream.close()

    def _log_cli_enabled(self) -> bool:
        """Return whether live logging is enabled."""
        enabled = self._config.getoption(
            "--log-cli-level"
        ) is not None or self._config.getini("log_cli")
        if not enabled:
            return False

        terminal_reporter = self._config.pluginmanager.get_plugin("terminalreporter")
        if terminal_reporter is None:
            # terminal reporter is disabled e.g. by pytest-xdist.
            return False

        return True

    @hookimpl(wrapper=True, tryfirst=True)
    def pytest_sessionstart(self) -> Generator[None]:
        self.log_cli_handler.set_when("sessionstart")

        with catching_logs(self.log_cli_handler, level=self.log_cli_level):
            with catching_logs(self.log_file_handler, level=self.log_file_level):
                return (yield)

    @hookimpl(wrapper=True, tryfirst=True)
    def pytest_collection(self) -> Generator[None]:
        self.log_cli_handler.set_when("collection")

        with catching_logs(self.log_cli_handler, level=self.log_cli_level):
            with catching_logs(self.log_file_handler, level=self.log_file_level):
                return (yield)

    @hookimpl(wrapper=True)
    def pytest_runtestloop(self, session: Session) -> Generator[None, object, object]:
        if session.config.option.collectonly:
            return (yield)

        if self._log_cli_enabled() and self._config.get_verbosity() < 1:
            # The verbose flag is needed to avoid messy test progress output.
            self._config.option.verbose = 1

        with catching_logs(self.log_cli_handler, level=self.log_cli_level):
            with catching_logs(self.log_file_handler, level=self.log_file_level):
                return (yield)  # Run all the tests.

    @hookimpl
    def pytest_runtest_logstart(self) -> None:
        self.log_cli_handler.reset()
        self.log_cli_handler.set_when("start")

    @hookimpl
    def pytest_runtest_logreport(self) -> None:
        self.log_cli_handler.set_when("logreport")

    @contextmanager
    def _runtest_for(self, item: nodes.Item, when: str) -> Generator[None]:
        """Implement the internals of the pytest_runtest_xxx() hooks."""
        with (
            catching_logs(
                self.caplog_handler,
                level=self.log_level,
            ) as caplog_handler,
            catching_logs(
                self.report_handler,
                level=self.log_level,
            ) as report_handler,
        ):
            caplog_handler.reset()
            report_handler.reset()
            item.stash[caplog_records_key][when] = caplog_handler.records
            item.stash[caplog_handler_key] = caplog_handler

            try:
                yield
            finally:
                log = report_handler.stream.getvalue().strip()
                item.add_report_section(when, "log", log)

    @hookimpl(wrapper=True)
    def pytest_runtest_setup(self, item: nodes.Item) -> Generator[None]:
        self.log_cli_handler.set_when("setup")

        empty: dict[str, list[logging.LogRecord]] = {}
        item.stash[caplog_records_key] = empty
        with self._runtest_for(item, "setup"):
            yield

    @hookimpl(wrapper=True)
    def pytest_runtest_call(self, item: nodes.Item) -> Generator[None]:
        self.log_cli_handler.set_when("call")

        with self._runtest_for(item, "call"):
            yield

    @hookimpl(wrapper=True)
    def pytest_runtest_teardown(self, item: nodes.Item) -> Generator[None]:
        self.log_cli_handler.set_when("teardown")

        try:
            with self._runtest_for(item, "teardown"):
                yield
        finally:
            del item.stash[caplog_records_key]
            del item.stash[caplog_handler_key]

    @hookimpl
    def pytest_runtest_logfinish(self) -> None:
        self.log_cli_handler.set_when("finish")

    @hookimpl(wrapper=True, tryfirst=True)
    def pytest_sessionfinish(self) -> Generator[None]:
        self.log_cli_handler.set_when("sessionfinish")

        with catching_logs(self.log_cli_handler, level=self.log_cli_level):
            with catching_logs(self.log_file_handler, level=self.log_file_level):
                return (yield)

    @hookimpl
    def pytest_unconfigure(self) -> None:
        # Close the FileHandler explicitly.
        # (logging.shutdown might have lost the weakref?!)
        self.log_file_handler.close()


class _FileHandler(logging.FileHandler):
    """A logging FileHandler with pytest tweaks."""

    def handleError(self, record: logging.LogRecord) -> None:
        # Handled by LogCaptureHandler.
        pass


class _LiveLoggingStreamHandler(logging_StreamHandler):
    """A logging StreamHandler used by the live logging feature: it will
    write a newline before the first log message in each test.

    During live logging we must also explicitly disable stdout/stderr
    capturing otherwise it will get captured and won't appear in the
    terminal.
    """

    # Officially stream needs to be a IO[str], but TerminalReporter
    # isn't. So force it.
    stream: TerminalReporter = None  # type: ignore

    def __init__(
        self,
        terminal_reporter: TerminalReporter,
        capture_manager: CaptureManager | None,
    ) -> None:
        super().__init__(stream=terminal_reporter)  # type: ignore[arg-type]
        self.capture_manager = capture_manager
        self.reset()
        self.set_when(None)
        self._test_outcome_written = False

    def reset(self) -> None:
        """Reset the handler; should be called before the start of each test."""
        self._first_record_emitted = False

    def set_when(self, when: str | None) -> None:
        """Prepare for the given test phase (setup/call/teardown)."""
        self._when = when
        self._section_name_shown = False
        if when == "start":
            self._test_outcome_written = False

    def emit(self, record: logging.LogRecord) -> None:
        ctx_manager = (
            self.capture_manager.global_and_fixture_disabled()
            if self.capture_manager
            else nullcontext()
        )
        with ctx_manager:
            if not self._first_record_emitted:
                self.stream.write("\n")
                self._first_record_emitted = True
            elif self._when in ("teardown", "finish"):
                if not self._test_outcome_written:
                    self._test_outcome_written = True
                    self.stream.write("\n")
            if not self._section_name_shown and self._when:
                self.stream.section("live log " + self._when, sep="-", bold=True)
                self._section_name_shown = True
            super().emit(record)

    def handleError(self, record: logging.LogRecord) -> None:
        # Handled by LogCaptureHandler.
        pass


class _LiveLoggingNullHandler(logging.NullHandler):
    """A logging handler used when live logging is disabled."""

    def reset(self) -> None:
        pass

    def set_when(self, when: str) -> None:
        pass

    def handleError(self, record: logging.LogRecord) -> None:
        # Handled by LogCaptureHandler.
        pass
