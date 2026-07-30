# mypy: allow-untyped-defs
"""Python test discovery, setup and run of test functions."""

from __future__ import annotations

import abc
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Mapping
from collections.abc import Sequence
import fnmatch
from functools import partial
import inspect
import os
from pathlib import Path
import types
from typing import Any
from typing import cast
from typing import final
from typing import get_args
from typing import Literal
from typing import TYPE_CHECKING
import warnings

import _pytest
from _pytest import fixtures
from _pytest import nodes
from _pytest._code import filter_traceback
from _pytest._code import getfslineno
from _pytest._code.code import ExceptionInfo
from _pytest._code.code import TerminalRepr
from _pytest._code.code import Traceback
from _pytest.compat import get_default_arg_names
from _pytest.compat import get_real_func
from _pytest.compat import getimfunc
from _pytest.compat import is_async_function
from _pytest.compat import NOTSET
from _pytest.compat import safe_getattr
from _pytest.compat import safe_isclass
from _pytest.config import Config
from _pytest.config import hookimpl
from _pytest.config import UsageError
from _pytest.config.argparsing import Parser
from _pytest.deprecated import CALLSPEC2_RENAMED
from _pytest.deprecated import check_ispytest
from _pytest.fixtures import FixtureDef
from _pytest.fixtures import FixtureRequest
from _pytest.fixtures import FixtureValue
from _pytest.fixtures import FuncFixtureInfo
from _pytest.fixtures import get_scope_node
from _pytest.main import Session
from _pytest.mark.structures import get_unpacked_marks
from _pytest.outcomes import fail
from _pytest.outcomes import skip
from _pytest.parametrize import _infer_parametrize_scope
from _pytest.parametrize import CallSpec
from _pytest.parametrize import ParametrizeContext
from _pytest.pathlib import fnmatch_ex
from _pytest.pathlib import import_path
from _pytest.pathlib import ImportPathMismatchError
from _pytest.pathlib import scandir
from _pytest.scope import Scope
from _pytest.stash import StashKey
from _pytest.warning_types import PytestCollectionWarning
from _pytest.warning_types import PytestReturnNotNoneWarning


if TYPE_CHECKING:
    from typing_extensions import Self

# Modes for the ``collect_function_definition`` option.
# - "hidden": legacy flat layout; the FunctionDefinition is used transiently to
#             drive parametrization and kept out of ("hidden" from) the tree.
# - "pedantic": insert the FunctionDefinition node; function-level markers are
#               scoped to it and each invocation only owns its callspec markers.
# - "messy": insert the node, but transfer the function-level markers down onto
#            each invocation to preserve the legacy marker layout. Emits a
#            warning, as this defeats the purpose of the definition scope.
FunctionDefinitionMode = Literal["hidden", "pedantic", "messy"]
_FUNCTION_DEFINITION_MODES: frozenset[FunctionDefinitionMode] = frozenset(
    get_args(FunctionDefinitionMode)
)


def _collect_function_definition_mode(config: Config) -> FunctionDefinitionMode:
    value = config.getini("collect_function_definition")
    if value not in _FUNCTION_DEFINITION_MODES:
        raise UsageError(
            f"Unknown collect_function_definition: {value!r}. "
            f"Valid values: {', '.join(sorted(_FUNCTION_DEFINITION_MODES))}"
        )
    return cast(FunctionDefinitionMode, value)


def pytest_addoption(parser: Parser) -> None:
    parser.addini(
        "python_files",
        type="args",
        # NOTE: default is also used in AssertionRewritingHook.
        default=["test_*.py", "*_test.py"],
        help="Glob-style file patterns for Python test module discovery",
    )
    parser.addini(
        "python_classes",
        type="args",
        default=["Test"],
        help="Prefixes or glob names for Python test class discovery",
    )
    parser.addini(
        "python_functions",
        type="args",
        default=["test"],
        help="Prefixes or glob names for Python test function and method discovery",
    )
    parser.addini(
        "disable_test_id_escaping_and_forfeit_all_rights_to_community_support",
        type="bool",
        default=False,
        help="Disable string escape non-ASCII characters, might cause unwanted "
        "side effects(use at your own risk)",
    )
    parser.addini(
        "strict_parametrization_ids",
        type="bool",
        # None => fallback to `strict`.
        default=None,
        help="Emit an error if non-unique parameter set IDs are detected",
    )
    parser.addini(
        "parametrize_long_str_id_strategy",
        type="string",
        default="short",
        help="strategy for long str/bytes parameter values in auto-generated ids\n"
        "- short (default): values over 100 chars fall back to argname+index\n"
        "- sha256: replace value with its sha256 hex digest\n"
        "- legacy: keep the full value (for temporary backward compatibility)\n"
        "- disallow: raise an error requesting explicit ids",
    )


def pytest_generate_tests(metafunc: Metafunc) -> None:
    for marker in metafunc.definition.iter_markers(name="parametrize"):
        metafunc.parametrize(*marker.args, **marker.kwargs, _param_mark=marker)


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers",
        "parametrize(argnames, argvalues): call a test function multiple "
        "times passing in different arguments in turn. argvalues generally "
        "needs to be a list of values if argnames specifies only one name "
        "or a list of tuples of values if argnames specifies multiple names. "
        "Example: @parametrize('arg1', [1,2]) would lead to two calls of the "
        "decorated test function, one with arg1=1 and another with arg1=2."
        "see https://docs.pytest.org/en/stable/how-to/parametrize.html for more info "
        "and examples.",
    )
    config.addinivalue_line(
        "markers",
        "usefixtures(fixturename1, fixturename2, ...): mark tests as needing "
        "all of the specified fixtures. see "
        "https://docs.pytest.org/en/stable/explanation/fixtures.html#usefixtures ",
    )


