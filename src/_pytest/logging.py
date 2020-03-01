""" Access and control log capturing. """
import logging
import re
from contextlib import contextmanager
from io import StringIO
from typing import AbstractSet
from typing import Dict
from typing import Generator
from typing import List
from typing import Mapping
from typing import Optional

import pytest
from _pytest import nodes
from _pytest.compat import nullcontext
from _pytest.config import _strtobool
from _pytest.config import Config
from _pytest.config import create_terminal_writer
from _pytest.pathlib import Path

DEFAULT_LOG_FORMAT = "%(levelname)-8s %(name)s:%(filename)s:%(lineno)d %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%H:%M:%S"
_ANSI_ESCAPE_SEQ = re.compile(r"\x1b\[[\d;]+m")


def _remove_ansi_escape_sequences(text):
    return _ANSI_ESCAPE_SEQ.sub("", text)


class ColoredLevelFormatter(logging.Formatter):
    """
    Colorize the %(levelname)..s part of the log format passed to __init__.
    """

    LOGLEVEL_COLOROPTS = {
        logging.CRITICAL: {"red"},
        logging.ERROR: {"red", "bold"},
        logging.WARNING: {"yellow"},
        logging.WARN: {"yellow"},
        logging.INFO: {"green"},
        logging.DEBUG: {"purple"},
        logging.NOTSET: set(),
    }  # type: Mapping[int, AbstractSet[str]]
    LEVELNAME_FMT_REGEX = re.compile(r"%\(levelname\)([+-.]?\d*s)")

    def __init__(self, terminalwriter, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._original_fmt = self._style._fmt
        self._level_to_fmt_mapping = {}  # type: Dict[int, str]

        assert self._fmt is not None
        levelname_fmt_match = self.LEVELNAME_FMT_REGEX.search(self._fmt)
        if not levelname_fmt_match:
            return
        levelname_fmt = levelname_fmt_match.group()

        for level, color_opts in self.LOGLEVEL_COLOROPTS.items():
            formatted_levelname = levelname_fmt % {
                "levelname": logging.getLevelName(level)
            }

            # add ANSI escape sequences around the formatted levelname
            color_kwargs = {name: True for name in color_opts}
            colorized_formatted_levelname = terminalwriter.markup(
                formatted_levelname, **color_kwargs
            )
            self._level_to_fmt_mapping[level] = self.LEVELNAME_FMT_REGEX.sub(
                colorized_formatted_levelname, self._fmt
            )

    def format(self, record):
        fmt = self._level_to_fmt_mapping.get(record.levelno, self._original_fmt)
        self._style._fmt = fmt
        return super().format(record)


class PercentStyleMultiline(logging.PercentStyle):
    """A logging style with special support for multiline messages.

    If the message of a record consists of multiple lines, this style
    formats the message as if each line were logged separately.
    """

    def __init__(self, fmt, auto_indent):
        super().__init__(fmt)
        self._auto_indent = self._get_auto_indent(auto_indent)

    @staticmethod
    def _update_message(record_dict, message):
        tmp = record_dict.copy()
        tmp["message"] = message
        return tmp

    @staticmethod
    def _get_auto_indent(auto_indent_option) -> int:
        """Determines the current auto indentation setting

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

        :param any auto_indent_option: User specified option for indentation
            from command line, config or extra kwarg. Accepts int, bool or str.
            str option accepts the same range of values as boolean config options,
            as well as positive integers represented in str form.

        :returns: indentation value, which can be
            -1 (automatically determine indentation) or
            0 (auto-indent turned off) or
            >0 (explicitly set indentation position).
        """

        if type(auto_indent_option) is int:
            return int(auto_indent_option)
        elif type(auto_indent_option) is str:
            try:
                return int(auto_indent_option)
            except ValueError:
                pass
            try:
                if _strtobool(auto_indent_option):
                    return -1
            except ValueError:
                return 0
        elif type(auto_indent_option) is bool:
            if auto_indent_option:
                return -1

        return 0

    def format(self, record):
        if "\n" in record.message:
            if hasattr(record, "auto_indent"):
                # passed in from the "extra={}" kwarg on the call to logging.log()
                auto_indent = self._get_auto_indent(record.auto_indent)
            else:
                auto_indent = self._auto_indent

            if auto_indent:
                lines = record.message.splitlines()
                formatted = self._fmt % self._update_message(record.__dict__, lines[0])

                if auto_indent < 0:
                    indentation = _remove_ansi_escape_sequences(formatted).find(
                        lines[0]
                    )
                else:
                    # optimizes logging by allowing a fixed indentation
                    indentation = auto_indent
                lines[0] = formatted
                return ("\n" + " " * indentation).join(lines)
        return self._fmt % record.__dict__


def get_option_ini(config, *names):
    for name in names:
        ret = config.getoption(name)  # 'default' arg won't work as expected
        if ret is None:
            ret = config.getini(name)
        if ret:
            return ret


def pytest_addoption(parser):
    """Add options to control log capturing."""
    group = parser.getgroup("logging")

    def add_option_ini(option, dest, default=None, type=None, **kwargs):
        parser.addini(
            dest, default=default, type=type, help="default value for " + option
        )
        group.addoption(option, dest=dest, **kwargs)

    add_option_ini(
        "--no-print-logs",
        dest="log_print",
        action="store_const",
        const=False,
        default=True,
        type="bool",
        help="disable printing caught logs on failed tests.",
    )
    add_option_ini(
        "--log-level",
        dest="log_level",
        default=None,
        metavar="LEVEL",
        help=(
            "level of messages to catch/display.\n"
            "Not set by default, so it depends on the root/parent log handler's"
            ' effective level, where it is "WARNING" by default.'
        ),
    )
    add_option_ini(
        "--log-format",
        dest="log_format",
        default=DEFAULT_LOG_FORMAT,
        help="log format as used by the logging module.",
    )
    add_option_ini(
        "--log-date-format",
        dest="log_date_format",
        default=DEFAULT_LOG_DATE_FORMAT,
        help="log date format as used by the logging module.",
    )
    parser.addini(
        "log_cli",
        default=False,
        type="bool",
        help='enable log display during test run (also known as "live logging").',
    )
    add_option_ini(
        "--log-cli-level", dest="log_cli_level", default=None, help="cli logging level."
    )
    add_option_ini(
        "--log-cli-format",
        dest="log_cli_format",
        default=None,
        help="log format as used by the logging module.",
    )
    add_option_ini(
        "--log-cli-date-format",
        dest="log_cli_date_format",
        default=None,
        help="log date format as used by the logging module.",
    )
    add_option_ini(
        "--log-file",
        dest="log_file",
        default=None,
        help="path to a file when logging will be written to.",
    )
    add_option_ini(
        "--log-file-level",
        dest="log_file_level",
        default=None,
        help="log file logging level.",
    )
    add_option_ini(
        "--log-file-format",
        dest="log_file_format",
        default=DEFAULT_LOG_FORMAT,
        help="log format as used by the logging module.",
    )
    add_option_ini(
        "--log-file-date-format",
        dest="log_file_date_format",
        default=DEFAULT_LOG_DATE_FORMAT,
        help="log date format as used by the logging module.",
    )
    add_option_ini(
        "--log-auto-indent",
        dest="log_auto_indent",
        default=None,
        help="Auto-indent multiline messages passed to the logging module. Accepts true|on, false|off or an integer.",
    )


@contextmanager
def catching_logs(handler, formatter=None, level=None):
    """Context manager that prepares the whole logging machinery properly."""
    root_logger = logging.getLogger()

    if formatter is not None:
        handler.setFormatter(formatter)
    if level is not None:
        handler.setLevel(level)

    # Adding the same handler twice would confuse logging system.
    # Just don't do that.
    add_new_handler = handler not in root_logger.handlers

    if add_new_handler:
        root_logger.addHandler(handler)
    if level is not None:
        orig_level = root_logger.level
        root_logger.setLevel(min(orig_level, level))
    try:
        yield handler
    finally:
        if level is not None:
            root_logger.setLevel(orig_level)
        if add_new_handler:
            root_logger.removeHandler(handler)


class LogCaptureHandler(logging.StreamHandler):
    """A logging handler that stores log records and the log text."""

    def __init__(self) -> None:
        """Creates a new log handler."""
        logging.StreamHandler.__init__(self, StringIO())
        self.records = []  # type: List[logging.LogRecord]

    def emit(self, record: logging.LogRecord) -> None:
        """Keep the log records in a list in addition to the log text."""
        self.records.append(record)
        logging.StreamHandler.emit(self, record)

    def reset(self) -> None:
        self.records = []
        self.stream = StringIO()


class LogCaptureFixture:
    """Provides access and control of log capturing."""

    def __init__(self, item) -> None:
        """Creates a new funcarg."""
        self._item = item
        # dict of log name -> log level
        self._initial_log_levels = {}  # type: Dict[str, int]

    def _finalize(self) -> None:
        """Finalizes the fixture.

        This restores the log levels changed by :meth:`set_level`.
        """
        # restore log levels
        for logger_name, level in self._initial_log_levels.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)

    @property
    def handler(self) -> LogCaptureHandler:
        """
        :rtype: LogCaptureHandler
        """
        return self._item.catch_log_handler  # type: ignore[no-any-return]  # noqa: F723

    def get_records(self, when: str) -> List[logging.LogRecord]:
        """
        Get the logging records for one of the possible test phases.

        :param str when:
            Which test phase to obtain the records from. Valid values are: "setup", "call" and "teardown".

        :rtype: List[logging.LogRecord]
        :return: the list of captured records at the given stage

        .. versionadded:: 3.4
        """
        handler = self._item.catch_log_handlers.get(when)
        if handler:
            return handler.records  # type: ignore[no-any-return]  # noqa: F723
        else:
            return []

    @property
    def text(self):
        """Returns the formatted log text."""
        return _remove_ansi_escape_sequences(self.handler.stream.getvalue())

    @property
    def records(self):
        """Returns the list of log records."""
        return self.handler.records

    @property
    def record_tuples(self):
        """Returns a list of a stripped down version of log records intended
        for use in assertion comparison.

        The format of the tuple is:

            (logger_name, log_level, message)
        """
        return [(r.name, r.levelno, r.getMessage()) for r in self.records]

    @property
    def messages(self):
        """Returns a list of format-interpolated log messages.

        Unlike 'records', which contains the format string and parameters for interpolation, log messages in this list
        are all interpolated.
        Unlike 'text', which contains the output from the handler, log messages in this list are unadorned with
        levels, timestamps, etc, making exact comparisons more reliable.

        Note that traceback or stack info (from :func:`logging.exception` or the `exc_info` or `stack_info` arguments
        to the logging functions) is not included, as this is added by the formatter in the handler.

        .. versionadded:: 3.7
        """
        return [r.getMessage() for r in self.records]

    def clear(self):
        """Reset the list of log records and the captured log text."""
        self.handler.reset()

    def set_level(self, level, logger=None):
        """Sets the level for capturing of logs. The level will be restored to its previous value at the end of
        the test.

        :param int level: the logger to level.
        :param str logger: the logger to update the level. If not given, the root logger level is updated.

        .. versionchanged:: 3.4
            The levels of the loggers changed by this function will be restored to their initial values at the
            end of the test.
        """
        logger_name = logger
        logger = logging.getLogger(logger_name)
        # save the original log-level to restore it during teardown
        self._initial_log_levels.setdefault(logger_name, logger.level)
        logger.setLevel(level)

    @contextmanager
    def at_level(self, level, logger=None):
        """Context manager that sets the level for capturing of logs. After the end of the 'with' statement the
        level is restored to its original value.

        :param int level: the logger to level.
        :param str logger: the logger to update the level. If not given, the root logger level is updated.
        """
        logger = logging.getLogger(logger)
        orig_level = logger.level
        logger.setLevel(level)
        try:
            yield
        finally:
            logger.setLevel(orig_level)


