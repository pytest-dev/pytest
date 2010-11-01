"""
py.test / pytest API for unit and functional testing with Python.

see http://pytest.org for documentation and details

(c) Holger Krekel and others, 2004-2010
"""
__version__ = '2.0.0.dev15'

__all__ = ['config', 'cmdline']

from pytest import _core as cmdline
UsageError = cmdline.UsageError

def __main__():
    raise SystemExit(cmdline.main())