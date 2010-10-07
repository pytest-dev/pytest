"""
extensible functional and unit testing with Python.
(c) Holger Krekel and others, 2004-2010
"""
__version__ = "1.4.0a1"

#__all__ = ['collect']

import pytest.collect
import pytest.config
from pytest import collect

def __main__():
    from pytest.session import main
    raise SystemExit(main())
