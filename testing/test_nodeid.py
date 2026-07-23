from __future__ import annotations

from unittest import mock

from _pytest._nodeid import coerce_node_id
from _pytest._nodeid import CollectionNodeId
from _pytest._nodeid import ItemNodeId
from _pytest._nodeid import OpaqueNodeId
from _pytest._nodeid import ParamId
from _pytest.nodes import Node
from _pytest.reports import TestReport
from _pytest.scope import Scope
import pytest


class TestParamId:
    def test_eq_and_hash(self) -> None:
        p1 = ParamId(id="1", argnames=("x",), scope=Scope.Function)
        p2 = ParamId(id="1", argnames=("x",), scope=Scope.Function)
        p3 = ParamId(id="1", argnames=("y",), scope=Scope.Function)
        assert p1 == p2
        assert hash(p1) == hash(p2)
        assert p1 != p3


class TestCollectionNodeId:
    def test_str_root(self) -> None:
        assert str(CollectionNodeId(path="")) == ""

    def test_str_path_only(self) -> None:
        assert str(CollectionNodeId(path="a/b/test_c.py")) == "a/b/test_c.py"

    def test_str_with_names(self) -> None:
        node_id = CollectionNodeId(path="a/test_b.py", names=("TestC", "test_d"))
        assert str(node_id) == "a/test_b.py::TestC::test_d"

    def test_child(self) -> None:
        parent = CollectionNodeId(path="a/test_b.py")
        child = parent.child("TestC")
        assert child == CollectionNodeId(path="a/test_b.py", names=("TestC",))
        grandchild = child.child("test_d")
        assert grandchild == CollectionNodeId(
            path="a/test_b.py", names=("TestC", "test_d")
        )

    def test_leaf(self) -> None:
        parent = CollectionNodeId(path="a/test_b.py")
        params = (ParamId(id="1", argnames=("x",), scope=Scope.Function),)
        leaf = parent.leaf("test_c", params)
        assert isinstance(leaf, ItemNodeId)
        assert leaf.params == params
        assert str(leaf) == "a/test_b.py::test_c[1]"

    def test_eq_and_hash(self) -> None:
        a = CollectionNodeId(path="a/test_b.py", names=("TestC",))
        b = CollectionNodeId(path="a/test_b.py", names=("TestC",))
        c = CollectionNodeId(path="a/test_b.py", names=("TestD",))
        assert a == b
        assert hash(a) == hash(b)
        assert a != c
        # Usable as dict keys / set members.
        assert {a: 1}[b] == 1
        assert {a, b, c} == {a, c}

    def test_as_opaque(self) -> None:
        node_id = CollectionNodeId(path="a/test_b.py", names=("TestC",))
        opaque = node_id.as_opaque()
        assert isinstance(opaque, OpaqueNodeId)
        assert opaque == node_id
        assert str(opaque) == str(node_id)


class TestItemNodeId:
    def test_str_no_params(self) -> None:
        node_id = ItemNodeId(path="a/test_b.py", names=("test_c",))
        assert str(node_id) == "a/test_b.py::test_c"

    def test_str_with_params(self) -> None:
        node_id = ItemNodeId(
            path="a/test_b.py",
            names=("test_c",),
            params=(ParamId(id="1"), ParamId(id="x")),
        )
        assert str(node_id) == "a/test_b.py::test_c[1-x]"

    def test_has_no_child_or_leaf(self) -> None:
        """Nothing ever builds further collection-tree structure on top of
        an item id -- calling .child()/.leaf() is a static AttributeError,
        not just a runtime mistake."""
        node_id = ItemNodeId(path="a/test_b.py", names=("test_c",))
        assert not hasattr(node_id, "child")
        assert not hasattr(node_id, "leaf")

    def test_eq_and_hash(self) -> None:
        a = ItemNodeId(path="a/test_b.py", names=("test_c",))
        b = ItemNodeId(path="a/test_b.py", names=("test_c",))
        c = ItemNodeId(path="a/test_b.py", names=("test_d",))
        assert a == b
        assert hash(a) == hash(b)
        assert a != c
        assert {a: 1}[b] == 1
        assert {a, b, c} == {a, c}

    def test_as_opaque(self) -> None:
        node_id = ItemNodeId(
            path="a/test_b.py", names=("test_c",), params=(ParamId(id="1"),)
        )
        opaque = node_id.as_opaque()
        assert isinstance(opaque, OpaqueNodeId)
        assert opaque == node_id
        assert str(opaque) == str(node_id)