def pytest_report_header(config: Config) -> list[str] | None:
    if _collect_function_definition_mode(config) == "messy":
        return [
            "warning: collect_function_definition=messy transfers markers to the "
            "individual invocations to preserve the legacy layout; prefer "
            "'pedantic' once your plugins handle the definition scope",
        ]
    return None


def async_fail(nodeid: str) -> None:
    msg = (
        "async def functions are not natively supported.\n"
        "You need to install a suitable plugin for your async framework, for example:\n"
        "  - anyio\n"
        "  - pytest-asyncio\n"
        "  - pytest-tornasync\n"
        "  - pytest-trio\n"
        "  - pytest-twisted"
    )
    fail(msg, pytrace=False)


@hookimpl(trylast=True)
def pytest_pyfunc_call(pyfuncitem: Function) -> object | None:
    testfunction = pyfuncitem.obj
    if is_async_function(testfunction):
        async_fail(pyfuncitem.nodeid)
    funcargs = pyfuncitem.funcargs
    testargs = {arg: funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames}
    result = testfunction(**testargs)
    if hasattr(result, "__await__") or hasattr(result, "__aiter__"):
        async_fail(pyfuncitem.nodeid)
    elif result is not None:
        warnings.warn(
            PytestReturnNotNoneWarning(
                f"Test functions should return None, but {pyfuncitem.nodeid} returned {type(result)!r}.\n"
                "Did you mean to use `assert` instead of `return`?\n"
                "See https://docs.pytest.org/en/stable/how-to/assert.html#return-not-none for more information."
            )
        )
    return True


def pytest_collect_directory(
    path: Path, parent: nodes.Collector
) -> nodes.Collector | None:
    pkginit = path / "__init__.py"
    try:
        has_pkginit = pkginit.is_file()
    except PermissionError:
        # See https://github.com/pytest-dev/pytest/issues/12120#issuecomment-2106349096.
        return None
    if has_pkginit:
        return Package.from_parent(parent, path=path)
    return None


def pytest_collect_file(file_path: Path, parent: nodes.Collector) -> Module | None:
    if file_path.suffix == ".py":
        if not parent.session.isinitpath(file_path):
            if not path_matches_patterns(
                file_path, parent.config.getini("python_files")
            ):
                return None
        ihook = parent.session.gethookproxy(file_path)
        module: Module = ihook.pytest_pycollect_makemodule(
            module_path=file_path, parent=parent
        )
        return module
    return None


def path_matches_patterns(path: Path, patterns: Iterable[str]) -> bool:
    """Return whether path matches any of the patterns in the list of globs given."""
    return any(fnmatch_ex(pattern, path) for pattern in patterns)


def pytest_pycollect_makemodule(module_path: Path, parent) -> Module:
    return Module.from_parent(parent, path=module_path)


@hookimpl(trylast=True)
def pytest_pycollect_makeitem(
    collector: Module | Class, name: str, obj: object
) -> None | nodes.Item | nodes.Collector | list[nodes.Item | nodes.Collector]:
    assert isinstance(collector, Class | Module), type(collector)
    # Nothing was collected elsewhere, let's do it here.
    if safe_isclass(obj):
        if collector.istestclass(obj, name):
            return Class.from_parent(collector, name=name, obj=obj)
    elif collector.istestfunction(obj, name):
        # mock seems to store unbound methods (issue473), normalize it.
        obj = getattr(obj, "__func__", obj)
        # We need to try and unwrap the function if it's a functools.partial
        # or a functools.wrapped.
        # We mustn't if it's been wrapped with mock.patch (python 2 only).
        if not (inspect.isfunction(obj) or inspect.isfunction(get_real_func(obj))):
            filename, lineno = getfslineno(obj)
            warnings.warn_explicit(
                message=PytestCollectionWarning(
                    f"cannot collect {name!r} because it is not a function."
                ),
                category=None,
                filename=str(filename),
                lineno=lineno + 1,
            )
        elif getattr(obj, "__test__", True):
            if inspect.isgeneratorfunction(obj):
                fail(
                    f"'yield' keyword is allowed in fixtures, but not in tests ({name})",
                    pytrace=False,
                )
            return list(collector._genfunctions(name, obj))
        return None
    return None


class PyobjMixin(nodes.Node):
    """this mix-in inherits from Node to carry over the typing information

    as its intended to always mix in before a node
    its position in the mro is unaffected"""

    _ALLOW_MARKERS = True

    @property
    def module(self):
        """Python module object this node was collected from (can be None)."""
        node = self.getparent(Module)
        return node.obj if node is not None else None

    @property
    def cls(self):
        """Python class object this node was collected from (can be None)."""
        node = self.getparent(Class)
        return node.obj if node is not None else None

    @property
    def instance(self):
        """Python instance object the function is bound to.

        Returns None if not a test method, e.g. for a standalone test function,
        a class or a module.
        """
        # Overridden by Function.
        return None

    @property
    def obj(self):
        """Underlying Python object."""
        obj = getattr(self, "_obj", None)
        if obj is None:
            self._obj = obj = self._getobj()
            # XXX evil hack
            # used to avoid Function marker duplication
            if self._ALLOW_MARKERS:
                self.own_markers.extend(get_unpacked_marks(self.obj))
                # This assumes that `obj` is called before there is a chance
                # to add custom keys to `self.keywords`, so no fear of overriding.
                self.keywords.update((mark.name, mark) for mark in self.own_markers)
        return obj

    @obj.setter
    def obj(self, value):
        self._obj = value

    def _getobj(self):
        """Get the underlying Python object. May be overwritten by subclasses."""
        # TODO: Improve the type of `parent` such that assert/ignore aren't needed.
        assert self.parent is not None
        obj = self.parent.obj  # type: ignore[attr-defined]
        return getattr(obj, self.name)

    def getmodpath(self, stopatmodule: bool = True, includemodule: bool = False) -> str:
        """Return Python path relative to the containing module."""
        parts = []
        for node in self.iter_parents():
            # A FunctionDefinition parent contributes the same name as the
            # Function collected under it, so skip it to avoid duplication
            # (but keep it when it is the node itself).
            if node is not self and isinstance(node, FunctionDefinition):
                continue
            name = node.name
            if isinstance(node, Module):
                name = os.path.splitext(name)[0]
                if stopatmodule:
                    if includemodule:
                        parts.append(name)
                    break
            parts.append(name)
        parts.reverse()
        return ".".join(parts)

    def reportinfo(self) -> tuple[os.PathLike[str] | str, int | None, str]:
        # XXX caching?
        path, lineno = getfslineno(self.obj)
        modpath = self.getmodpath()
        return path, lineno, modpath


