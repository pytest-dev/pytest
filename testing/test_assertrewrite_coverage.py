"""Systematic coverage tests for assertion rewriting.

This module provides a structured testing framework that verifies assertion
rewriting behavior across all expression types, checking:

1. Introspection depth: failure messages contain expected intermediate values
2. Semantic correctness: rewritten code has identical behavior to original
3. Single evaluation: side-effecting expressions are not evaluated multiple times
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from collections.abc import Mapping
import copy
import sys
import textwrap
from typing import cast

from _pytest.assertion.rewrite import rewrite_asserts
import pytest


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _rewrite_source(src: str) -> ast.Module:
    """Parse and rewrite assertions in source code."""
    tree = ast.parse(src)
    rewrite_asserts(tree, src.encode())
    return tree


def get_failure_message(
    src: str,
    extra_ns: Mapping[str, object] | None = None,
) -> str:
    """Compile rewritten source, execute it, and return the failure message.

    The source should contain a function named ``check`` with a failing assert.
    Returns the AssertionError message string.

    Raises AssertionError via pytest.fail if the code does not raise.
    """
    src = textwrap.dedent(src)
    mod = _rewrite_source(src)
    code = compile(mod, "<test>", "exec")
    ns: dict[str, object] = {}
    if extra_ns is not None:
        ns.update(extra_ns)
    exec(code, ns)
    func = cast(Callable[[], None], ns["check"])
    try:
        func()
    except AssertionError:
        s = str(sys.exc_info()[1])
        if not s.startswith("assert"):
            return "AssertionError: " + s
        return s
    else:
        pytest.fail("check() did not raise AssertionError")


def assert_introspects(
    src: str,
    *,
    must_contain: list[str],
    must_not_contain: list[str] | None = None,
    extra_ns: Mapping[str, object] | None = None,
) -> str:
    """Verify a failing assert produces a message with expected intermediate values.

    Parameters
    ----------
    src : str
        Source code containing a ``check()`` function with a failing assertion.
    must_contain : list[str]
        Substrings that MUST appear in the failure message.
    must_not_contain : list[str] | None
        Substrings that must NOT appear in the failure message.
    extra_ns : Mapping[str, object] | None
        Additional namespace entries available during execution.

    Returns
    -------
    str
        The full failure message (for further inspection if needed).
    """
    msg = get_failure_message(src, extra_ns=extra_ns)
    for expected in must_contain:
        assert expected in msg, (
            f"Expected {expected!r} in failure message.\nGot:\n{msg}"
        )
    for unexpected in must_not_contain or []:
        assert unexpected not in msg, (
            f"Did NOT expect {unexpected!r} in failure message.\nGot:\n{msg}"
        )
    return msg


def assert_single_evaluation(
    src: str,
    *,
    expected_call_count: int = 1,
    extra_ns: Mapping[str, object] | None = None,
) -> None:
    """Verify side-effecting expressions in assert are evaluated exactly once.

    The source should define a ``check()`` function and use a ``counter`` list
    (provided via extra_ns or defined in the source) that tracks how many times
    a side-effecting expression is evaluated.

    Parameters
    ----------
    src : str
        Source containing a ``check()`` function whose assert has side effects.
    expected_call_count : int
        How many times the side-effecting expression should be evaluated.
    extra_ns : Mapping[str, object] | None
        Additional namespace. Should include ``counter`` if not defined in src.
    """
    src = textwrap.dedent(src)
    mod = _rewrite_source(src)
    code = compile(mod, "<test>", "exec")
    ns: dict[str, object] = {"counter": [0]}
    if extra_ns is not None:
        ns.update(extra_ns)
    exec(code, ns)
    func = cast(Callable[[], None], ns["check"])
    counter = cast(list[int], ns["counter"])
    counter[0] = 0
    try:
        func()
    except AssertionError:
        pass
    actual = counter[0]
    assert actual == expected_call_count, (
        f"Expression evaluated {actual} times, expected {expected_call_count}"
    )


def assert_passes_when_true(
    src: str,
    *,
    extra_ns: Mapping[str, object] | None = None,
) -> None:
    """Verify rewritten assertion does not raise when the condition is true.

    Parameters
    ----------
    src : str
        Source containing a ``check()`` function with a passing assertion.
    extra_ns : Mapping[str, object] | None
        Additional namespace entries available during execution.
    """
    src = textwrap.dedent(src)
    mod = _rewrite_source(src)
    code = compile(mod, "<test>", "exec")
    ns: dict[str, object] = {}
    if extra_ns is not None:
        ns.update(extra_ns)
    exec(code, ns)
    func = cast(Callable[[], None], ns["check"])
    func()


def assert_semantically_equivalent(
    src: str,
    *,
    extra_ns: Mapping[str, object] | None = None,
) -> None:
    """Verify rewritten code has same pass/fail semantics as unrewritten code.

    Runs the source both with and without rewriting, and asserts they agree
    on whether an AssertionError is raised.

    Parameters
    ----------
    src : str
        Source containing a ``check()`` function with an assertion.
    extra_ns : Mapping[str, object] | None
        Additional namespace entries available during execution.
    """
    src = textwrap.dedent(src)

    # Run without rewriting — use deepcopy of extra_ns to isolate mutable state
    plain_code = compile(src, "<test-plain>", "exec")
    plain_ns: dict[str, object] = {}
    if extra_ns is not None:
        plain_ns.update(copy.deepcopy(dict(extra_ns)))
    exec(plain_code, plain_ns)
    plain_func = cast(Callable[[], None], plain_ns["check"])
    plain_raised = False
    try:
        plain_func()
    except AssertionError:
        plain_raised = True

    # Run with rewriting — fresh deepcopy so mutations from first run don't leak
    mod = _rewrite_source(src)
    rewritten_code = compile(mod, "<test-rewritten>", "exec")
    rewritten_ns: dict[str, object] = {}
    if extra_ns is not None:
        rewritten_ns.update(copy.deepcopy(dict(extra_ns)))
    exec(rewritten_code, rewritten_ns)
    rewritten_func = cast(Callable[[], None], rewritten_ns["check"])
    rewritten_raised = False
    try:
        rewritten_func()
    except AssertionError:
        rewritten_raised = True

    assert plain_raised == rewritten_raised, (
        f"Semantic mismatch: plain {'raised' if plain_raised else 'passed'}, "
        f"rewritten {'raised' if rewritten_raised else 'passed'}"
    )


# ---------------------------------------------------------------------------
# Smoke tests for the helpers themselves
# ---------------------------------------------------------------------------


class TestHelpersSmokeTest:
    """Verify the test helpers work correctly."""

    def test_get_failure_message_returns_message(self) -> None:
        msg = get_failure_message("""
