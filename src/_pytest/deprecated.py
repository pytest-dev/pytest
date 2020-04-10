"""
This module contains deprecation messages and bits of code used elsewhere in the codebase
that is planned to be removed in the next pytest release.

Keeping it in a central location makes it easy to track what is deprecated and should
be removed when the time comes.

All constants defined in this module should be either PytestWarning instances or UnformattedWarning
in case of warnings which need to format their messages.
"""
from _pytest.warning_types import PytestDeprecationWarning
from _pytest.warning_types import UnformattedWarning

# set of plugins which have been integrated into the core; we use this list to ignore
# them during registration to avoid conflicts
DEPRECATED_EXTERNAL_PLUGINS = {
    "pytest_catchlog",
    "pytest_capturelog",
    "pytest_faulthandler",
}

FUNCARGNAMES = PytestDeprecationWarning(
    "The `funcargnames` attribute was an alias for `fixturenames`, "
    "since pytest 2.3 - use the newer attribute instead."
)

RESULT_LOG = PytestDeprecationWarning(
    "--result-log is deprecated, please try the new pytest-reportlog plugin.\n"
    "See https://docs.pytest.org/en/latest/deprecations.html#result-log-result-log for more information."
)

FIXTURE_POSITIONAL_ARGUMENTS = PytestDeprecationWarning(
    "Passing arguments to pytest.fixture() as positional arguments is deprecated - pass them "
    "as a keyword argument instead."
)

NODE_USE_FROM_PARENT = UnformattedWarning(
    PytestDeprecationWarning,
    "direct construction of {name} has been deprecated, please use {name}.from_parent",
)

JUNIT_XML_DEFAULT_FAMILY = PytestDeprecationWarning(
    "The 'junit_family' default value will change to 'xunit2' in pytest 6.0.\n"
    "Add 'junit_family=xunit1' to your pytest.ini file to keep the current format "
    "in future versions of pytest and silence this warning."
)

NO_PRINT_LOGS = PytestDeprecationWarning(
    "--no-print-logs is deprecated and scheduled for removal in pytest 6.0.\n"
    "Please use --show-capture instead."
)

COLLECT_DIRECTORY_HOOK = PytestDeprecationWarning(
    "The pytest_collect_directory hook is not working.\n"
    "Please use collect_ignore in conftests or pytest_collection_modifyitems."
)


TERMINALWRITER_WRITER = PytestDeprecationWarning(
    "The TerminalReporter.writer attribute is deprecated, use TerminalReporter._tw instead at your own risk.\n"
    "See https://docs.pytest.org/en/latest/deprecations.html#terminalreporter-writer for more information."
)