# As an optimization, these builtin attribute names are pre-ignored when
# iterating over an object during collection -- the pytest_pycollect_makeitem
# hook is not called for them.
# fmt: off
class _EmptyClass: pass  # noqa: E701
IGNORED_ATTRIBUTES = frozenset.union(
    frozenset(),
    # Module.
    dir(types.ModuleType("empty_module")),
    # Some extra module attributes the above doesn't catch.
    {"__builtins__", "__file__", "__cached__"},
    # Class.
    dir(_EmptyClass),
    # Instance.
    dir(_EmptyClass()),
)
del _EmptyClass
# fmt: on


class PyCollector(PyobjMixin, nodes.Collector, abc.ABC):
    def funcnamefilter(self, name: str) -> bool:
        return self._matches_prefix_or_glob_option("python_functions", name)

    def isnosetest(self, obj: object) -> bool:
        """Look for the __test__ attribute, which is applied by the
        @nose.tools.istest decorator.
        """
        # We explicitly check for "is True" here to not mistakenly treat
        # classes with a custom __getattr__ returning something truthy (like a
        # function) as test classes.
        return safe_getattr(obj, "__test__", False) is True

    def classnamefilter(self, name: str) -> bool:
        return self._matches_prefix_or_glob_option("python_classes", name)

    def istestfunction(self, obj: object, name: str) -> bool:
        if self.funcnamefilter(name) or self.isnosetest(obj):
            if isinstance(obj, staticmethod | classmethod):
                # staticmethods and classmethods need to be unwrapped.
                obj = safe_getattr(obj, "__func__", False)
            return callable(obj) and fixtures.getfixturemarker(obj) is None
        else:
            return False

    def istestclass(self, obj: object, name: str) -> bool:
        if not (self.classnamefilter(name) or self.isnosetest(obj)):
            return False
        if inspect.isabstract(obj):
            return False
        return True

    def _matches_prefix_or_glob_option(self, option_name: str, name: str) -> bool:
        """Check if the given name matches the prefix or glob-pattern defined
        in configuration."""
        for option in self.config.getini(option_name):
            if name.startswith(option):
                return True
            # Check that name looks like a glob-string before calling fnmatch
            # because this is called for every name in each collected module,
            # and fnmatch is somewhat expensive to call.
            elif ("*" in option or "?" in option or "[" in option) and fnmatch.fnmatch(
                name, option
            ):
                return True
        return False

    def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
        if not getattr(self.obj, "__test__", True):
            return []

        # Avoid random getattrs and peek in the __dict__ instead.
        dicts = [getattr(self.obj, "__dict__", {})]
        if isinstance(self.obj, type):
            for basecls in self.obj.__mro__:
                dicts.append(basecls.__dict__)

        # In each class, nodes should be definition ordered.
        # __dict__ is definition ordered.
        seen: set[str] = set()
        dict_values: list[list[nodes.Item | nodes.Collector]] = []
        collect_imported_tests = self.session.config.getini("collect_imported_tests")
        ihook = self.ihook
        for dic in dicts:
            values: list[nodes.Item | nodes.Collector] = []
            # Note: seems like the dict can change during iteration -
            # be careful not to remove the list() without consideration.
            for name, obj in list(dic.items()):
                if name in IGNORED_ATTRIBUTES:
                    continue
                if name in seen:
                    continue
                seen.add(name)

                if not collect_imported_tests and isinstance(self, Module):
                    # Do not collect functions and classes from other modules.
                    if inspect.isfunction(obj) or inspect.isclass(obj):
                        if obj.__module__ != self._getobj().__name__:
                            continue

                res = ihook.pytest_pycollect_makeitem(
                    collector=self, name=name, obj=obj
                )
                if res is None:
                    continue
                elif isinstance(res, list):
                    values.extend(res)
                else:
                    values.append(res)
            dict_values.append(values)

        # Between classes in the class hierarchy, reverse-MRO order -- nodes
        # inherited from base classes should come before subclasses.
        result = []
        for values in reversed(dict_values):
            result.extend(values)
        return result

    def _genfunctions(
        self, name: str, funcobj
    ) -> Iterator[nodes.Item | FunctionDefinition]:
        definition = FunctionDefinition.from_parent(self, name=name, callobj=funcobj)
        if not definition.in_collection_tree:
            # Legacy flat layout: the definition is used only to drive
            # parametrization and is discarded ("hidden"), the invocations are
            # collected directly under this collector.
            yield from definition.generate_items(self)
        else:
            # Insert the function definition as a collector node into the tree;
            # its ``collect()`` yields the (possibly parametrized) invocations.
            yield definition


