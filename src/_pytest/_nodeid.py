"""Structured representation of a pytest "nodeid".

A nodeid is a ``::``-separated string identifying a node in the collection
tree, e.g. ``path/to/test_file.py::TestClass::test_method[param]``.
:class:`NodeId` is the structured, internal representation of this concept,
but it is only ever built from live collection data -- so that its
``params`` field can be trusted: a nodeid string's trailing ``[params]``
bracket cannot be reliably decomposed back into individual
``parametrize()``-call boundaries once flattened (``"-"`` is used both to
join sub-ids within one call and to join separate stacked calls), so a
:class:`NodeId` built from an external string would either have to fabricate
that structure or silently lie about not having it. :class:`OpaqueNodeId` is
the honest alternative for that case: it only knows the ``path`` and an
unparsed ``rest``, and makes no claim to structured names or params. The
legacy ``::``-joined string form remains available (via ``str(node_id)``)
for backward compatibility with external plugins, for both types.

This module must stay a dependency-free leaf: it is imported from
``_pytest.nodes``, which is itself imported by ``_pytest.config``, so
importing anything from ``_pytest.config``/``_pytest.nodes`` here would
create a cycle. Importing :class:`~_pytest.scope.Scope` is safe, since
``_pytest.scope`` is itself documented as a dependency-free leaf module.
"""

from __future__ import annotations

import dataclasses
from typing import overload

from _pytest.scope import Scope


@dataclasses.dataclass(frozen=True)
class ParamId:
    """One resolved id contributed by a single (possibly stacked)
    ``parametrize()`` call.

    Multiple ``ParamId``s are joined with ``"-"`` to form the legacy
    ``[bracket]`` content of a nodeid, mirroring
    :attr:`_pytest.python.CallSpec2.param_ids`.

    ``argnames``/``scope`` are only known when built from live collection
    data (see ``Function.__init__``) -- a :class:`NodeId` never has one of
    these guessed from a string; see :class:`OpaqueNodeId` for the
    string-boundary case, which has no ``ParamId``s at all.
    """

    id: str
    argnames: tuple[str, ...] = ()
    scope: Scope | None = None


@dataclasses.dataclass(frozen=True, eq=False)
class NodeId:
    """Structured collection-tree address.

    Only ever constructed from live collection data: either directly (for
    trivial/root cases, e.g. the session root or a bare collector path) or
    via :meth:`child`, chaining off an already-live parent's ``.id``. There
    is deliberately no way to build one from an arbitrary string -- see the
    module docstring and :class:`OpaqueNodeId`.

    :param path:
        ``/``-normalized, rootpath-relative filesystem path. Empty string
        for the session root.
    :param names:
        Ordered ``::``-segment names. The *last* element may or may not
        carry an embedded ``[params]`` suffix -- see :attr:`params`.
    :param params:
        Ordered per-``parametrize()``-call ids.

    .. note::

        Equality and hashing are based on the canonical string form
        (:meth:`__str__`), *not* on the raw ``path``/``names``/``params``
        fields, and compare equal across :class:`NodeId`/:class:`OpaqueNodeId`
        -- e.g. a currently-collected ``item.id`` (``NodeId``) must compare
        equal to a matching entry read back from an on-disk cache file
        (``OpaqueNodeId``). Only the string form is a reliable,
        source-independent identity for a node.
    """

    path: str
    names: tuple[str, ...] = ()
    params: tuple[ParamId, ...] = ()

    def __str__(self) -> str:
        # Lazily compute and cache the joined string on first access -- it's
        # used on every __eq__/__hash__ call (see the class docstring), so
        # it's worth not repeating the join/format work on every comparison.
        # Not a dataclass field: just an ad hoc cached attribute.
        cached: str | None = getattr(self, "_str", None)
        if cached is not None:
            return cached
        base = "::".join((self.path, *self.names))
        if self.params:
            base += "[" + "-".join(p.id for p in self.params) + "]"
        object.__setattr__(self, "_str", base)
        return base

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (NodeId, OpaqueNodeId)):
            return NotImplemented
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def child(self, name: str, params: tuple[ParamId, ...] = ()) -> NodeId:
        """Return a new NodeId for a child node with the given name."""
        return NodeId(self.path, (*self.names, name), params)


@dataclasses.dataclass(frozen=True, eq=False)
class OpaqueNodeId:
    """A nodeid reconstructed from an external string source (an on-disk
    cache file, an xdist JSON wire payload, a duck-typed report-like
    object's ``.nodeid`` attribute, ...), rather than from live collection.

    Unlike :class:`NodeId`, this makes no claim to structured names or
    params: everything after the first ``"::"`` is left opaque and unsplit,
    since it cannot be reliably decomposed (see the module docstring). There
    is no ``.child()`` -- nothing ever builds further collection-tree
    structure on top of a boundary-sourced id.
    """

    path: str
    # Everything after the first "::", left opaque/unsplit. None means no
    # "::" was present at all (distinct from "" after a trailing "::", for
    # lossless round-tripping through str.partition()).
    rest: str | None = None

    @classmethod
    def parse(cls, nodeid: str) -> OpaqueNodeId:
        """Split a nodeid string into its path and an opaque remainder."""
        path, sep, rest = nodeid.partition("::")
        return cls(path, rest if sep else None)

    def __str__(self) -> str:
        # Same lazy-cache-on-first-access rationale as NodeId.__str__ --
        # these live in hot dict/set paths (--lf/--nf/--sw caches), hashed
        # and compared once per collected item per run.
        cached: str | None = getattr(self, "_str", None)
        if cached is not None:
            return cached
        base = self.path if self.rest is None else f"{self.path}::{self.rest}"
        object.__setattr__(self, "_str", base)
        return base

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (NodeId, OpaqueNodeId)):
            return NotImplemented
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))


@overload
def coerce_node_id(nodeid: NodeId) -> NodeId: ...
@overload
def coerce_node_id(nodeid: str) -> OpaqueNodeId: ...
def coerce_node_id(nodeid: str | NodeId) -> NodeId | OpaqueNodeId:
    """Return ``nodeid`` unchanged if already a :class:`NodeId` (live
    collection data); otherwise treat it as an external nodeid string and
    wrap it in an :class:`OpaqueNodeId`."""
    if isinstance(nodeid, NodeId):
        return nodeid
    return OpaqueNodeId.parse(nodeid)
