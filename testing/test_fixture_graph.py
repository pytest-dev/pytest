from __future__ import annotations

import dataclasses
from typing import Any
from typing import cast

from _pytest.fixtures import _fixture_graph
from _pytest.fixtures import traverse_fixture_closure
from _pytest.pytester import Pytester
import pytest


class StaticDefinition:
    def __init__(self, name: str, dependencies: tuple[str, ...]) -> None:
        self.argname = name
        self.argnames = dependencies


def fake_def(name: str, *dependencies: str) -> pytest.FixtureDef[Any]:
    """Model only static fields; pytester cases below exercise real definitions."""
    return cast(pytest.FixtureDef[Any], StaticDefinition(name, dependencies))


def test_shared_requester_edges_and_parameter_identity() -> None:
    left = fake_def("left", "value")
    right = fake_def("right", "value")
    graph = _fixture_graph(
        ("left", "right", "value"),
        getfixturedefs={"left": (left,), "right": (right,)}.get,
        direct_parametrize_args={"value"},
    )
    edges = [e for e in graph.edges if e.name == "value"]
    parameter = edges[0].target
    assert isinstance(parameter, pytest.FixtureGraphParameter)
    assert parameter.name == "value"
    assert all(e.target is parameter for e in edges)
    assert {e.requester for e in edges} == {left, right, None}
    assert graph.dependents(parameter) == tuple(edges)
    assert graph.dependencies(parameter) == ()
    assert graph.dependencies(left) == (edges[0],)
    assert all(e.kind == "parameter" and e.origin == "declared" for e in edges)
    assert graph.fixturedefs == (left, right)
    assert graph.declared_fixturedefs == (left, right)
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(parameter, "name", "changed")
    other = (
        _fixture_graph(
            ("value",),
            getfixturedefs=lambda name: None,
            direct_parametrize_args={"value"},
        )
        .roots[0]
        .target
    )
    assert other is not parameter and other != parameter


@pytest.mark.parametrize("order", [("wrapper", "shared"), ("shared", "wrapper")])
def test_declared_reachability_is_path_based(order: tuple[str, ...]) -> None:
    leaf = fake_def("leaf")
    shared = fake_def("shared", "leaf")
    hidden = fake_def("hidden")
    base = fake_def("wrapper", "shared", "hidden")
    override = fake_def("wrapper", "request")
    definitions = {
        "wrapper": (base, override),
        "shared": (shared,),
        "leaf": (leaf,),
        "hidden": (hidden,),
    }
    graph = _fixture_graph(order, getfixturedefs=definitions.get)
    assert set(graph.fixturedefs) == {base, override, shared, leaf, hidden}
    assert set(graph.declared_fixturedefs) == {override, shared, leaf}
    assert any(
        e.requester is override and e.target is base and e.origin == "dynamic"
        for e in graph.edges
    )
    assert any(
        e.requester is base and e.target is hidden and e.origin == "declared"
        for e in graph.edges
    )
    # Query-only over-approximation must not add fixtures to normal setup.
    assert "hidden" not in tuple(
        traverse_fixture_closure(order, getfixturedefs=definitions.get)
    )


@pytest.mark.parametrize(
    "dependencies", [(), ("request",), ("resource",), ("resource", "request")]
)
def test_override_edges_match_resolution(dependencies: tuple[str, ...]) -> None:
    base = fake_def("resource")
    override = fake_def("resource", *dependencies)
    graph = _fixture_graph(
        ("resource",), getfixturedefs={"resource": (base, override)}.get
    )
    assert graph.roots[0].target is override
    assert (base in graph.fixturedefs) == bool(dependencies)
    assert (base in graph.declared_fixturedefs) == ("resource" in dependencies)
    assert len(graph.edges) == len(set(graph.edges))
    assert any(e.origin == "dynamic" for e in graph.edges) == (
        "request" in dependencies and "resource" not in dependencies
    )


