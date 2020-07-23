import re
import sys
import warnings
from contextlib import contextmanager
from functools import lru_cache
from typing import Generator
from typing import Optional
from typing import Tuple

import pytest
from _pytest.compat import TYPE_CHECKING
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.terminal import TerminalReporter

if TYPE_CHECKING:
    from typing import Type
    from typing_extensions import Literal


@lru_cache(maxsize=50)
def _parse_filter(
    arg: str, *, escape: bool
) -> "Tuple[str, str, Type[Warning], str, int]":
    """Parse a warnings filter string.

    This is copied from warnings._setoption, but does not apply the filter,
    only parses it, and makes the escaping optional.
    """
    parts = arg.split(":")
    if len(parts) > 5:
        raise warnings._OptionError("too many fields (max 5): {!r}".format(arg))
    while len(parts) < 5:
        parts.append("")
    action_, message, category_, module, lineno_ = [s.strip() for s in parts]
    action = warnings._getaction(action_)  # type: str # type: ignore[attr-defined]
    category = warnings._getcategory(
        category_
    )  # type: Type[Warning] # type: ignore[attr-defined]
    if message and escape:
        message = re.escape(message)
    if module and escape:
        module = re.escape(module) + r"\Z"
    if lineno_:
        try:
            lineno = int(lineno_)
            if lineno < 0:
                raise ValueError
        except (ValueError, OverflowError) as e:
            raise warnings._OptionError("invalid lineno {!r}".format(lineno_)) from e
    else:
        lineno = 0
    return (action, message, category, module, lineno)


def pytest_addoption(parser: Parser) -> None:
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
        "Processed after -W/--pythonwarnings.",
    )


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers",
        "filterwarnings(warning): add a warning filter to the given test. "
        "see https://docs.pytest.org/en/stable/warnings.html#pytest-mark-filterwarnings ",
    )


@contextmanager
def catch_warnings_for_item(
    config: Config,
    ihook,
    when: "Literal['config', 'collect', 'runtest']",
    item: Optional[Item],
) -> Generator[None, None, None]:
    """
    Context manager that catches warnings generated in the contained execution block.

    ``item`` can be None if we are not in the context of an item execution.

    Each warning captured triggers the ``pytest_warning_recorded`` hook.
    """
    cmdline_filters = config.getoption("pythonwarnings") or []
    inifilters = config.getini("filterwarnings")
    with warnings.catch_warnings(record=True) as log:
        # mypy can't infer that record=True means log is not None; help it.
        assert log is not None

        if not sys.warnoptions:
            # if user is not explicitly configuring warning filters, show deprecation warnings by default (#2908)
            warnings.filterwarnings("always", category=DeprecationWarning)
            warnings.filterwarnings("always", category=PendingDeprecationWarning)

        warnings.filterwarnings("error", category=pytest.PytestDeprecationWarning)

        # filters should have this precedence: mark, cmdline options, ini
        # filters should be applied in the inverse order of precedence
        for arg in inifilters:
            warnings.filterwarnings(*_parse_filter(arg, escape=False))

        for arg in cmdline_filters:
            warnings.filterwarnings(*_parse_filter(arg, escape=True))

        nodeid = "" if item is None else item.nodeid
        if item is not None:
            for mark in item.iter_markers(name="filterwarnings"):
                for arg in mark.args:
                    warnings.filterwarnings(*_parse_filter(arg, escape=False))

        yield

        for warning_message in log:
            ihook.pytest_warning_captured.call_historic(
                kwargs=dict(
                    warning_message=warning_message,
                    when=when,
                    item=item,
                    location=None,
                )
            )
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
    warn_msg = warning_message.message
    msg = warnings.formatwarning(
        str(warn_msg),
        warning_message.category,
        warning_message.filename,
        warning_message.lineno,
        warning_message.line,
    )
    return msg


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item: Item) -> Generator[None, None, None]:
    with catch_warnings_for_item(
        config=item.config, ihook=item.ihook, when="runtest", item=item
    ):
        yield


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection(session: Session) -> Generator[None, None, None]:
    config = session.config
    with catch_warnings_for_item(
        config=config, ihook=config.hook, when="collect", item=None
    ):
        yield


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(
    terminalreporter: TerminalReporter,
) -> Generator[None, None, None]:
    config = terminalreporter.config
    with catch_warnings_for_item(
        config=config, ihook=config.hook, when="config", item=None
    ):
        yield


@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(session: Session) -> Generator[None, None, None]:
    config = session.config
    with catch_warnings_for_item(
        config=config, ihook=config.hook, when="config", item=None
    ):
        yield


def _issue_warning_captured(warning: Warning, hook, stacklevel: int) -> None:
    """
    This function should be used instead of calling ``warnings.warn`` directly when we are in the "configure" stage:
    at this point the actual options might not have been set, so we manually trigger the pytest_warning_recorded
    hook so we can display these warnings in the terminal. This is a hack until we can sort out #2891.

    :param warning: the warning instance.
    :param hook: the hook caller
    :param stacklevel: stacklevel forwarded to warnings.warn
    """
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always", type(warning))
        warnings.warn(warning, stacklevel=stacklevel)
    frame = sys._getframe(stacklevel - 1)
    location = frame.f_code.co_filename, frame.f_lineno, frame.f_code.co_name
    hook.pytest_warning_captured.call_historic(
        kwargs=dict(
            warning_message=records[0], when="config", item=None, location=location
        )
    )
    hook.pytest_warning_recorded.call_historic(
        kwargs=dict(
            warning_message=records[0], when="config", nodeid="", location=location
        )
    )
