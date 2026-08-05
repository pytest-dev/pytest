"""Structured representation of a pytest "nodeid".

A nodeid is represented as a ``::``-separated string, identifying a node in the collection
tree, e.g. ``path/to/test_file.py::TestClass::test_method[param]``.

There are three structured, internal representations of this concept, all
only ever built from live collection data or from a specific external
boundary -- so that their fields can always be trusted:

- :class:`CollectionNodeId` -- for a ``Collector`` node (can still have
  children). ``.child()``/``.leaf()`` build further ids on top of it.
- :class:`ItemNodeId` -- for an ``Item`` node (a leaf, e.g. a test
  function). Also serves as the boundary type for nodeids reconstructed
  from external strings (on-disk cache files, xdist JSON wire payloads,
  duck-typed report-like objects' ``.nodeid`` attributes) -- use
  :meth:`ItemNodeId.parse` for that case. It recovers ``names`` and the
  raw ``[params]`` bracket contents (a single opaque string); the internal
  ``"-"`` delimiter joining separate ``parametrize()``-call ids cannot be
  reliably distinguished from a literal ``"-"`` in a param value, so
  ``params`` is left as one unparsed string rather than split further.
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


if TYPE_CHECKING:
    from typing_extensions import Self


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
        # on every __eq__/__hash__ call site elsewhere (e.g. as_leaf()),
        # so it's worth not repeating the join work on every call.
        if self._str_cache is not None:
            return self._str_cache
        s = "::".join((self.path, *self.names))
        object.__setattr__(self, "_str_cache", s)
        return s

    @classmethod
    def parse(cls, nodeid: str) -> CollectionNodeId:
        """Parse a nodeid string into a CollectionNodeId.

        Collector nodeids never carry a ``[params]`` bracket, so this is a
        straightforward ``::`` split.  Used at the string-boundary (e.g.
        ``CollectReport._from_json``) to reconstruct a collector id with the
        correct concrete type.
        """
        path, sep, tail = nodeid.partition("::")
        names = tuple(tail.split("::")) if sep else ()
        self = cls(path=path, names=names)
        object.__setattr__(self, "_str_cache", nodeid)
        return self

    def child(self, name: str) -> CollectionNodeId:
        """Return a new CollectionNodeId for a child collector node."""
        return CollectionNodeId(path=self.path, names=(*self.names, name))

    def leaf(self, name: str, params: str | None) -> ItemNodeId:
        """Return a new ItemNodeId for a terminal item node."""
        return ItemNodeId(path=self.path, names=(*self.names, name), params=params)

    def as_leaf(self) -> ItemNodeId:
        """Return the ``ItemNodeId`` form of this id.

        Used by genuinely mixed containers (e.g. :attr:`LFPlugin.lastfailed`,
        junitxml ``node_reporters``) that receive both collector and item ids
        and need a single comparable key type.
        """
        return ItemNodeId.parse(str(self))


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class ItemNodeId:
    """Structured address for an ``Item`` node -- a leaf, e.g. a test
    function. Has no ``.child()``/``.leaf()``: nothing ever builds further
    collection-tree structure on top of an item id.

    Also serves as the external-string boundary type (via :meth:`parse`)
    for nodeids reconstructed from on-disk cache files, xdist JSON wire
    payloads, or duck-typed report-like objects' ``.nodeid`` attributes.

    :param path:
        ``/``-normalized, rootpath-relative filesystem path.
    :param names:
        Ordered ``::``-segment names.
    :param params:
        Raw contents inside the outermost ``[...]`` bracket, kept as one
        opaque string (the param-call-boundary structure cannot be
        recovered from the ``"-"``-joined flat string).
        ``None`` means no bracket at all; ``""`` means an empty ``[]``.
    """

    path: str
    names: tuple[str, ...] = ()
    params: str | None = None
    _str_cache: str | None = dataclasses.field(
        default=None, init=False, repr=False, compare=False
    )

    @classmethod
    def parse(cls, nodeid: str) -> ItemNodeId:
        """Parse a nodeid string into its path, names, and raw params.

        The bracket is peeled off *before* splitting on ``"::"`` so that a
        ``"::"`` appearing *inside* a params bracket (e.g. a param value
        ``"double::colon"``) is never mistaken for a name separator
        (issue #469).
        """
        path, sep, tail = nodeid.partition("::")
        if not sep:
            # No "::" -- everything is the path.  Never interpret a bracket
            # here: file paths can legitimately contain "[" (e.g. test[1].py).
            self = cls(path=path)
        else:
            # Peel the params bracket off the tail FIRST.
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

        This derived property exists so that code which only needs to
        re-emit the tail (e.g. ``cwd_relative_nodeid``) can work with a
        plain string without caring about the internal structure.
        """
        if not self.names:
            return None
        s = "::".join(self.names)
        if self.params is not None:
            s += f"[{self.params}]"
        return s

    def as_leaf(self) -> Self:
        """Return ``self`` unchanged.

        Exists so that code holding a ``NodeId`` value can call
        ``.as_leaf()`` unconditionally to obtain an ``ItemNodeId`` key,
        regardless of which concrete type it holds.  The collector-side
        counterpart (:meth:`CollectionNodeId.as_leaf`) does the actual
        conversion.
        """
        return self


#: Either kind of live-collection node id, for code that genuinely needs to
#: accept/hold both a CollectionNodeId and an ItemNodeId.
NodeId = CollectionNodeId | ItemNodeId


_N = TypeVar("_N", bound=NodeId)


@overload
def coerce_node_id(nodeid: _N) -> _N: ...
@overload
def coerce_node_id(nodeid: str) -> ItemNodeId: ...
def coerce_node_id(nodeid: str | NodeId) -> NodeId:
    """Return ``nodeid`` unchanged if already a :data:`NodeId` (live
    collection data); otherwise treat it as an external nodeid string and
    wrap it in an :class:`ItemNodeId`."""
    if isinstance(nodeid, CollectionNodeId | ItemNodeId):
        return nodeid
    return ItemNodeId.parse(nodeid)