@pytest.mark.parametrize(
    "name,kind", [("absent", "unresolved"), ("request", "request")]
)
def test_special_roots(name: str, kind: str) -> None:
    graph = _fixture_graph((name,), getfixturedefs=lambda name: None)
    assert len(graph.roots) == 1
    edge = graph.roots[0]
    assert edge.requester is None and edge.name == name and edge.target is None
    assert edge.kind == kind and edge.origin == "declared"
    assert graph.fixturedefs == graph.declared_fixturedefs == ()


def test_declared_definitions_keep_distinct_identities() -> None:
    class EqualDefinition(StaticDefinition):
        def __eq__(self, other: object) -> bool:
            return isinstance(other, EqualDefinition)

    first = cast(pytest.FixtureDef[Any], EqualDefinition("first", ("second",)))
    second = cast(pytest.FixtureDef[Any], EqualDefinition("second", ()))
    assert first == second
    graph = _fixture_graph(
        ("first",), getfixturedefs={"first": (first,), "second": (second,)}.get
    )
    assert len(graph.declared_fixturedefs) == 2
    assert graph.declared_fixturedefs[0] is first
    assert graph.declared_fixturedefs[1] is second
    assert graph.dependencies(first)[0].target is second
    assert graph.dependencies(second) == ()


def test_cycle_is_finite_and_reports_exhaustion() -> None:
    first = fake_def("first", "second")
    second = fake_def("second", "first")
    graph = _fixture_graph(
        ("first",), getfixturedefs={"first": (first,), "second": (second,)}.get
    )
    assert graph.fixturedefs == graph.declared_fixturedefs == (first, second)
    exhausted = graph.dependencies(second)
    assert len(exhausted) == 1
    assert exhausted[0].kind == "exhausted"
    assert exhausted[0].target is None


@pytest.mark.parametrize("roots", [("y", "x"), ("x", "y")])
def test_speculative_branch_does_not_suppress_declared_edge(
    roots: tuple[str, ...],
) -> None:
    x = fake_def("x", "y")
    base = fake_def("y", "x")
    top = fake_def("y", "request")
    graph = _fixture_graph(roots, getfixturedefs={"x": (x,), "y": (base, top)}.get)
    assert any(
        e.target is top and e.origin == "declared" for e in graph.dependencies(x)
    )
    assert set(graph.declared_fixturedefs) == {x, top}
    assert base in graph.fixturedefs


def test_declared_definitions_do_not_follow_a_speculative_context_edge() -> None:
    x = fake_def("x", "y")
    bottom = fake_def("y")
    middle = fake_def("y", "x")
    top = fake_def("y", "request")
    graph = _fixture_graph(
        ("y", "x"), getfixturedefs={"x": (x,), "y": (bottom, middle, top)}.get
    )
    assert bottom in graph.fixturedefs
    assert any(e.target is bottom for e in graph.dependencies(x))
    assert any(e.target is top for e in graph.dependencies(x))
    assert set(graph.declared_fixturedefs) == {x, top}


def test_speculative_context_does_not_replace_real_runtime_dependency(
    pytester: Pytester,
) -> None:
    pytester.makeconftest("""
        import pytest
        @pytest.fixture
        def y(): raise AssertionError("unused bottom ran")
        @pytest.fixture
        def x(y): return y
        def check(graph):
            x = next(fd for fd in graph.fixturedefs if fd.argname == "x")
            top = next(e.target for e in graph.roots if e.name == "y")
            assert any(e.target is top for e in graph.dependencies(x))
            assert set(graph.declared_fixturedefs) == {x, top}
        def pytest_generate_tests(metafunc): check(metafunc.fixture_graph())
        def pytest_collection_modifyitems(items):
            for item in items: check(item.fixture_graph())
    """)
    pytester.makepyfile("""
        import pytest
        @pytest.fixture
        def y(x): raise AssertionError("unused middle ran")
        class TestCase:
            @pytest.fixture
            def y(self, request): return "top"
            def test_case(self, y, x): assert (y, x) == ("top", "top")
    """)
    pytester.runpytest().assert_outcomes(passed=1)


