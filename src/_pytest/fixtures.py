import dataclasses
import functools
import inspect
import os
import sys
import warnings
from collections import defaultdict
from collections import deque
from contextlib import suppress
from pathlib import Path
from types import TracebackType
from typing import Any
from typing import Callable
from typing import cast
from typing import Dict
from typing import final
from typing import Generator
from typing import Generic
from typing import Hashable
from typing import Iterable
from typing import Iterator
from typing import List
from typing import MutableMapping
from typing import NoReturn
from typing import Optional
from typing import overload
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Union

import _pytest
from _pytest import nodes
from _pytest._code import getfslineno
from _pytest._code.code import FormattedExcinfo
from _pytest._code.code import TerminalRepr
from _pytest._io import TerminalWriter
from _pytest.compat import _PytestWrapper
from _pytest.compat import assert_never
from _pytest.compat import get_real_func
from _pytest.compat import get_real_method
from _pytest.compat import getfuncargnames
from _pytest.compat import getimfunc
from _pytest.compat import getlocation
from _pytest.compat import is_generator
from _pytest.compat import NOTSET
from _pytest.compat import NotSetType
from _pytest.compat import safe_getattr
from _pytest.config import _PluggyPlugin
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.deprecated import check_ispytest
from _pytest.deprecated import MARKED_FIXTURE
from _pytest.deprecated import YIELD_FIXTURE
from _pytest.mark import Mark
from _pytest.mark import ParameterSet
from _pytest.mark.structures import MarkDecorator
from _pytest.outcomes import fail
from _pytest.outcomes import skip
from _pytest.outcomes import TEST_OUTCOME
from _pytest.pathlib import absolutepath
from _pytest.pathlib import bestrelpath
from _pytest.scope import HIGH_SCOPES
from _pytest.scope import Scope
from _pytest.stash import StashKey


if TYPE_CHECKING:
    from typing import Deque

    from _pytest.scope import _ScopeName
    from _pytest.main import Session
    from _pytest.python import Metafunc


# The value of the fixture -- return/yield of the fixture function (type variable).
FixtureValue = TypeVar("FixtureValue")
# The type of the fixture function (type variable).
FixtureFunction = TypeVar("FixtureFunction", bound=Callable[..., object])
# The type of a fixture function (type alias generic in fixture value).
_FixtureFunc = Union[
    Callable[..., FixtureValue], Callable[..., Generator[FixtureValue, None, None]]
]
# The type of FixtureDef.cached_result (type alias generic in fixture value).
_FixtureCachedResult = Union[
    Tuple[
        # The result.
        FixtureValue,
        # Cache key.
        object,
        None,
    ],
    Tuple[
        None,
        # Cache key.
        object,
        # Exc info if raised.
        Tuple[Type[BaseException], BaseException, TracebackType],
    ],
]


@dataclasses.dataclass(frozen=True)
class PseudoFixtureDef(Generic[FixtureValue]):
    cached_result: "_FixtureCachedResult[FixtureValue]"
    _scope: Scope


def pytest_sessionstart(session: "Session") -> None:
    session._fixturemanager = FixtureManager(session)


def get_scope_package(
    node: nodes.Item,
    fixturedef: "FixtureDef[object]",
) -> Optional[Union[nodes.Item, nodes.Collector]]:
    from _pytest.python import Package

    current: Optional[Union[nodes.Item, nodes.Collector]] = node
    fixture_package_name = "{}/{}".format(fixturedef.baseid, "__init__.py")
    while current and (
        not isinstance(current, Package) or fixture_package_name != current.nodeid
    ):
        current = current.parent  # type: ignore[assignment]
    if current is None:
        return node.session
    return current


def get_scope_node(
    node: nodes.Node, scope: Scope
) -> Optional[Union[nodes.Item, nodes.Collector]]:
    import _pytest.python

    if scope is Scope.Function:
        return node.getparent(nodes.Item)
    elif scope is Scope.Class:
        return node.getparent(_pytest.python.Class)
    elif scope is Scope.Module:
        return node.getparent(_pytest.python.Module)
    elif scope is Scope.Package:
        return node.getparent(_pytest.python.Package)
    elif scope is Scope.Session:
        return node.getparent(_pytest.main.Session)
    else:
        assert_never(scope)


def resolve_unique_values_and_their_indices_in_parametersets(
    argnames: Sequence[str],
    parametersets: Sequence[ParameterSet],
) -> Tuple[Dict[str, List[object]], List[Tuple[int]]]:
    """Resolve unique values and their indices in parameter sets. The index of a value
    is determined by when it appears in the possible values for the first time.
    For example, given ``argnames`` and ``parametersets`` below, the result would be:

    ::

        argnames = ["A", "B", "C"]
        parametersets = [("a1", "b1", "c1"), ("a1", "b2", "c1"), ("a1", "b3", "c2")]
        result[0] = {"A": ["a1"], "B": ["b1", "b2", "b3"], "C": ["c1", "c2"]}
        result[1] = [(0, 0, 0), (0, 1, 0), (0, 2, 1)]

    result is used in reordering `indirect`ly parametrized with multiple
    parameters or directly parametrized tests to keep items using the same fixture or
    pseudo-fixture values respectively, close together.

    :param argnames:
        Argument names passed to ``parametrize()``.
    :param parametersets:
        The parameter sets, each containing a set of values corresponding
        to ``argnames``.
    :returns:
        Tuple of unique parameter values and their indices in parametersets.
    """
    indices = []
    argname_value_indices_for_hashable_ones: Dict[str, Dict[object, int]] = defaultdict(
        dict
    )
    argvalues_count: Dict[str, int] = defaultdict(lambda: 0)
    unique_values: Dict[str, List[object]] = defaultdict(list)
    for i, argname in enumerate(argnames):
        argname_indices = []
        for parameterset in parametersets:
            value = parameterset.values[i]
            try:
                argname_indices.append(
                    argname_value_indices_for_hashable_ones[argname][value]
                )
            except KeyError:  # New unique value
                argname_value_indices_for_hashable_ones[argname][
                    value
                ] = argvalues_count[argname]
                argname_indices.append(argvalues_count[argname])
                argvalues_count[argname] += 1
                unique_values[argname].append(value)
            except TypeError:  # `value` is not hashable
                argname_indices.append(argvalues_count[argname])
                argvalues_count[argname] += 1
                unique_values[argname].append(value)
        indices.append(argname_indices)
    return unique_values, list(zip(*indices))


# Used for storing artificial fixturedefs for direct parametrization.
name2pseudofixturedef_key = StashKey[Dict[str, "FixtureDef[Any]"]]()


def getfixturemarker(obj: object) -> Optional["FixtureFunctionMarker"]:
    """Return fixturemarker or None if it doesn't exist or raised
    exceptions."""
    return cast(
        Optional[FixtureFunctionMarker],
        safe_getattr(obj, "_pytestfixturefunction", None),
    )


@dataclasses.dataclass(frozen=True)
class FixtureArgKey:
    argname: str
    param_index: Optional[int]
    param_value: Optional[Hashable]
    scoped_item_path: Optional[Path]
    item_cls: Optional[type]
    baseid: Optional[str]


def get_fixture_arg_key(
    item: nodes.Item,
    argname: str,
    scope: Scope,
    baseid: Optional[str] = None,
    is_parametrized: Optional[bool] = False,
) -> FixtureArgKey:
    param_index = None
    param_value = None
    if is_parametrized:
        if isinstance(item.callspec.params[argname], Hashable):
            param_value = item.callspec.params[argname]
        else:
            param_index = item.callspec.indices[argname]

    if scope is Scope.Session:
        scoped_item_path = None
    elif scope is Scope.Package:
        scoped_item_path = item.path.parent
    elif scope in (Scope.Module, Scope.Class):
        scoped_item_path = item.path
    else:
        assert_never(scope)

    if scope is Scope.Class and type(item).__name__ != "DoctestItem":
        item_cls = item.cls  # type: ignore[attr-defined]
    else:
        item_cls = None

    return FixtureArgKey(
        argname, param_index, param_value, scoped_item_path, item_cls, baseid
    )


