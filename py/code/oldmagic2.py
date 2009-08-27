
import py

py.log._apiwarn("1.1", "py.magic.AssertionError is deprecated, use py.code._AssertionError", stacklevel=2)

from py.code import _AssertionError as AssertionError
