"""Structured representation of a pytest "nodeid".

A nodeid is represented as a ``::``-separated string, identifying a node in the collection
tree, e.g. ``path/to/test_file.py::TestClass::test_method[param]``.

There are three structured, internal representations of this concept, all
only ever built from live collection data or from a specific external
boundary -- so that their fields can always be trusted:

- :class:`CollectionNodeId` -- for a ``Collector`` node (can still have
  children). ``.child()``/``.leaf()`` build further ids on top of it.
- :class:`ItemNodeId` -- for an ``Item`` node (a leaf, e.g. a test
  function). Carries ``params``; has no ``.child()``/``.leaf()`` at all, so
  building further collection-tree structure on top of one is a static
  type error, not just a runtime mistake.
- :class:`OpaqueNodeId` -- A nodeid reconstructed from an external string
  source, rather than from live collection. It makes no claim to structured
  names or params, given they cannot be inferred from the plain string.
- :data:`NodeId` -- a type alias, ``CollectionNodeId | ItemNodeId``, for
  code that genuinely needs to accept/hold either kind.

A nodeid string's trailing ``[params]`` bracket cannot be reliably
decomposed back into individual ``parametrize()``-call boundaries once
flattened (``"-"`` is used both to join sub-ids within one call and to join
separate stacked calls), so a :class:`ItemNodeId` built from an external
string would either have to fabricate that structure or silently lie about
not having it. :class:`OpaqueNodeId` is the honest alternative for that
case: it only knows the ``path`` and an unparsed ``rest``, and makes no
claim to structured names or params. The legacy ``::``-joined string form
remains available (via ``str(node_id)``) for backward compatibility with
external plugins, for all types.
"""

from __future__ import annotations

import abc
import dataclasses
from typing import overload
from typing import TYPE_CHECKING
from typing import TypeVar

from _pytest.compat import assert_never
from _pytest.compat import override
from _pytest.scope import Scope


if TYPE_CHECKING:
    from typing_extensions import Self


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class ParamId:
    """One resolved id contributed by a single (possibly stacked)
    ``parametrize()`` call.

    Multiple ``ParamId``s are joined with ``"-"`` to form the legacy
    ``[bracket]`` content of a nodeid, mirroring
    :attr:`_pytest.python.CallSpec.param_ids`.

    ``argnames``/``scope`` are only known when built from live collection
    data (see ``Function.__init__``) -- an :class:`ItemNodeId` never has one
    of these guessed from a string; see :class:`OpaqueNodeId` for the
    string-boundary case, which has no ``ParamId``s at all.
    """

    id: str
    argnames: tuple[str, ...] = ()
    scope: Scope | None = None


class _CachedStrEqHash(abc.ABC):
    """Shared ``str(self)`` caching plus cross-type equality/hashing for
    :class:`CollectionNodeId`, :class:`ItemNodeId` and :class:`OpaqueNodeId`.

    An ABC, not a dataclass itself -- just method bodies reused by all
    three, since they must compare/hash equal to each other by canonical
    string form (e.g. a currently-collected ``item.id`` must compare equal
    to a matching entry read back from an on-disk cache file), but each
    builds its string differently. Each concrete subclass declares its own
    ``_str_cache`` dataclass field (rather than it living here) so that
    ``slots=True`` gives it a real slot.
    """

    # Without this, subclasses would get an instance __dict__ despite their
    # own slots=True, since a __slots__-less base class in the MRO grants
    # one to every subclass regardless -- abc.ABC's own __slots__ = () does
    # not propagate down to subclasses that don't redeclare it themselves.
    __slots__ = ()

    _str_cache: str | None

    @abc.abstractmethod
    def _build_str(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        # Lazily compute and cache the string on first access -- it's used
        # on every __eq__/__hash__ call, so it's worth not repeating the
        # join/format work on every comparison.
        if self._str_cache is not None:
            return self._str_cache
        base = self._build_str()
        object.__setattr__(self, "_str_cache", base)
        return base

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _CachedStrEqHash):
            return NotImplemented
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))