def get_fixture_keys(item: nodes.Item, scope: Scope) -> Iterator[FixtureArgKey]:
    """Return list of keys for all parametrized arguments which match
    the specified scope."""
    assert scope is not Scope.Function
    if hasattr(item, "_fixtureinfo"):
        for argname in item._fixtureinfo.names_closure:
            is_parametrized = (
                hasattr(item, "callspec") and argname in item.callspec._arg2scope
            )
            for i in reversed(
                range(item._fixtureinfo.name2num_fixturedefs_used[argname])
            ):
                fixturedef = item._fixtureinfo.name2fixturedefs[argname][-(i + 1)]
                # In the case item is parametrized on the `argname` with
                # a scope, it overrides that of the fixture.
                if (is_parametrized and item.callspec._arg2scope[argname] != scope) or (
                    not is_parametrized and fixturedef._scope != scope
                ):
                    break
                yield get_fixture_arg_key(
                    item,
                    argname,
                    scope,
                    None if fixturedef.is_pseudo else fixturedef.baseid,
                    is_parametrized,
                )


# Algorithm for sorting on a per-parametrized resource setup basis.
# It is called for Session scope first and performs sorting
# down to the lower scopes such as to minimize number of "high scope"
# setups and teardowns.


def reorder_items(items: Sequence[nodes.Item]) -> List[nodes.Item]:
    argkeys_cache: Dict[Scope, Dict[nodes.Item, Dict[FixtureArgKey, None]]] = {}
    items_by_argkey: Dict[Scope, Dict[FixtureArgKey, Deque[nodes.Item]]] = {}
    for scope in HIGH_SCOPES:
        d: Dict[nodes.Item, Dict[FixtureArgKey, None]] = {}
        argkeys_cache[scope] = d
        item_d: Dict[FixtureArgKey, Deque[nodes.Item]] = defaultdict(deque)
        items_by_argkey[scope] = item_d
        for item in items:
            keys = dict.fromkeys(get_fixture_keys(item, scope), None)
            if keys:
                d[item] = keys
                for key in keys:
                    item_d[key].append(item)
    items_dict = dict.fromkeys(items, None)
    last_item_by_argkey: Dict[FixtureArgKey, nodes.Item] = {}
    reordered_items = list(
        reorder_items_atscope(
            items_dict,
            argkeys_cache,
            items_by_argkey,
            last_item_by_argkey,
            Scope.Session,
        )
    )
    for scope in reversed(HIGH_SCOPES):
        for key in items_by_argkey[scope]:
            last_item_dependent_on_key = last_item_by_argkey[key]
            if key.baseid is None:
                continue
            for i in range(
                last_item_dependent_on_key._fixtureinfo.name2num_fixturedefs_used[
                    key.argname
                ]
            ):
                fixturedef = last_item_dependent_on_key._fixtureinfo.name2fixturedefs[
                    key.argname
                ][-(i + 1)]
                if fixturedef.baseid == key.baseid:
                    break
            last_item_dependent_on_key.teardown = functools.partial(
                lambda other_finalizers, new_finalizer: [
                    finalizer() for finalizer in (new_finalizer, other_finalizers)
                ],
                last_item_dependent_on_key.teardown,
                functools.partial(
                    fixturedef.finish, last_item_dependent_on_key._request
                ),
            )
    return reordered_items


def fix_cache_order(
    item: nodes.Item,
    argkeys_cache: Dict[Scope, Dict[nodes.Item, Dict[FixtureArgKey, None]]],
    items_by_argkey: Dict[Scope, Dict[FixtureArgKey, "Deque[nodes.Item]"]],
    ignore: Set[Optional[FixtureArgKey]],
    current_scope: Scope,
) -> None:
    for scope in HIGH_SCOPES:
        if current_scope < scope:
            continue
        for key in argkeys_cache[scope].get(item, []):
            if key in ignore:
                continue
            items_by_argkey[scope][key].appendleft(item)


def reorder_items_atscope(
    items: Dict[nodes.Item, None],
    argkeys_cache: Dict[Scope, Dict[nodes.Item, Dict[FixtureArgKey, None]]],
    items_by_argkey: Dict[Scope, Dict[FixtureArgKey, "Deque[nodes.Item]"]],
    last_item_by_argkey: Dict[FixtureArgKey, nodes.Item],
    scope: Scope,
) -> Dict[nodes.Item, None]:
    if scope is Scope.Function:
        return items
    elif len(items) < 3:
        for item in items:
            for key in argkeys_cache[scope].get(item, []):
                last_item_by_argkey[key] = item
        return reorder_items_atscope(
            items,
            argkeys_cache,
            items_by_argkey,
            last_item_by_argkey,
            scope.next_lower(),
        )
    ignore: Set[Optional[FixtureArgKey]] = set()
    items_deque = deque(items)
    items_done: Dict[nodes.Item, None] = {}
    scoped_items_by_argkey = items_by_argkey[scope]
    scoped_argkeys_cache = argkeys_cache[scope]
    while items_deque:
        no_argkey_group: Dict[nodes.Item, None] = {}
        slicing_argkey = None
        while items_deque:
            item = items_deque.popleft()
            if item in items_done or item in no_argkey_group:
                continue
            argkeys = dict.fromkeys(
                (k for k in scoped_argkeys_cache.get(item, []) if k not in ignore), None
            )
            if not argkeys:
                no_argkey_group[item] = None
            else:
                slicing_argkey, _ = argkeys.popitem()
                # deque because they'll just be ignored.
                unique_matching_items = dict.fromkeys(scoped_items_by_argkey[slicing_argkey])
                for i in reversed(unique_matching_items if sys.version_info.minor > 7 else list(unique_matching_items)):
                    if i not in items:
                        continue
                    fix_cache_order(i, argkeys_cache, items_by_argkey, ignore, scope)
                    items_deque.appendleft(i)
                break
        if no_argkey_group:
            no_argkey_group = reorder_items_atscope(
                no_argkey_group,
                argkeys_cache,
                items_by_argkey,
                last_item_by_argkey,
                scope.next_lower(),
            )
            for item in no_argkey_group:
                for key in scoped_argkeys_cache.get(item, []):
                    last_item_by_argkey[key] = item
                items_done[item] = None
        ignore.add(slicing_argkey)
    return items_done


@dataclasses.dataclass
class FuncFixtureInfo:
    __slots__ = (
        "argnames",
        "initialnames",
        "names_closure",
        "name2fixturedefs",
        "name2num_fixturedefs_used",
    )

    # Original function argument names.
    argnames: Tuple[str, ...]
    # Argnames that function immediately requires. These include argnames +
    # fixture names specified via usefixtures and via autouse=True in fixture
    # definitions.
    initialnames: Tuple[str, ...]
    names_closure: List[str]
    name2fixturedefs: Dict[str, Sequence["FixtureDef[Any]"]]
    name2num_fixturedefs_used: Dict[str, int]

    def prune_dependency_tree(self) -> None:
        """Recompute names_closure from initialnames and name2fixturedefs.

        Can only reduce names_closure, which means that the new closure will
        always be a subset of the old one. The order is preserved.

        This method is needed because dynamic direct parametrization may shadow
        some of the fixtures that were included in the originally built dependency
        tree. In this way the dependency tree can get pruned, and the closure
        of argnames may get reduced.
        """


