"""Small sample tests for pytestdemo.

These are intentionally simple so running the single file should pass
in any standard pytest environment.
"""

import pytest


def add(a, b):
    """Simple helper used by the tests."""
    return a + b


def test_add_positive_numbers():
    """A basic happy-path test."""
    assert add(2, 3) == 5


def test_add_with_zero():
    """Edge case: adding zero should be identity."""
    assert add(0, 7) == 7


def test_add_negative_numbers():
    """Ensure negatives work as expected."""
    assert add(-2, -3) == -5


@pytest.mark.parametrize("a,b,expected", [(1, 2, 3), (10, -1, 9), (0, 0, 0)])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected
