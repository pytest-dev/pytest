# PYTHON_ARGCOMPLETE_OK
"""
pytest: unit and functional testing with Python.
"""
__all__ = [
    'main',
    'UsageError',
    'cmdline',
    'hookspec',
    'hookimpl',
    '__version__',
    'register_assert_rewrite',
    'freeze_includes',
    'set_trace',
    'warns',
    'deprecated_call',
    'fixture',
    'yield_fixture',
    'fail',
    'skip',
    'xfail',
    'importorskip',
    'exit',
    'mark',

]

if __name__ == '__main__': # if run as a script or by 'python -m pytest'
    # we trigger the below "else" condition by the following import
    import pytest
    raise SystemExit(pytest.main())

# else we are imported

from _pytest.config import (
    main, UsageError, _preloadplugins, cmdline,
    hookspec, hookimpl
)
from _pytest.fixtures import fixture, yield_fixture
from _pytest.assertion import register_assert_rewrite
from _pytest.freeze_support import freeze_includes
from _pytest import __version__
from _pytest.debugging import pytestPDB as __pytestPDB
from _pytest.recwarn import warns, deprecated_call
from _pytest.runner import fail, skip, importorskip, exit
from _pytest.mark import MARK_GEN as mark
from _pytest.skipping import xfail
set_trace = __pytestPDB.set_trace

_preloadplugins() # to populate pytest.* namespace so help(pytest) works
