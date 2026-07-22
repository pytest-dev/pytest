from __future__ import annotations

from _pytest._nodeid import NodeId
from _pytest._nodeid import ParamId
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

    def test_eq_and_hash_across_construction_paths(self) -> None:
        """Equality/hash must be based on the canonical string form, not the
        raw fields -- a NodeId built from live collection data (rich
        params, clean names) and one built from a plain string (degraded,
        bracket glued into names) must compare equal and hash equal when
        they represent the same logical node. This matters for e.g.
        comparing a currently-collected item.id against a NodeId read back
        from an on-disk cache file.
        """
        via_child = NodeId(path="a/test_b.py").child(
            "test_c", (ParamId(id="1", argnames=("x",), scope=Scope.Function),)
        )
        via_string = NodeId.parse("a/test_b.py::test_c[1]")
        assert str(via_child) == str(via_string)
        assert via_child.params != via_string.params  # structurally different...
        assert via_child == via_string  # ...but logically the same node.
        assert hash(via_child) == hash(via_string)
        assert {via_child: "value"}[via_string] == "value"


class TestNodeIdCoerce:
    def test_from_str(self) -> None:
        node_id = NodeId.coerce("a/test_b.py::test_c")
        assert node_id == NodeId(path="a/test_b.py", names=("test_c",))

    def test_from_node_id_returns_same_object(self) -> None:
        node_id = NodeId(path="a/test_b.py", names=("test_c",))
        assert NodeId.coerce(node_id) is node_id


class TestNodeIdParse:
    def test_root(self) -> None:
        node_id = NodeId.parse("")
        assert node_id == NodeId(path="")
        assert str(node_id) == ""

    def test_path_only(self) -> None:
        node_id = NodeId.parse("a/b/test_c.py")
        assert node_id == NodeId(path="a/b/test_c.py")

    def test_with_names(self) -> None:
        node_id = NodeId.parse("a/test_b.py::TestC::test_d")
        assert node_id == NodeId(path="a/test_b.py", names=("TestC", "test_d"))

    def test_bracket_stays_glued_and_params_empty(self) -> None:
        """The [params] bracket cannot be reliably decomposed from a plain
        string, so it stays glued verbatim to the last name and params is
        always empty -- see NodeId's docstring."""
        node_id = NodeId.parse("a/test_b.py::test_c[1-x]")
        assert node_id.names == ("test_c[1-x]",)
        assert node_id.params == ()

    def test_round_trip_matches_original_string(self) -> None:
        for s in (
            "",
            "a/test_b.py",
            "a/test_b.py::TestC",
            "a/test_b.py::TestC::test_d",
            "a/test_b.py::test_c[1-x]",
        ):
            assert str(NodeId.parse(s)) == s

    def test_equivalent_to_child_when_no_params(self) -> None:
        """A NodeId built from a plain string and one built via .child()
        with no params stringify identically for the same logical id."""
        via_string = NodeId.parse("a/test_b.py::test_c")
        via_child = NodeId(path="a/test_b.py").child("test_c")
        assert str(via_string) == str(via_child)
