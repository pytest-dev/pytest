from __future__ import absolute_import, division, print_function

import sys
import warnings
from contextlib import contextmanager

import pytest

from _pytest import compat


def _setoption(wmod, arg):
    """
    Copy of the warning._setoption function but does not escape arguments.
    """
    parts = arg.split(":")
    if len(parts) > 5:
        raise wmod._OptionError("too many fields (max 5): %r" % (arg,))
    while len(parts) < 5:
        parts.append("")
    action, message, category, module, lineno = [s.strip() for s in parts]
    action = wmod._getaction(action)
    category = wmod._getcategory(category)
    if lineno:
        try:
            lineno = int(lineno)
            if lineno < 0:
                raise ValueError
        except (ValueError, OverflowError):
            raise wmod._OptionError("invalid lineno %r" % (lineno,))
    else:
        lineno = 0
    wmod.filterwarnings(action, message, category, module, lineno)


def pytest_addoption(parser):
    group = parser.getgroup("pytest-warnings")
    group.addoption(
        "-W",
        "--pythonwarnings",
        action="append",
        help="set which warnings to report, see -W option of python itself.",
    )
    parser.addini(
        "filterwarnings",
        type="linelist",
        help="Each line specifies a pattern for "
        "warnings.filterwarnings. "
        "Processed after -W and --pythonwarnings.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "filterwarnings(warning): add a warning filter to the given test. "
        "see https://docs.pytest.org/en/latest/warnings.html#pytest-mark-filterwarnings ",
    )


@contextmanager
def catch_warnings_for_item(config, ihook, item):
    """
    Context manager that catches warnings generated in the contained execution block.

    ``item`` can be None if we are not in the context of an item execution.

    Each warning captured triggers the ``pytest_warning_captured`` hook.
    """
    args = config.getoption("pythonwarnings") or []
    inifilters = config.getini("filterwarnings")
    with warnings.catch_warnings(record=True) as log:
        filters_configured = args or inifilters or sys.warnoptions

        for arg in args:
            warnings._setoption(arg)

        for arg in inifilters:
            _setoption(warnings, arg)

        if item is not None:
            for mark in item.iter_markers(name="filterwarnings"):
                for arg in mark.args:
                    warnings._setoption(arg)
                    filters_configured = True

        if not filters_configured:
            warnings.filterwarnings("always", category=DeprecationWarning)
            warnings.filterwarnings("always", category=PendingDeprecationWarning)

        yield

        for warning_message in log:
            ihook.pytest_warning_captured.call_historic(
                kwargs=dict(warning_message=warning_message, when="runtest", item=item)
            )


def warning_record_to_str(warning_message):
    """Convert a warnings.WarningMessage to a string, taking in account a lot of unicode shenaningans in Python 2.

    When Python 2 support is dropped this function can be greatly simplified.
    """
    warn_msg = warning_message.message
    unicode_warning = False
    if compat._PY2 and any(isinstance(m, compat.UNICODE_TYPES) for m in warn_msg.args):
        new_args = []
        for m in warn_msg.args:
            new_args.append(
                compat.ascii_escaped(m) if isinstance(m, compat.UNICODE_TYPES) else m
            )
        unicode_warning = list(warn_msg.args) != new_args
        warn_msg.args = new_args

    msg = warnings.formatwarning(
        warn_msg,
        warning_message.category,
        warning_message.filename,
        warning_message.lineno,
        warning_message.line,
    )
    if unicode_warning:
        warnings.warn(
            "Warning is using unicode non convertible to ascii, "
            "converting to a safe representation:\n  %s" % msg,
            UnicodeWarning,
        )
    return msg


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item):
    with catch_warnings_for_item(config=item.config, ihook=item.ihook, item=item):
        yield


@pytest.hookimpl(hookwrapper=True)
def pytest_collection(session):
    config = session.config
    with catch_warnings_for_item(config=config, ihook=config.hook, item=None):
        yield


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(terminalreporter):
    config = terminalreporter.config
    with catch_warnings_for_item(config=config, ihook=config.hook, item=None):
        yield
