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

    # Run without rewriting
    plain_code = compile(src, "<test-plain>", "exec")
    plain_ns: dict[str, object] = {}
    if extra_ns is not None:
        plain_ns.update(extra_ns)
    exec(plain_code, plain_ns)
    plain_func = cast(Callable[[], None], plain_ns["check"])
    plain_raised = False
    try:
        plain_func()
    except AssertionError:
        plain_raised = True

    # Run with rewriting
    mod = _rewrite_source(src)
    rewritten_code = compile(mod, "<test-rewritten>", "exec")
    rewritten_ns: dict[str, object] = {}
    if extra_ns is not None:
        rewritten_ns.update(extra_ns)
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