class FixtureRequest:
    """A request for a fixture from a test or fixture function.

    A request object gives access to the requesting test context and has
    an optional ``param`` attribute in case the fixture is parametrized
    indirectly.
    """

    def __init__(self, pyfuncitem, *, _ispytest: bool = False) -> None:
        check_ispytest(_ispytest)
        self._pyfuncitem = pyfuncitem
        #: Fixture for which this request is being performed.
        self.fixturename: Optional[str] = None
        self._scope = Scope.Function
        self._fixture_defs: Dict[str, FixtureDef[Any]] = {}
        fixtureinfo: FuncFixtureInfo = pyfuncitem._fixtureinfo
        self._arg2fixturedefs = fixtureinfo.name2fixturedefs.copy()
        self._arg2index: Dict[str, int] = {}
        self._fixturemanager: FixtureManager = pyfuncitem.session._fixturemanager
        # Notes on the type of `param`:
        # -`request.param` is only defined in parametrized fixtures, and will raise
        #   AttributeError otherwise. Python typing has no notion of "undefined", so
        #   this cannot be reflected in the type.
        # - Technically `param` is only (possibly) defined on SubRequest, not
        #   FixtureRequest, but the typing of that is still in flux so this cheats.
        # - In the future we might consider using a generic for the param type, but
        #   for now just using Any.
        self.param: Any

    @property
    def scope(self) -> "_ScopeName":
        """Scope string, one of "function", "class", "module", "package", "session"."""
        return self._scope.value

    @property
    def fixturenames(self) -> List[str]:
        """Names of all active fixtures in this request."""
        result = list(self._pyfuncitem._fixtureinfo.names_closure)
        result.extend(set(self._fixture_defs).difference(result))
        return result

    @property
    def node(self):
        """Underlying collection node (depends on current request scope)."""
        scope = self._scope
        if scope is Scope.Function:
            # This might also be a non-function Item despite its attribute name.
            node: Optional[Union[nodes.Item, nodes.Collector]] = self._pyfuncitem
        elif scope is Scope.Package:
            # FIXME: _fixturedef is not defined on FixtureRequest (this class),
            # but on FixtureRequest (a subclass).
            node = get_scope_package(self._pyfuncitem, self._fixturedef)  # type: ignore[attr-defined]
        else:
            node = get_scope_node(self._pyfuncitem, scope)
        if node is None and scope is Scope.Class:
            # Fallback to function item itself.
            node = self._pyfuncitem
        assert node, 'Could not obtain a node for scope "{}" for function {!r}'.format(
            scope, self._pyfuncitem
        )
        return node

    def _getnextfixturedef(self, argname: str) -> "FixtureDef[Any]":
        fixturedefs = self._arg2fixturedefs.get(argname, None)
        if fixturedefs is None:
            # We arrive here because of a dynamic call to
            # getfixturevalue(argname) usage which was naturally
            # not known at parsing/collection time.
            assert self._pyfuncitem.parent is not None
            parentid = self._pyfuncitem.parent.nodeid
            fixturedefs = self._fixturemanager.getfixturedefs(argname, parentid)
            # TODO: Fix this type ignore. Either add assert or adjust types.
            #       Can this be None here?
            self._arg2fixturedefs[argname] = fixturedefs  # type: ignore[assignment]
        # fixturedefs list is immutable so we maintain a decreasing index.
        index = self._arg2index.get(argname, 0) - 1
        if fixturedefs is None or (-index > len(fixturedefs)):
            raise FixtureLookupError(argname, self)
        self._arg2index[argname] = index
        return fixturedefs[index]

    @property
    def config(self) -> Config:
        """The pytest config object associated with this request."""
        return self._pyfuncitem.config  # type: ignore[no-any-return]

    @property
    def function(self):
        """Test function object if the request has a per-function scope."""
        if self.scope != "function":
            raise AttributeError(
                f"function not available in {self.scope}-scoped context"
            )
        return self._pyfuncitem.obj

    @property
    def cls(self):
        """Class (can be None) where the test function was collected."""
        if self.scope not in ("class", "function"):
            raise AttributeError(f"cls not available in {self.scope}-scoped context")
        clscol = self._pyfuncitem.getparent(_pytest.python.Class)
        if clscol:
            return clscol.obj

    @property
    def instance(self):
        """Instance (can be None) on which test function was collected."""
        # unittest support hack, see _pytest.unittest.TestCaseFunction.
        try:
            return self._pyfuncitem._testcase
        except AttributeError:
            function = getattr(self, "function", None)
            return getattr(function, "__self__", None)

    @property
    def module(self):
        """Python module object where the test function was collected."""
        if self.scope not in ("function", "class", "module"):
            raise AttributeError(f"module not available in {self.scope}-scoped context")
        return self._pyfuncitem.getparent(_pytest.python.Module).obj

    @property
    def path(self) -> Path:
        """Path where the test function was collected."""
        if self.scope not in ("function", "class", "module", "package"):
            raise AttributeError(f"path not available in {self.scope}-scoped context")
        # TODO: Remove ignore once _pyfuncitem is properly typed.
        return self._pyfuncitem.path  # type: ignore

    @property
    def keywords(self) -> MutableMapping[str, Any]:
        """Keywords/markers dictionary for the underlying node."""
        node: nodes.Node = self.node
        return node.keywords

    @property
    def session(self) -> "Session":
        """Pytest session object."""
        return self._pyfuncitem.session  # type: ignore[no-any-return]

    def addfinalizer(self, finalizer: Callable[[], object]) -> None:
        """Add finalizer/teardown function to be called without arguments after
        the last test within the requesting test context finished execution."""
        # XXX usually this method is shadowed by fixturedef specific ones.
        self.node.addfinalizer(finalizer)

    def applymarker(self, marker: Union[str, MarkDecorator]) -> None:
        """Apply a marker to a single test function invocation.

        This method is useful if you don't want to have a keyword/marker
        on all function invocations.

        :param marker:
            An object created by a call to ``pytest.mark.NAME(...)``.
        """
        self.node.add_marker(marker)

    def raiseerror(self, msg: Optional[str]) -> NoReturn:
        """Raise a FixtureLookupError exception.

        :param msg:
            An optional custom error message.
        """
        raise self._fixturemanager.FixtureLookupError(None, self, msg)

    def _fillfixtures(self) -> None:
        item = self._pyfuncitem
        fixturenames = getattr(item, "fixturenames", self.fixturenames)
        for argname in fixturenames:
            if argname not in item.funcargs:
                item.funcargs[argname] = self.getfixturevalue(argname)

    def getfixturevalue(self, argname: str) -> Any:
        """Dynamically run a named fixture function.

        Declaring fixtures via function argument is recommended where possible.
        But if you can only decide whether to use another fixture at test
        setup time, you may use this function to retrieve it inside a fixture
        or test function body.

        This method can be used during the test setup phase or the test run
        phase, but during the test teardown phase a fixture's value may not
        be available.

        :param argname:
            The fixture name.
        :raises pytest.FixtureLookupError:
            If the given fixture could not be found.
        """
        fixturedef = self._get_active_fixturedef(argname)
        assert fixturedef.cached_result is not None, (
            f'The fixture value for "{argname}" is not available.  '
            "This can happen when the fixture has already been torn down."
        )
        return fixturedef.cached_result[0]

    def _get_active_fixturedef(
        self, argname: str
    ) -> Union["FixtureDef[object]", PseudoFixtureDef[object]]:
        try:
            return self._fixture_defs[argname]
        except KeyError:
            try:
                fixturedef = self._getnextfixturedef(argname)
            except FixtureLookupError:
                if argname == "request":
                    cached_result = (self, [0], None)
                    return PseudoFixtureDef(cached_result, Scope.Function)
                raise
        # Remove indent to prevent the python3 exception
        # from leaking into the call.
        self._compute_fixture_value(fixturedef)
        self._fixture_defs[argname] = fixturedef
        return fixturedef

    def _get_fixturestack(self) -> List["FixtureDef[Any]"]:
        current = self
        values: List[FixtureDef[Any]] = []
        while isinstance(current, SubRequest):
            values.append(current._fixturedef)  # type: ignore[has-type]
            current = current._parent_request
        values.reverse()
        return values

    def _compute_fixture_value(self, fixturedef: "FixtureDef[object]") -> None:
        """Create a SubRequest based on "self" and call the execute method
        of the given FixtureDef object.

        This will force the FixtureDef object to throw away any previous
        results and compute a new fixture value, which will be stored into
        the FixtureDef object itself.
        """
        # prepare a subrequest object before calling fixture function
        # (latter managed by fixturedef)
        argname = fixturedef.argname
        funcitem = self._pyfuncitem
        scope = fixturedef._scope
        try:
            callspec = funcitem.callspec
        except AttributeError:
            callspec = None
        if callspec is not None and argname in callspec.params:
            param = callspec.params[argname]
            param_index = callspec.indices[argname]
            # If a parametrize invocation set a scope it will override
            # the static scope defined with the fixture function.
            with suppress(KeyError):
                scope = callspec._arg2scope[argname]
        else:
            param = NOTSET
            param_index = 0
            has_params = fixturedef.params is not None
            fixtures_not_supported = getattr(funcitem, "nofuncargs", False)
            if has_params and fixtures_not_supported:
                msg = (
                    "{name} does not support fixtures, maybe unittest.TestCase subclass?\n"
                    "Node id: {nodeid}\n"
                    "Function type: {typename}"
                ).format(
                    name=funcitem.name,
                    nodeid=funcitem.nodeid,
                    typename=type(funcitem).__name__,
                )
                fail(msg, pytrace=False)
            if has_params:
                frame = inspect.stack()[3]
                frameinfo = inspect.getframeinfo(frame[0])
                source_path = absolutepath(frameinfo.filename)
                source_lineno = frameinfo.lineno
                try:
                    source_path_str = str(
                        source_path.relative_to(funcitem.config.rootpath)
                    )
                except ValueError:
                    source_path_str = str(source_path)
                msg = (
                    "The requested fixture has no parameter defined for test:\n"
                    "    {}\n\n"
                    "Requested fixture '{}' defined in:\n{}"
                    "\n\nRequested here:\n{}:{}".format(
                        funcitem.nodeid,
                        fixturedef.argname,
                        getlocation(fixturedef.func, funcitem.config.rootpath),
                        source_path_str,
                        source_lineno,
                    )
                )
                fail(msg, pytrace=False)

        subrequest = SubRequest(
            self, scope, param, param_index, fixturedef, _ispytest=True
        )

        # Check if a higher-level scoped fixture accesses a lower level one.
        subrequest._check_scope(argname, self._scope, scope)
        try:
            # Call the fixture function.
            fixturedef.execute(request=subrequest)
        finally:
            self._schedule_finalizers(fixturedef, subrequest)

    def _schedule_finalizers(
        self, fixturedef: "FixtureDef[object]", subrequest: "SubRequest"
    ) -> None:
        # If fixture function failed it might have registered finalizers.
        subrequest.node.addfinalizer(lambda: fixturedef.finish(request=subrequest))

    def _check_scope(
        self,
        argname: str,
        invoking_scope: Scope,
        requested_scope: Scope,
    ) -> None:
        if argname == "request":
            return
        if invoking_scope > requested_scope:
            # Try to report something helpful.
            text = "\n".join(self._factorytraceback())
            fail(
                f"ScopeMismatch: You tried to access the {requested_scope.value} scoped "
                f"fixture {argname} with a {invoking_scope.value} scoped request object, "
                f"involved factories:\n{text}",
                pytrace=False,
            )

    def _factorytraceback(self) -> List[str]:
        lines = []
        for fixturedef in self._get_fixturestack():
            factory = fixturedef.func
            fs, lineno = getfslineno(factory)
            if isinstance(fs, Path):
                session: Session = self._pyfuncitem.session
                p = bestrelpath(session.path, fs)
            else:
                p = fs
            lines.append(
                "%s:%d:  def %s%s"
                % (p, lineno + 1, factory.__name__, inspect.signature(factory))
            )
        return lines

    def __repr__(self) -> str:
        return "<FixtureRequest for %r>" % (self.node)


