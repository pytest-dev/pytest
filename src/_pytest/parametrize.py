"""The parametrization core: turning ``parametrize()`` calls into callspecs.

This machinery is deliberately independent of the Python test collector, so
that any :class:`~_pytest.nodes.ItemDefinition` -- not only
:class:`~_pytest.python.FunctionDefinition` -- can be parametrized through
:hook:`pytest_generate_tests`.

:class:`~_pytest.python.Metafunc` is the Python-specific subclass of
:class:`ParametrizeContext` and remains the object plugins receive for Python
tests. ``CallSpec``, ``IdMaker`` and friends live here rather than in
``python.py`` for the same reason, and are re-exported from there.
"""

from __future__ import annotations

from collections import Counter
from collections import defaultdict
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Sequence
import dataclasses
import enum
import hashlib
import itertools
import re
import textwrap
from typing import Any
from typing import cast
from typing import final
from typing import get_args
from typing import Literal
from typing import NoReturn
from typing import TYPE_CHECKING

from _pytest._io.saferepr import saferepr
from _pytest.compat import ascii_escaped
from _pytest.compat import NOTSET
from _pytest.config import Config
from _pytest.config import UsageError
from _pytest.deprecated import check_ispytest
from _pytest.mark.structures import _HiddenParam
from _pytest.mark.structures import HIDDEN_PARAM
from _pytest.mark.structures import Mark
from _pytest.mark.structures import MarkDecorator
from _pytest.mark.structures import normalize_mark_list
from _pytest.mark.structures import ParameterSet
from _pytest.outcomes import fail
from _pytest.scope import Scope
from _pytest.scope import ScopeName


if TYPE_CHECKING:
    from _pytest import nodes
    from _pytest.fixtures import FixtureDef


LongStrIdStrategy = Literal["short", "sha256", "legacy", "disallow"]
_LONG_STR_STRATEGIES: frozenset[LongStrIdStrategy] = frozenset(
    get_args(LongStrIdStrategy)
)


def _collect_error(msg: str) -> Exception:
    """Build a ``Collector.CollectError``.

    ``nodes`` imports this module (for :class:`~_pytest.nodes.ItemDefinition`),
    so it can only be imported here lazily.
    """
    from _pytest.nodes import Collector

    return Collector.CollectError(msg)


