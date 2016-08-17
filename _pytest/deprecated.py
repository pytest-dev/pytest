"""
This module contains deprecation messages and bits of code used elsewhere in the codebase
that is planned to be removed in the next pytest release.

Keeping it in a central location makes it easy to track what is deprecated and should
be removed when the time comes.
"""


MAIN_STR_ARGS = 'passing a string to pytest.main() is deprecated, ' \
                      'pass a list of arguments instead.'

YIELD_TESTS = 'yield tests are deprecated, and scheduled to be removed in pytest 4.0'

FUNCARG_PREFIX = (
    '{name}: declaring fixtures using "pytest_funcarg__" prefix is deprecated '
    'and scheduled to be removed in pytest 4.0.  '
    'Please remove the prefix and use the @pytest.fixture decorator instead.')

SETUP_CFG_PYTEST = '[pytest] section in setup.cfg files is deprecated, use [tool:pytest] instead.'

GETFUNCARGVALUE = "use of getfuncargvalue is deprecated, use getfixturevalue"

RESULT_LOG = '--result-log is deprecated and scheduled for removal in pytest 4.0'