@final
class SubRequest(FixtureRequest):
    """A sub request for handling getting a fixture from a test function/fixture."""

    def __init__(
        self,
        request: "FixtureRequest",
        scope: Scope,
        param: Any,
        param_index: int,
        fixturedef: "FixtureDef[object]",
        *,
        _ispytest: bool = False,
    ) -> None:
        check_ispytest(_ispytest)
        self._parent_request = request
        self.fixturename = fixturedef.argname
        if param is not NOTSET:
            self.param = param
        self.param_index = param_index
        self._scope = scope
        self._fixturedef = fixturedef
        self._pyfuncitem = request._pyfuncitem
        self._fixture_defs = request._fixture_defs
        self._arg2fixturedefs = request._arg2fixturedefs
        self._arg2index = request._arg2index
        self._fixturemanager = request._fixturemanager

    def __repr__(self) -> str:
        return f"<SubRequest {self.fixturename!r} for {self._pyfuncitem!r}>"

    def addfinalizer(self, finalizer: Callable[[], object]) -> None:
        """Add finalizer/teardown function to be called without arguments after
        the last test within the requesting test context finished execution."""
        self._fixturedef.addfinalizer(finalizer)

    def _schedule_finalizers(
        self, fixturedef: "FixtureDef[object]", subrequest: "SubRequest"
    ) -> None:
        # If the executing fixturedef was not explicitly requested in the argument list (via
        # getfixturevalue inside the fixture call) then ensure this fixture def will be finished
        # first.
        if fixturedef.argname not in self.fixturenames:
            fixturedef.addfinalizer(
                functools.partial(self._fixturedef.finish, request=self)
            )
        super()._schedule_finalizers(fixturedef, subrequest)


@final
class FixtureLookupError(LookupError):
    """Could not return a requested fixture (missing or invalid)."""

    def __init__(
        self, argname: Optional[str], request: FixtureRequest, msg: Optional[str] = None
    ) -> None:
        self.argname = argname
        self.request = request
        self.fixturestack = request._get_fixturestack()
        self.msg = msg

    def formatrepr(self) -> "FixtureLookupErrorRepr":
        tblines: List[str] = []
        addline = tblines.append
        stack = [self.request._pyfuncitem.obj]
        stack.extend(map(lambda x: x.func, self.fixturestack))
        msg = self.msg
        if msg is not None:
            # The last fixture raise an error, let's present
            # it at the requesting side.
            stack = stack[:-1]
        for function in stack:
            fspath, lineno = getfslineno(function)
            try:
                lines, _ = inspect.getsourcelines(get_real_func(function))
            except (OSError, IndexError, TypeError):
                error_msg = "file %s, line %s: source code not available"
                addline(error_msg % (fspath, lineno + 1))
            else:
                addline(f"file {fspath}, line {lineno + 1}")
                for i, line in enumerate(lines):
                    line = line.rstrip()
                    addline("  " + line)
                    if line.lstrip().startswith("def"):
                        break

        if msg is None:
            fm = self.request._fixturemanager
            available = set()
            parentid = self.request._pyfuncitem.parent.nodeid
            for name, fixturedefs in fm._arg2fixturedefs.items():
                faclist = list(fm._matchfactories(fixturedefs, parentid))
                if faclist:
                    available.add(name)
            if self.argname in available:
                msg = " recursive dependency involving fixture '{}' detected".format(
                    self.argname
                )
            else:
                msg = f"fixture '{self.argname}' not found"
            msg += "\n available fixtures: {}".format(", ".join(sorted(available)))
            msg += "\n use 'pytest --fixtures [testpath]' for help on them."

        return FixtureLookupErrorRepr(fspath, lineno, tblines, msg, self.argname)


class FixtureLookupErrorRepr(TerminalRepr):
    def __init__(
        self,
        filename: Union[str, "os.PathLike[str]"],
        firstlineno: int,
        tblines: Sequence[str],
        errorstring: str,
        argname: Optional[str],
    ) -> None:
        self.tblines = tblines
        self.errorstring = errorstring
        self.filename = filename
        self.firstlineno = firstlineno
        self.argname = argname

    def toterminal(self, tw: TerminalWriter) -> None:
        # tw.line("FixtureLookupError: %s" %(self.argname), red=True)
        for tbline in self.tblines:
            tw.line(tbline.rstrip())
        lines = self.errorstring.split("\n")
        if lines:
            tw.line(
                f"{FormattedExcinfo.fail_marker}       {lines[0].strip()}",
                red=True,
            )
            for line in lines[1:]:
                tw.line(
                    f"{FormattedExcinfo.flow_marker}       {line.strip()}",
                    red=True,
                )
        tw.line()
        tw.line("%s:%d" % (os.fspath(self.filename), self.firstlineno + 1))


