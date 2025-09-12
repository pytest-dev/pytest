# content of test_sample.py
from __future__ import annotations


def inc(x):
    return x + 1


def test_answer():
    assert inc(3) == 5
