# test_math_operations.py

import add_function

import pytest


result_index = [(1, 2, 3), (-1, 1, 0), (0, 0, 0), (5, -3, 2), (1, 1, 2)]


@pytest.mark.parametrize("a, b,expected_result", result_index)
def test_add(a: int, b: int, expected_result: int) -> None:
    assert add_function.add(a, b) == expected_result
