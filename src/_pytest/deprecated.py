"""
This module contains deprecation messages and bits of code used elsewhere in the codebase
that is planned to be removed in the next pytest release.

Keeping it in a central location makes it easy to track what is deprecated and should
be removed when the time comes.

All constants defined in this module should be either PytestWarning instances or UnformattedWarning
in case of warnings which need to format their messages.
"""
from _pytest.warning_types import PytestDeprecationWarning

YIELD_TESTS = "yield tests were removed in pytest 4.0 - {name} will be ignored"

# set of plugins which have been integrated into the core; we use this list to ignore
# them during registration to avoid conflicts
DEPRECATED_EXTERNAL_PLUGINS = {
    "pytest_catchlog",
    "pytest_capturelog",
    "pytest_faulthandler",
}


FIXTURE_FUNCTION_CALL = (
    'Fixture "{name}" called directly. Fixtures are not meant to be called directly,\n'
    "but are created automatically when test functions request them as parameters.\n"
    "See https://docs.pytest.org/en/latest/fixture.html for more information about fixtures, and\n"
    "https://docs.pytest.org/en/latest/deprecations.html#calling-fixtures-directly about how to update your code."
)

FIXTURE_NAMED_REQUEST = PytestDeprecationWarning(
    "'request' is a reserved name for fixtures and will raise an error in future versions"
)


FUNCARGNAMES = PytestDeprecationWarning(
    "The `funcargnames` attribute was an alias for `fixturenames`, "
    "since pytest 2.3 - use the newer attribute instead."
)


RESULT_LOG = PytestDeprecationWarning(
    "--result-log is deprecated and scheduled for removal in pytest 6.0.\n"
    "See https://docs.pytest.org/en/latest/deprecations.html#result-log-result-log for more information."
)


PYTEST_LOGWARNING = PytestDeprecationWarning(
    "pytest_logwarning is deprecated, no longer being called, and will be removed soon\n"
    "please use pytest_warning_captured instead"
)
