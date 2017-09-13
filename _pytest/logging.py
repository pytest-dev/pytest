from __future__ import absolute_import, division, print_function

import logging
from contextlib import closing, contextmanager
import functools
import sys

import pytest
import py


DEFAULT_LOG_FORMAT = '%(filename)-25s %(lineno)4d %(levelname)-8s %(message)s'
DEFAULT_LOG_DATE_FORMAT = '%H:%M:%S'


def add_option_ini(parser, option, dest, default=None, **kwargs):
    parser.addini(dest, default=default,
                  help='default value for ' + option)
    parser.getgroup('catchlog').addoption(option, dest=dest, **kwargs)


def get_option_ini(config, name):
    ret = config.getoption(name)  # 'default' arg won't work as expected
    if ret is None:
        ret = config.getini(name)
    return ret


def pytest_addoption(parser):
    """Add options to control log capturing."""

    group = parser.getgroup('catchlog', 'Log catching')
    add_option_ini(parser,
        '--no-print-logs',
        dest='log_print', action='store_const', const=False, default=True,
        help='disable printing caught logs on failed tests.'
    )
    add_option_ini(
        parser,
        '--log-level',
        dest='log_level', default=None,
        help='logging level used by the logging module'
    )
    add_option_ini(parser,
        '--log-format',
        dest='log_format', default=DEFAULT_LOG_FORMAT,
        help='log format as used by the logging module.'
    )
    add_option_ini(parser,
        '--log-date-format',
        dest='log_date_format', default=DEFAULT_LOG_DATE_FORMAT,
        help='log date format as used by the logging module.'
    )
    add_option_ini(
        parser,
        '--log-cli-level',
        dest='log_cli_level', default=None,
        help='cli logging level.'
    )
    add_option_ini(
        parser,
        '--log-cli-format',
        dest='log_cli_format', default=None,
        help='log format as used by the logging module.'
    )
    add_option_ini(
        parser,
        '--log-cli-date-format',
        dest='log_cli_date_format', default=None,
        help='log date format as used by the logging module.'
    )
    add_option_ini(
        parser,
        '--log-file',
        dest='log_file', default=None,
        help='path to a file when logging will be written to.'
    )
    add_option_ini(
        parser,
        '--log-file-level',
        dest='log_file_level', default=None,
        help='log file logging level.'
    )
    add_option_ini(
        parser,
        '--log-file-format',
        dest='log_file_format', default=DEFAULT_LOG_FORMAT,
        help='log format as used by the logging module.'
    )
    add_option_ini(
        parser,
        '--log-file-date-format',
        dest='log_file_date_format', default=DEFAULT_LOG_DATE_FORMAT,
        help='log date format as used by the logging module.'
    )


def get_logger_obj(logger=None):
    """Get a logger object that can be specified by its name, or passed as is.

    Defaults to the root logger.
    """
    if logger is None or isinstance(logger, py.builtin._basestring):
        logger = logging.getLogger(logger)
    return logger


@contextmanager
def logging_at_level(level, logger=None):
    """Context manager that sets the level for capturing of logs."""
    logger = get_logger_obj(logger)

    orig_level = logger.level
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(orig_level)


@contextmanager
def logging_using_handler(handler, logger=None):
    """Context manager that safely registers a given handler."""
    logger = get_logger_obj(logger)

    if handler in logger.handlers:  # reentrancy
        # Adding the same handler twice would confuse logging system.
        # Just don't do that.
        yield
    else:
        logger.addHandler(handler)
        try:
            yield
        finally:
            logger.removeHandler(handler)


@contextmanager
def catching_logs(handler, filter=None, formatter=None,
                  level=logging.NOTSET, logger=None):
    """Context manager that prepares the whole logging machinery properly."""
    logger = get_logger_obj(logger)

    if filter is not None:
        handler.addFilter(filter)
    if formatter is not None:
        handler.setFormatter(formatter)
    handler.setLevel(level)

    with closing(handler):
        with logging_using_handler(handler, logger):
            with logging_at_level(min(handler.level, logger.level), logger):

                yield handler