@final
@dataclasses.dataclass(frozen=True)
class IdMaker:
    """Make IDs for a parametrization."""

    __slots__ = (
        "argnames",
        "config",
        "idfn",
        "ids",
        "nodeid",
        "parametersets",
    )

    # The argnames of the parametrization.
    argnames: Sequence[str]
    # The ParameterSets of the parametrization.
    parametersets: Sequence[ParameterSet]
    # Optionally, a user-provided callable to make IDs for parameters in a
    # ParameterSet.
    idfn: Callable[[Any], object | None] | None
    # Optionally, explicit IDs for ParameterSets by index.
    ids: Sequence[object | None] | None
    # Optionally, the pytest config.
    # Used for controlling ASCII escaping, determining parametrization ID
    # strictness, and for calling the :hook:`pytest_make_parametrize_id` hook.
    config: Config | None
    # Optionally, the ID of the node being parametrized.
    # Used only for clearer error messages.
    nodeid: str | None

    def make_unique_parameterset_ids(self) -> list[str | _HiddenParam]:
        """Make a unique identifier for each ParameterSet, that may be used to
        identify the parametrization in a node ID.

        If strict_parametrization_ids is enabled, and duplicates are detected,
        raises CollectError. Otherwise makes the IDs unique as follows:

        Format is <prm_1_token>-...-<prm_n_token>[counter], where prm_x_token is
        - user-provided id, if given
        - else an id derived from the value, applicable for certain types
        - else <argname><parameterset index>
        The counter suffix is appended only in case a string wouldn't be unique
        otherwise.
        """
        resolved_ids = list(self._resolve_ids())
        # All IDs must be unique!
        if len(resolved_ids) != len(set(resolved_ids)):
            # Record the number of occurrences of each ID.
            id_counts = Counter(resolved_ids)

            if self._strict_parametrization_ids_enabled():
                parameters = ", ".join(self.argnames)
                parametersets = ", ".join(
                    [saferepr(list(param.values)) for param in self.parametersets]
                )
                ids = ", ".join(
                    id if id is not HIDDEN_PARAM else "<hidden>" for id in resolved_ids
                )
                duplicates = ", ".join(
                    id if id is not HIDDEN_PARAM else "<hidden>"
                    for id, count in id_counts.items()
                    if count > 1
                )
                msg = textwrap.dedent(f"""
                    Duplicate parametrization IDs detected, but strict_parametrization_ids is set.

                    Test name:      {self.nodeid}
                    Parameters:     {parameters}
                    Parameter sets: {parametersets}
                    IDs:            {ids}
                    Duplicates:     {duplicates}

                    You can fix this problem using `@pytest.mark.parametrize(..., ids=...)` or `pytest.param(..., id=...)`.
                """).strip()  # noqa: E501
                raise _collect_error(msg)

            # Map the ID to its next suffix.
            id_suffixes: dict[str, int] = defaultdict(int)
            # Suffix non-unique IDs to make them unique.
            for index, id in enumerate(resolved_ids):
                if id_counts[id] > 1:
                    if id is HIDDEN_PARAM:
                        self._complain_multiple_hidden_parameter_sets()
                    suffix = ""
                    if id and id[-1].isdigit():
                        suffix = "_"
                    new_id = f"{id}{suffix}{id_suffixes[id]}"
                    while new_id in set(resolved_ids):
                        id_suffixes[id] += 1
                        new_id = f"{id}{suffix}{id_suffixes[id]}"
                    resolved_ids[index] = new_id
                    id_suffixes[id] += 1
        assert len(resolved_ids) == len(set(resolved_ids)), (
            f"Internal error: {resolved_ids=}"
        )
        return resolved_ids

    def _strict_parametrization_ids_enabled(self) -> bool:
        if self.config is None:
            return False
        strict_parametrization_ids = self.config.getini("strict_parametrization_ids")
        if strict_parametrization_ids is None:
            strict_parametrization_ids = self.config.getini("strict")
        return cast(bool, strict_parametrization_ids)

    def _resolve_ids(self) -> Iterable[str | _HiddenParam]:
        """Resolve IDs for all ParameterSets (may contain duplicates)."""
        for idx, parameterset in enumerate(self.parametersets):
            if parameterset.id is not None:
                # ID provided directly - pytest.param(..., id="...")
                if parameterset.id is HIDDEN_PARAM:
                    yield HIDDEN_PARAM
                else:
                    yield _ascii_escaped_by_config(parameterset.id, self.config)
            elif self.ids and idx < len(self.ids) and self.ids[idx] is not None:
                # ID provided in the IDs list - parametrize(..., ids=[...]).
                if self.ids[idx] is HIDDEN_PARAM:
                    yield HIDDEN_PARAM
                else:
                    yield self._idval_from_value_required(self.ids[idx], idx)
            else:
                # ID not provided - generate it.
                yield "-".join(
                    self._idval(val, argname, idx)
                    for val, argname in zip(
                        parameterset.values, self.argnames, strict=True
                    )
                )

    def _idval(self, val: object, argname: str, idx: int) -> str:
        """Make an ID for a parameter in a ParameterSet."""
        idval = self._idval_from_function(val, argname, idx)
        if idval is not None:
            return idval
        idval = self._idval_from_hook(val, argname)
        if idval is not None:
            return idval
        if isinstance(val, str | bytes):
            idval = self._apply_long_str_strategy(val, argname, idx)
            if idval is not None:
                return idval
        else:
            idval = self._idval_from_value(val)
            if idval is not None:
                return idval
        return self._idval_from_argname(argname, idx)

    def _get_long_str_strategy(self) -> LongStrIdStrategy:
        if not self.config:
            return "short"
        value = self.config.getini("parametrize_long_str_id_strategy")
        if value not in _LONG_STR_STRATEGIES:
            raise UsageError(
                f"Unknown parametrize_long_str_id_strategy: {value!r}. "
                f"Valid values: {', '.join(sorted(_LONG_STR_STRATEGIES))}"
            )
        return cast(LongStrIdStrategy, value)

    def _apply_long_str_strategy(
        self, val: str | bytes, argname: str, idx: int
    ) -> str | None:
        """Apply the configured strategy for long str/bytes parameter values.

        Only used for auto-generated IDs (not explicit ids=[...] or
        pytest.param(id=...)).
        """
        if len(val) <= 100:
            return _ascii_escaped_by_config(val, self.config)
        match self._get_long_str_strategy():
            case "legacy":
                return _ascii_escaped_by_config(val, self.config)
            case "short":
                return None
            case "sha256":
                encoded = val.encode("utf-8") if isinstance(val, str) else val
                return hashlib.sha256(encoded).hexdigest()
            case "disallow":  # pragma: no branch -- fail() raises, confuses coverage
                prefix = self._make_error_prefix()
                fail(
                    f"{prefix}parametrize value for '{argname}' at index {idx} "
                    f"is too long for an auto-generated ID ({len(val)} characters). "
                    f"Use pytest.param(..., id=...) or parametrize(..., ids=...) "
                    f"to set an explicit ID, or change parametrize_long_str_id_strategy.",
                    pytrace=False,
                )

    def _idval_from_function(self, val: object, argname: str, idx: int) -> str | None:
        """Try to make an ID for a parameter in a ParameterSet using the
        user-provided id callable, if given."""
        if self.idfn is None:
            return None
        try:
            id = self.idfn(val)
        except Exception as e:
            prefix = f"{self.nodeid}: " if self.nodeid is not None else ""
            msg = "error raised while trying to determine id of parameter '{}' at position {}"
            msg = prefix + msg.format(argname, idx)
            raise ValueError(msg) from e
        if id is None:
            return None
        return self._idval_from_value(id)

    def _idval_from_hook(self, val: object, argname: str) -> str | None:
        """Try to make an ID for a parameter in a ParameterSet by calling the
        :hook:`pytest_make_parametrize_id` hook."""
        if self.config:
            id: str | None = self.config.hook.pytest_make_parametrize_id(
                config=self.config, val=val, argname=argname
            )
            return id
        return None

    def _idval_from_value(self, val: object) -> str | None:
        """Try to make an ID for a parameter in a ParameterSet from its value,
        if the value type is supported."""
        if isinstance(val, str | bytes):
            return _ascii_escaped_by_config(val, self.config)
        elif val is None or isinstance(val, float | int | bool | complex):
            return str(val)
        elif isinstance(val, re.Pattern):
            return ascii_escaped(val.pattern)
        elif val is NOTSET:
            # Fallback to default. Note that NOTSET is an enum.Enum.
            pass
        elif isinstance(val, enum.Enum):
            return str(val)
        elif isinstance(getattr(val, "__name__", None), str):
            # Name of a class, function, module, etc.
            name: str = getattr(val, "__name__")
            return name
        return None

    def _idval_from_value_required(self, val: object, idx: int) -> str:
        """Like _idval_from_value(), but fails if the type is not supported."""
        id = self._idval_from_value(val)
        if id is not None:
            return id

        # Fail.
        prefix = self._make_error_prefix()
        msg = (
            f"{prefix}ids contains unsupported value {saferepr(val)} (type: {type(val)!r}) at index {idx}. "
            "Supported types are: str, bytes, int, float, complex, bool, enum, regex or anything with a __name__."
        )
        fail(msg, pytrace=False)

    @staticmethod
    def _idval_from_argname(argname: str, idx: int) -> str:
        """Make an ID for a parameter in a ParameterSet from the argument name
        and the index of the ParameterSet."""
        return str(argname) + str(idx)

    def _complain_multiple_hidden_parameter_sets(self) -> NoReturn:
        fail(
            f"{self._make_error_prefix()}multiple instances of HIDDEN_PARAM "
            "cannot be used in the same parametrize call, "
            "because the tests names need to be unique."
        )

    def _make_error_prefix(self) -> str:
        if self.nodeid is not None:
            return f"In {self.nodeid}: "
        else:
            return ""