def importtestmodule(
    path: Path,
    config: Config,
):
    # We assume we are only called once per module.
    importmode = config.getoption("--import-mode")
    try:
        mod = import_path(
            path,
            mode=importmode,
            root=config.rootpath,
            consider_namespace_packages=config.getini("consider_namespace_packages"),
        )
    except SyntaxError as e:
        raise nodes.Collector.CollectError(
            ExceptionInfo.from_current().getrepr(style="short")
        ) from e
    except ImportPathMismatchError as e:
        raise nodes.Collector.CollectError(
            "import file mismatch:\n"
            "imported module {!r} has this __file__ attribute:\n"
            "  {}\n"
            "which is not the same as the test file we want to collect:\n"
            "  {}\n"
            "HINT: remove __pycache__ / .pyc files and/or use a "
            "unique basename for your test file modules".format(*e.args)
        ) from e
    except ImportError as e:
        exc_info = ExceptionInfo.from_current()
        if config.get_verbosity() < 2:
            exc_info.traceback = exc_info.traceback.filter(filter_traceback)
        exc_repr = (
            exc_info.getrepr(style="short")
            if exc_info.traceback
            else exc_info.exconly()
        )
        formatted_tb = str(exc_repr)
        raise nodes.Collector.CollectError(
            f"ImportError while importing test module '{path}'.\n"
            "Hint: make sure your test modules/packages have valid Python names.\n"
            "Traceback:\n"
            f"{formatted_tb}"
        ) from e
    except skip.Exception as e:
        if e.allow_module_level:
            raise
        raise nodes.Collector.CollectError(
            "Using pytest.skip outside of a test will skip the entire module. "
            "If that's your intention, pass `allow_module_level=True`. "
            "If you want to skip a specific test or an entire class, "
            "use the @pytest.mark.skip or @pytest.mark.skipif decorators."
        ) from e
    config.pluginmanager.consider_module(mod)
    return mod


class Module(nodes.File, PyCollector):
    """Collector for test classes and functions in a Python module."""

    def _getobj(self):
        return importtestmodule(self.path, self.config)

    def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
        self._register_setup_module_fixture()
        self._register_setup_function_fixture()
        self.session._fixturemanager.parsefactories(self)
        return super().collect()

    def _register_setup_module_fixture(self) -> None:
        """Register an autouse, module-scoped fixture for the collected module object
        that invokes setUpModule/tearDownModule if either or both are available.

        Using a fixture to invoke this methods ensures we play nicely and unsurprisingly with
        other fixtures (#517).
        """
        setup_module = _get_first_non_fixture_func(
            self.obj, ("setUpModule", "setup_module")
        )
        teardown_module = _get_first_non_fixture_func(
            self.obj, ("tearDownModule", "teardown_module")
        )

        if setup_module is None and teardown_module is None:
            return

        def xunit_setup_module_fixture(request) -> Generator[None]:
            module = request.module
            if setup_module is not None:
                _call_with_optional_argument(setup_module, module)
            yield
            if teardown_module is not None:
                _call_with_optional_argument(teardown_module, module)

        fixtures.register_fixture(
            # Use a unique name to speed up lookup.
            name=f"_xunit_setup_module_fixture_{self.obj.__name__}",
            func=xunit_setup_module_fixture,
            node=self,
            scope="module",
            autouse=True,
        )

    def _register_setup_function_fixture(self) -> None:
        """Register an autouse, function-scoped fixture for the collected module object
        that invokes setup_function/teardown_function if either or both are available.

        Using a fixture to invoke this methods ensures we play nicely and unsurprisingly with
        other fixtures (#517).
        """
        setup_function = _get_first_non_fixture_func(self.obj, ("setup_function",))
        teardown_function = _get_first_non_fixture_func(
            self.obj, ("teardown_function",)
        )
        if setup_function is None and teardown_function is None:
            return

        def xunit_setup_function_fixture(request) -> Generator[None]:
            if request.instance is not None:
                # in this case we are bound to an instance, so we need to let
                # setup_method handle this
                yield
                return
            function = request.function
            if setup_function is not None:
                _call_with_optional_argument(setup_function, function)
            yield
            if teardown_function is not None:
                _call_with_optional_argument(teardown_function, function)

        fixtures.register_fixture(
            # Use a unique name to speed up lookup.
            name=f"_xunit_setup_function_fixture_{self.obj.__name__}",
            func=xunit_setup_function_fixture,
            node=self,
            scope="function",
            autouse=True,
        )


class Package(nodes.Directory):
    """Collector for files and directories in a Python packages -- directories
    with an `__init__.py` file.

    .. note::

        Directories without an `__init__.py` file are instead collected by
        :class:`~pytest.Dir` by default. Both are :class:`~pytest.Directory`
        collectors.

    .. versionchanged:: 8.0

        Now inherits from :class:`~pytest.Directory`.
    """

    def __init__(
        self,
        fspath: None,
        parent: nodes.Collector,
        # NOTE: following args are unused:
        config=None,
        session=None,
        nodeid=None,
        path: Path | None = None,
    ) -> None:
        # NOTE: Could be just the following, but kept as-is for compat.
        # super().__init__(self, fspath, parent=parent)
        session = parent.session
        super().__init__(
            fspath=fspath,
            path=path,
            parent=parent,
            config=config,
            session=session,
            nodeid=nodeid,
        )

    def setup(self) -> None:
        init_mod = importtestmodule(self.path / "__init__.py", self.config)

        # Not using fixtures to call setup_module here because autouse fixtures
        # from packages are not called automatically (#4085).
        setup_module = _get_first_non_fixture_func(
            init_mod, ("setUpModule", "setup_module")
        )
        if setup_module is not None:
            _call_with_optional_argument(setup_module, init_mod)

        teardown_module = _get_first_non_fixture_func(
            init_mod, ("tearDownModule", "teardown_module")
        )
        if teardown_module is not None:
            func = partial(_call_with_optional_argument, teardown_module, init_mod)
            self.addfinalizer(func)

    def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
        # Always collect __init__.py first.
        def sort_key(entry: os.DirEntry[str]) -> object:
            return (entry.name != "__init__.py", entry.name)

        config = self.config
        col: nodes.Collector | None
        cols: Sequence[nodes.Collector]
        ihook = self.ihook
        for direntry in scandir(self.path, sort_key):
            if direntry.is_dir():
                path = Path(direntry.path)
                if not self.session.isinitpath(path, with_parents=True):
                    if ihook.pytest_ignore_collect(collection_path=path, config=config):
                        continue
                col = ihook.pytest_collect_directory(path=path, parent=self)
                if col is not None:
                    yield col

            elif direntry.is_file():
                path = Path(direntry.path)
                if not self.session.isinitpath(path):
                    if ihook.pytest_ignore_collect(collection_path=path, config=config):
                        continue
                cols = ihook.pytest_collect_file(file_path=path, parent=self)
                yield from cols


