"""Tests for the `collect_function_definition` configuration value."""

from __future__ import annotations

from _pytest.pytester import Pytester
import pytest


@pytest.fixture
def sample(pytester: Pytester) -> Pytester:
    pytester.makepyfile(
        """
        import pytest

        def test_plain():
            pass

        @pytest.mark.parametrize("x", [1, 2])
        def test_param(x):
            assert x

        class TestCls:
            @pytest.mark.parametrize("y", [3, 4])
            def test_method(self, y):
                assert y

            def test_single(self):
                pass
        """
    )
    return pytester


def _set_mode(pytester: Pytester, mode: str) -> None:
    pytester.makeini(f"[pytest]\ncollect_function_definition = {mode}\n")


FLAT_IDS = [
    "test_plain",
    "test_param[1]",
    "test_param[2]",
    "TestCls::test_method[3]",
    "TestCls::test_method[4]",
    "TestCls::test_single",
]

TREE_MODES = ["pedantic", "messy"]
ALL_MODES = ["hidden", *TREE_MODES]


def test_hidden_is_default(sample: Pytester) -> None:
    """Without the option the definition node is not part of the tree."""
    items, _ = sample.inline_genitems()
    for item in items:
        assert type(item.parent).__name__ in ("Module", "Class")


@pytest.mark.parametrize("mode", TREE_MODES)
def test_definition_node_inserted(sample: Pytester, mode: str) -> None:
    """In tree modes a FunctionDefinition collector wraps each test."""
    from _pytest.python import Function
    from _pytest.python import FunctionDefinition

    _set_mode(sample, mode)
    items, _ = sample.inline_genitems()
    assert len(items) == len(FLAT_IDS)
    for item in items:
        assert isinstance(item, Function)
        # Every invocation, including non-parametrized ones, is wrapped.
        assert isinstance(item.parent, FunctionDefinition)


@pytest.mark.parametrize("mode", ALL_MODES)
def test_nodeids_are_stable(sample: Pytester, mode: str) -> None:
    """Invocation nodeids stay flat regardless of the mode."""
    _set_mode(sample, mode)
    items, _ = sample.inline_genitems()
    suffixes = [item.nodeid.split("::", 1)[1] for item in items]
    assert suffixes == FLAT_IDS


@pytest.mark.parametrize("mode", ALL_MODES)
def test_tests_run(sample: Pytester, mode: str) -> None:
    _set_mode(sample, mode)
    result = sample.runpytest()
    result.assert_outcomes(passed=6)


def test_selection_and_reporting(sample: Pytester) -> None:
    """-k selection and failure reporting address the flat nodeid."""
    _set_mode(sample, "pedantic")
    result = sample.runpytest("-k", "test_param and 1", "-v")
    assert "test_param[1] PASSED" in result.stdout.str()
    result.assert_outcomes(passed=1, deselected=5)


def test_collect_only_tree(sample: Pytester) -> None:
    _set_mode(sample, "pedantic")
    result = sample.runpytest("--collect-only")
    out = result.stdout.str()
    for expected in [
        "<Module test_collect_only_tree.py>",
        "<FunctionDefinition test_plain>",
        "<Function test_plain>",
        "<FunctionDefinition test_param>",
        "<Function test_param[1]>",
        "<Function test_param[2]>",
    ]:
        assert expected in out


@pytest.mark.parametrize("mode", ALL_MODES)
def test_markers_are_not_duplicated(pytester: Pytester, mode: str) -> None:
    """A function-level marker resolves exactly once in every mode.

    Regression guard: with the definition node in the tree both it and the
    invocation carry the same function-level marks, which must not double up
    when walking parents in ``iter_markers``.
    """
    pytester.makeini(f"[pytest]\ncollect_function_definition = {mode}\n")
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.foo
        @pytest.mark.parametrize("x", [1])
        def test_it(x):
            pass
        """
    )
    items, _ = pytester.inline_genitems()
    (item,) = items
    assert len(list(item.iter_markers(name="foo"))) == 1


def test_pedantic_scopes_markers_to_definition(pytester: Pytester) -> None:
    """In pedantic mode function-level markers live on the definition node."""
    from _pytest.python import FunctionDefinition

    pytester.makeini("[pytest]\ncollect_function_definition = pedantic\n")
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.foo
        def test_it():
            pass
        """
    )
    (item,) = pytester.inline_genitems()[0]
    assert isinstance(item.parent, FunctionDefinition)
    assert [m.name for m in item.own_markers] == []
    assert [m.name for m in item.parent.own_markers] == ["foo"]


def test_messy_transfers_markers_to_invocation(pytester: Pytester) -> None:
    """In messy mode markers are transferred back onto the invocation."""
    from _pytest.python import FunctionDefinition

    pytester.makeini("[pytest]\ncollect_function_definition = messy\n")
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.foo
        def test_it():
            pass
        """
    )
    (item,) = pytester.inline_genitems()[0]
    assert isinstance(item.parent, FunctionDefinition)
    assert [m.name for m in item.own_markers] == ["foo"]
    # Transferred away from the definition scope to avoid duplication.
    assert [m.name for m in item.parent.own_markers] == []


def test_messy_emits_header_warning(sample: Pytester) -> None:
    _set_mode(sample, "messy")
    result = sample.runpytest()
    result.stdout.fnmatch_lines(["*collect_function_definition=messy*"])


def test_pedantic_has_no_header_warning(sample: Pytester) -> None:
    _set_mode(sample, "pedantic")
    result = sample.runpytest()
    result.stdout.no_fnmatch_line("*collect_function_definition=messy*")


def test_invalid_value_errors(sample: Pytester) -> None:
    _set_mode(sample, "bogus")
    result = sample.runpytest()
    result.stderr.fnmatch_lines(["*Unknown collect_function_definition: 'bogus'*"])
    assert result.ret != 0