def test_declared_roots_and_shared_dependencies(pytester: Pytester) -> None:
    pytester.makeconftest("""
        import pytest
        @pytest.fixture
        def leaf(): return 1
        @pytest.fixture(autouse=True)
        def automatic(leaf): pass
        @pytest.fixture
        def marked(): pass
        @pytest.fixture
        def resource(leaf): return leaf
        def check(graph):
            assert isinstance(graph, pytest.FixtureGraph)
            assert {e.name for e in graph.roots} == {"automatic", "marked", "resource", "request"}
            assert all(e.origin == "declared" for e in graph.edges)
            leaf = next(fd for fd in graph.fixturedefs if fd.argname == "leaf")
            assert {e.requester.argname for e in graph.dependents(leaf)} == {"automatic", "resource"}
            assert graph.fixturedefs == graph.declared_fixturedefs
        def pytest_generate_tests(metafunc): check(metafunc.fixture_graph())
        def pytest_collection_modifyitems(items):
            for item in items: check(item.fixture_graph())
    """)
    pytester.makepyfile("""
        import pytest
        @pytest.mark.usefixtures("marked")
        def test_case(resource, request): assert resource == 1
    """)
    pytester.runpytest().assert_outcomes(passed=1)


@pytest.mark.parametrize("call_base", [False, True])
def test_dynamic_three_level_chain_is_conservative(
    pytester: Pytester, call_base: bool
) -> None:
    pytester.makeconftest("""
        import pytest
        seen = []
        @pytest.fixture
        def base_dep():
            seen.append("base_dep")
            return "base"
        @pytest.fixture
        def resource(base_dep):
            seen.append("base")
            return base_dep
        def check(graph):
            layers = [fd for fd in graph.fixturedefs if fd.argname == "resource"]
            assert len(layers) == 3
            top, middle, base = layers
            assert any(e.requester is top and e.target is middle and e.origin == "dynamic" for e in graph.edges)
            assert any(e.requester is middle and e.target is base and e.origin == "dynamic" for e in graph.edges)
            assert {fd.argname for fd in graph.declared_fixturedefs} == {"resource", "top_dep"}
            assert top in graph.declared_fixturedefs
            assert base not in graph.declared_fixturedefs
            assert {fd.argname for fd in graph.fixturedefs} == {"resource", "base_dep", "middle_dep", "top_dep"}
        def pytest_generate_tests(metafunc): check(metafunc.fixture_graph())
        def pytest_collection_modifyitems(items):
            for item in items: check(item.fixture_graph())
    """)
    pytester.makepyfile(f"""
        import pytest
        import conftest
        @pytest.fixture
        def middle_dep(): return "middle"
        @pytest.fixture
        def resource(request, middle_dep):
            return request.getfixturevalue("resource") + middle_dep
        class TestLayer:
            @pytest.fixture
            def top_dep(self): return "top"
            @pytest.fixture
            def resource(self, request, top_dep):
                if {call_base!r}:
                    return request.getfixturevalue("resource") + top_dep
                return top_dep
            def test_case(self, resource):
                assert resource == {"basemiddletop" if call_base else "top"!r}
                assert conftest.seen == {["base_dep", "base"] if call_base else []!r}
    """)
    pytester.runpytest().assert_outcomes(passed=1)