class LogCaptureFixture(object):
    """Provides access and control of log capturing."""

    def __init__(self, item):
        """Creates a new funcarg."""
        self._item = item

    @property
    def handler(self):
        return self._item.catch_log_handler

    @property
    def text(self):
        """Returns the log text."""
        return self.handler.stream.getvalue()

    @property
    def records(self):
        """Returns the list of log records."""
        return self.handler.records

    @property
    def record_tuples(self):
        """Returns a list of a striped down version of log records intended
        for use in assertion comparison.

        The format of the tuple is:

            (logger_name, log_level, message)
        """
        return [(r.name, r.levelno, r.getMessage()) for r in self.records]

    def clear(self):
        """Reset the list of log records."""
        self.handler.records = []

    def set_level(self, level, logger=None):
        """Sets the level for capturing of logs.

        By default, the level is set on the handler used to capture
        logs. Specify a logger name to instead set the level of any
        logger.
        """

        obj = logger and logging.getLogger(logger) or self.handler
        obj.setLevel(level)

    def at_level(self, level, logger=None):
        """Context manager that sets the level for capturing of logs.

        By default, the level is set on the handler used to capture
        logs. Specify a logger name to instead set the level of any
        logger.
        """

        obj = logger and logging.getLogger(logger) or self.handler
        return logging_at_level(level, obj)


class CallablePropertyMixin(object):
    """Backward compatibility for functions that became properties."""

    @classmethod
    def compat_property(cls, func):
        if isinstance(func, property):
            make_property = func.getter
            func = func.fget
        else:
            make_property = property

        @functools.wraps(func)
        def getter(self):
            naked_value = func(self)
            ret = cls(naked_value)
            ret._naked_value = naked_value
            ret._warn_compat = self._warn_compat
            ret._prop_name = func.__name__
            return ret

        return make_property(getter)

    def __call__(self):
        new = "'caplog.{0}' property".format(self._prop_name)
        if self._prop_name == 'records':
            new += ' (or caplog.clear())'
        self._warn_compat(old="'caplog.{0}()' syntax".format(self._prop_name),
                          new=new)
        return self._naked_value  # to let legacy clients modify the object


class CallableList(CallablePropertyMixin, list):
    pass


class CallableStr(CallablePropertyMixin, py.builtin.text):
    pass


class CompatLogCaptureFixture(LogCaptureFixture):
    """Backward compatibility with pytest-capturelog."""

    def _warn_compat(self, old, new):
        self._item.warn(code='L1',
                        message=("{0} is deprecated, use {1} instead"
                                 .format(old, new)))

    @CallableStr.compat_property
    def text(self):
        return super(CompatLogCaptureFixture, self).text

    @CallableList.compat_property
    def records(self):
        return super(CompatLogCaptureFixture, self).records

    @CallableList.compat_property
    def record_tuples(self):
        return super(CompatLogCaptureFixture, self).record_tuples

    def setLevel(self, level, logger=None):
        self._warn_compat(old="'caplog.setLevel()'",
                          new="'caplog.set_level()'")
        return self.set_level(level, logger)

    def atLevel(self, level, logger=None):
        self._warn_compat(old="'caplog.atLevel()'",
                          new="'caplog.at_level()'")
        return self.at_level(level, logger)


@pytest.fixture
def caplog(request):
    """Access and control log capturing.

    Captured logs are available through the following methods::

    * caplog.text()          -> string containing formatted log output
    * caplog.records()       -> list of logging.LogRecord instances
    * caplog.record_tuples() -> list of (logger_name, level, message) tuples
    """
    return CompatLogCaptureFixture(request.node)


def get_actual_log_level(config, setting_name):
    """Return the actual logging level."""
    log_level = get_option_ini(config, setting_name)
    if not log_level:
        return
    if isinstance(log_level, py.builtin.text):
        log_level = log_level.upper()
    try:
        return int(getattr(logging, log_level, log_level))
    except ValueError:
        # Python logging does not recognise this as a logging level
        raise pytest.UsageError(
            "'{0}' is not recognized as a logging level name for "
            "'{1}'. Please consider passing the "
            "logging level num instead.".format(
                log_level,
                setting_name))


def pytest_configure(config):
    """Always register the log catcher plugin with py.test or tests can't
    find the  fixture function.
    """
    log_cli_level = get_actual_log_level(config, 'log_cli_level')
    if log_cli_level is None:
        # No specific CLI logging level was provided, let's check
        # log_level for a fallback
        log_cli_level = get_actual_log_level(config, 'log_level')
        if log_cli_level is None:
            # No log_level was provided, default to WARNING
            log_cli_level = logging.WARNING
    config._catchlog_log_cli_level = log_cli_level
    config._catchlog_log_file = get_option_ini(config, 'log_file')
    if config._catchlog_log_file:
        log_file_level = get_actual_log_level(config, 'log_file_level')
        if log_file_level is None:
            # No log_level was provided, default to WARNING
            log_file_level = logging.WARNING
        config._catchlog_log_file_level = log_file_level
    config.pluginmanager.register(LoggingPlugin(config))


