"""Structured representation of a pytest "nodeid".

A nodeid is represented as a ``::``-separated string, identifying a node in the collection
tree, e.g. ``path/to/test_file.py::TestClass::test_method[param]``.

The :class:`NodeId` class represents that information in a proper dataclass with the relevant
parts readily available, avoiding reparsing that information when needed and also making for
a better type than `str`.

The legacy ``::``-joined string form remains available (via ``str(node_id)``)
for backward compatibility with external plugins.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class NodeId:
    """Structured address for a node in the collection tree.

    Collector ids (``Collector`` nodes) have ``params=None`` and can still
    have children built under them via :meth:`child` and :meth:`leaf`.

    Item ids (``Item`` nodes, i.e. test leaves) carry the raw ``[params]``
    bracket as a string and cannot have further children.

    :param path:
        ``/``-normalized, rootpath-relative filesystem path.  Empty string
        for the session root.
    :param names:
        Ordered ``::``-segment names after the path.
    :param params:
        Raw contents inside the outermost ``[...]`` bracket, kept as one
        opaque string (the param-call-boundary structure cannot be recovered
        from the ``"-"``-joined flat string).
        ``None`` means no bracket (a collector id); ``""`` means an empty ``[]``.
    """

    path: str
    names: tuple[str, ...] = ()
    params: str | None = None
    _str_cache: str | None = dataclasses.field(
        default=None, init=False, repr=False, compare=False
    )

    @classmethod
    def parse(cls, nodeid: str) -> NodeId:
        """Parse a nodeid string into its path, names, and raw params.

        The bracket is peeled off *before* splitting on ``"::"`` so that a
        ``"::"`` appearing *inside* a params bracket (e.g. a param value
        ``"double::colon"``) is never mistaken for a name separator
        (issue #469).

        Collector nodeids (no ``[params]`` bracket) parse with ``params=None``,
        so this works for both collector and item ids.
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
        """
        if not self.names:
            return None
        s = "::".join(self.names)
        if self.params is not None:
            s += f"[{self.params}]"
        return s

    def child(self, name: str) -> NodeId:
        """Return a new :class:`NodeId` for a child collector node.

        :raises ValueError: if called on a node that already has params
            (i.e., a leaf item) -- only collector ids (``params=None``) can
            have children.
        """
        if self.params is not None:
            raise ValueError(
                f"cannot call .child() on a parameterised id {self!r}; "
                "only collector ids (params=None) can have children"
            )
        return NodeId(path=self.path, names=(*self.names, name))

    def with_params(self, params: str | None) -> NodeId:
        """Return a new :class:`NodeId` with ``params`` set.

        :raises ValueError: if ``self`` is already parameterised (i.e. an
            item id with ``params is not None``).
        """
        if self.params is not None:
            raise ValueError(
                f"cannot call .with_params() on a parameterised id {self!r}; "
                "only collector ids (params=None) can be parameterised"
            )
        return NodeId(path=self.path, names=self.names, params=params)


def coerce_node_id(nodeid: str | NodeId) -> NodeId:
    """Return ``nodeid`` unchanged if already a :class:`NodeId` (live
    collection data); otherwise treat it as an external nodeid string and
    wrap it in a :class:`NodeId` via :meth:`NodeId.parse`."""
    if isinstance(nodeid, NodeId):
        return nodeid
    return NodeId.parse(nodeid)
