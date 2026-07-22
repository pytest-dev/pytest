"""Structured representation of a pytest "nodeid".

A nodeid is a ``::``-separated string identifying a node in the collection
tree, e.g. ``path/to/test_file.py::TestClass::test_method[param]``.
:class:`NodeId` is the structured, internal representation of this concept;
the legacy string form remains available (via ``str(node_id)``) for
backward compatibility with external plugins.

This module must stay a dependency-free leaf: it is imported from
``_pytest.nodes``, which is itself imported by ``_pytest.config``, so
importing anything from ``_pytest.config``/``_pytest.nodes`` here would
create a cycle. Importing :class:`~_pytest.scope.Scope` is safe, since
``_pytest.scope`` is itself documented as a dependency-free leaf module.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from _pytest.scope import Scope


if TYPE_CHECKING:
    from typing_extensions import Self


@dataclasses.dataclass(frozen=True)
class ParamId:
    """One resolved id contributed by a single (possibly stacked)
    ``parametrize()`` call.

    Multiple ``ParamId``s are joined with ``"-"`` to form the legacy
    ``[bracket]`` content of a nodeid, mirroring
    :attr:`_pytest.python.CallSpec2.param_ids`.

    ``argnames``/``scope`` are only known when built from live collection
    data (see ``Function.__init__``); a :class:`NodeId` built from a plain
    nodeid string (see :meth:`NodeId.parse`) never
    constructs one of these, since the individual per-call boundaries
    cannot be reliably recovered once flattened into a string.
    """

    id: str
    argnames: tuple[str, ...] = ()
    scope: Scope | None = None


@dataclasses.dataclass(frozen=True, eq=False)
class NodeId:
    """Structured collection-tree address.

    :param path:
        ``/``-normalized, rootpath-relative filesystem path. Empty string
        for the session root.
    :param names:
        Ordered ``::``-segment names. The *last* element may or may not
        carry an embedded ``[params]`` suffix -- see :attr:`params`.
    :param params:
        Ordered per-``parametrize()``-call ids. Only ever non-empty when
        this ``NodeId`` was built directly from live collection data (see
        ``Function.__init__``); a ``NodeId`` built from a plain string
        (:meth:`parse`) always has ``params == ()``,
        with any ``[params]`` bracket instead left glued, verbatim, onto
        the last element of :attr:`names`. Both forms stringify identically
        -- see :meth:`__str__`.

    .. note::

        Equality and hashing are based on the canonical string form
        (:meth:`__str__`), *not* on the raw ``path``/``names``/``params``
        fields. This is deliberate: two ``NodeId``s for the same logical
        node must compare equal and hash equal regardless of whether one
        was built from live collection data (rich ``params``) and the other
        from a plain string (degraded, bracket glued into ``names``) --
        e.g. a currently-collected ``item.id`` vs. a ``NodeId`` read back
        from an on-disk cache file. Only the string form is a reliable,
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
        if not isinstance(other, NodeId):
            return NotImplemented
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def child(self, name: str, params: tuple[ParamId, ...] = ()) -> NodeId:
        """Return a new NodeId for a child node with the given name."""
        return NodeId(self.path, (*self.names, name), params)

    @property
    def fspath(self) -> str:
        """The path portion of this node id."""
        return self.path

    @classmethod
    def parse(cls, nodeid: str) -> Self:
        """Split a nodeid string into its path and name segments.

        This does **not** attempt to decompose any trailing ``[params]``
        bracket into individual :class:`ParamId` entries -- that structure only
        exists in live collection data (see ``Function.__init__``) and cannot
        be reliably recovered from an already-flattened string (``"-"`` is used
        both to join sub-ids *within* one ``parametrize()`` call and to join
        separate stacked calls, and either may itself contain value-derived
        text with dashes in it). Any bracket present stays glued, verbatim, to
        the last name segment, and the returned NodeId's ``params`` is always
        empty.
        """
        path, *names = nodeid.split("::")
        return cls(path, tuple(names))

    @classmethod
    def coerce(cls, nodeid: str | Self) -> Self:
        """Return ``nodeid`` unchanged if already a :class:`NodeId`, otherwise
        :meth:`parse` it."""
        if isinstance(nodeid, str):
            return cls.parse(nodeid)
        return nodeid