@pytest.mark.parametrize("phase", ["generate", "item"])
def test_appended_closure_fixture_is_resolved_and_runs(
    pytester: Pytester, phase: str
) -> None:
    pytester.makeconftest(f"""
        import pytest
        seen = []
        @pytest.fixture
        def dependency():
            seen.append("dependency")
        @pytest.fixture
        def extra(dependency):
            seen.append("extra")
        def check(graph):
            extra = [e for e in graph.roots if e.name == "extra"]
            assert len(extra) == 1 and extra[0].origin == "closure"
            assert extra[0].kind == "fixture"
            assert {{fd.argname for fd in graph.fixturedefs}} == {{"extra", "dependency"}}
            assert graph.declared_fixturedefs == ()
            edge = graph.dependencies(extra[0].target)[0]
            assert edge.name == "dependency" and edge.origin == "declared"
        def pytest_generate_tests(metafunc):
            if {phase!r} == "generate":
                before = metafunc.fixture_graph()
                assert "extra" not in metafunc._arg2fixturedefs
                metafunc.fixturenames.append("extra")
                check(metafunc.fixture_graph())
                assert not any(e.name == "extra" for e in before.roots)
        def pytest_collection_modifyitems(items):
            if {phase!r} == "item":
                items[0].fixturenames.append("extra")
            check(items[0].fixture_graph())
    """)
    pytester.makepyfile("""
        import conftest
        def test_case(): assert conftest.seen == ["dependency", "extra"]
    """)
    pytester.runpytest().assert_outcomes(passed=1)


def test_appended_fixture_uses_late_registered_definition(pytester: Pytester) -> None:
    pytester.makeconftest("""
        import pytest
        class Plugin:
            @pytest.fixture
            def extra(self): return "new"
        def pytest_collection_modifyitems(session, items):
            item = items[0]
            item.fixturenames.append("extra")
            before = item.fixture_graph()
            assert next(e for e in before.roots if e.name == "extra").kind == "unresolved"
            session.config.pluginmanager.register(Plugin())
            graph = item.fixture_graph()
            root = next(e for e in graph.roots if e.name == "extra")
            # Runtime sees the late plugin too; this query must not cache a failed lookup.
            assert root.target is session._fixturemanager.getfixturedefs("extra", item)[-1]
            assert root.origin == "closure"
    """)
    pytester.makepyfile("""
        def test_case(request): assert request.getfixturevalue("extra") == "new"
    """)
    pytester.runpytest().assert_outcomes(passed=1)


@pytest.mark.parametrize("through_fixture", [False, True])
def test_early_decorator_parameter_is_terminal(
    pytester: Pytester, through_fixture: bool
) -> None:
    pytester.makeconftest("""
        import pytest
        @pytest.fixture
        def shadowed(): raise AssertionError("must not execute")
        @pytest.fixture
        def value(shadowed): raise AssertionError("must not execute")
        @pytest.fixture
        def holder(value): return value
        def check(graph):
            edges = [e for e in graph.edges if e.name == "value"]
            assert len(edges) == 1
            node = edges[0].target
            assert isinstance(node, pytest.FixtureGraphParameter)
            assert edges[0].kind == "parameter" and node.name == "value"
            assert graph.dependents(node) == tuple(edges)
            assert not any(e.name == "shadowed" for e in graph.edges)
        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_generate_tests(metafunc):
            assert not metafunc._calls
            check(metafunc.fixture_graph())
            yield
            check(metafunc.fixture_graph())
        def pytest_collection_modifyitems(items):
            for item in items: check(item.fixture_graph())
    """)
    name = "holder" if through_fixture else "value"
    pytester.makepyfile(f"""
        import pytest
        @pytest.mark.parametrize("value", [1, 2])
        def test_case({name}): assert {name} in (1, 2)
    """)
    pytester.runpytest().assert_outcomes(passed=2)


@pytest.mark.parametrize("append", [False, True])
def test_hook_parameter_does_not_restore_pruned_dependency(
    pytester: Pytester, append: bool
) -> None:
    pytester.makeconftest(f"""
        import pytest
        @pytest.fixture
        def stale(): raise AssertionError("pruned fixture ran")
        @pytest.fixture
        def value(stale): raise AssertionError("shadowed fixture ran")
        @pytest.fixture
        def extra(): return 1
        def pytest_generate_tests(metafunc):
            before = metafunc.fixture_graph()
            assert {{fd.argname for fd in before.fixturedefs}} == {{"value", "stale"}}
            metafunc.parametrize("value", [1, 2])
            if {append!r}: metafunc.fixturenames.append("extra")
            after = metafunc.fixture_graph()
            assert "stale" in metafunc.fixturenames
            assert not any(e.name == "stale" for e in after.edges)
            assert {{e.name for e in after.roots if e.origin == "closure"}} == ({{"extra"}} if {append!r} else set())
            assert {{fd.argname for fd in before.fixturedefs}} == {{"value", "stale"}}
        def pytest_collection_modifyitems(items):
            for item in items:
                graph = item.fixture_graph()
                assert "stale" not in item.fixturenames
                assert not any(e.name in ("stale", "extra") for e in graph.edges)
    """)
    pytester.makepyfile("def test_case(value): assert value in (1, 2)")
    pytester.runpytest().assert_outcomes(passed=2)