@final
@dataclasses.dataclass(frozen=True)
class CallSpec:
    """A planned parameterized invocation of a test function.

    Calculated during collection for a given test function's Metafunc.
    Once collection is over, each callspec is turned into a single Item
    and stored in item.callspec.
    """

    # arg name -> arg value which will be passed to a fixture of the same name.
    params: dict[str, object] = dataclasses.field(default_factory=dict)
    # arg name -> arg index.
    indices: dict[str, int] = dataclasses.field(default_factory=dict)
    # arg name -> parameter scope.
    # Used for sorting parametrized resources.
    _arg2scope: Mapping[str, Scope] = dataclasses.field(default_factory=dict)
    # Parts which will be added to the item's name in `[..]` separated by "-".
    _idlist: Sequence[str] = dataclasses.field(default_factory=tuple)
    # Marks which will be applied to the item.
    marks: list[Mark] = dataclasses.field(default_factory=list)

    def setmulti(
        self,
        *,
        argnames: Iterable[str],
        valset: Iterable[object],
        id: str | _HiddenParam,
        marks: Iterable[Mark | MarkDecorator],
        scope: Scope,
        param_index: int,
        nodeid: str,
    ) -> CallSpec:
        params = self.params.copy()
        indices = self.indices.copy()
        arg2scope = dict(self._arg2scope)
        for arg, val in zip(argnames, valset, strict=True):
            if arg in params:
                raise _collect_error(f"{nodeid}: duplicate parametrization of {arg!r}")
            params[arg] = val
            indices[arg] = param_index
            arg2scope[arg] = scope
        return CallSpec(
            params=params,
            indices=indices,
            _arg2scope=arg2scope,
            _idlist=self._idlist if id is HIDDEN_PARAM else [*self._idlist, id],
            marks=[*self.marks, *normalize_mark_list(marks)],
        )

    def getparam(self, name: str) -> object:
        try:
            return self.params[name]
        except KeyError as e:
            raise ValueError(name) from e

    @property
    def id(self) -> str:
        return "-".join(self._idlist)


