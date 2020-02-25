# PYTHON_ARGCOMPLETE_OK
"""
pytest: unit and functional testing with Python.
"""
from _pytest import __version__
from _pytest.assertion import register_assert_rewrite
from _pytest.compat import _setup_collect_fakemodule
from _pytest.config import cmdline
from _pytest.config import ExitCode
from _pytest.config import hookimpl
from _pytest.config import hookspec
from _pytest.config import main
from _pytest.config import UsageError
from _pytest.debugging import pytestPDB as __pytestPDB
from _pytest.fixtures import fillfixtures as _fillfuncargs
from _pytest.fixtures import fixture
from _pytest.fixtures import yield_fixture
from _pytest.freeze_support import freeze_includes
from _pytest.main import Session
from _pytest.mark import MARK_GEN as mark
from _pytest.mark import param
from _pytest.nodes import Collector
from _pytest.nodes import File
from _pytest.nodes import Item
from _pytest.outcomes import exit
from _pytest.outcomes import fail
from _pytest.outcomes import importorskip
from _pytest.outcomes import skip
from _pytest.outcomes import xfail
from _pytest.python import Class
from _pytest.python import Function
from _pytest.python import Instance
from _pytest.python import Module
from _pytest.python import Package
from _pytest.python_api import approx
from _pytest.python_api import raises
from _pytest.recwarn import deprecated_call
from _pytest.recwarn import warns
from _pytest.warning_types import PytestAssertRewriteWarning
from _pytest.warning_types import PytestCacheWarning
from _pytest.warning_types import PytestCollectionWarning
from _pytest.warning_types import PytestConfigWarning
from _pytest.warning_types import PytestDeprecationWarning
from _pytest.warning_types import PytestExperimentalApiWarning
from _pytest.warning_types import PytestUnhandledCoroutineWarning
from _pytest.warning_types import PytestUnknownMarkWarning
from _pytest.warning_types import PytestWarning

# For mypy Any type checking purposes.
# This file sets disallow_any_expr to ensure that the public API
# does not have dynamic typing via Any. Manually using each public API
# type as an expression to enforce this.
__version__ = __version__
register_assert_rewrite = register_assert_rewrite
_setup_collect_fakemodule = _setup_collect_fakemodule
cmdline = cmdline
ExitCode = ExitCode
# hookimpl = hookimpl
# hookspec = hookspec
main = main
UsageError = UsageError
__pytestPDB = __pytestPDB
_fillfuncargs = _fillfuncargs
fixture = fixture
yield_fixture = yield_fixture
freeze_includes = freeze_includes
Session = Session
mark = mark
param = param
Collector = Collector
File = File
Item = Item
exit = exit
fail = fail
importorskip = importorskip
skip = skip
xfail = xfail
Class = Class
Function = Function
Instance = Instance
Module = Module
Package = Package
approx = approx
raises = raises
deprecated_call = deprecated_call
warns = warns
PytestAssertRewriteWarning = PytestAssertRewriteWarning
PytestCacheWarning = PytestCacheWarning
PytestCollectionWarning = PytestCollectionWarning
PytestConfigWarning = PytestConfigWarning
PytestDeprecationWarning = PytestDeprecationWarning
PytestExperimentalApiWarning = PytestExperimentalApiWarning
PytestUnhandledCoroutineWarning = PytestUnhandledCoroutineWarning
PytestUnknownMarkWarning = PytestUnknownMarkWarning
PytestWarning = PytestWarning


# Allow set_trace() to be typed with None
set_trace = __pytestPDB.set_trace  # type: ignore

__all__ = [
    "__version__",
    "_fillfuncargs",
    "approx",
    "Class",
    "cmdline",
    "Collector",
    "deprecated_call",
    "exit",
    "ExitCode",
    "fail",
    "File",
    "fixture",
    "freeze_includes",
    "Function",
    "hookimpl",
    "hookspec",
    "importorskip",
    "Instance",
    "Item",
    "main",
    "mark",
    "Module",
    "Package",
    "param",
    "PytestAssertRewriteWarning",
    "PytestCacheWarning",
    "PytestCollectionWarning",
    "PytestConfigWarning",
    "PytestDeprecationWarning",
    "PytestExperimentalApiWarning",
    "PytestUnhandledCoroutineWarning",
    "PytestUnknownMarkWarning",
    "PytestWarning",
    "raises",
    "register_assert_rewrite",
    "Session",
    "set_trace",
    "skip",
    "UsageError",
    "warns",
    "xfail",
    "yield_fixture",
]


_setup_collect_fakemodule()
del _setup_collect_fakemodule
