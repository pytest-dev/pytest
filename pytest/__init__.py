"""
py.test / pytest API for unit and functional testing with Python.
(c) Holger Krekel and others, 2004-2010
"""
__version__ = "2.0.0dev0"

__all__ = ['collect', 'cmdline', 'config']

import pytest._config
config = pytest._config.Config()
from pytest import collect
from pytest import main as cmdline

def __main__():
    raise SystemExit(cmdline.main())
