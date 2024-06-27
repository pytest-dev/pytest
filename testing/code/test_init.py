# mypy: allow-untyped-defs
"""Command line options, ini-file and conftest.py processing."""

import os
import sys

from _pytest.config import Config
from _pytest.config import PytestPluginManager
from _pytest.config.__init__ import _strtobool
from _pytest.config.__init__ import Config
from _pytest.config.__init__ import create_terminal_writer

# from .compat import PathAwareHookProxy
# from .exceptions import PrintHelp as PrintHelp
# from .exceptions import UsageError as UsageError
# from .findpaths import determine_setup
# from _pytest._code.code import TracebackStyle
import pytest


sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)


# Test branches 1,3 in create_terminal_writer
pluginmanager = PytestPluginManager()
config = Config(pluginmanager=pluginmanager)
config.option.color = "yes"
config.option.code_highlight = "yes"

tw = create_terminal_writer(config)
assert tw.hasmarkup == True
assert tw.code_highlight == True

# Test branches 2,4 in create_terminal_writer
pluginmanager = PytestPluginManager()
config = Config(pluginmanager=pluginmanager)
config.option.color = "no"
config.option.code_highlight = "no"

tw = create_terminal_writer(config)
assert tw.hasmarkup == False
assert tw.code_highlight == False

# Test branch 1 in _strtobool
assert _strtobool("y") == True

# Test branch 2 in _strtobool
assert _strtobool("n") == False

# Test branch 3 in _strtobool
with pytest.raises(ValueError) as excinfo:
    _strtobool("a")

assert str(excinfo.value) == "invalid truth value 'a'"