def _ascii_escaped_by_config(val: str | bytes, config: Config | None) -> str:
    if config is None:
        escape_option = False
    else:
        escape_option = config.getini(
            "disable_test_id_escaping_and_forfeit_all_rights_to_community_support"
        )
    # TODO: If escaping is turned off and the user passes bytes,
    #       will return a bytes. For now we ignore this but the
    #       code *probably* doesn't handle this case.
    return val if escape_option else ascii_escaped(val)  # type: ignore


def _infer_parametrize_scope(
    argnames: Sequence[str],
    arg2fixturedefs: Mapping[str, Sequence[FixtureDef[object]]],
    indirect: bool | Sequence[str],
) -> Scope:
    """Infer the most appropriate scope for a parametrize() call based on its
    arguments, for when the scope is not explicitly specified.

    When there's at least one direct argument, always use "function" scope.

    When a test function is parametrized and all its arguments are indirect
    (e.g. fixtures), return the most narrow scope based on the fixtures used.

    Related to issue #1832, based on code posted by @Kingdread.
    """
    if isinstance(indirect, Sequence):
        all_arguments_are_fixtures = len(indirect) == len(argnames)
    else:
        all_arguments_are_fixtures = bool(indirect)

    if all_arguments_are_fixtures:
        # Takes the most narrow scope from used fixtures.
        used_scopes = (
            # Higher scope can't request lower scope, so it's OK to only
            # look at the first fixturedef in the override chain.
            arg2fixturedefs[argname][-1]._scope
            for argname in argnames
            if argname in arg2fixturedefs
        )
        return min(used_scopes, default=Scope.Function)

    return Scope.Function