def fail_fixturefunc(fixturefunc, msg: str) -> NoReturn:
    fs, lineno = getfslineno(fixturefunc)
    location = f"{fs}:{lineno + 1}"
    source = _pytest._code.Source(fixturefunc)
    fail(msg + ":\n\n" + str(source.indent()) + "\n" + location, pytrace=False)


def call_fixture_func(
    fixturefunc: "_FixtureFunc[FixtureValue]", request: SubRequest, kwargs
) -> FixtureValue:
    if is_generator(fixturefunc):
        fixturefunc = cast(
            Callable[..., Generator[FixtureValue, None, None]], fixturefunc
        )
        generator = fixturefunc(**kwargs)
        try:
            fixture_result = next(generator)
        except StopIteration:
            raise ValueError(f"{request.fixturename} did not yield a value") from None
        finalizer = functools.partial(_teardown_yield_fixture, fixturefunc, generator)
        request.addfinalizer(finalizer)
    else:
        fixturefunc = cast(Callable[..., FixtureValue], fixturefunc)
        fixture_result = fixturefunc(**kwargs)
    return fixture_result


def _teardown_yield_fixture(fixturefunc, it) -> None:
    """Execute the teardown of a fixture function by advancing the iterator
    after the yield and ensure the iteration ends (if not it means there is
    more than one yield in the function)."""
    try:
        next(it)
    except StopIteration:
        pass
    else:
        fail_fixturefunc(fixturefunc, "fixture function has more than one 'yield'")


def _eval_scope_callable(
    scope_callable: "Callable[[str, Config], _ScopeName]",
    fixture_name: str,
    config: Config,
) -> "_ScopeName":
    try:
        # Type ignored because there is no typing mechanism to specify
        # keyword arguments, currently.
        result = scope_callable(fixture_name=fixture_name, config=config)  # type: ignore[call-arg]
    except Exception as e:
        raise TypeError(
            "Error evaluating {} while defining fixture '{}'.\n"
            "Expected a function with the signature (*, fixture_name, config)".format(
                scope_callable, fixture_name
            )
        ) from e
    if not isinstance(result, str):
        fail(
            "Expected {} to return a 'str' while defining fixture '{}', but it returned:\n"
            "{!r}".format(scope_callable, fixture_name, result),
            pytrace=False,
        )
    return result


@final
class FixtureDef(Generic[FixtureValue]):
    """A container for a fixture definition."""

    def __init__(
        self,
        fixturemanager: "FixtureManager",
        baseid: Optional[str],
        argname: str,
        func: "_FixtureFunc[FixtureValue]",
        scope: Union[Scope, "_ScopeName", Callable[[str, Config], "_ScopeName"], None],
        params: Optional[Sequence[object]],
        unittest: bool = False,
        ids: Optional[
            Union[Tuple[Optional[object], ...], Callable[[Any], Optional[object]]]
        ] = None,
        is_pseudo: bool = False,
    ) -> None:
        self._fixturemanager = fixturemanager
        # The "base" node ID for the fixture.
        #
        # This is a node ID prefix. A fixture is only available to a node (e.g.
        # a `Function` item) if the fixture's baseid is a parent of the node's
        # nodeid (see the `iterparentnodeids` function for what constitutes a
        # "parent" and a "prefix" in this context).
        #
        # For a fixture found in a Collector's object (e.g. a `Module`s module,
        # a `Class`'s class), the baseid is the Collector's nodeid.
        #
        # For a fixture found in a conftest plugin, the baseid is the conftest's
        # directory path relative to the rootdir.
        #
        # For other plugins, the baseid is the empty string (always matches).
        self.baseid = baseid or ""
        # Whether the fixture was found from a node or a conftest in the
        # collection tree. Will be false for fixtures defined in non-conftest
        # plugins.
        self.has_location = baseid is not None
        # The fixture factory function.
        self.func = func
        # The name by which the fixture may be requested.
        self.argname = argname
        if scope is None:
            scope = Scope.Function
        elif callable(scope):
            scope = _eval_scope_callable(scope, argname, fixturemanager.config)
        if isinstance(scope, str):
            scope = Scope.from_user(
                scope, descr=f"Fixture '{func.__name__}'", where=baseid
            )
        self._scope = scope
        # If the fixture is directly parametrized, the parameter values.
        self.params: Optional[Sequence[object]] = params
        # If the fixture is directly parametrized, a tuple of explicit IDs to
        # assign to the parameter values, or a callable to generate an ID given
        # a parameter value.
        self.ids = ids
        # The names requested by the fixtures.
        self.argnames = getfuncargnames(func, name=argname, is_method=unittest)
        # Whether the fixture was collected from a unittest TestCase class.
        # Note that it really only makes sense to define autouse fixtures in
        # unittest TestCases.
        self.unittest = unittest
        # If the fixture was executed, the current value of the fixture.
        # Can change if the fixture is executed with different parameters.
        self.cached_result: Optional[_FixtureCachedResult[FixtureValue]] = None
        self._finalizers: List[Callable[[], object]] = []

        # Whether fixture is a pseudo-fixture made in direct parametrizations.
        self.is_pseudo = is_pseudo

    @property
    def scope(self) -> "_ScopeName":
        """Scope string, one of "function", "class", "module", "package", "session"."""
        return self._scope.value

    def addfinalizer(self, finalizer: Callable[[], object]) -> None:
        self._finalizers.append(finalizer)

    def finish(self, request: SubRequest) -> None:
        exc = None
        try:
            while self._finalizers:
                try:
                    func = self._finalizers.pop()
                    func()
                except BaseException as e:
                    # XXX Only first exception will be seen by user,
                    #     ideally all should be reported.
                    if exc is None:
                        exc = e
            if exc:
                raise exc
        finally:
            ihook = request.node.ihook
            ihook.pytest_fixture_post_finalizer(fixturedef=self, request=request)
            # Even if finalization fails, we invalidate the cached fixture
            # value and remove all finalizers because they may be bound methods
            # which will keep instances alive.
            self.cached_result = None
            self._finalizers = []

    def execute(self, request: SubRequest) -> FixtureValue:
        # Get required arguments and register our own finish()
        # with their finalization.
        for argname in self.argnames:
            fixturedef = request._get_active_fixturedef(argname)
            if argname != "request":
                # PseudoFixtureDef is only for "request".
                assert isinstance(fixturedef, FixtureDef)
                fixturedef.addfinalizer(functools.partial(self.finish, request=request))

        my_cache_key = self.cache_key(request)
        if self.cached_result is not None:
            # note: comparison with `==` can fail (or be expensive) for e.g.
            # numpy arrays (#6497).
            cache_key = self.cached_result[1]
            if my_cache_key is cache_key:
                if self.cached_result[2] is not None:
                    _, val, tb = self.cached_result[2]
                    raise val.with_traceback(tb)
                else:
                    result = self.cached_result[0]
                    return result
            # We have a previous but differently parametrized fixture instance
            # so we need to tear it down before creating a new one.
            self.finish(request)
            assert self.cached_result is None

        ihook = request.node.ihook
        result = ihook.pytest_fixture_setup(fixturedef=self, request=request)
        return result

    def cache_key(self, request: SubRequest) -> object:
        return request.param_index if not hasattr(request, "param") else request.param

    def __repr__(self) -> str:
        return "<FixtureDef argname={!r} scope={!r} baseid={!r}>".format(
            self.argname, self.scope, self.baseid
        )


