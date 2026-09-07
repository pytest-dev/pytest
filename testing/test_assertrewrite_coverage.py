"""Systematic coverage tests for assertion rewriting.

This module provides a structured testing framework that verifies assertion
rewriting behavior across all expression types, checking:

1. Introspection depth: failure messages contain expected intermediate values
2. Semantic correctness: rewritten code has identical behavior to original
3. Single evaluation: side-effecting expressions are not evaluated multiple times
4. Evaluation order: operands see the values Python would give them
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from collections.abc import Sequence
import textwrap
from typing import cast

from _pytest.assertion.rewrite import rewrite_asserts
import pytest


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _exec_check(
    src: str,
    *,
    rewrite: bool = True,
    ns: dict[str, object] | None = None,
) -> Callable[[], object]:
    """Compile and execute ``src``, returning the ``check`` function it defines.

    When ``rewrite`` is true the assertions are rewritten before compiling.

    ``ns`` is the namespace the source executes in.
    """
    src = textwrap.dedent(src)
    tree = ast.parse(src)
    if rewrite:
        rewrite_asserts(tree, src.encode())
    if ns is None:
        ns = {}
    exec(compile(tree, "<test-rewritten>" if rewrite else "<test-plain>", "exec"), ns)
    return cast(Callable[[], object], ns["check"])


def get_failure_message(src: str) -> str:
    """Compile rewritten source, execute it, and return the failure message.

    The source should contain a function named ``check`` with a failing assert.
    Returns the AssertionError message string.

    Raises AssertionError via pytest.fail if the code does not raise.
    """
    func = _exec_check(src)
    try:
        func()
    except AssertionError as e:
        s = str(e)
        if not s.startswith("assert"):
            return "AssertionError: " + s
        return s
    else:
        pytest.fail("check() did not raise AssertionError")


def assert_introspects(
    src: str,
    *,
    must_contain: Sequence[str],
    must_not_contain: Sequence[str] = (),
) -> str:
    """Verify a failing assert produces a message with expected intermediate values.

    :param src: Source containing a ``check()`` function with a failing assert.
    :param must_contain: Substrings that must appear in the failure message.
    :param must_not_contain: Substrings that must not appear in it.
    :returns: The full failure message.
    """
    msg = get_failure_message(src)
    for expected in must_contain:
        assert expected in msg, (
            f"Expected {expected!r} in failure message.\nGot:\n{msg}"
        )
    for unexpected in must_not_contain:
        assert unexpected not in msg, (
            f"Did NOT expect {unexpected!r} in failure message.\nGot:\n{msg}"
        )
    return msg


def assert_single_evaluation(
    src: str,
    *,
    expected_call_count: int = 1,
) -> None:
    """Verify a side-effecting expression runs the expected number of times.

    The source should define a ``check()`` function and use the ``counter``
    list seeded here, which tracks how many times a side-effecting expression
    is evaluated.

    :param src: Source containing a ``check()`` function with side effects.
    :param expected_call_count: How many times it should be evaluated.
    """
    ns: dict[str, object] = {"counter": [0]}
    func = _exec_check(src, ns=ns)
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


def assert_passes_when_true(src: str) -> None:
    """Verify rewritten assertion does not raise when the condition is true.

    :param src: Source containing a ``check()`` function with a passing assert.
    """
    _exec_check(src)()


_Outcome = tuple[bool, object]


def _run_both(src: str) -> tuple[_Outcome, _Outcome]:
    """Execute ``check()`` plain and rewritten, returning (raised, result) pairs."""
    outcomes: list[_Outcome] = []
    for rewrite in (False, True):
        func = _exec_check(src, rewrite=rewrite)
        try:
            outcomes.append((False, func()))
        except AssertionError:
            outcomes.append((True, None))
    plain, rewritten = outcomes
    return plain, rewritten


def assert_semantically_equivalent(src: str) -> None:
    """Verify rewritten code has same pass/fail semantics as unrewritten code.

    Runs the source both with and without rewriting, and asserts they agree
    on whether an AssertionError is raised.  Only the raise is compared --
    :func:`assert_evaluation_order` compares the returned observations too.

    :param src: Source containing a ``check()`` function with an assertion.
    """
    (plain_raised, _), (rewritten_raised, _) = _run_both(src)
    assert plain_raised == rewritten_raised, (
        f"Semantic mismatch: plain {'raised' if plain_raised else 'passed'}, "
        f"rewritten {'raised' if rewritten_raised else 'passed'}"
    )


def assert_evaluation_order(src: str) -> None:
    """Verify rewriting preserves the values Python's evaluation order produces.

    ``check()`` should return whatever the order is observable through -- the
    operand values it saw, a trace list it appended to, the final binding of a
    name a walrus operator rebinds.  Both runs must agree on that return value
    and on whether ``AssertionError`` was raised.

    This is stricter than :func:`assert_semantically_equivalent`, which compares
    pass/fail only.  An operand read after a later walrus operator rebound its
    name can still fail the assertion, just having compared the wrong value, and
    it is evaluated exactly once either way -- so neither of the other axes sees
    it.

    Note that the observation cannot wrap the fragile operand itself: a bare
    name is exactly the case the rewriter leaves unhoisted, and putting a call
    around it would hoist it and hide the bug.  Observe through the result
    instead.

    :param src: Source containing a ``check()`` function returning observations.
    """
    plain, rewritten = _run_both(src)
    assert plain == rewritten, (
        f"Evaluation order mismatch:\n  plain     (raised, result) = {plain}\n"
        f"  rewritten (raised, result) = {rewritten}"
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

    def test_assert_introspects_must_not_contain(self) -> None:
        assert_introspects(
            """
            def check():
                x = 3
                assert x == 5
            """,
            must_contain=["assert 3 == 5"],
            must_not_contain=["this is not in the message"],
        )

    def test_assert_introspects_fails_on_unexpected(self) -> None:
        with pytest.raises(AssertionError, match=r"Did NOT expect.*in failure"):
            assert_introspects(
                """
                def check():
                    x = 3
                    assert x == 5
                """,
                must_contain=["assert 3 == 5"],
                must_not_contain=["assert 3"],
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

    def test_assert_evaluation_order_passing(self) -> None:
        assert_evaluation_order("""
            def check():
                value = 1
                assert value == 1
                return value
            """)

    def test_assert_evaluation_order_detects_value_mismatch(self) -> None:
        """A divergence both runs agree to pass on must still be caught.

        The rewritten function keeps its ``@py_assert`` temporaries in locals,
        so this diverges in the return value while both runs pass.
        """
        with pytest.raises(AssertionError, match="Evaluation order mismatch"):
            assert_evaluation_order("""
                def check():
                    assert 1 == 1
                    return sorted(n for n in locals() if n.startswith("@py"))
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
    """Subscript / indexing."""

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
    """Ternary / if-expression."""

    def test_ifexp_semantics_preserved(self) -> None:
        assert_semantically_equivalent("""
            def check():
                flag = True
                assert (0 if flag else 1) == 1
            """)

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
    """Container literals ([...], {...}, {k:v})."""

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
    """Comprehensions."""

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
    """F-string expressions."""

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
    """Method calls — currently show the bound method as its own "where" line."""

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

    def test_walrus_in_boolop_reports_each_operand(self) -> None:
        """Two walrus assignments to one name: each operand shows what it saw."""
        assert_introspects(
            """
            def check():
                def side_effect():
                    return True
                assert (x := side_effect()) and (x := False)
            """,
            must_contain=["assert (True and False)"],
        )

    def test_walrus_in_boolop_reports_assigned_value(self) -> None:
        assert_introspects(
            """
            def check():
                a = True
                assert not (a and ((a := False) is False))
            """,
            must_contain=["assert not (True and False is False)"],
        )

    def test_walrus_in_boolop_reports_left_operand(self) -> None:
        """A comparator walrus must not overwrite the left operand's report."""
        assert_introspects(
            """
            def check():
                a = "Hello"
                b = "World"
                c = "Test"
                assert (a := b) == c and (a := "Test") == "Test"
            """,
            must_contain=["assert ('World' == 'Test'"],
        )


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
# Evaluation-order tests: operands must see the values Python gives them
# ---------------------------------------------------------------------------