def _resolve_args_directness(
    argnames: Sequence[str],
    indirect: bool | Sequence[str],
    nodeid: str,
) -> dict[str, Literal["indirect", "direct"]]:
    """Resolve if each parametrized argument must be considered an indirect
    parameter to a fixture of the same name, or a direct parameter to the
    parametrized function, based on the ``indirect`` parameter of the
    parametrize() call.

    :param argnames:
        List of argument names passed to ``parametrize()``.
    :param indirect:
        Same as the ``indirect`` parameter of ``parametrize()``.
    :param nodeid:
        Node ID to which the parametrization is applied.
    :returns:
        A dict mapping each arg name to either "indirect" or "direct".
    """
    arg_directness: dict[str, Literal["indirect", "direct"]]
    if isinstance(indirect, bool):
        arg_directness = dict.fromkeys(argnames, "indirect" if indirect else "direct")
    elif isinstance(indirect, Sequence):
        arg_directness = dict.fromkeys(argnames, "direct")
        for arg in indirect:
            if arg not in argnames:
                fail(
                    f"In {nodeid}: indirect fixture '{arg}' doesn't exist",
                    pytrace=False,
                )
            arg_directness[arg] = "indirect"
    else:
        fail(
            f"In {nodeid}: expected Sequence or boolean for indirect, got {type(indirect).__name__}",
            pytrace=False,
        )
    return arg_directness