def _call_with_optional_argument(func, arg) -> None:
    """Call the given function with the given argument if func accepts one argument, otherwise
    calls func without arguments."""
    arg_count = func.__code__.co_argcount
    if inspect.ismethod(func):
        arg_count -= 1
    if arg_count:
        func(arg)
    else:
        func()


def _get_first_non_fixture_func(obj: object, names: Iterable[str]) -> object | None:
    """Return the attribute from the given object to be used as a setup/teardown
    xunit-style function, but only if not marked as a fixture to avoid calling it twice.
    """
    for name in names:
        meth: object | None = getattr(obj, name, None)
        if meth is not None and fixtures.getfixturemarker(meth) is None:
            return meth
    return None


class Class(PyCollector):
    """Collector for test methods (and nested classes) in a Python class."""

    @classmethod
    def from_parent(cls, parent, *, name, obj=None, **kw) -> Self:  # type: ignore[override]
        """The public constructor."""
        return super().from_parent(name=name, parent=parent, **kw)

    def newinstance(self):
        return self.obj()

    def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
        if not safe_getattr(self.obj, "__test__", True):
            return []
        if hasinit(self.obj):
            assert self.parent is not None
            self.warn(
                PytestCollectionWarning(
                    f"cannot collect test class {self.obj.__name__!r} because it has a "
                    f"__init__ constructor (from: {self.parent.nodeid})"
                )
            )
            return []
        elif hasnew(self.obj):
            assert self.parent is not None
            self.warn(
                PytestCollectionWarning(
                    f"cannot collect test class {self.obj.__name__!r} because it has a "
                    f"__new__ constructor (from: {self.parent.nodeid})"
                )
            )
            return []

        self._register_setup_class_fixture()
        self._register_setup_method_fixture()

        self.session._fixturemanager.parsefactories(
            holder=self.newinstance(), node=self
        )

        return super().collect()

    def _register_setup_class_fixture(self) -> None:
        """Register an autouse, class scoped fixture into the collected class object
        that invokes setup_class/teardown_class if either or both are available.

        Using a fixture to invoke this methods ensures we play nicely and unsurprisingly with
        other fixtures (#517).
        """
        setup_class = _get_first_non_fixture_func(self.obj, ("setup_class",))
        teardown_class = _get_first_non_fixture_func(self.obj, ("teardown_class",))
        if setup_class is None and teardown_class is None:
            return

        def xunit_setup_class_fixture(request) -> Generator[None]:
            cls = request.cls
            if setup_class is not None:
                func = getimfunc(setup_class)
                _call_with_optional_argument(func, cls)
            yield
            if teardown_class is not None:
                func = getimfunc(teardown_class)
                _call_with_optional_argument(func, cls)

        fixtures.register_fixture(
            # Use a unique name to speed up lookup.
            name=f"_xunit_setup_class_fixture_{self.obj.__qualname__}",
            func=xunit_setup_class_fixture,
            node=self,
            scope="class",
            autouse=True,
        )

    def _register_setup_method_fixture(self) -> None:
        """Register an autouse, function scoped fixture into the collected class object
        that invokes setup_method/teardown_method if either or both are available.

        Using a fixture to invoke these methods ensures we play nicely and unsurprisingly with
        other fixtures (#517).
        """
        setup_name = "setup_method"
        setup_method = _get_first_non_fixture_func(self.obj, (setup_name,))
        teardown_name = "teardown_method"
        teardown_method = _get_first_non_fixture_func(self.obj, (teardown_name,))
        if setup_method is None and teardown_method is None:
            return

        def xunit_setup_method_fixture(request) -> Generator[None]:
            instance = request.instance
            method = request.function
            if setup_method is not None:
                func = getattr(instance, setup_name)
                _call_with_optional_argument(func, method)
            yield
            if teardown_method is not None:
                func = getattr(instance, teardown_name)
                _call_with_optional_argument(func, method)

        fixtures.register_fixture(
            # Use a unique name to speed up lookup.
            name=f"_xunit_setup_method_fixture_{self.obj.__qualname__}",
            func=xunit_setup_method_fixture,
            node=self,
            scope="function",
            autouse=True,
        )


def hasinit(obj: object) -> bool:
    init: object = getattr(obj, "__init__", None)
    if init:
        return init != object.__init__
    return False


def hasnew(obj: object) -> bool:
    new: object = getattr(obj, "__new__", None)
    if new:
        return new != object.__new__
    return False


if TYPE_CHECKING:
    # Deprecated alias kept for type checkers; runtime access goes through __getattr__.
    CallSpec2 = CallSpec


def get_direct_param_fixture_func(request: FixtureRequest) -> Any:
    return request.param


class DirectParamFixtureDef(FixtureDef[FixtureValue]):
    """A custom FixtureDef for direct parametrization fixtures.

    Each parameter in direct parametrization is desugared to a parametrized
    fixture which returns the direct parameterization value as its param.
    We use this custom type as a "marker" for this type of FixtureDef, but
    usually behaves like any other FixtureDef.
    """

    def __init__(self, *, node: nodes.Node, argname: str, scope: Scope) -> None:
        super().__init__(
            config=node.config,
            baseid=NOTSET,
            argname=argname,
            func=get_direct_param_fixture_func,
            scope=scope,
            params=None,
            ids=None,
            node=node,
            _ispytest=True,
        )