def test_partial_indirect_parameters_and_definition_scope(pytester: Pytester) -> None:
    pytester.makeconftest("""
        import pytest
        @pytest.fixture
        def stale(): raise AssertionError("must not execute")
        @pytest.fixture
        def direct(stale): raise AssertionError("must not execute")
        @pytest.fixture
        def dependency(): return 10
        @pytest.fixture
        def indirect(dependency, request): return dependency + request.param
        def check(graph):
            direct = next(e for e in graph.roots if e.name == "direct")
            indirect = next(e for e in graph.roots if e.name == "indirect")
            assert isinstance(direct.target, pytest.FixtureGraphParameter)
            assert isinstance(indirect.target, pytest.FixtureDef)
            assert indirect.target.scope == "function"
            assert {fd.argname for fd in graph.fixturedefs} == {"indirect", "dependency"}
        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_generate_tests(metafunc):
            check(metafunc.fixture_graph())
            yield
            check(metafunc.fixture_graph())
        def pytest_collection_modifyitems(items):
            for item in items: check(item.fixture_graph())
    """)
    pytester.makepyfile("""
        import pytest
        @pytest.mark.parametrize(("direct", "indirect"), [(1, 2)], indirect=["indirect"])
        def test_case(direct, indirect): assert (direct, indirect) == (1, 12)
    """)
    pytester.runpytest().assert_outcomes(passed=1)


def test_effective_invocation_scope_is_not_definition_scope(pytester: Pytester) -> None:
    pytester.makeconftest("""
        import pytest
        @pytest.fixture
        def value(request):
            assert request.scope == "session"
            return request.param
        def pytest_collection_modifyitems(items):
            fd = items[0].fixture_graph().fixturedefs[0]
            assert fd.argname == "value" and fd.scope == "function"
    """)
    pytester.makepyfile("""
        import pytest
        @pytest.mark.parametrize("value", [1], indirect=True, scope="session")
        def test_case(value): assert value == 1
    """)
    pytester.runpytest().assert_outcomes(passed=1)


def test_late_item_marker_cannot_hide_running_fixture(pytester: Pytester) -> None:
    pytester.makeconftest("""
        import pytest
        seen = []
        @pytest.fixture
        def value():
            seen.append("value")
            return 1
        def pytest_collection_modifyitems(items):
            item = items[0]
            item.add_marker(pytest.mark.parametrize("value", [99]))
            graph = item.fixture_graph()
            assert graph.roots[0].kind == "fixture"
            assert graph.roots[0].target.func.__name__ == "value"
    """)
    pytester.makepyfile("""
        import conftest
        def test_case(value):
            assert value == 1
            assert conftest.seen == ["value"]
    """)
    pytester.runpytest().assert_outcomes(passed=1)


def test_arbitrary_dynamic_name_remains_outside_contract(pytester: Pytester) -> None:
    pytester.makeconftest("""
        import pytest
        @pytest.fixture
        def hidden(): return 1
        @pytest.fixture
        def resource(request): return request.getfixturevalue("hidden")
        def pytest_collection_modifyitems(items):
            graph = items[0].fixture_graph()
            assert {fd.argname for fd in graph.fixturedefs} == {"resource"}
            assert not any(e.origin == "dynamic" for e in graph.edges)
    """)
    pytester.makepyfile("def test_case(resource): assert resource == 1")
    pytester.runpytest().assert_outcomes(passed=1)