def check():
    assert 1 == 2
""")
        assert "assert 1 == 2" in msg

    def test_get_failure_message_fails_on_passing_assert(self) -> None:
        with pytest.raises(pytest.fail.Exception, match="did not raise"):
            get_failure_message("""
def check():
    assert 1 == 1
""")

    def test_assert_introspects_succeeds(self) -> None:
        assert_introspects(
            """
def check():
    x = 3
    assert x == 5
""",
            must_contain=["assert 3 == 5"],
        )

    def test_assert_introspects_fails_on_missing(self) -> None:
        with pytest.raises(AssertionError, match=r"Expected.*in failure"):
            assert_introspects(
                """
def check():
    assert 1 == 2
""",
                must_contain=["this is not in the message"],
            )

    def test_assert_single_evaluation(self) -> None:
        assert_single_evaluation("""
def check():
    def inc():
        counter[0] += 1
        return False
    assert inc()
""")

    def test_assert_passes_when_true(self) -> None:
        assert_passes_when_true("""
def check():
    assert 1 == 1
""")

    def test_assert_semantically_equivalent_passing(self) -> None:
        assert_semantically_equivalent("""
def check():
    assert 1 == 1
""")

    def test_assert_semantically_equivalent_failing(self) -> None:
        assert_semantically_equivalent("""
