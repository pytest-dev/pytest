from __future__ import annotations

from unittest import mock

from _pytest._nodeid import coerce_node_id
from _pytest._nodeid import NodeId
from _pytest._nodeid import OpaqueNodeId
from _pytest._nodeid import ParamId
from _pytest.nodes import Node
from _pytest.reports import TestReport
from _pytest.scope import Scope


class TestNodeId:
    def test_str_root(self) -> None:
        assert str(NodeId(path="")) == ""

    def test_str_path_only(self) -> None:
        assert str(NodeId(path="a/b/test_c.py")) == "a/b/test_c.py"

    def test_str_with_names(self) -> None:
        node_id = NodeId(path="a/test_b.py", names=("TestC", "test_d"))
        assert str(node_id) == "a/test_b.py::TestC::test_d"

    def test_str_with_params(self) -> None:
        node_id = NodeId(
            path="a/test_b.py",
            names=("test_c",),
            params=(ParamId(id="1"), ParamId(id="x")),
        )
        assert str(node_id) == "a/test_b.py::test_c[1-x]"

    def test_child(self) -> None:
        parent = NodeId(path="a/test_b.py")
        child = parent.child("TestC")
        assert child == NodeId(path="a/test_b.py", names=("TestC",))
        grandchild = child.child("test_d")
        assert grandchild == NodeId(path="a/test_b.py", names=("TestC", "test_d"))

    def test_child_with_params(self) -> None:
        parent = NodeId(path="a/test_b.py")
        params = (ParamId(id="1", argnames=("x",), scope=Scope.Function),)
        child = parent.child("test_c", params)
        assert child.params == params
        assert str(child) == "a/test_b.py::test_c[1]"

    def test_eq_and_hash(self) -> None:
        a = NodeId(path="a/test_b.py", names=("test_c",))
        b = NodeId(path="a/test_b.py", names=("test_c",))
        c = NodeId(path="a/test_b.py", names=("test_d",))
        assert a == b
        assert hash(a) == hash(b)
        assert a != c
        # Usable as dict keys / set members.
        assert {a: 1}[b] == 1
        assert {a, b, c} == {a, c}

    def test_eq_and_hash_with_params(self) -> None:
        p1 = ParamId(id="1", argnames=("x",), scope=Scope.Function)
        p2 = ParamId(id="1", argnames=("x",), scope=Scope.Function)
        p3 = ParamId(id="1", argnames=("y",), scope=Scope.Function)
        assert p1 == p2
        assert hash(p1) == hash(p2)
        assert p1 != p3

    def test_eq_and_hash_across_types(self) -> None:
        """Equality/hash must be based on the canonical string form, not the
        raw fields -- a NodeId built from live collection data (rich
        params, clean names) and an OpaqueNodeId built from a plain string
        (opaque, unsplit rest) must compare equal and hash equal when they
        represent the same logical node. This matters for e.g. comparing a
        currently-collected item.id against a node id read back from an
        on-disk cache file.
        """
        via_child = NodeId(path="a/test_b.py").child(
            "test_c", (ParamId(id="1", argnames=("x",), scope=Scope.Function),)
        )
        via_string = OpaqueNodeId.parse("a/test_b.py::test_c[1]")
        assert str(via_child) == str(via_string)
        assert via_child == via_string
        assert hash(via_child) == hash(via_string)
        by_node_id: dict[NodeId | OpaqueNodeId, str] = {via_child: "value"}
        assert by_node_id[via_string] == "value"

    def test_string_construction_via_node_init(self) -> None:
        """Node.__init__'s string branch (used e.g. by FSCollector for bare
        paths) still supports a "::"-joined string for backward
        compatibility, splitting it into clean names -- this never sees a
        "[params]" bracket in practice (Function always pre-builds a real
        NodeId instead), so producing a NodeId here is safe."""
        session = mock.Mock()
        session.own_markers = []
        session.parent = None
        session.nodeid = ""
        session.id = NodeId(path="")
        node = Node.from_parent(
            session, name="ignored", nodeid="a/test_b.py::TestC::test_d"
        )
        assert node.id == NodeId(path="a/test_b.py", names=("TestC", "test_d"))
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

    def test_round_trip_matches_original_string(self) -> None:
        for s in (
            "",
            "a/test_b.py",
            "a/test_b.py::",
            "a/test_b.py::TestC",
            "a/test_b.py::TestC::test_d",
            "a/test_b.py::test_c[1-x]",
        ):
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

    def test_from_node_id_returns_same_object(self) -> None:
        node_id = NodeId(path="a/test_b.py", names=("test_c",))
        assert coerce_node_id(node_id) is node_id


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
