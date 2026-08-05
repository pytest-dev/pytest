from __future__ import annotations

from _pytest.nodeid import coerce_node_id
from _pytest.nodeid import CollectionNodeId
from _pytest.nodeid import ItemNodeId
from _pytest.reports import TestReport
import pytest


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
        leaf = parent.leaf("test_c", "1")
        assert isinstance(leaf, ItemNodeId)
        assert leaf.params == "1"
        assert str(leaf) == "a/test_b.py::test_c[1]"

    def test_leaf_no_params(self) -> None:
        parent = CollectionNodeId(path="a/test_b.py")
        leaf = parent.leaf("test_c", None)
        assert leaf.params is None
        assert str(leaf) == "a/test_b.py::test_c"

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

    def test_parse(self) -> None:
        node_id = CollectionNodeId.parse("a/test_b.py::TestC::test_d")
        assert node_id == CollectionNodeId(
            path="a/test_b.py", names=("TestC", "test_d")
        )
        assert str(node_id) == "a/test_b.py::TestC::test_d"

    def test_parse_path_only(self) -> None:
        node_id = CollectionNodeId.parse("a/b/test_c.py")
        assert node_id == CollectionNodeId(path="a/b/test_c.py")

    def test_as_leaf(self) -> None:
        node_id = CollectionNodeId(path="a/test_b.py", names=("TestC",))
        leaf = node_id.as_leaf()
        assert isinstance(leaf, ItemNodeId)
        assert str(leaf) == str(node_id)


class TestItemNodeId:
    def test_str_no_params(self) -> None:
        node_id = ItemNodeId(path="a/test_b.py", names=("test_c",))
        assert str(node_id) == "a/test_b.py::test_c"

    def test_str_with_params(self) -> None:
        node_id = ItemNodeId(path="a/test_b.py", names=("test_c",), params="1-x")
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

    def test_as_leaf_returns_self(self) -> None:
        """ItemNodeId.as_leaf() is a no-op: it returns self so that code
        holding a NodeId value can call .as_leaf() unconditionally."""
        node_id = ItemNodeId(path="a/test_b.py", names=("test_c",))
        assert node_id.as_leaf() is node_id

    def test_parse_path_only(self) -> None:
        node_id = ItemNodeId.parse("a/b/test_c.py")
        assert node_id == ItemNodeId(path="a/b/test_c.py")
        assert node_id.names == ()
        assert node_id.params is None
        assert str(node_id) == "a/b/test_c.py"

    def test_parse_with_names(self) -> None:
        node_id = ItemNodeId.parse("a/test_b.py::TestC::test_d")
        assert node_id == ItemNodeId(path="a/test_b.py", names=("TestC", "test_d"))
        assert node_id.params is None

    def test_parse_names_and_params(self) -> None:
        node_id = ItemNodeId.parse("a/test_b.py::test_c[1-x]")
        assert node_id.names == ("test_c",)
        assert node_id.params == "1-x"
        assert node_id.rest == "test_c[1-x]"

    def test_parse_params_boundary_not_inferred(self) -> None:
        """The '-' inside params is used both to join sub-ids within one
        parametrize() call and to join separate stacked calls, so the
        internal call-boundary structure cannot be recovered.  params is
        therefore a single opaque string, not decomposed further."""
        node_id = ItemNodeId.parse("a/test_b.py::test_c[a-b-c]")
        assert node_id.params == "a-b-c"

    def test_parse_double_colon_inside_params(self) -> None:
        """A '::' inside the [params] bracket must NOT be mistaken for a
        name separator (issue #469, e.g. a param value 'double::colon')."""
        node_id = ItemNodeId.parse("a/test_b.py::test_func[double::colon]")
        assert node_id.names == ("test_func",)
        assert node_id.params == "double::colon"
        assert str(node_id) == "a/test_b.py::test_func[double::colon]"

    def test_parse_empty_params(self) -> None:
        node_id = ItemNodeId.parse("a/test_b.py::test_c[]")
        assert node_id.names == ("test_c",)
        assert node_id.params == ""

    def test_parse_rest_none_vs_empty_string(self) -> None:
        """None means no "::" was present at all, distinct from "" after a
        trailing "::" -- both must round-trip losslessly.
        """
        no_sep = ItemNodeId.parse("a/test_b.py")
        trailing_sep = ItemNodeId.parse("a/test_b.py::")
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
            "a/test_b.py::test_func[double::colon]",
            "a/test_b.py::TestC::test_d[a-b]",
        ],
    )
    def test_parse_round_trip_matches_original_string(self, s: str) -> None:
        assert str(ItemNodeId.parse(s)) == s


class TestCoerceNodeId:
    def test_from_str(self) -> None:
        node_id = coerce_node_id("a/test_b.py::test_c")
        assert isinstance(node_id, ItemNodeId)
        assert node_id == ItemNodeId(path="a/test_b.py", names=("test_c",))

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


class TestWithNodeIdSetter:
    def test_nodeid_setter_builds_item_node_id(self) -> None:
        report = TestReport(
            nodeid="a/test_b.py::test_c",
            location=("a/test_b.py", 0, "test_c"),
            keywords={},
            outcome="passed",
            longrepr=None,
            when="call",
        )
        report.nodeid = "a/test_b.py::test_d"
        assert report.id == ItemNodeId(path="a/test_b.py", names=("test_d",))
        assert report.nodeid == "a/test_b.py::test_d"