def check():
    assert 1 == 2
""")

    def test_assert_semantically_equivalent_detects_mismatch(self) -> None:
        # This would only trigger on a bug in the rewriter itself;
        # for now just verify both paths execute without error.
        assert_semantically_equivalent("""
def check():
    x = [1, 2, 3]
    assert len(x) == 3
""")


# ---------------------------------------------------------------------------
# Introspection matrix: verify what information each expression type exposes
# ---------------------------------------------------------------------------


class TestIntrospectionCompare:
    """Comparisons (==, !=, <, >, <=, >=, in, not in, is, is not)."""

    def test_simple_equality(self) -> None:
        assert_introspects(
            """
def check():
    x = 3
    assert x == 5
""",
            must_contain=["assert 3 == 5"],
        )

    def test_chained_compare(self) -> None:
        # Chained compares only show the failing pair
        assert_introspects(
            """
def check():
    x = 10
    assert 1 < x < 5
""",
            must_contain=["assert 10 < 5"],
        )

    def test_in_operator(self) -> None:
        assert_introspects(
            """
def check():
    x = 4
    assert x in [1, 2, 3]
""",
            must_contain=["assert 4 in [1, 2, 3]"],
        )

    def test_not_in_operator(self) -> None:
        assert_introspects(
            """
def check():
    x = 2
    assert x not in [1, 2, 3]
""",
            must_contain=["assert 2 not in [1, 2, 3]"],
        )

    def test_is_operator(self) -> None:
        assert_introspects(
            """
def check():
    x = []
    y = []
    assert x is y
""",
            must_contain=["assert [] is []"],
        )


class TestIntrospectionBoolOp:
    """Boolean operations (and, or) with short-circuit."""

    def test_and_both_shown(self) -> None:
        assert_introspects(
            """
def check():
    a = True
    b = False
    assert a and b
""",
            must_contain=["(True and False)"],
        )

    def test_or_both_shown(self) -> None:
        assert_introspects(
            """
def check():
    a = False
    b = False
    assert a or b
""",
            must_contain=["(False or False)"],
        )

    def test_and_short_circuit(self) -> None:
        assert_introspects(
            """
def check():
    a = False
    assert a and explode
""",
            must_contain=["False"],
        )


class TestIntrospectionUnaryOp:
    """Unary operations (not, ~, -, +)."""

    def test_not(self) -> None:
        assert_introspects(
            """
def check():
    x = True
    assert not x
""",
            must_contain=["assert not True"],
        )

    def test_invert(self) -> None:
        # ~(-1) == 0, which is falsy
        assert_introspects(
            """
def check():
    x = -1
    assert ~x
""",
            must_contain=["assert ~-1"],
        )


class TestIntrospectionBinOp:
    """Binary operations (+, -, *, /, etc.)."""

    def test_addition(self) -> None:
        assert_introspects(
            """
def check():
    x = 3
    y = 4
    assert x + y == 10
""",
            must_contain=["(3 + 4)"],
        )

    def test_subtraction(self) -> None:
        assert_introspects(
            """
def check():
    x = 3
    y = 4
    assert x - y == 10
""",
            must_contain=["(3 - 4)"],
        )


class TestIntrospectionCall:
    """Function/method calls."""

    def test_simple_call_shows_result(self) -> None:
        # Currently local functions show full repr in the "where" line
        assert_introspects(
            """
def check():
    def f():
        return 42
    assert f() == 100
""",
            must_contain=["where 42 = ", "()"],
        )

    def test_call_with_args_shows_result(self) -> None:
        assert_introspects(
            """