def resolve_fixture_function(
    fixturedef: FixtureDef[FixtureValue], request: FixtureRequest
) -> "_FixtureFunc[FixtureValue]":
    """Get the actual callable that can be called to obtain the fixture
    value, dealing with unittest-specific instances and bound methods."""
    fixturefunc = fixturedef.func
    if fixturedef.unittest:
        if request.instance is not None:
            # Bind the unbound method to the TestCase instance.
            fixturefunc = fixturedef.func.__get__(request.instance)  # type: ignore[union-attr]
    else:
        # The fixture function needs to be bound to the actual
        # request.instance so that code working with "fixturedef" behaves
        # as expected.
        if request.instance is not None:
            # Handle the case where fixture is defined not in a test class, but some other class
            # (for example a plugin class with a fixture), see #2270.
            if hasattr(fixturefunc, "__self__") and not isinstance(
                request.instance, fixturefunc.__self__.__class__  # type: ignore[union-attr]
            ):
                return fixturefunc
            fixturefunc = getimfunc(fixturedef.func)
            if fixturefunc != fixturedef.func:
                fixturefunc = fixturefunc.__get__(request.instance)  # type: ignore[union-attr]
    return fixturefunc


def pytest_fixture_setup(
    fixturedef: FixtureDef[FixtureValue], request: SubRequest
) -> FixtureValue:
    """Execution of fixture setup."""
    kwargs = {}
    for argname in fixturedef.argnames:
        fixdef = request._get_active_fixturedef(argname)
        assert fixdef.cached_result is not None
        result, arg_cache_key, exc = fixdef.cached_result
        request._check_scope(argname, request._scope, fixdef._scope)
        kwargs[argname] = result

    fixturefunc = resolve_fixture_function(fixturedef, request)
    my_cache_key = fixturedef.cache_key(request)
    try:
        result = call_fixture_func(fixturefunc, request, kwargs)
    except TEST_OUTCOME:
        exc_info = sys.exc_info()
        assert exc_info[0] is not None
        if isinstance(
            exc_info[1], skip.Exception
        ) and not fixturefunc.__name__.startswith("xunit_setup"):
            exc_info[1]._use_item_location = True  # type: ignore[attr-defined]
        fixturedef.cached_result = (None, my_cache_key, exc_info)
        raise
    fixturedef.cached_result = (result, my_cache_key, None)
    return result


def _ensure_immutable_ids(
    ids: Optional[Union[Sequence[Optional[object]], Callable[[Any], Optional[object]]]]
) -> Optional[Union[Tuple[Optional[object], ...], Callable[[Any], Optional[object]]]]:
    if ids is None:
        return None
    if callable(ids):
        return ids
    return tuple(ids)


def _params_converter(
    params: Optional[Iterable[object]],
) -> Optional[Tuple[object, ...]]:
    return tuple(params) if params is not None else None


def wrap_function_to_error_out_if_called_directly(
    function: FixtureFunction,
    fixture_marker: "FixtureFunctionMarker",
) -> FixtureFunction:
    """Wrap the given fixture function so we can raise an error about it being called directly,
    instead of used as an argument in a test function."""
    message = (
        'Fixture "{name}" called directly. Fixtures are not meant to be called directly,\n'
        "but are created automatically when test functions request them as parameters.\n"
        "See https://docs.pytest.org/en/stable/explanation/fixtures.html for more information about fixtures, and\n"
        "https://docs.pytest.org/en/stable/deprecations.html#calling-fixtures-directly about how to update your code."
    ).format(name=fixture_marker.name or function.__name__)

    @functools.wraps(function)
    def result(*args, **kwargs):
        fail(message, pytrace=False)

    # Keep reference to the original function in our own custom attribute so we don't unwrap
    # further than this point and lose useful wrappings like @mock.patch (#3774).
    result.__pytest_wrapped__ = _PytestWrapper(function)  # type: ignore[attr-defined]

    return cast(FixtureFunction, result)


@final
@dataclasses.dataclass(frozen=True)
class FixtureFunctionMarker:
    scope: "Union[_ScopeName, Callable[[str, Config], _ScopeName]]"
    params: Optional[Tuple[object, ...]]
    autouse: bool = False
    ids: Optional[
        Union[Tuple[Optional[object], ...], Callable[[Any], Optional[object]]]
    ] = None
    name: Optional[str] = None

    _ispytest: dataclasses.InitVar[bool] = False

    def __post_init__(self, _ispytest: bool) -> None:
        check_ispytest(_ispytest)

    def __call__(self, function: FixtureFunction) -> FixtureFunction:
        if inspect.isclass(function):
            raise ValueError("class fixtures not supported (maybe in the future)")

        if getattr(function, "_pytestfixturefunction", False):
            raise ValueError(
                "fixture is being applied more than once to the same function"
            )

        if hasattr(function, "pytestmark"):
            warnings.warn(MARKED_FIXTURE, stacklevel=2)

        function = wrap_function_to_error_out_if_called_directly(function, self)

        name = self.name or function.__name__
        if name == "request":
            location = getlocation(function)
            fail(
                "'request' is a reserved word for fixtures, use another name:\n  {}".format(
                    location
                ),
                pytrace=False,
            )

        # Type ignored because https://github.com/python/mypy/issues/2087.
        function._pytestfixturefunction = self  # type: ignore[attr-defined]
        return function


@overload
def fixture(
    fixture_function: FixtureFunction,
    *,
    scope: "Union[_ScopeName, Callable[[str, Config], _ScopeName]]" = ...,
    params: Optional[Iterable[object]] = ...,
    autouse: bool = ...,
    ids: Optional[
        Union[Sequence[Optional[object]], Callable[[Any], Optional[object]]]
    ] = ...,
    name: Optional[str] = ...,
) -> FixtureFunction:
    ...


@overload
def fixture(  # noqa: F811
    fixture_function: None = ...,
    *,
    scope: "Union[_ScopeName, Callable[[str, Config], _ScopeName]]" = ...,
    params: Optional[Iterable[object]] = ...,
    autouse: bool = ...,
    ids: Optional[
        Union[Sequence[Optional[object]], Callable[[Any], Optional[object]]]
    ] = ...,
    name: Optional[str] = None,
) -> FixtureFunctionMarker:
    ...


def fixture(  # noqa: F811
    fixture_function: Optional[FixtureFunction] = None,
    *,
    scope: "Union[_ScopeName, Callable[[str, Config], _ScopeName]]" = "function",
    params: Optional[Iterable[object]] = None,
    autouse: bool = False,
    ids: Optional[
        Union[Sequence[Optional[object]], Callable[[Any], Optional[object]]]
    ] = None,
    name: Optional[str] = None,
) -> Union[FixtureFunctionMarker, FixtureFunction]:
    """Decorator to mark a fixture factory function.

    This decorator can be used, with or without parameters, to define a
    fixture function.

    The name of the fixture function can later be referenced to cause its
    invocation ahead of running tests: test modules or classes can use the
    ``pytest.mark.usefixtures(fixturename)`` marker.

    Test functions can directly use fixture names as input arguments in which
    case the fixture instance returned from the fixture function will be
    injected.

    Fixtures can provide their values to test functions using ``return`` or
    ``yield`` statements. When using ``yield`` the code block after the
    ``yield`` statement is executed as teardown code regardless of the test
    outcome, and must yield exactly once.

    :param scope:
        The scope for which this fixture is shared; one of ``"function"``
        (default), ``"class"``, ``"module"``, ``"package"`` or ``"session"``.

        This parameter may also be a callable which receives ``(fixture_name, config)``
        as parameters, and must return a ``str`` with one of the values mentioned above.

        See :ref:`dynamic scope` in the docs for more information.

    :param params:
        An optional list of parameters which will cause multiple invocations
        of the fixture function and all of the tests using it. The current
        parameter is available in ``request.param``.

    :param autouse:
        If True, the fixture func is activated for all tests that can see it.
        If False (the default), an explicit reference is needed to activate
        the fixture.

    :param ids:
        Sequence of ids each corresponding to the params so that they are
        part of the test id. If no ids are provided they will be generated
        automatically from the params.

    :param name:
        The name of the fixture. This defaults to the name of the decorated
        function. If a fixture is used in the same module in which it is
        defined, the function name of the fixture will be shadowed by the
        function arg that requests the fixture; one way to resolve this is to
        name the decorated function ``fixture_<fixturename>`` and then use
        ``@pytest.fixture(name='<fixturename>')``.
    """
    fixture_marker = FixtureFunctionMarker(
        scope=scope,
        params=tuple(params) if params is not None else None,
        autouse=autouse,
        ids=None if ids is None else ids if callable(ids) else tuple(ids),
        name=name,
        _ispytest=True,
    )

    # Direct decoration.
    if fixture_function:
        return fixture_marker(fixture_function)

    return fixture_marker


