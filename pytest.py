"""
unit and functional testing with Python.

see http://pytest.org for documentation and details

(c) Holger Krekel and others, 2004-2010
"""
__version__ = '2.0.0.dev34'
__all__ = ['main']

from _pytest.core import main, UsageError, _preloadplugins
from _pytest import core as cmdline

if __name__ == '__main__': # if run as a script or by 'python -m pytest'
    raise SystemExit(main())
else:
    _preloadplugins() # to populate pytest.* namespace so help(pytest) works
