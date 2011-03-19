"""
unit and functional testing with Python.
"""
__all__ = ['main']

from _pytest.core import main, UsageError, _preloadplugins
from _pytest import core as cmdline
from _pytest import __version__

if __name__ == '__main__': # if run as a script or by 'python -m pytest'
    raise SystemExit(main())
else:
    _preloadplugins() # to populate pytest.* namespace so help(pytest) works