# Used for storing fixturedefs for direct parametrization.
name2directparamfixturedef_key = StashKey[dict[str, DirectParamFixtureDef[object]]]()


@final
class Metafunc(ParametrizeContext):
    """Objects passed to the :hook:`pytest_generate_tests` hook.

    They help to inspect a test function and to generate tests according to
    test configuration or values specified in the class or module where a
    test function is defined.

    The Python-specific :class:`~_pytest.parametrize.ParametrizeContext`: it
    resolves ``argnames`` against the test function's fixture closure and
    signature, and desugars direct parametrization into fixtures.
    """

    definition: FunctionDefinition

    def __init__(
        self,
        definition: FunctionDefinition,
        fixtureinfo: fixtures.FuncFixtureInfo,
        config: Config,
        cls=None,
        module=None,
        *,
        _ispytest: bool = False,
    ) -> None:
        check_ispytest(_ispytest)
        #: Access to the underlying :class:`_pytest.python.FunctionDefinition`.
        #:
        #: Access to the :class:`pytest.Config` object for the test session is
        #: available as ``config``, and the set of fixture names required by the
        #: test function as ``fixturenames``.
        super().__init__(
            definition,
            config,
            # Note: passed through by reference, so that a later
            # prune_dependency_tree() is reflected in ``fixturenames``.
            argnames=fixtureinfo.names_closure,
            _ispytest=True,
        )

        #: The module object where the test function is defined in.
        self.module = module

        #: Underlying Python test function.
        self.function = definition.obj

        #: Class object where the test function is defined in or ``None``.
        self.cls = cls

        # The fixture closure driving this parametrization, handed on to the
        # generated Functions by FunctionDefinition.make_item().
        self._fixtureinfo = fixtureinfo
        self._arg2fixturedefs = fixtureinfo.name2fixturedefs

    @property
    def _introspection_target(self) -> object:
        return self.function

    @property
    def _target_name(self) -> str:
        return cast(str, self.function.__name__)

    def _infer_scope(
        self, argnames: Sequence[str], indirect: bool | Sequence[str]
    ) -> Scope:
        return _infer_parametrize_scope(argnames, self._arg2fixturedefs, indirect)

    def _validate_argnames(
        self,
        argnames: Sequence[str],
        indirect: bool | Sequence[str],
    ) -> None:
        self._validate_if_using_arg_names(argnames, indirect)

    def _register_direct_params(
        self,
        argnames: Sequence[str],
        arg_directness: Mapping[str, Literal["indirect", "direct"]],
        scope: Scope,
    ) -> None:
        """Desugar direct parametrizations into artificial fixturedefs.

        Registering a :class:`DirectParamFixtureDef` for every direct argname
        means that at test setup time we can rely on a FixtureDef existing for
        all argnames.
        """
        # For scopes higher than function, a DirectParamFixtureDef might have
        # already been created for the scope. We thus store and cache the
        # DirectParamFixtureDef on the node related to the scope.
        if scope is Scope.Function:
            name2directparamfixturedef = None
        else:
            node = self._scope_node_for_direct_params(scope)
            default: dict[str, DirectParamFixtureDef[object]] = {}
            name2directparamfixturedef = node.stash.setdefault(
                name2directparamfixturedef_key, default
            )
        for argname in argnames:
            if arg_directness[argname] == "indirect":
                continue
            if (
                name2directparamfixturedef is not None
                and argname in name2directparamfixturedef
            ):
                fixturedef = name2directparamfixturedef[argname]
            else:
                fixturedef = DirectParamFixtureDef(
                    node=self.definition.session,
                    argname=argname,
                    scope=scope,
                )
                if name2directparamfixturedef is not None:
                    name2directparamfixturedef[argname] = fixturedef
            self._arg2fixturedefs[argname] = [fixturedef]

    def _scope_node_for_direct_params(self, scope: Scope) -> nodes.Node:
        """The node the DirectParamFixtureDefs for ``scope`` are cached on."""
        if scope is Scope.Definition:
            if not self.definition.in_collection_tree:
                fixtures.fail_definition_scope_unavailable(
                    self.definition.nodeid,
                    f"parametrize(scope='definition') in {self._target_name}",
                )
            # The definition is the scope node for its own invocations; unlike
            # the other scopes it is not found by looking at ancestors.
            return self.definition
        collector = self.definition.parent
        assert collector is not None
        node = get_scope_node(collector, scope)
        if node is None:
            # If used class scope and there is no class, use module-level
            # collector (for now).
            if scope is Scope.Class:
                assert isinstance(collector, Module)
                node = collector
            # If used package scope and there is no package, use session
            # (for now).
            elif scope is Scope.Package:
                node = collector.session
            else:
                assert False, f"Unhandled missing scope: {scope}"
        return node

    def _validate_if_using_arg_names(
        self,
        argnames: Sequence[str],
        indirect: bool | Sequence[str],
    ) -> None:
        """Check if all argnames are being used, by default values, or directly/indirectly.

        :param List[str] argnames: List of argument names passed to ``parametrize()``.
        :param indirect: Same as the ``indirect`` parameter of ``parametrize()``.
        :raises ValueError: If validation fails.
        """
        default_arg_names = set(get_default_arg_names(self.function))
        nodeid = self.definition.nodeid
        for arg in argnames:
            if arg not in self.fixturenames:
                if arg in default_arg_names:
                    fail(
                        f"In {nodeid}: function already takes an argument '{arg}' with a default value",
                        pytrace=False,
                    )
                else:
                    if isinstance(indirect, Sequence):
                        name = "fixture" if arg in indirect else "argument"
                    else:
                        name = "fixture" if indirect else "argument"
                    fail(
                        f"In {nodeid}: function uses no {name} '{arg}'",
                        pytrace=False,
                    )