def check():
    def f(x):
        return x * 2
    assert f(3) == 10
""",
            must_contain=["where 6 = ", "(3)"],
        )

    @pytest.mark.xfail(
        reason="Local function calls show full <function ...> repr: blind spot"
    )
    def test_simple_call_clean_name(self) -> None:
        """Ideally the message should show 'f()' not '<function ... at 0x...>()'."""
        assert_introspects(
            """
def check():
    def f():
        return 42
    assert f() == 100
""",
            must_contain=["where 42 = f()"],
            must_not_contain=["<function"],
        )

    def test_method_call_shows_result(self) -> None:
        assert_introspects(
            """
def check():
    class Obj:
        def method(self):
            return 42
    obj = Obj()
    assert obj.method() == 100
""",
            must_contain=["42", "100"],
        )


class TestIntrospectionAttribute:
    """Attribute access."""

    def test_attribute_access(self) -> None:
        assert_introspects(
            """
def check():
    class Obj:
        x = 3
        def __repr__(self):
            return "Obj()"
    obj = Obj()
    assert obj.x == 5
""",
            must_contain=["where 3 = Obj().x"],
        )


class TestIntrospectionName:
    """Variable name display."""

    def test_local_variable_shown(self) -> None:
        assert_introspects(
            """
def check():
    result = 42
    assert result == 100
""",
            must_contain=["assert 42 == 100"],
        )


class TestIntrospectionSubscript:
    """Subscript / indexing — now has dedicated visitor."""

    def test_dict_subscript_shows_key_and_container(self) -> None:
        assert_introspects(
            """
def check():
    d = {"a": 1, "b": 2}
    assert d["a"] == 99
""",
            must_contain=["where 1 = ", "['a']"],
        )

    def test_list_subscript_shows_index_and_container(self) -> None:
        assert_introspects(
            """
def check():
    items = [10, 20, 30]
    assert items[1] == 99
""",
            must_contain=["where 20 = ", "[1]"],
        )

    def test_subscript_semantics_preserved(self) -> None:
        assert_semantically_equivalent("""
def check():
    d = {"key": "value"}
    assert d["key"] == "wrong"
""")

    def test_subscript_in_compare_shows_value(self) -> None:
        """Even without decomposition, the value is shown in comparisons."""
        assert_introspects(
            """
def check():
    d = {"a": 1}
    assert d["a"] == 99
""",
            must_contain=["assert 1 == 99"],
        )


class TestIntrospectionIfExp:
    """Ternary / if-expression — now has dedicated visitor."""

    def test_ifexp_shows_condition_value(self) -> None:
        assert_introspects(
            """
def check():
    flag = True
    assert (0 if flag else 1) == 1
""",
            must_contain=["if True else"],
        )

    def test_ifexp_semantics_preserved(self) -> None:
        assert_semantically_equivalent("""
def check():
    flag = True
    assert (0 if flag else 1) == 1
""")

    def test_ifexp_in_compare_shows_result(self) -> None:
        assert_introspects(
            """
def check():
    flag = True
    assert (0 if flag else 1) == 99
""",
            must_contain=["assert 0 == 99", "if True else"],
        )

    def test_ifexp_short_circuit_true(self) -> None:
        """Orelse branch must NOT be evaluated when condition is True."""
        assert_passes_when_true("""
def check():
    flag = True
    assert (1 if flag else (1/0)) == 1
""")

    def test_ifexp_short_circuit_false(self) -> None:
        """Body branch must NOT be evaluated when condition is False."""
        assert_passes_when_true("""
def check():
    flag = False
    assert (1/0 if flag else 1) == 1
""")


class TestIntrospectionContainerLiteral:
    """Container literals ([...], {...}, {k:v}) — currently hits generic_visit."""

    @pytest.mark.xfail(reason="Container literals not introspected: blind spot")
    def test_list_literal_shows_elements(self) -> None:
        assert_introspects(
            """