class LoggingPlugin(object):
    """Attaches to the logging module and captures log messages for each test.
    """

    def __init__(self, config):
        """Creates a new plugin to capture log messages.

        The formatter can be safely shared across all handlers so
        create a single one for the entire test session here.
        """
        print_logs = get_option_ini(config, 'log_print')
        if not isinstance(print_logs, bool):
            if print_logs.lower() in ('true', 'yes', '1'):
                print_logs = True
            elif print_logs.lower() in ('false', 'no', '0'):
                print_logs = False
        self.print_logs = print_logs
        self.formatter = logging.Formatter(
                get_option_ini(config, 'log_format'),
                get_option_ini(config, 'log_date_format'))
        self.log_cli_handler = logging.StreamHandler(sys.stderr)
        log_cli_format = get_option_ini(config, 'log_cli_format')
        if not log_cli_format:
            # No CLI specific format was provided, use log_format
            log_cli_format = get_option_ini(config, 'log_format')
        log_cli_date_format = get_option_ini(config, 'log_cli_date_format')
        if not log_cli_date_format:
            # No CLI specific date format was provided, use log_date_format
            log_cli_date_format = get_option_ini(config, 'log_date_format')
        log_cli_formatter = logging.Formatter(
                log_cli_format,
                datefmt=log_cli_date_format)
        self.log_cli_handler.setFormatter(log_cli_formatter)
        if config._catchlog_log_file:
            log_file_format = get_option_ini(config, 'log_file_format')
            if not log_file_format:
                # No log file specific format was provided, use log_format
                log_file_format = get_option_ini(config, 'log_format')
            log_file_date_format = get_option_ini(config, 'log_file_date_format')
            if not log_file_date_format:
                # No log file specific date format was provided, use log_date_format
                log_file_date_format = get_option_ini(config, 'log_date_format')
            self.log_file_handler = logging.FileHandler(
                config._catchlog_log_file,
                # Each pytest runtests session will write to a clean logfile
                mode='w',
            )
            log_file_formatter = logging.Formatter(
                    log_file_format,
                    datefmt=log_file_date_format)
            self.log_file_handler.setFormatter(log_file_formatter)
        else:
            self.log_file_handler = None

    @contextmanager
    def _runtest_for(self, item, when):
        """Implements the internals of pytest_runtest_xxx() hook."""
        with catching_logs(LogCaptureHandler(),
                           formatter=self.formatter) as log_handler:
            item.catch_log_handler = log_handler
            try:
                yield  # run test
            finally:
                del item.catch_log_handler

            if self.print_logs:
                # Add a captured log section to the report.
                log = log_handler.stream.getvalue().strip()
                item.add_report_section(when, 'log', log)

    @pytest.mark.hookwrapper
    def pytest_runtest_setup(self, item):
        with self._runtest_for(item, 'setup'):
            yield

    @pytest.mark.hookwrapper
    def pytest_runtest_call(self, item):
        with self._runtest_for(item, 'call'):
            yield

    @pytest.mark.hookwrapper
    def pytest_runtest_teardown(self, item):
        with self._runtest_for(item, 'teardown'):
            yield

    @pytest.mark.hookwrapper
    def pytest_runtestloop(self, session):
        """Runs all collected test items."""
        with catching_logs(self.log_cli_handler,
                           level=session.config._catchlog_log_cli_level):
            if self.log_file_handler is not None:
                with catching_logs(self.log_file_handler,
                                   level=session.config._catchlog_log_file_level):
                    yield  # run all the tests
            else:
                yield  # run all the tests


class LogCaptureHandler(logging.StreamHandler):
    """A logging handler that stores log records and the log text."""

    def __init__(self):
        """Creates a new log handler."""

        logging.StreamHandler.__init__(self)
        self.stream = py.io.TextIO()
        self.records = []

    def close(self):
        """Close this log handler and its underlying stream."""

        logging.StreamHandler.close(self)
        self.stream.close()

    def emit(self, record):
        """Keep the log records in a list in addition to the log text."""

        self.records.append(record)
        logging.StreamHandler.emit(self, record)