class Function(PyobjMixin, nodes.Item):
    """Item responsible for setting up and executing a Python test function.

    :param name:
        The full function name, including any decorations like those
        added by parametrization (``my_func[my_param]``).
    :param parent:
        The parent Node.
    :param config:
        The pytest Config object.
    :param callspec:
        If given, this function has been parametrized and the callspec contains
        meta information about the parametrization.
    :param callobj:
        If given, the object which will be called when the Function is invoked,
        otherwise the callobj will be obtained from ``parent`` using ``originalname``.
    :param keywords:
        Keywords bound to the function object for "-k" matching.
    :param session:
        The pytest Session object.
    :param fixtureinfo:
        Fixture information already resolved at this fixture node..
    :param originalname:
        The attribute name to use for accessing the underlying function object.
        Defaults to ``name``. Set this if name is different from the original name,
        for example when it contains decorations like those added by parametrization
        (``my_func[my_param]``).
    """

    # Disable since functions handle it themselves.
    _ALLOW_MARKERS = False

    def __init__(
        self,
        name: str,
        parent,
        config: Config | None = None,
        callspec: CallSpec | None = None,
        callobj=NOTSET,
        keywords: Mapping[str, Any] | None = None,
        session: Session | None = None,
        fixtureinfo: FuncFixtureInfo | None = None,
        originalname: str | None = None,
        nodeid: str | None = None,
    ) -> None:
        super().__init__(name, parent, config=config, session=session, nodeid=nodeid)

        if callobj is not NOTSET:
            self._obj = callobj
            self._instance = getattr(callobj, "__self__", None)

        #: Original function name, without any decorations (for example
        #: parametrization adds a ``"[...]"`` suffix to function names), used to access
        #: the underlying function object from ``parent`` (in case ``callobj`` is not given
        #: explicitly).
        #:
        #: .. versionadded:: 3.0
        self.originalname = originalname or name

        # Note: when FunctionDefinition is introduced, we should change ``originalname``
        # to a readonly property that returns FunctionDefinition.name.

        # Function-level markers are owned by the FunctionDefinition scope when
        # that node is part of the collection tree; otherwise (flat layout) the
        # Function owns them itself. In "messy" mode FunctionDefinition.collect()
        # transfers them back onto each invocation for legacy compatibility.
        if not isinstance(self.parent, FunctionDefinition):
            self.own_markers.extend(get_unpacked_marks(self.obj))
        if callspec:
            self.callspec = callspec
            self.own_markers.extend(callspec.marks)

        # todo: this is a hell of a hack
        # https://github.com/pytest-dev/pytest/issues/4569
        # Note: the order of the updates is important here; indicates what
        # takes priority (ctor argument over function attributes over markers).
        # Take own_markers only; NodeKeywords handles parent traversal on its own.
        self.keywords.update((mark.name, mark) for mark in self.own_markers)
        self.keywords.update(self.obj.__dict__)
        if keywords:
            self.keywords.update(keywords)

        if fixtureinfo is None:
            fm = self.session._fixturemanager
            fixtureinfo = fm.getfixtureinfo(self, self.obj, self.cls)
        self._fixtureinfo: FuncFixtureInfo = fixtureinfo
        self.fixturenames = fixtureinfo.names_closure
        self._initrequest()

    # todo: determine sound type limitations
    @classmethod
    def from_parent(cls, parent, **kw) -> Self:
        """The public constructor."""
        return super().from_parent(parent=parent, **kw)

    def _initrequest(self) -> None:
        self.funcargs: dict[str, object] = {}
        self._request = fixtures.TopRequest(self, _ispytest=True)

    @property
    def function(self):
        """Underlying python 'function' object."""
        return getimfunc(self.obj)

    @property
    def instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._getinstance()
        return self._instance

    def _getinstance(self):
        # The containing class, if any -- skipping over an interposed
        # FunctionDefinition node (see the ``collect_function_definition`` option).
        cls = self.getparent(Class)
        if cls is not None:
            # Each Function gets a fresh class instance.
            return cls.newinstance()
        else:
            return None

    def _getobj(self):
        instance = self.instance
        if instance is not None:
            parent_obj = instance
        else:
            # The namespace this function was collected from -- a Module (or a
            # Class handled above), skipping over an interposed FunctionDefinition.
            parent = self.parent
            while isinstance(parent, FunctionDefinition):
                parent = parent.parent
            assert parent is not None
            parent_obj = parent.obj  # type: ignore[attr-defined]
        return getattr(parent_obj, self.originalname)

    @property
    def _pyfuncitem(self):
        """(compatonly) for code expecting pytest-2.2 style request objects."""
        return self

    def runtest(self) -> None:
        """Execute the underlying test function."""
        self.ihook.pytest_pyfunc_call(pyfuncitem=self)

    def setup(self) -> None:
        self._request._fillfixtures()

    def _traceback_filter(self, excinfo: ExceptionInfo[BaseException]) -> Traceback:
        if hasattr(self, "_obj") and not self.config.getoption("fulltrace", False):
            code = _pytest._code.Code.from_function(get_real_func(self.obj))
            path, firstlineno = code.path, code.firstlineno
            traceback = excinfo.traceback
            ntraceback = traceback.cut(path=path, firstlineno=firstlineno)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(path=path)
                if ntraceback == traceback:
                    ntraceback = ntraceback.filter(filter_traceback)
                    if not ntraceback:
                        ntraceback = traceback
            ntraceback = ntraceback.filter(excinfo)

            # issue364: mark all but first and last frames to
            # only show a single-line message for each frame.
            if self.config.getoption("tbstyle", "auto") == "auto":
                if len(ntraceback) > 2:
                    ntraceback = Traceback(
                        (
                            ntraceback[0],
                            *(t.with_repr_style("short") for t in ntraceback[1:-1]),
                            ntraceback[-1],
                        )
                    )

            return ntraceback
        return excinfo.traceback

    # TODO: Type ignored -- breaks Liskov Substitution.
    def repr_failure(  # type: ignore[override]
        self,
        excinfo: ExceptionInfo[BaseException],
    ) -> str | TerminalRepr:
        style = self.config.getoption("tbstyle", "auto")
        if style == "auto":
            style = "long"
        return self._repr_failure_py(excinfo, style=style)


