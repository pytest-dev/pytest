"""The parametrization core.

Holds the pieces which turn a set of parameter sets into planned invocations,
independent of what is being parametrized:

* :class:`IdMaker` -- derives the ``[...]`` ids of a parametrization.
* :class:`CallSpec` -- one planned invocation and its parameters.

:class:`~_pytest.python.Metafunc` drives these for Python test functions and
re-exports them, so ``_pytest.python.CallSpec`` keeps working.
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
import re
import textwrap
from typing import Any
from typing import cast
from typing import final
from typing import get_args
from typing import Literal
from typing import NoReturn

from _pytest._io.saferepr import saferepr
from _pytest.compat import ascii_escaped
from _pytest.compat import NotSetType
from _pytest.config import Config
from _pytest.config import UsageError
from _pytest.mark.structures import _HiddenParam
from _pytest.mark.structures import HIDDEN_PARAM
from _pytest.mark.structures import Mark
from _pytest.mark.structures import MarkDecorator
from _pytest.mark.structures import normalize_mark_list
from _pytest.mark.structures import ParameterSet
from _pytest.outcomes import fail
from _pytest.scope import Scope


LongStrIdStrategy = Literal["short", "sha256", "legacy", "disallow"]
_LONG_STR_STRATEGIES: frozenset[LongStrIdStrategy] = frozenset(
    get_args(LongStrIdStrategy)
)


def _collect_error(msg: str) -> Exception:
    """Build a ``Collector.CollectError``.

    Imported lazily so that ``nodes`` stays free to import this module.
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
        match val:
            case str() | bytes():
                return _ascii_escaped_by_config(val, self.config)
            case None | float() | int() | bool() | complex():
                return str(val)
            case re.Pattern():
                return ascii_escaped(val.pattern)
            # Fallback to default. Note that NOTSET is an enum.Enum.
            case NotSetType():
                pass
            case enum.Enum():
                return str(val)
            case _ if isinstance(getattr(val, "__name__", None), str):
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