def check():
    def f():
        return 99
    assert [f(), 2, 3] == [1, 2, 3]
""",
            must_contain=["where 99 = f()"],
        )

    def test_list_literal_semantics_preserved(self) -> None:
        assert_semantically_equivalent("""
def check():
    assert [1, 2, 3] == [1, 2, 4]
""")

    def test_dict_literal_semantics_preserved(self) -> None:
        assert_semantically_equivalent("""
def check():
    assert {"a": 1} == {"a": 2}
""")


class TestIntrospectionComprehension:
    """Comprehensions — currently hits generic_visit."""

    def test_listcomp_semantics_preserved(self) -> None:
        assert_semantically_equivalent("""
def check():
    assert [x * 2 for x in range(3)] == [0, 2, 5]
""")

    def test_listcomp_in_compare_shows_result(self) -> None:
        assert_introspects(
            """
def check():
    assert [x * 2 for x in range(3)] == [0, 2, 5]
""",
            must_contain=["[0, 2, 4]"],
        )


class TestIntrospectionFString:
    """F-string expressions — currently hits generic_visit."""

    def test_fstring_semantics_preserved(self) -> None:
        assert_semantically_equivalent("""
def check():
    x = 42
    assert f"value={x}" == "value=99"
""")

    def test_fstring_in_compare_shows_result(self) -> None:
        assert_introspects(
            """
def check():
    x = 42
    assert f"value={x}" == "value=99"
""",
            must_contain=["value=42"],
        )


class TestIntrospectionMethodCall:
    """Method calls — flat obj.method() display without bound-method noise."""

    def test_method_call_flat_format(self) -> None:
        """Method calls show 'where result = obj.method()' in one line."""
        assert_introspects(
            """
def check():
    class Obj:
        def compute(self):
            return 42
        def __repr__(self):
            return "Obj()"
    obj = Obj()
    assert obj.compute() == 100
""",
            must_contain=["where 42 = Obj().compute()"],
        )

    def test_method_call_no_bound_method_noise(self) -> None:
        """No separate 'where compute = obj.compute' line."""
        msg = get_failure_message("""
def check():
    class Obj:
        def compute(self):
            return 42
        def __repr__(self):
            return "Obj()"
    obj = Obj()
    assert obj.compute() == 100
""")
        lines = msg.splitlines()
        for line in lines:
            assert "where compute = " not in line, (
                f"Noisy bound-method intermediate found:\n{msg}"
            )

    def test_callable_variable_shows_result(self) -> None:
        # Current behavior: shows full function repr, not variable name
        assert_introspects(
            """
def check():
    def factory():
        return 42
    fn = factory
    assert fn() == 100
""",
            must_contain=["where 42 = ", "()"],
        )

    @pytest.mark.xfail(reason="Callable variables show <function ...> repr: blind spot")
    def test_callable_variable_clean_name(self) -> None:
        """Ideally should show 'fn()' not '<function factory at 0x...>()'."""
        assert_introspects(
            """
def check():
    def factory():
        return 42
    fn = factory
    assert fn() == 100
""",
            must_contain=["where 42 = fn()"],
            must_not_contain=["<function"],
        )


class TestIntrospectionWalrus:
    """Walrus operator (:=) — has dedicated visitor."""

    def test_walrus_in_compare(self) -> None:
        assert_introspects(
            """
def check():
    x = 10
    assert (y := x * 2) == 100
""",
            must_contain=["assert 20 == 100"],
        )

    def test_walrus_semantics_preserved(self) -> None:
        assert_semantically_equivalent("""
def check():
    x = 10
    assert (y := x * 2) == 100
