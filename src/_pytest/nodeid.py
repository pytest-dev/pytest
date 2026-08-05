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
  source, rather than from live collection. It recovers the ``::``-separated
  ``names`` and the raw ``[params]`` bracket contents (a single opaque
  string), but makes no claim to the *internal* structure of the params
  string: the ``"-"`` delimiter joining separate ``parametrize()``-call ids
  cannot be reliably distinguished from a literal ``"-"`` in a param value,
  so :class:`OpaqueNodeId` deliberately leaves ``params`` as one unparsed
  string rather than fabricating :class:`ParamId` boundaries.
- :data:`NodeId` -- a type alias, ``CollectionNodeId | ItemNodeId``, for
  code that genuinely needs to accept/hold either kind.

The legacy ``::``-joined string form remains available (via ``str(node_id)``)
for backward compatibility with external plugins, for all types.
"""

from __future__ import annotations

import dataclasses
from typing import overload
from typing import TYPE_CHECKING
from typing import TypeVar

from _pytest.compat import assert_never
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


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CollectionNodeId:
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
    _str_cache: str | None = dataclasses.field(
        default=None, init=False, repr=False, compare=False
    )

    def __str__(self) -> str:
        # Lazily compute and cache the string on first access -- it's used
        # on every __eq__/__hash__ call site elsewhere (e.g. as_opaque()),
        # so it's worth not repeating the join work on every call.
        if self._str_cache is not None:
            return self._str_cache
        s = "::".join((self.path, *self.names))
        object.__setattr__(self, "_str_cache", s)
        return s

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


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class ItemNodeId:
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
    _str_cache: str | None = dataclasses.field(
        default=None, init=False, repr=False, compare=False
    )

    def __str__(self) -> str:
        if self._str_cache is not None:
            return self._str_cache
        s = "::".join((self.path, *self.names))
        if self.params:
            s += "[" + "-".join(p.id for p in self.params) + "]"
        object.__setattr__(self, "_str_cache", s)
        return s

    def as_opaque(self) -> OpaqueNodeId:
        """Return the OpaqueNodeId form of this id, for code that only ever
        needs a single, non-structured lookup type (e.g. cache boundaries
        that mix live and cache-sourced ids)."""
        return OpaqueNodeId.parse(str(self))


#: Either kind of live-collection node id, for code that genuinely needs to
#: accept/hold both a CollectionNodeId and an ItemNodeId.
NodeId = CollectionNodeId | ItemNodeId


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class OpaqueNodeId:
    """A nodeid reconstructed from an external string source (an on-disk
    cache file, an xdist JSON wire payload, a duck-typed report-like
    object's ``.nodeid`` attribute, ...), rather than from live collection.

    Unlike :class:`CollectionNodeId`/:class:`ItemNodeId`, this makes no
    claim to the *internal* structure of the params string: the ``"-"``
    delimiter is used both to join sub-ids within one ``parametrize()`` call
    and to join separate stacked calls, so it cannot be reliably decomposed
    back into :class:`ParamId` boundaries. ``params`` is therefore kept as a
    single raw string rather than guessing. There is no
    ``.child()``/``.leaf()`` -- nothing ever builds further collection-tree
    structure on top of a boundary-sourced id.
    """

    path: str
    #: ``::``-separated name segments, recovered reliably from the string.
    #: Empty tuple when there is no ``::`` in the nodeid.
    names: tuple[str, ...] = ()
    #: Raw contents inside the outermost ``[...]`` bracket, kept as one
    #: opaque string (the param-call-boundary structure cannot be recovered).
    #: ``None`` means no bracket at all; ``""`` means an empty ``[]``.
    params: str | None = None
    _str_cache: str | None = dataclasses.field(
        default=None, init=False, repr=False, compare=False
    )

    @classmethod
    def parse(cls, nodeid: str) -> OpaqueNodeId:
        """Parse a nodeid string into its path, names, and raw params."""
        path, sep, tail = nodeid.partition("::")
        if not sep:
            # No "::" -- everything is the path.  Never interpret a bracket
            # here: file paths can legitimately contain "[" (e.g. test[1].py).
            self = cls(path=path)
        else:
            # Peel the params bracket off the tail FIRST, so a "::" that
            # appears *inside* a params bracket is never mistaken for a name
            # separator.
            name_part, bracket, param_part = tail.partition("[")
            names = tuple(name_part.split("::"))
            params = param_part.removesuffix("]") if bracket else None
            self = cls(path=path, names=names, params=params)
        # We already have the original string in hand -- cache it directly
        # as _str_cache instead of letting __str__ reconstruct it later.
        object.__setattr__(self, "_str_cache", nodeid)
        return self

    def __str__(self) -> str:
        if self._str_cache is not None:
            return self._str_cache
        s = "::".join((self.path, *self.names))
        if self.params is not None:
            s += f"[{self.params}]"
        object.__setattr__(self, "_str_cache", s)
        return s

    @property
    def rest(self) -> str | None:
        """Everything after the first ``"::"`` as a single string, or
        ``None`` when there is no ``"::"`` (i.e. ``names`` is empty).
        """
        if not self.names:
            return None
        s = "::".join(self.names)
        if self.params is not None:
            s += f"[{self.params}]"
        return s

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