def yield_fixture(
    fixture_function=None,
    *args,
    scope="function",
    params=None,
    autouse=False,
    ids=None,
    name=None,
):
    """(Return a) decorator to mark a yield-fixture factory function.

    .. deprecated:: 3.0
        Use :py:func:`pytest.fixture` directly instead.
    """
    warnings.warn(YIELD_FIXTURE, stacklevel=2)
    return fixture(
        fixture_function,
        *args,
        scope=scope,
        params=params,
        autouse=autouse,
        ids=ids,
        name=name,
    )


@fixture(scope="session")
def pytestconfig(request: FixtureRequest) -> Config:
    """Session-scoped fixture that returns the session's :class:`pytest.Config`
    object.

    Example::

        def test_foo(pytestconfig):
            if pytestconfig.getoption("verbose") > 0:
                ...

    """
    return request.config


def pytest_addoption(parser: Parser) -> None:
    parser.addini(
        "usefixtures",
        type="args",
        default=[],
        help="List of default fixtures to be used with this project",
    )


def _get_direct_parametrize_args(node: nodes.Node) -> List[str]:
    """Return all direct parametrization arguments of a node, so we don't
    mistake them for fixtures.

    Check https://github.com/pytest-dev/pytest/issues/5036.

    These things are done later as well when dealing with parametrization
    so this could be improved.
    """
    parametrize_argnames: List[str] = []
    for marker in node.iter_markers(name="parametrize"):
        if not marker.kwargs.get("indirect", False):
            p_argnames, _ = ParameterSet._parse_parametrize_args(
                *marker.args, **marker.kwargs
            )
            parametrize_argnames.extend(p_argnames)

    return parametrize_argnames