""")


# ---------------------------------------------------------------------------
# Single-evaluation tests: ensure no expression is evaluated multiple times
# ---------------------------------------------------------------------------


class TestSingleEvaluation:
    """Verify the rewriter doesn't cause double-evaluation of side effects.

    Each test uses a counter to track how many times a side-effecting
    expression is evaluated. The rewritten assert should evaluate each
    expression exactly once, regardless of whether the assertion passes or fails.
    """

    def test_call_in_compare_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    def side_effect():
        counter[0] += 1
        return 42
    assert side_effect() == 100
""")

    def test_call_in_boolean_and_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    def side_effect():
        counter[0] += 1
        return True
    assert side_effect() and False
""")

    def test_call_in_boolean_or_short_circuit(self) -> None:
        # With `or`, if first is truthy, second is NOT evaluated
        assert_single_evaluation(
            """
def check():
    def first():
        counter[0] += 1
        return False
    def second():
        counter[0] += 1
        return False
    assert first() or second()
""",
            expected_call_count=2,
        )

    def test_call_in_unary_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    def side_effect():
        counter[0] += 1
        return True
    assert not side_effect()
""")

    def test_call_in_binop_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    def side_effect():
        counter[0] += 1
        return 5
    assert side_effect() + 1 == 100
""")

    def test_attribute_access_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    class Obj:
        @property
        def prop(self):
            counter[0] += 1
            return 42
    obj = Obj()
    assert obj.prop == 100
""")

    def test_subscript_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    class CountingDict(dict):
        def __getitem__(self, key):
            counter[0] += 1
            return super().__getitem__(key)
    d = CountingDict(a=1)
    assert d["a"] == 100
""")

    def test_walrus_in_compare_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    def side_effect():
        counter[0] += 1
        return 42
    assert (x := side_effect()) == 100
""")

    def test_walrus_in_boolean_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    def side_effect():
        counter[0] += 1
        return 42
    assert (x := side_effect()) and False
""")

    def test_walrus_in_chained_compare_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    def side_effect():
        counter[0] += 1
        return 5
    assert 1 < (x := side_effect()) < 3
""")

    def test_method_call_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    class Obj:
        def compute(self):
            counter[0] += 1
            return 42
    obj = Obj()
    assert obj.compute() == 100
""")

    def test_nested_calls_each_evaluated_once(self) -> None:
        assert_single_evaluation(
            """
def check():
    def outer(x):
        counter[0] += 1
        return x + 1
    def inner():
        counter[0] += 1
        return 5
    assert outer(inner()) == 100
""",
            expected_call_count=2,
        )

    def test_multiple_comparators_evaluated_once_each(self) -> None:
        assert_single_evaluation(
            """
def check():
    def make_val(n):
        counter[0] += 1
        return n
    assert make_val(1) < make_val(5) < make_val(3)
""",
            expected_call_count=3,
        )

    def test_ifexp_condition_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    def cond():
        counter[0] += 1
        return True
    assert (0 if cond() else 1) == 1
""")

    def test_comprehension_generator_evaluated_once(self) -> None:
        assert_single_evaluation("""
def check():
    def items():
        counter[0] += 1
        return [1, 2, 3]
    assert [x * 2 for x in items()] == [2, 4, 7]
""")


# ---------------------------------------------------------------------------
# Edge cases: combinations of new visitors with existing ones
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Regression and edge-case tests combining multiple expression types."""

    def test_subscript_with_variable_key(self) -> None:
        """Subscript where the key is a variable (not constant)."""
        assert_introspects(
            """
def check():
    d = {"hello": 42}
    key = "hello"
    assert d[key] == 100
""",
            must_contain=["where 42 = ", "['hello']"],
        )

    def test_subscript_with_call_key(self) -> None:
        """Subscript where the key is a function call."""
        assert_introspects(
            """
def check():
    d = {0: "zero", 1: "one"}
    def get_key():
        return 0
    assert d[get_key()] == "wrong"
""",
            must_contain=["'zero'", "'wrong'"],
        )

    def test_nested_subscript(self) -> None:
        """Nested subscript: d[k1][k2]."""
        assert_introspects(
            """