class TestEvaluationOrder:
    """Verify rewriting does not reorder operands against a walrus operator.

    The rewriter turns sub-expressions into statements that run in source
    order, but an operand it leaves unhoisted is read only when the enclosing
    expression is assembled -- after the statements belonging to the operands
    that follow it.  A walrus operator in one of those rebinds the name in
    between, and the earlier operand then sees a value Python would never have
    given it.
    """

    def test_compare_left_operand_precedes_walrus(self) -> None:
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                value = "Hello"
                try:
                    assert value != identity(value := value.lower())
                except AssertionError:
                    return "raised", value
                return "passed", value
            """)

    def test_compare_reports_left_operand(self) -> None:
        assert_introspects(
            """
            def check():
                def identity(v):
                    return v
                value = 2
                assert value == identity(value := 3)
            """,
            must_contain=["assert 2 == 3"],
        )

    def test_call_earlier_argument_precedes_walrus(self) -> None:
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                def collect(*values):
                    return values
                value = "Hello"
                try:
                    assert collect(value, identity(value := value.lower())) == ("Hello", "hello")
                except AssertionError:
                    return "raised", value
                return "passed", value
            """)

    def test_call_later_argument_sees_walrus_value(self) -> None:
        """The mirror of the case above: a later operand sees the new value."""
        assert_evaluation_order("""
            def check():
                def collect(*values):
                    return values
                value = "Hello"
                try:
                    assert collect(value := value.lower(), value) == ("hello", "hello")
                except AssertionError:
                    return "raised", value
                return "passed", value
            """)

    def test_boolop_chain_rebinds_in_order(self) -> None:
        assert_evaluation_order("""
            def check():
                a = True
                try:
                    assert a and True and ((a := False) is False) and (a is False) and ((a := None) is None)
                except AssertionError:
                    return "raised", a
                return "passed", a
            """)

    def test_binop_left_operand_precedes_walrus(self) -> None:
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                value = 1
                try:
                    assert value + identity(value := 5) == 6
                except AssertionError:
                    return "raised", value
                return "passed", value
            """)

    def test_chained_compare_operands_in_order(self) -> None:
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                value = 1
                try:
                    assert value < identity(value := 5) < 9
                except AssertionError:
                    return "raised", value
                return "passed", value
            """)

    def test_container_literal_operand_in_order(self) -> None:
        """Guard: ``generic_visit`` hoists container literals into a temporary."""
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                value = 1
                try:
                    assert [value] == identity([value := 2])
                except AssertionError:
                    return "raised", value
                return "passed", value
            """)

    def test_fstring_operand_in_order(self) -> None:
        """Guard: ``generic_visit`` hoists f-strings into a temporary."""
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                value = "a"
                try:
                    assert f"{value}" != identity(str(value := "b"))
                except AssertionError:
                    return "raised", value
                return "passed", value
            """)

    def test_attribute_operand_in_order(self) -> None:
        """Guard: ``visit_Attribute`` hoists the attribute into a temporary."""
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                class Box:
                    def __init__(self, value):
                        self.value = value
                box = Box(1)
                try:
                    assert box.value == identity((box := Box(2)).value)
                except AssertionError:
                    return "raised", box.value
                return "passed", box.value
            """)

    def test_subscript_container_in_order(self) -> None:
        """Guard: the container is read before a walrus in the key rebinds it."""
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                first = {"k": 1}
                second = {"k": 2}
                box = first
                try:
                    assert box[identity((box := second) and "k")] == 1
                except AssertionError:
                    return "raised", box is second
                return "passed", box is second
            """)

    def test_method_receiver_in_order(self) -> None:
        """Guard: the receiver is read before a walrus in an argument rebinds it."""
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                class Box:
                    def take(self, value):
                        return value
                obj = Box()
                try:
                    assert obj.take(identity(obj := None)) is None
                except AssertionError:
                    return "raised", obj
                return "passed", obj
            """)

    def test_keyword_argument_precedes_walrus(self) -> None:
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                def collect(**kwargs):
                    return kwargs
                value = 1
                try:
                    assert collect(a=value, b=identity(value := 2)) == {"a": 1, "b": 2}
                except AssertionError:
                    return "raised", value
                return "passed", value
            """)

    def test_double_star_argument_precedes_walrus(self) -> None:
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                def collect(**kwargs):
                    return kwargs
                mapping = {"a": 1}
                try:
                    assert collect(**mapping, b=identity(mapping := {"a": 9})) == {"a": 1, "b": {"a": 9}}
                except AssertionError:
                    return "raised", mapping
                return "passed", mapping
            """)

    def test_ifexp_branches_in_order(self) -> None:
        """Guard: the condition is evaluated before the selected branch."""
        assert_evaluation_order("""
            def check():
                def identity(v):
                    return v
                flag = True
                try:
                    assert (1 if flag else 2) == identity(1 if (flag := False) or True else 3)
                except AssertionError:
                    return "raised", flag
                return "passed", flag
            """)


# ---------------------------------------------------------------------------
# Edge cases: combinations of new visitors with existing ones
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Regression and edge-case tests combining multiple expression types."""

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