class FixtureManager:
    """pytest fixture definitions and information is stored and managed
    from this class.

    During collection fm.parsefactories() is called multiple times to parse
    fixture function definitions into FixtureDef objects and internal
    data structures.

    During collection of test functions, metafunc-mechanics instantiate
    a FuncFixtureInfo object which is cached per node/func-name.
    This FuncFixtureInfo object is later retrieved by Function nodes
    which themselves offer a fixturenames attribute.

    The FuncFixtureInfo object holds information about fixtures and FixtureDefs
    relevant for a particular function. An initial list of fixtures is
    assembled like this:

    - ini-defined usefixtures
    - autouse-marked fixtures along the collection chain up from the function
    - usefixtures markers at module/class/function level
    - test function funcargs

    Subsequently the funcfixtureinfo.fixturenames attribute is computed
    as the closure of the fixtures needed to setup the initial fixtures,
    i.e. fixtures needed by fixture functions themselves are appended
    to the fixturenames list.

    Upon the test-setup phases all fixturenames are instantiated, retrieved
    by a lookup of their FuncFixtureInfo.
    """

    FixtureLookupError = FixtureLookupError
    FixtureLookupErrorRepr = FixtureLookupErrorRepr

    def __init__(self, session: "Session") -> None:
        self.session = session
        self.config: Config = session.config
        self._arg2fixturedefs: Dict[str, List[FixtureDef[Any]]] = {}
        self._holderobjseen: Set[object] = set()
        # A mapping from a nodeid to a list of autouse fixtures it defines.
        self._nodeid_autousenames: Dict[str, List[str]] = {
            "": self.config.getini("usefixtures"),
        }
        session.config.pluginmanager.register(self, "funcmanage")

    def getfixtureinfo(
        self, node: nodes.Node, func, cls, funcargs: bool = True
    ) -> FuncFixtureInfo:
        if funcargs and not getattr(node, "nofuncargs", False):
            argnames = getfuncargnames(func, name=node.name, cls=cls)
        else:
            argnames = ()

        usefixtures = tuple(
            arg for mark in node.iter_markers(name="usefixtures") for arg in mark.args
        )
        initialnames = tuple(
            dict.fromkeys(
                tuple(self._getautousenames(node.nodeid)) + usefixtures + argnames
            )
        )

        arg2fixturedefs: Dict[str, Sequence[FixtureDef[Any]]] = {}
        names_closure, arg2num_fixturedefs_used = self.getfixtureclosure(
            node,
            initialnames,
            arg2fixturedefs,
            self,
            ignore_args=_get_direct_parametrize_args(node),
        )
        return FuncFixtureInfo(
            argnames,
            initialnames,
            names_closure,
            arg2fixturedefs,
            arg2num_fixturedefs_used,
        )

    def pytest_plugin_registered(self, plugin: _PluggyPlugin) -> None:
        nodeid = None
        try:
            p = absolutepath(plugin.__file__)  # type: ignore[attr-defined]
        except AttributeError:
            pass
        else:
            # Construct the base nodeid which is later used to check
            # what fixtures are visible for particular tests (as denoted
            # by their test id).
            if p.name.startswith("conftest.py"):
                try:
                    nodeid = str(p.parent.relative_to(self.config.rootpath))
                except ValueError:
                    nodeid = ""
                if nodeid == ".":
                    nodeid = ""
                if os.sep != nodes.SEP:
                    nodeid = nodeid.replace(os.sep, nodes.SEP)

        self.parsefactories(plugin, nodeid)

    def _getautousenames(self, nodeid: str) -> Iterator[str]:
        """Return the names of autouse fixtures applicable to nodeid."""
        for parentnodeid in nodes.iterparentnodeids(nodeid):
            basenames = self._nodeid_autousenames.get(parentnodeid)
            if basenames:
                yield from basenames

    @staticmethod
    def getfixtureclosure(
        parentnode: nodes.Node,
        initialnames: Tuple[str],
        arg2fixturedefs: Dict[str, Sequence[FixtureDef[Any]]],
        fixturemanager: Optional["FixtureManager"] = None,
        ignore_args: Sequence[str] = (),
    ) -> Tuple[List[str], Dict[str, List[FixtureDef[Any]]]]:
        # Collect the closure of all fixtures, starting with the given
        # fixturenames as the initial set.  As we have to visit all
        # factory definitions anyway, we also return an arg2fixturedefs
        # mapping so that the caller can reuse it and does not have
        # to re-discover fixturedefs again for each fixturename
        # (discovering matching fixtures for a given name/node is expensive).

        parentid = parentnode.nodeid
        fixturenames_closure: Dict[str, int] = {}

        # At this point, fixturenames_closure contains what we call "initialnames",
        # which is a set of fixturenames the function immediately requests. We
        # need to return it as well, so save this.

        arg2num_fixturedefs_used: Dict[str, int] = defaultdict(lambda: 0)
        arg2num_def_used_in_path: Dict[str, int] = defaultdict(lambda: 0)
        nodes_in_fixture_tree: Deque[Tuple[str, bool]] = deque(
            [(name, name != initialnames[-1]) for name in initialnames]
        )
        nodes_in_path: Deque[Tuple[str, bool]] = deque()

        while nodes_in_fixture_tree:
            node, has_sibling = nodes_in_fixture_tree.popleft()
            if node not in fixturenames_closure or fixturenames_closure[node][0] > len(
                nodes_in_path
            ):
                fixturenames_closure[node] = (
                    len(nodes_in_path),
                    len(fixturenames_closure),
                )
            if node not in arg2fixturedefs:
                if node not in ignore_args:
                    fixturedefs = fixturemanager.getfixturedefs(node, parentid)
                    if fixturedefs:
                        arg2fixturedefs[node] = fixturedefs
            if node in arg2fixturedefs:
                def_index = arg2num_def_used_in_path[node] + 1
                if (
                    def_index <= len(arg2fixturedefs[node])
                    and def_index > arg2num_fixturedefs_used[node]
                ):
                    arg2num_fixturedefs_used[node] = def_index
                    fixturedef = arg2fixturedefs[node][-def_index]
                    if fixturedef.argnames:
                        nodes_in_path.append((node, has_sibling))
                        arg2num_def_used_in_path[node] += 1
                        nodes_in_fixture_tree.extendleft(
                            [
                                (argname, argname != fixturedef.argnames[-1])
                                for argname in reversed(fixturedef.argnames)
                            ]
                        )
                        continue
            while not has_sibling:
                try:
                    node, has_sibling = nodes_in_path.pop()
                except IndexError:
                    assert len(nodes_in_fixture_tree) == 0
                    break
                arg2num_def_used_in_path[node] -= 1

        fixturenames_closure_list = list(fixturenames_closure)

        def sort_by_scope_depth_and_arrival(arg_name: str) -> Scope:
            depth, arrival = fixturenames_closure[arg_name]
            try:
                fixturedefs = arg2fixturedefs[arg_name]
            except KeyError:
                return (Scope.Function, -depth, -arrival)
            else:
                return (fixturedefs[-1]._scope, -depth, -arrival)

        fixturenames_closure_list.sort(
            key=sort_by_scope_depth_and_arrival, reverse=True
        )
        return fixturenames_closure_list, arg2num_fixturedefs_used

    def pytest_generate_tests(self, metafunc: "Metafunc") -> None:
        """Generate new tests based on parametrized fixtures used by the given metafunc"""

        def get_parametrize_mark_argnames(mark: Mark) -> Sequence[str]:
            args, _ = ParameterSet._parse_parametrize_args(*mark.args, **mark.kwargs)
            return args

        for argname in metafunc.fixturenames:
            # Get the FixtureDefs for the argname.
            fixture_defs = metafunc._arg2fixturedefs.get(argname)
            if not fixture_defs:
                # Will raise FixtureLookupError at setup time if not parametrized somewhere
                # else (e.g @pytest.mark.parametrize)
                continue

            # If the test itself parametrizes using this argname, give it
            # precedence.
            if any(
                argname in get_parametrize_mark_argnames(mark)
                for mark in metafunc.definition.iter_markers("parametrize")
            ):
                continue

            # In the common case we only look at the fixture def with the
            # closest scope (last in the list). But if the fixture overrides
            # another fixture, while requesting the super fixture, keep going
            # in case the super fixture is parametrized (#1953).
            for fixturedef in reversed(fixture_defs):
                # Skip pseudo-fixtures
                if fixturedef.is_pseudo:
                    continue
                # Fixture is parametrized, apply it and stop.
                if fixturedef.params is not None:
                    metafunc.parametrize(
                        argname,
                        fixturedef.params,
                        indirect=True,
                        scope=fixturedef.scope,
                        ids=fixturedef.ids,
                    )
                    break

                # Not requesting the overridden super fixture, stop.
                if argname not in fixturedef.argnames:
                    break

                # Try next super fixture, if any.

    def pytest_collection_modifyitems(self, items: List[nodes.Item]) -> None:
        # Separate parametrized setups.
        items[:] = reorder_items(items)

    @overload
    def parsefactories(
        self,
        node_or_obj: nodes.Node,
        *,
        unittest: bool = ...,
    ) -> None:
        raise NotImplementedError()

    @overload
    def parsefactories(  # noqa: F811
        self,
        node_or_obj: object,
        nodeid: Optional[str],
        *,
        unittest: bool = ...,
    ) -> None:
        raise NotImplementedError()

    def parsefactories(  # noqa: F811
        self,
        node_or_obj: Union[nodes.Node, object],
        nodeid: Union[str, NotSetType, None] = NOTSET,
        *,
        unittest: bool = False,
    ) -> None:
        """Collect fixtures from a collection node or object.

        Found fixtures are parsed into `FixtureDef`s and saved.

        If `node_or_object` is a collection node (with an underlying Python
        object), the node's object is traversed and the node's nodeid is used to
        determine the fixtures' visibilty. `nodeid` must not be specified in
        this case.

        If `node_or_object` is an object (e.g. a plugin), the object is
        traversed and the given `nodeid` is used to determine the fixtures'
        visibility. `nodeid` must be specified in this case; None and "" mean
        total visibility.
        """
        if nodeid is not NOTSET:
            holderobj = node_or_obj
        else:
            assert isinstance(node_or_obj, nodes.Node)
            holderobj = cast(object, node_or_obj.obj)  # type: ignore[attr-defined]
            assert isinstance(node_or_obj.nodeid, str)
            nodeid = node_or_obj.nodeid
        if holderobj in self._holderobjseen:
            return

        self._holderobjseen.add(holderobj)
        autousenames = []
        for name in dir(holderobj):
            # ugly workaround for one of the fspath deprecated property of node
            # todo: safely generalize
            if isinstance(holderobj, nodes.Node) and name == "fspath":
                continue

            # The attribute can be an arbitrary descriptor, so the attribute
            # access below can raise. safe_getatt() ignores such exceptions.
            obj = safe_getattr(holderobj, name, None)
            marker = getfixturemarker(obj)
            if not isinstance(marker, FixtureFunctionMarker):
                # Magic globals  with __getattr__ might have got us a wrong
                # fixture attribute.
                continue

            if marker.name:
                name = marker.name

            # During fixture definition we wrap the original fixture function
            # to issue a warning if called directly, so here we unwrap it in
            # order to not emit the warning when pytest itself calls the
            # fixture function.
            obj = get_real_method(obj, holderobj)

            fixture_def = FixtureDef(
                fixturemanager=self,
                baseid=nodeid,
                argname=name,
                func=obj,
                scope=marker.scope,
                params=marker.params,
                unittest=unittest,
                ids=marker.ids,
            )

            faclist = self._arg2fixturedefs.setdefault(name, [])
            if fixture_def.has_location:
                faclist.append(fixture_def)
            else:
                # fixturedefs with no location are at the front
                # so this inserts the current fixturedef after the
                # existing fixturedefs from external plugins but
                # before the fixturedefs provided in conftests.
                i = len([f for f in faclist if not f.has_location])
                faclist.insert(i, fixture_def)
            if marker.autouse:
                autousenames.append(name)

        if autousenames:
            self._nodeid_autousenames.setdefault(nodeid or "", []).extend(autousenames)

    def getfixturedefs(
        self, argname: str, nodeid: str
    ) -> Optional[Sequence[FixtureDef[Any]]]:
        """Get a list of fixtures which are applicable to the given node id.

        :param str argname: Name of the fixture to search for.
        :param str nodeid: Full node id of the requesting test.
        :rtype: Sequence[FixtureDef]
        """
        try:
            fixturedefs = self._arg2fixturedefs[argname]
        except KeyError:
            return None
        return tuple(self._matchfactories(fixturedefs, nodeid))

    def _matchfactories(
        self, fixturedefs: Iterable[FixtureDef[Any]], nodeid: str
    ) -> Iterator[FixtureDef[Any]]:
        """Yields the visible fixturedefs to a node with the given id
        from among the specified fixturedefs.

        :param Iterable[FixtureDef] fixturedefs: The list of specified fixturedefs.
        :param str nodeid: Full node id of the node.
        :rtype: Iterator[FixtureDef]
        """
        parentnodeids = set(nodes.iterparentnodeids(nodeid))
        for fixturedef in fixturedefs:
            if fixturedef.baseid in parentnodeids:
                yield fixturedef
