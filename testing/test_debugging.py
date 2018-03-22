# encoding: utf-8
from __future__ import absolute_import
from _pytest.debugging import SUPPORTS_BREAKPOINT_BUILTIN
import sys


class TestDebugging(object):

    def test_supports_breakpoint_module_global(self):
        """
        Test that supports breakpoint global marks on Python 3.7+
        """
        if sys.version_info.major == 3 and sys.version_info.minor >= 7:
            assert SUPPORTS_BREAKPOINT_BUILTIN is True
        if sys.version_info.major == 3 and sys.version_info.minor == 5:
            assert SUPPORTS_BREAKPOINT_BUILTIN is False
        if sys.version_info.major == 2 and sys.version_info.minor == 7:
            assert SUPPORTS_BREAKPOINT_BUILTIN is False
