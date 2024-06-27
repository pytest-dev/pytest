# mypy: allow-untyped-defs
"""Command line options, ini-file and conftest.py processing."""

import argparse
import collections.abc
import copy
import dataclasses
import enum
from functools import lru_cache
import glob
import importlib.metadata
import inspect
import os
from pathlib import Path
import re
import shlex
import sys
from textwrap import dedent
import types
from types import FunctionType
from typing import Any
from typing import Callable
from typing import cast
from typing import Dict
from typing import Final
from typing import final
from typing import Generator
from typing import IO
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import TextIO
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import Union
import warnings

import pluggy
from pluggy import HookimplMarker
from pluggy import HookimplOpts
from pluggy import HookspecMarker
from pluggy import HookspecOpts
from pluggy import PluginManager

# from .compat import PathAwareHookProxy
# from .exceptions import PrintHelp as PrintHelp
# from .exceptions import UsageError as UsageError
# from .findpaths import determine_setup
from _pytest import __version__
import _pytest._code
from _pytest._code import ExceptionInfo
from _pytest._code import filter_traceback

# from _pytest._code.code import TracebackStyle
from _pytest._io import TerminalWriter
from _pytest.config.argparsing import Argument
from _pytest.config.argparsing import Parser
import _pytest.deprecated
import _pytest.hookspec
from _pytest.outcomes import fail
from _pytest.outcomes import Skipped
from _pytest.pathlib import absolutepath
from _pytest.pathlib import bestrelpath
from _pytest.pathlib import import_path
from _pytest.pathlib import ImportMode
from _pytest.pathlib import resolve_package_path
from _pytest.pathlib import safe_exists
from _pytest.stash import Stash
from _pytest.warning_types import PytestConfigWarning
from _pytest.warning_types import warn_explicit_for
from _pytest.config import PytestPluginManager
from _pytest.config import Config
from _pytest.config.__init__ import create_terminal_writer
from _pytest.config.__init__ import Config
from _pytest.config.__init__ import _strtobool


if TYPE_CHECKING:
    from _pytest.cacheprovider import Cache
    from _pytest.terminal import TerminalReporter

from _pytest._code import __init__
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


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


assert _strtobool("y") == True
assert _strtobool("n") == False
print("%d", _strtobool("a"))




# self = PytestPluginManager()

# # Test branches 1,3,4 in consider_pluginarg
# print("Given input: no:cacheprovider")    
# self.consider_pluginarg("no:cacheprovider")

# assert name == "cacheprovider"
# assert self._name2plugin[name] == None
# assert self.set_blocked == "stepwise"
# assert self.set_blocked == "pytest_stepwise"
# assert self.set_blocked == "pytest_" + name

# # Test branches 5,6 in consider_pluginarg  
# arg = "mark"
# something.consider_pluginarg("mark")
# assert name == "mark"
# assert self.unblock == "pytset_" + name
# assert consider_entry_points == True

# # Test branches 1,2,4 in consider_pluginarg
# arg = "no:mark"
# something.consider_pluginarg("no:mark")
# assert name == "mark"
# assert self.set_blocked == "pytest_" + name
 