@dataclasses.dataclass(frozen=True, eq=False, slots=True, kw_only=True)
class CollectionNodeId(_CachedStrEqHash):
    """Structured address for a ``Collector`` node -- one that can still
    have children built under it.

    :param path:
        ``/``-normalized, rootpath-relative filesystem path. Empty string
        for the session root.
    :param names:
        Ordered ``::``-segment names.
    """

    path: str
    names: tuple[str, ...] = ()
    _str_cache: str | None = dataclasses.field(default=None, init=False, repr=False)

    @override
    def _build_str(self) -> str:
        return "::".join((self.path, *self.names))

    def child(self, name: str) -> CollectionNodeId:
        """Return a new CollectionNodeId for a child collector node."""
        return CollectionNodeId(path=self.path, names=(*self.names, name))

    def leaf(self, name: str, params: tuple[ParamId, ...]) -> ItemNodeId:
        """Return a new ItemNodeId for a terminal item node."""
        return ItemNodeId(path=self.path, names=(*self.names, name), params=params)

    def as_opaque(self) -> OpaqueNodeId:
        """Return the OpaqueNodeId form of this id, for code that only ever
        needs a single, non-structured lookup type (e.g. cache boundaries
        that mix live and cache-sourced ids)."""
        return OpaqueNodeId.parse(str(self))


@dataclasses.dataclass(frozen=True, eq=False, slots=True, kw_only=True)
class ItemNodeId(_CachedStrEqHash):
    """Structured address for an ``Item`` node -- a leaf, e.g. a test
    function. Has no ``.child()``/``.leaf()``: nothing ever builds further
    collection-tree structure on top of an item id.

    :param path:
        ``/``-normalized, rootpath-relative filesystem path.
    :param names:
        Ordered ``::``-segment names.
    :param params:
        Ordered per-``parametrize()``-call ids.
    """

    path: str
    names: tuple[str, ...] = ()
    params: tuple[ParamId, ...] = ()
    _str_cache: str | None = dataclasses.field(default=None, init=False, repr=False)

    @override
    def _build_str(self) -> str:
        base = "::".join((self.path, *self.names))
        if self.params:
            base += "[" + "-".join(p.id for p in self.params) + "]"
        return base

    def as_opaque(self) -> OpaqueNodeId:
        """Return the OpaqueNodeId form of this id, for code that only ever
        needs a single, non-structured lookup type (e.g. cache boundaries
        that mix live and cache-sourced ids)."""
        return OpaqueNodeId.parse(str(self))


#: Either kind of live-collection node id, for code that genuinely needs to
#: accept/hold both a CollectionNodeId and an ItemNodeId.
NodeId = CollectionNodeId | ItemNodeId


@dataclasses.dataclass(frozen=True, eq=False, slots=True, kw_only=True)
class OpaqueNodeId(_CachedStrEqHash):
    """A nodeid reconstructed from an external string source (an on-disk
    cache file, an xdist JSON wire payload, a duck-typed report-like
    object's ``.nodeid`` attribute, ...), rather than from live collection.

    Unlike :class:`CollectionNodeId`/:class:`ItemNodeId`, this makes no
    claim to structured names or params: everything after the first ``"::"``
    is left opaque and unsplit, since it cannot be reliably decomposed (see
    the module docstring). There is no ``.child()``/``.leaf()`` -- nothing
    ever builds further collection-tree structure on top of a
    boundary-sourced id.
    """

    path: str
    # Everything after the first "::", left opaque/unsplit. None means no
    # "::" was present at all (distinct from "" after a trailing "::", for
    # lossless round-tripping through str.partition()).
    rest: str | None = None
    _str_cache: str | None = dataclasses.field(default=None, init=False, repr=False)

    @classmethod
    def parse(cls, nodeid: str) -> OpaqueNodeId:
        """Split a nodeid string into its path and an opaque remainder."""
        path, sep, rest = nodeid.partition("::")
        self = cls(path=path, rest=rest if sep else None)
        # We already have the original string in hand -- cache it directly
        # as _str_cache instead of letting __str__ reconstruct it later.
        object.__setattr__(self, "_str_cache", nodeid)
        return self

    @override
    def _build_str(self) -> str:
        return self.path if self.rest is None else f"{self.path}::{self.rest}"

    def as_opaque(self) -> Self:
        return self


_N = TypeVar("_N", bound=NodeId)


@overload
def coerce_node_id(nodeid: _N) -> _N: ...
@overload
def coerce_node_id(nodeid: str) -> OpaqueNodeId: ...
def coerce_node_id(nodeid: str | NodeId) -> NodeId | OpaqueNodeId:
    """Return ``nodeid`` unchanged if already a :data:`NodeId` (live
    collection data); otherwise treat it as an external nodeid string and
    wrap it in an :class:`OpaqueNodeId`."""
    match nodeid:
        case CollectionNodeId() | ItemNodeId():
            return nodeid
        case str():
            return OpaqueNodeId.parse(nodeid)
        case _:  # pragma: no cover
            assert_never(nodeid)
