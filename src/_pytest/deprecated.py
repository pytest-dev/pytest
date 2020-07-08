"""
This module contains deprecation messages and bits of code used elsewhere in the codebase
that is planned to be removed in the next pytest release.

Keeping it in a central location makes it easy to track what is deprecated and should
be removed when the time comes.

All constants defined in this module should be either instances of
:class:`PytestWarning`, or :class:`UnformattedWarning`
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

FILLFUNCARGS = PytestDeprecationWarning(
    "The `_fillfuncargs` function is deprecated, use "
    "function._request._fillfixtures() instead if you cannot avoid reaching into internals."
)

RESULT_LOG = PytestDeprecationWarning(
    "--result-log is deprecated, please try the new pytest-reportlog plugin.\n"
    "See https://docs.pytest.org/en/stable/deprecations.html#result-log-result-log for more information."
)

FIXTURE_POSITIONAL_ARGUMENTS = PytestDeprecationWarning(
    "Passing arguments to pytest.fixture() as positional arguments is deprecated - pass them "
    "as a keyword argument instead."
)

NODE_USE_FROM_PARENT = UnformattedWarning(
    PytestDeprecationWarning,
    "Direct construction of {name} has been deprecated, please use {name}.from_parent.\n"
    "See "
    "https://docs.pytest.org/en/stable/deprecations.html#node-construction-changed-to-node-from-parent"
    " for more details.",
)

JUNIT_XML_DEFAULT_FAMILY = PytestDeprecationWarning(
    "The 'junit_family' default value will change to 'xunit2' in pytest 6.0. See:\n"
    "  https://docs.pytest.org/en/stable/deprecations.html#junit-family-default-value-change-to-xunit2\n"
    "for more information."
)

COLLECT_DIRECTORY_HOOK = PytestDeprecationWarning(
    "The pytest_collect_directory hook is not working.\n"
    "Please use collect_ignore in conftests or pytest_collection_modifyitems."
)

PYTEST_COLLECT_MODULE = UnformattedWarning(
    PytestDeprecationWarning,
    "pytest.collect.{name} was moved to pytest.{name}\n"
    "Please update to the new name.",
)


TERMINALWRITER_WRITER = PytestDeprecationWarning(
    "The TerminalReporter.writer attribute is deprecated, use TerminalReporter._tw instead at your own risk.\n"
    "See https://docs.pytest.org/en/stable/deprecations.html#terminalreporter-writer for more information."
)


MINUS_K_DASH = PytestDeprecationWarning(
    "The `-k '-expr'` syntax to -k is deprecated.\nUse `-k 'not expr'` instead."
)

MINUS_K_COLON = PytestDeprecationWarning(
    "The `-k 'expr:'` syntax to -k is deprecated.\n"
    "Please open an issue if you use this and want a replacement."
)

WARNING_CAPTURED_HOOK = PytestDeprecationWarning(
    "The pytest_warning_captured is deprecated and will be removed in a future release.\n"
    "Please use pytest_warning_recorded instead."
)