def check():
    d = {"a": {"b": 42}}
    assert d["a"]["b"] == 100
""",
            must_contain=["42", "100"],
        )

    def test_method_call_with_args(self) -> None:
        """Method call with arguments shows flat format."""
        assert_introspects(
            """
def check():
    class Calculator:
        def add(self, a, b):
            return a + b
        def __repr__(self):
            return "Calc()"
    c = Calculator()
    assert c.add(2, 3) == 10
""",
            must_contain=["where 5 = Calc().add(2, 3)"],
        )

    def test_chained_method_calls(self) -> None:
        """Chained method call: obj.method1().method2()."""
        assert_introspects(
            """
def check():
    class Builder:
        def __init__(self, val=0):
            self.val = val
        def add(self, n):
            return Builder(self.val + n)
        def result(self):
            return self.val
        def __repr__(self):
            return f"Builder({self.val})"
    b = Builder()
    assert b.add(5).result() == 100
""",
            must_contain=["where 5 = ", ".result()"],
        )

    def test_subscript_on_method_result(self) -> None:
        """Subscript on method return value: obj.method()[key]."""
        assert_introspects(
            """
def check():
    class Store:
        def get_data(self):
            return {"x": 42}
        def __repr__(self):
            return "Store()"
    s = Store()
    assert s.get_data()["x"] == 100
""",
            must_contain=["42", "100"],
        )

    def test_ifexp_with_call_condition(self) -> None:
        """IfExp where condition is a function call."""
        assert_introspects(
            """
def check():
    def is_ready():
        return False
    assert (1 if is_ready() else 0) == 1
""",
            must_contain=["if False else"],
        )

    def test_walrus_in_subscript(self) -> None:
        """Walrus operator used as subscript key."""
        assert_semantically_equivalent("""
def check():
    d = {1: "one", 2: "two"}
    x = 1
    assert d[(y := x + 1)] == "wrong"
""")

    def test_method_call_single_evaluation(self) -> None:
        """Method with side effects is only called once."""
        assert_single_evaluation("""
def check():
    class Obj:
        def compute(self):
            counter[0] += 1
            return 42
    obj = Obj()
    assert obj.compute() == 100
""")

    def test_subscript_single_evaluation(self) -> None:
        """Custom __getitem__ with side effects is only called once."""
        assert_single_evaluation("""
def check():
    class CountingList:
        def __init__(self, items):
            self.items = items
        def __getitem__(self, idx):
            counter[0] += 1
            return self.items[idx]
        def __repr__(self):
            return repr(self.items)
    lst = CountingList([10, 20, 30])
    assert lst[1] == 99
""")

    def test_ifexp_condition_single_evaluation(self) -> None:
        """IfExp condition with side effects is only evaluated once."""
        assert_single_evaluation("""
def check():
    def check_flag():
        counter[0] += 1
        return True
    assert (0 if check_flag() else 1) == 99
""")

    def test_complex_assertion_semantics(self) -> None:
        """Complex assertion combining multiple new visitors."""
        assert_semantically_equivalent("""
def check():
    class Config:
        def __init__(self):
            self.data = {"timeout": 30}
        def get(self, key):
            return self.data[key]
    cfg = Config()
    flag = True
    assert (cfg.get("timeout") if flag else 0) > 60
""")

    def test_assert_with_message_still_works(self) -> None:
        """Assert with a custom message still works with new visitors."""
        msg = get_failure_message("""
def check():
    d = {"key": 42}
    assert d["key"] == 100, "custom failure message"
""")
        assert "custom failure message" in msg

    def test_method_call_on_global(self) -> None:
        """Method call on a global/module-level object."""
        assert_introspects(
            """
items = [1, 2, 3]
def check():
    assert items.count(99) == 1
""",
            must_contain=["where 0 = [1, 2, 3].count(99)"],
        )