class TestCrossTypeEquality:
    def test_eq_and_hash_across_all_three_types(self) -> None:
        """Equality/hash must be based on the canonical string form, not the
        raw fields or concrete class -- a CollectionNodeId/ItemNodeId built
        from live collection data and an OpaqueNodeId built from a plain
        string must all compare equal and hash equal when they represent
        the same logical node. This matters for e.g. comparing a
        currently-collected item.id against a node id read back from an
        on-disk cache file, and for containers that deliberately mix live
        and cache-sourced ids (e.g. cacheprovider's lastfailed).
        """
        collection = CollectionNodeId(path="a/test_b.py", names=("test_c",))
        item = CollectionNodeId(path="a/test_b.py").leaf(
            "test_c", (ParamId(id="1", argnames=("x",), scope=Scope.Function),)
        )
        opaque_collection = OpaqueNodeId.parse("a/test_b.py::test_c")
        opaque_item = OpaqueNodeId.parse("a/test_b.py::test_c[1]")

        assert str(collection) == str(opaque_collection)
        assert collection == opaque_collection
        assert hash(collection) == hash(opaque_collection)

        assert str(item) == str(opaque_item)
        assert item == opaque_item
        assert hash(item) == hash(opaque_item)

        # Different concrete classes must not spuriously compare equal just
        # because they're both "some kind of NodeId".
        assert collection != item
        assert collection != opaque_item
        assert item != opaque_collection

        by_node_id: dict[object, str] = {item: "value"}
        assert by_node_id[opaque_item] == "value"

    def test_string_construction_via_node_init(self) -> None:
        """Node.__init__'s string branch (used e.g. by FSCollector for bare
        paths) still supports a "::"-joined string for backward
        compatibility, splitting it into clean names -- this never sees a
        "[params]" bracket in practice (Function always pre-builds a real
        ItemNodeId instead), so producing a CollectionNodeId here is
        safe."""
        session = mock.Mock()
        session.own_markers = []
        session.parent = None
        session.nodeid = ""
        session.id = CollectionNodeId(path="")
        node = Node.from_parent(
            session, name="ignored", nodeid="a/test_b.py::TestC::test_d"
        )
        assert node.id == CollectionNodeId(
            path="a/test_b.py", names=("TestC", "test_d")
        )
        assert node.nodeid == "a/test_b.py::TestC::test_d"


class TestOpaqueNodeId:
    def test_root(self) -> None:
        node_id = OpaqueNodeId.parse("")
        assert node_id == OpaqueNodeId(path="")
        assert str(node_id) == ""

    def test_path_only(self) -> None:
        node_id = OpaqueNodeId.parse("a/b/test_c.py")
        assert node_id == OpaqueNodeId(path="a/b/test_c.py", rest=None)
        assert str(node_id) == "a/b/test_c.py"

    def test_with_rest(self) -> None:
        node_id = OpaqueNodeId.parse("a/test_b.py::TestC::test_d")
        assert node_id == OpaqueNodeId(path="a/test_b.py", rest="TestC::test_d")

    def test_rest_stays_opaque_including_brackets(self) -> None:
        """The [params] bracket (and everything else past the first "::")
        cannot be reliably decomposed from a plain string, so it stays
        opaque, verbatim, in .rest -- see OpaqueNodeId's docstring."""
        node_id = OpaqueNodeId.parse("a/test_b.py::test_c[1-x]")
        assert node_id.rest == "test_c[1-x]"

    def test_rest_none_vs_empty_string(self) -> None:
        """None means no "::" was present at all, distinct from "" after a
        trailing "::" -- both must round-trip losslessly via str.partition().
        """
        no_sep = OpaqueNodeId.parse("a/test_b.py")
        trailing_sep = OpaqueNodeId.parse("a/test_b.py::")
        assert no_sep.rest is None
        assert trailing_sep.rest == ""
        assert str(no_sep) == "a/test_b.py"
        assert str(trailing_sep) == "a/test_b.py::"
        assert no_sep != trailing_sep

    @pytest.mark.parametrize(
        "s",
        [
            "",
            "a/test_b.py",
            "a/test_b.py::",
            "a/test_b.py::TestC",
            "a/test_b.py::TestC::test_d",
            "a/test_b.py::test_c[1-x]",
        ],
    )
    def test_round_trip_matches_original_string(self, s: str) -> None:
        assert str(OpaqueNodeId.parse(s)) == s

    def test_eq_and_hash(self) -> None:
        a = OpaqueNodeId.parse("a/test_b.py::test_c")
        b = OpaqueNodeId.parse("a/test_b.py::test_c")
        c = OpaqueNodeId.parse("a/test_b.py::test_d")
        assert a == b
        assert hash(a) == hash(b)
        assert a != c
        assert {a: 1}[b] == 1
        assert {a, b, c} == {a, c}


class TestCoerceNodeId:
    def test_from_str(self) -> None:
        node_id = coerce_node_id("a/test_b.py::test_c")
        assert node_id == OpaqueNodeId(path="a/test_b.py", rest="test_c")

    def test_from_collection_node_id_returns_same_object(self) -> None:
        node_id = CollectionNodeId(path="a/test_b.py", names=("test_c",))
        assert coerce_node_id(node_id) is node_id

    def test_from_item_node_id_returns_same_object_and_type(self) -> None:
        """Regression test: an earlier plain `NodeId -> NodeId` overload
        widened the return type to the full union, erasing which concrete
        subtype was passed in -- coerce_node_id must echo back the exact
        concrete type given."""
        node_id = ItemNodeId(path="a/test_b.py", names=("test_c",))
        result = coerce_node_id(node_id)
        assert result is node_id
        assert isinstance(result, ItemNodeId)


class TestOpaqueNodeIdAsOpaque:
    def test_returns_self(self) -> None:
        """OpaqueNodeId.as_opaque() exists only so that code holding a
        NodeId | OpaqueNodeId value can call .as_opaque() unconditionally,
        regardless of which concrete type it actually has."""
        node_id = OpaqueNodeId.parse("a/test_b.py::test_c")
        assert node_id.as_opaque() is node_id


class TestWithNodeIdSetter:
    def test_nodeid_setter_builds_opaque_node_id(self) -> None:
        report = TestReport(
            nodeid="a/test_b.py::test_c",
            location=("a/test_b.py", 0, "test_c"),
            keywords={},
            outcome="passed",
            longrepr=None,
            when="call",
        )
        report.nodeid = "a/test_b.py::test_d"
        assert report.id == OpaqueNodeId(path="a/test_b.py", rest="test_d")
        assert report.nodeid == "a/test_b.py::test_d"
