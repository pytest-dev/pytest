from __future__ import annotations


def func(x: int, y: int):
    assert x > 0
    assert y > 0
    return 0 if x == y else 1 if x > y else -1