@pytest.mark.parametrize(
    "source,error",
    [
        ("def test_case(absent): pass", "fixture 'absent' not found"),
        (
            "import pytest\n@pytest.fixture\ndef resource(resource): pass\ndef test_case(resource): pass",
            "recursive dependency involving fixture 'resource' detected",
        ),
    ],
)
def test_query_preserves_runtime_lookup_errors(
    pytester: Pytester, source: str, error: str
) -> None:
    pytester.makeconftest("""
        def pytest_generate_tests(metafunc): metafunc.fixture_graph()
        def pytest_collection_modifyitems(items):
            for item in items: item.fixture_graph()
    """)
    pytester.makepyfile(source)
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines([f"*{error}*"])


def test_custom_item_without_fixture_information_has_empty_graph(
    pytester: Pytester,
) -> None:
    pytester.makeconftest("""
        import pytest
        class CustomItem(pytest.Item):
            def runtest(self):
                graph = self.fixture_graph()
                assert graph.roots == graph.edges == ()
                assert graph.fixturedefs == graph.declared_fixturedefs == ()
        class CustomFile(pytest.File):
            def collect(self): yield CustomItem.from_parent(self, name="case")
        def pytest_collect_file(parent, file_path):
            if file_path.suffix == ".custom":
                return CustomFile.from_parent(parent, path=file_path)
    """)
    pytester.makefile(".custom", example="data")
    pytester.runpytest().assert_outcomes(passed=1)


def test_late_generation_marker_cannot_hide_running_fixture(pytester: Pytester) -> None:
    pytester.makeconftest("""
        import pytest
        seen = []
        @pytest.fixture
        def value():
            seen.append("fixture")
            return 1
        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_generate_tests(metafunc):
            yield
            metafunc.definition.add_marker(pytest.mark.parametrize("value", [99]))
            graph = metafunc.fixture_graph()
            assert graph.roots[0].kind == "fixture"
            assert graph.roots[0].target.func.__name__ == "value"
    """)
    pytester.makepyfile("""
        import conftest
        def test_case(value):
            assert value == 1 and conftest.seen == ["fixture"]
    """)
    pytester.runpytest().assert_outcomes(passed=1)


def test_appended_indirect_fixture_is_a_closure_root(pytester: Pytester) -> None:
    pytester.makeconftest("""
        import pytest
        @pytest.fixture
        def extra(request): return request.param
        def pytest_generate_tests(metafunc):
            metafunc.fixturenames.append("extra")
            metafunc.parametrize("extra", [1, 2], indirect=True)
            assert "extra" not in metafunc._arg2fixturedefs
            graph = metafunc.fixture_graph()
            extra = next(e for e in graph.roots if e.name == "extra")
            assert extra.origin == "closure" and extra.kind == "fixture"
            assert isinstance(extra.target, pytest.FixtureDef)
            assert graph.declared_fixturedefs == ()
    """)
    pytester.makepyfile("""
        def test_case(request): assert request.getfixturevalue("extra") in (1, 2)
    """)
    pytester.runpytest().assert_outcomes(passed=2)


def test_closure_root_also_reached_by_dynamic_path(pytester: Pytester) -> None:
    pytester.makeconftest("""
        import pytest
        seen = []
        @pytest.fixture
        def extra(): seen.append("extra")
        @pytest.fixture
        def resource(extra): raise AssertionError("unused base executed")
        def pytest_collection_modifyitems(items):
            item = items[0]
            item.fixturenames.append("extra")
            graph = item.fixture_graph()
            extra = next(e for e in graph.roots if e.name == "extra")
            assert extra.origin == "closure"
            assert len(graph.dependents(extra.target)) == 2
            assert all(fd.argname != "extra" for fd in graph.declared_fixturedefs)
    """)
    pytester.makepyfile("""
        import pytest
        import conftest
        @pytest.fixture
        def resource(request): return "override"
        def test_case(resource):
            assert resource == "override"
            assert conftest.seen == ["extra"]
    """)
    pytester.runpytest().assert_outcomes(passed=1)