@pytest.fixture
def caplog(request):
    """Access and control log capturing.

    Captured logs are available through the following properties/methods::

    * caplog.messages        -> list of format-interpolated log messages
    * caplog.text            -> string containing formatted log output
    * caplog.records         -> list of logging.LogRecord instances
    * caplog.record_tuples   -> list of (logger_name, level, message) tuples
    * caplog.clear()         -> clear captured records and formatted log output string
    """
    result = LogCaptureFixture(request.node)
    yield result
    result._finalize()


def get_log_level_for_setting(config: Config, *setting_names: str) -> Optional[int]:
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
    except ValueError:
        # Python logging does not recognise this as a logging level
        raise pytest.UsageError(
            "'{}' is not recognized as a logging level name for "
            "'{}'. Please consider passing the "
            "logging level num instead.".format(log_level, setting_name)
        )


# run after terminalreporter/capturemanager are configured
@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    config.pluginmanager.register(LoggingPlugin(config), "logging-plugin")


class LoggingPlugin:
    """Attaches to the logging module and captures log messages for each test.
    """

    def __init__(self, config: Config) -> None:
        """Creates a new plugin to capture log messages.

        The formatter can be safely shared across all handlers so
        create a single one for the entire test session here.
        """
        self._config = config

        self.print_logs = get_option_ini(config, "log_print")
        if not self.print_logs:
            from _pytest.warnings import _issue_warning_captured
            from _pytest.deprecated import NO_PRINT_LOGS

            _issue_warning_captured(NO_PRINT_LOGS, self._config.hook, stacklevel=2)

        self.formatter = self._create_formatter(
            get_option_ini(config, "log_format"),
            get_option_ini(config, "log_date_format"),
            get_option_ini(config, "log_auto_indent"),
        )
        self.log_level = get_log_level_for_setting(config, "log_level")

        self.log_file_level = get_log_level_for_setting(config, "log_file_level")
        self.log_file_format = get_option_ini(config, "log_file_format", "log_format")
        self.log_file_date_format = get_option_ini(
            config, "log_file_date_format", "log_date_format"
        )
        self.log_file_formatter = logging.Formatter(
            self.log_file_format, datefmt=self.log_file_date_format
        )

        log_file = get_option_ini(config, "log_file")
        if log_file:
            self.log_file_handler = logging.FileHandler(
                log_file, mode="w", encoding="UTF-8"
            )  # type: Optional[logging.FileHandler]
            self.log_file_handler.setFormatter(self.log_file_formatter)
        else:
            self.log_file_handler = None

        self.log_cli_handler = None

        self.live_logs_context = lambda: nullcontext()
        # Note that the lambda for the live_logs_context is needed because
        # live_logs_context can otherwise not be entered multiple times due
        # to limitations of contextlib.contextmanager.

        if self._log_cli_enabled():
            self._setup_cli_logging()

    def _create_formatter(self, log_format, log_date_format, auto_indent):
        # color option doesn't exist if terminal plugin is disabled
        color = getattr(self._config.option, "color", "no")
        if color != "no" and ColoredLevelFormatter.LEVELNAME_FMT_REGEX.search(
            log_format
        ):
            formatter = ColoredLevelFormatter(
                create_terminal_writer(self._config), log_format, log_date_format
            )  # type: logging.Formatter
        else:
            formatter = logging.Formatter(log_format, log_date_format)

        formatter._style = PercentStyleMultiline(
            formatter._style._fmt, auto_indent=auto_indent
        )

        return formatter

    def _setup_cli_logging(self):
        config = self._config
        terminal_reporter = config.pluginmanager.get_plugin("terminalreporter")
        if terminal_reporter is None:
            # terminal reporter is disabled e.g. by pytest-xdist.
            return

        capture_manager = config.pluginmanager.get_plugin("capturemanager")
        # if capturemanager plugin is disabled, live logging still works.
        log_cli_handler = _LiveLoggingStreamHandler(terminal_reporter, capture_manager)

        log_cli_formatter = self._create_formatter(
            get_option_ini(config, "log_cli_format", "log_format"),
            get_option_ini(config, "log_cli_date_format", "log_date_format"),
            get_option_ini(config, "log_auto_indent"),
        )

        log_cli_level = get_log_level_for_setting(config, "log_cli_level", "log_level")
        self.log_cli_handler = log_cli_handler
        self.live_logs_context = lambda: catching_logs(
            log_cli_handler, formatter=log_cli_formatter, level=log_cli_level
        )

    def set_log_path(self, fname):
        """Public method, which can set filename parameter for
        Logging.FileHandler(). Also creates parent directory if
        it does not exist.

        .. warning::
            Please considered as an experimental API.
        """
        fname = Path(fname)

        if not fname.is_absolute():
            fname = Path(self._config.rootdir, fname)

        if not fname.parent.exists():
            fname.parent.mkdir(exist_ok=True, parents=True)

        self.log_file_handler = logging.FileHandler(
            str(fname), mode="w", encoding="UTF-8"
        )
        self.log_file_handler.setFormatter(self.log_file_formatter)

    def _log_cli_enabled(self):
        """Return True if log_cli should be considered enabled, either explicitly
        or because --log-cli-level was given in the command-line.
        """
        return self._config.getoption(
            "--log-cli-level"
        ) is not None or self._config.getini("log_cli")

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_collection(self) -> Generator[None, None, None]:
        with self.live_logs_context():
            if self.log_cli_handler:
                self.log_cli_handler.set_when("collection")

            if self.log_file_handler is not None:
                with catching_logs(self.log_file_handler, level=self.log_file_level):
                    yield
            else:
                yield

    @contextmanager
    def _runtest_for(self, item, when):
        with self._runtest_for_main(item, when):
            if self.log_file_handler is not None:
                with catching_logs(self.log_file_handler, level=self.log_file_level):
                    yield
            else:
                yield

    @contextmanager
    def _runtest_for_main(
        self, item: nodes.Item, when: str
    ) -> Generator[None, None, None]:
        """Implements the internals of pytest_runtest_xxx() hook."""
        with catching_logs(
            LogCaptureHandler(), formatter=self.formatter, level=self.log_level
        ) as log_handler:
            if self.log_cli_handler:
                self.log_cli_handler.set_when(when)

            if item is None:
                yield  # run the test
                return

            if not hasattr(item, "catch_log_handlers"):
                item.catch_log_handlers = {}  # type: ignore[attr-defined]  # noqa: F821
            item.catch_log_handlers[when] = log_handler  # type: ignore[attr-defined]  # noqa: F821
            item.catch_log_handler = log_handler  # type: ignore[attr-defined]  # noqa: F821
            try:
                yield  # run test
            finally:
                if when == "teardown":
                    del item.catch_log_handler  # type: ignore[attr-defined]  # noqa: F821
                    del item.catch_log_handlers  # type: ignore[attr-defined]  # noqa: F821

            if self.print_logs:
                # Add a captured log section to the report.
                log = log_handler.stream.getvalue().strip()
                item.add_report_section(when, "log", log)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        with self._runtest_for(item, "setup"):
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        with self._runtest_for(item, "call"):
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(self, item):
        with self._runtest_for(item, "teardown"):
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_logstart(self):
        if self.log_cli_handler:
            self.log_cli_handler.reset()
        with self._runtest_for(None, "start"):
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_logfinish(self):
        with self._runtest_for(None, "finish"):
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_logreport(self):
        with self._runtest_for(None, "logreport"):
            yield

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_sessionfinish(self):
        with self.live_logs_context():
            if self.log_cli_handler:
                self.log_cli_handler.set_when("sessionfinish")
            if self.log_file_handler is not None:
                try:
                    with catching_logs(
                        self.log_file_handler, level=self.log_file_level
                    ):
                        yield
                finally:
                    # Close the FileHandler explicitly.
                    # (logging.shutdown might have lost the weakref?!)
                    self.log_file_handler.close()
            else:
                yield

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_sessionstart(self):
        with self.live_logs_context():
            if self.log_cli_handler:
                self.log_cli_handler.set_when("sessionstart")
            if self.log_file_handler is not None:
                with catching_logs(self.log_file_handler, level=self.log_file_level):
                    yield
            else:
                yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtestloop(self, session):
        """Runs all collected test items."""

        if session.config.option.collectonly:
            yield
            return

        if self._log_cli_enabled() and self._config.getoption("verbose") < 1:
            # setting verbose flag is needed to avoid messy test progress output
            self._config.option.verbose = 1

        with self.live_logs_context():
            if self.log_file_handler is not None:
                with catching_logs(self.log_file_handler, level=self.log_file_level):
                    yield  # run all the tests
            else:
                yield  # run all the tests


class _LiveLoggingStreamHandler(logging.StreamHandler):
    """
    Custom StreamHandler used by the live logging feature: it will write a newline before the first log message
    in each test.

    During live logging we must also explicitly disable stdout/stderr capturing otherwise it will get captured
    and won't appear in the terminal.
    """

    def __init__(self, terminal_reporter, capture_manager):
        """
        :param _pytest.terminal.TerminalReporter terminal_reporter:
        :param _pytest.capture.CaptureManager capture_manager:
        """
        logging.StreamHandler.__init__(self, stream=terminal_reporter)
        self.capture_manager = capture_manager
        self.reset()
        self.set_when(None)
        self._test_outcome_written = False

    def reset(self):
        """Reset the handler; should be called before the start of each test"""
        self._first_record_emitted = False

    def set_when(self, when):
        """Prepares for the given test phase (setup/call/teardown)"""
        self._when = when
        self._section_name_shown = False
        if when == "start":
            self._test_outcome_written = False

    def emit(self, record):
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
            logging.StreamHandler.emit(self, record)