class ParametrizeContext:
    """The object passed to :hook:`pytest_generate_tests`.

    Accumulates :meth:`parametrize` calls into a list of :class:`CallSpec`
    objects, which the owning :class:`~_pytest.nodes.ItemDefinition` then turns
    into items.

    For Python tests this is subclassed by :class:`pytest.Metafunc`, which adds
    the fixture-aware behaviour: scope inference from fixture scopes, indirect
    parametrization and validation against the test function's signature.

    A non-Python definition can use this class as-is. It declares the names it
    accepts up front (``argnames``), and the values chosen for them are handed
    to the generated items on ``item.callspec.params``; there is no fixture
    resolution involved.
    """

    def __init__(
        self,
        definition: nodes.ItemDefinition,
        config: Config,
        *,
        argnames: Sequence[str] = (),
        _ispytest: bool = False,
    ) -> None:
        check_ispytest(_ispytest)

        #: The definition being parametrized.
        self.definition = definition

        #: Access to the :class:`pytest.Config` object for the test session.
        self.config = config

        #: The names this definition can be parametrized on.
        #:
        #: Named ``fixturenames`` rather than ``argnames`` because that is what
        #: :hook:`pytest_generate_tests` implementations in the wild inspect --
        #: keeping the name is what lets them work with non-Python definitions.
        #:
        #: Stored by reference, so that a caller which later narrows the
        #: sequence in place (as the Python fixture closure does) is reflected
        #: here.
        self.fixturenames: Sequence[str] = argnames

        # Result of parametrize().
        self._calls: list[CallSpec] = []

        self._params_directness: dict[str, Literal["indirect", "direct"]] = {}

    # Seams for subclasses. The Python implementation (Metafunc) overrides
    # these to bring fixtures and the test function's signature into play.

    @property
    def _introspection_target(self) -> object:
        """The object to introspect for a signature and a source location.

        Used when reporting an empty parameter set. Defaults to the definition
        node, for which the source location degrades to "unknown"; Metafunc
        returns the test function.
        """
        return self.definition

    @property
    def _target_name(self) -> str:
        """Human readable name of what is being parametrized."""
        return self.definition.name

    def _infer_scope(
        self, argnames: Sequence[str], indirect: bool | Sequence[str]
    ) -> Scope:
        """Determine the scope of a parametrize() call that did not specify one."""
        return Scope.Function

    def _validate_argnames(
        self, argnames: Sequence[str], indirect: bool | Sequence[str]
    ) -> None:
        """Check that the definition actually accepts all of ``argnames``."""
        for argname in argnames:
            if argname not in self.fixturenames:
                kind = "fixture" if indirect else "argument"
                fail(
                    f"In {self.definition.nodeid}: definition uses no {kind} '{argname}'",
                    pytrace=False,
                )

    def _register_direct_params(
        self,
        argnames: Sequence[str],
        arg_directness: Mapping[str, Literal["indirect", "direct"]],
        scope: Scope,
    ) -> None:
        """Hook for making the chosen params reachable at setup time.

        Only meaningful where parametrization feeds a fixture system; the
        generic path delivers params on ``item.callspec.params`` instead.
        """

    def parametrize(
        self,
        argnames: str | Sequence[str],
        argvalues: Iterable[ParameterSet | Sequence[object] | object],
        *,
        indirect: bool | Sequence[str] = False,
        ids: Iterable[object | None] | Callable[[Any], object | None] | None = None,
        scope: ScopeName | None = None,
        _param_mark: Mark | None = None,
    ) -> None:
        """Add new invocations to the underlying test function using the list
        of argvalues for the given argnames. Parametrization is performed
        during the collection phase. If you need to setup expensive resources
        see about setting ``indirect`` to do it at test setup time instead.

        Can be called multiple times per test function (but only on different
        argument names), in which case each call parametrizes all previous
        parametrizations, e.g.

        ::

            unparametrized:         t
            parametrize ["x", "y"]: t[x], t[y]
            parametrize [1, 2]:     t[x-1], t[x-2], t[y-1], t[y-2]

        :param argnames:
            A comma-separated string denoting one or more argument names, or
            a list/tuple of argument strings.

        :param argvalues:
            The list of argvalues determines how often a test is invoked with
            different argument values.

            If only one argname was specified argvalues is a list of values.
            If N argnames were specified, argvalues must be a list of
            N-tuples, where each tuple-element specifies a value for its
            respective argname.

            .. versionchanged:: 9.1

                Passing a non-:class:`~collections.abc.Collection` iterable
                (such as a generator or iterator) is deprecated. See
                :ref:`parametrize-iterators` for details.

        :param indirect:
            A list of arguments' names (subset of argnames) or a boolean.
            If True the list contains all names from the argnames. Each
            argvalue corresponding to an argname in this list will
            be passed as request.param to its respective argname fixture
            function so that it can perform more expensive setups during the
            setup phase of a test rather than at collection time.

        :param ids:
            Sequence of (or generator for) ids for ``argvalues``,
            or a callable to return part of the id for each argvalue.

            With sequences (and generators like ``itertools.count()``) the
            returned ids should be of type ``string``, ``int``, ``float``,
            ``bool``, or ``None``.
            They are mapped to the corresponding index in ``argvalues``.
            ``None`` means to use the auto-generated id.

            .. versionadded:: 8.4
                :ref:`hidden-param` means to hide the parameter set
                from the test name. Can only be used at most 1 time, as
                test names need to be unique.

            If it is a callable it will be called for each entry in
            ``argvalues``, and the return value is used as part of the
            auto-generated id for the whole set (where parts are joined with
            dashes ("-")).
            This is useful to provide more specific ids for certain items, e.g.
            dates.  Returning ``None`` will use an auto-generated id.

            If no ids are provided they will be generated automatically from
            the argvalues.

        :param scope:
            If specified it denotes the scope of the parameters.
            The scope is used for grouping tests by parameter instances.
            It will also override any fixture-function defined scope, allowing
            to set a dynamic scope using test context or configuration.

        .. versionchanged:: 9.1

            ``indirect``, ``ids`` and ``scope`` are now keyword-only.
        """
        nodeid = self.definition.nodeid

        argnames, parametersets = ParameterSet._for_parametrize(
            argnames,
            argvalues,
            self._introspection_target,
            self.config,
            nodeid=nodeid,
        )
        del argvalues

        if "request" in argnames:
            fail(
                f"{nodeid}: 'request' is a reserved name and cannot be used in @pytest.mark.parametrize",
                pytrace=False,
            )

        if scope is not None:
            scope_ = Scope.from_user(
                scope, descr=f"parametrize() call in {self._target_name}"
            )
        else:
            scope_ = self._infer_scope(argnames, indirect)

        self._validate_argnames(argnames, indirect)

        # Use any already (possibly) generated ids with parametrize Marks.
        generated_ids = None
        if _param_mark and _param_mark._param_ids_from:
            generated_ids = _param_mark._param_ids_from._param_ids_generated
            if generated_ids is not None:
                ids = generated_ids

        ids = self._resolve_parameter_set_ids(
            argnames, ids, parametersets, nodeid=nodeid
        )

        # Store used (possibly generated) ids with parametrize Marks.
        if _param_mark and _param_mark._param_ids_from and generated_ids is None:
            object.__setattr__(_param_mark._param_ids_from, "_param_ids_generated", ids)

        # Calculate directness.
        arg_directness = _resolve_args_directness(argnames, indirect, nodeid)
        self._params_directness.update(arg_directness)

        self._register_direct_params(argnames, arg_directness, scope_)

        # Create the new calls: if we are parametrize() multiple times (by applying the decorator
        # more than once) then we accumulate those calls generating the cartesian product
        # of all calls.
        newcalls = []
        for callspec in self._calls or [CallSpec()]:
            for param_index, (param_id, param_set) in enumerate(
                zip(ids, parametersets, strict=True)
            ):
                newcallspec = callspec.setmulti(
                    argnames=argnames,
                    valset=param_set.values,
                    id=param_id,
                    marks=param_set.marks,
                    scope=scope_,
                    param_index=param_index,
                    nodeid=nodeid,
                )
                newcalls.append(newcallspec)
        self._calls = newcalls

    def _resolve_parameter_set_ids(
        self,
        argnames: Sequence[str],
        ids: Iterable[object | None] | Callable[[Any], object | None] | None,
        parametersets: Sequence[ParameterSet],
        nodeid: str,
    ) -> list[str | _HiddenParam]:
        """Resolve the actual ids for the given parameter sets.

        :param argnames:
            Argument names passed to ``parametrize()``.
        :param ids:
            The `ids` parameter of the ``parametrize()`` call (see docs).
        :param parametersets:
            The parameter sets, each containing a set of values corresponding
            to ``argnames``.
        :param nodeid str:
            The nodeid of the definition item that generated this
            parametrization.
        :returns:
            List with ids for each parameter set given.
        """
        if ids is None:
            idfn = None
            ids_ = None
        elif callable(ids):
            idfn = ids
            ids_ = None
        else:
            idfn = None
            ids_ = self._validate_ids(ids, parametersets)
        id_maker = IdMaker(
            argnames,
            parametersets,
            idfn,
            ids_,
            self.config,
            nodeid=nodeid,
        )
        return id_maker.make_unique_parameterset_ids()

    def _validate_ids(
        self,
        ids: Iterable[object | None],
        parametersets: Sequence[ParameterSet],
    ) -> list[object | None]:
        try:
            num_ids = len(ids)  # type: ignore[arg-type]
        except TypeError:
            try:
                iter(ids)
            except TypeError as e:
                raise TypeError("ids must be a callable or an iterable") from e
            num_ids = len(parametersets)

        # num_ids == 0 is a special case: https://github.com/pytest-dev/pytest/issues/1849
        if num_ids != len(parametersets) and num_ids != 0:
            nodeid = self.definition.nodeid
            fail(
                f"In {nodeid}: {len(parametersets)} parameter sets specified, with different number of ids: {num_ids}",
                pytrace=False,
            )

        return list(itertools.islice(ids, num_ids))

    def _recompute_direct_params_indices(self) -> None:
        for argname, param_type in self._params_directness.items():
            if param_type == "direct":
                for i, callspec in enumerate(self._calls):
                    callspec.indices[argname] = i
