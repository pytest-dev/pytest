"""
unit and functional testing with Python.

see http://pytest.org for documentation and details

(c) Holger Krekel and others, 2004-2010
"""
__version__ = '2.0.0.dev24'

__all__ = ['config', 'cmdline']

from pytest import main as cmdline
UsageError = cmdline.UsageError
main = cmdline.main