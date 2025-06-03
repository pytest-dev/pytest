from typing import Callable

from testing.example_scripts.rewrite.src.main import func


def test_plugin(a: int, b: int, special_asserter: Callable[[int, int], bool]):
    special_asserter(a, b)

def test_func(a: int, b: int, special_asserter: Callable[[int, int], bool]):
    assert {'res': func(a, b)} == {'res': 0}