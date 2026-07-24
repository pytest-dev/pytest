from __future__ import annotations

from _pytest.nodeid import coerce_node_id
from _pytest.nodeid import CollectionNodeId
from _pytest.nodeid import ItemNodeId
from _pytest.nodeid import OpaqueNodeId
from _pytest.nodeid import ParamId
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
        assert str(opaque) == str(node_id)


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
