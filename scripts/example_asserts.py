"""Example file for dump-assert-rewrite.py and diff-assert-rewrite.py.

Includes bluetech's walrus-in-BoolOp case from the #14445 review, plus
other common assertion patterns useful for spotting rewrite changes.
"""

from __future__ import annotations


def side_effect() -> bool:
    return True


def test_walrus_boolop() -> None:
    """Bluetech's example: walrus reassignment inside BoolOp."""
    assert (x := side_effect()) and (x := False)  # noqa: F841


def test_simple_equality() -> None:
    x = 1
    assert x == 2


def test_comparison() -> None:
    a = [1, 2, 3]
    b = [1, 2, 4]
    assert a == b


def test_boolean() -> None:
    x = True
    y = False
    assert x and y


def test_membership() -> None:
    assert 5 in [1, 2, 3]


def test_message() -> None:
    value = 42
    assert value > 100, f"expected > 100, got {value}"