class FunctionDefinition(nodes.ItemDefinition, PyCollector):
    """Collector node for a single test function definition.

    Its children are the (possibly parametrized) :class:`Function` invocations
    generated from the definition via :hook:`pytest_generate_tests`.

    This node is only inserted into the collection tree when the
    :confval:`collect_function_definition` option is enabled. Otherwise it is
    created transiently to drive parametrization (backing :class:`Metafunc`)
    and then discarded, with the resulting :class:`Function` items collected
    directly under the containing :class:`Class`/:class:`Module`.
    """

    # Markers are handled explicitly below, mirroring Function.
    _ALLOW_MARKERS = False

    def __init__(
        self,
        name: str,
        parent,
        callobj,
        config: Config | None = None,
        session: Session | None = None,
    ) -> None:
        super().__init__(name, parent, config=config, session=session)

        # The definition always stands for a concrete function object; unlike
        # Function it never looks the object up from its parent lazily.
        self._obj = callobj

        self.own_markers.extend(get_unpacked_marks(self.obj))
        self.keywords.update((mark.name, mark) for mark in self.own_markers)
        self.keywords.update(self.obj.__dict__)

    @property
    def in_collection_tree(self) -> bool:
        """Whether this definition is a node of the collection tree.

        False in the default ``hidden`` mode of
        :confval:`collect_function_definition`, where the definition only exists
        transiently during collection -- and thus cannot anchor anything at run
        time, such as a ``"definition"`` scoped fixture.
        """
        return _collect_function_definition_mode(self.config) != "hidden"

    def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
        children = list(super().collect())
        if _collect_function_definition_mode(self.config) == "messy":
            # Legacy marker layout: transfer this scope's markers back onto each
            # invocation and drop them here, so marker resolution matches the flat
            # layout exactly (no duplication when walking parents in iter_markers).
            marks = self.own_markers
            for child in children:
                child.own_markers[:0] = marks
                child.keywords.update((mark.name, mark) for mark in marks)
            self.own_markers = []
        return children

    # The generate-tests protocol, see nodes.ItemDefinition.

    @property
    def _module_obj(self) -> types.ModuleType:
        modulecol = self.getparent(Module)
        assert modulecol is not None
        return cast(types.ModuleType, modulecol.obj)

    @property
    def _cls_obj(self) -> type | None:
        clscol = self.getparent(Class)
        return (clscol and clscol.obj) or None

    def make_parametrize_context(self) -> Metafunc:
        cls = self._cls_obj
        # Compute the function's fixture closure. This drives parametrization and
        # is shared with the generated invocations; it is carried by the Metafunc
        # rather than stored here -- fixtures belong to the executed items, not
        # to this collector.
        # TODO(#3926): getfixtureinfo() is item-scoped, but here the definition
        # (a collector) stands in for the not-yet-created invocations. Resolve by
        # giving fixture-closure computation a node-level entry point instead of
        # casting a collector to an item.
        fixtureinfo = self.session._fixturemanager.getfixtureinfo(
            cast(nodes.Item, self), self.obj, cls
        )
        return Metafunc(
            definition=self,
            fixtureinfo=fixtureinfo,
            config=self.config,
            cls=cls,
            module=self._module_obj,
            _ispytest=True,
        )

    def parametrize_hook_extras(self) -> Sequence[Callable[..., object]]:
        module = self._module_obj
        cls = self._cls_obj
        methods = []
        if hasattr(module, "pytest_generate_tests"):
            methods.append(module.pytest_generate_tests)
        if cls is not None and hasattr(cls, "pytest_generate_tests"):
            methods.append(cls().pytest_generate_tests)
        return methods

    def finalize_parametrization(self, context: ParametrizeContext) -> None:
        super().finalize_parametrization(context)
        # Direct parametrizations taking place in module/class-specific
        # `metafunc.parametrize` calls may have shadowed some fixtures, so make sure
        # we update what the function really needs a.k.a its fixture closure. Note that
        # direct parametrizations using `@pytest.mark.parametrize` have already been considered
        # into making the closure using `ignore_args` arg to `getfixtureclosure`.
        assert isinstance(context, Metafunc)
        context._fixtureinfo.prune_dependency_tree()

    def make_item(
        self,
        parent: nodes.Collector,
        *,
        name: str,
        callspec: CallSpec | None,
        nodeid: str,
        context: ParametrizeContext,
    ) -> Function:
        assert isinstance(context, Metafunc)
        fixtureinfo = context._fixtureinfo
        if callspec is None:
            return Function.from_parent(
                parent,
                name=name,
                fixtureinfo=fixtureinfo,
                nodeid=nodeid,
            )
        return Function.from_parent(
            parent,
            name=name,
            callspec=callspec,
            fixtureinfo=fixtureinfo,
            keywords={callspec.id: True},
            originalname=self.name,
            nodeid=nodeid,
        )


def __getattr__(name: str) -> object:
    if name == "CallSpec2":
        warnings.warn(CALLSPEC2_RENAMED, stacklevel=2)
        return CallSpec
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
