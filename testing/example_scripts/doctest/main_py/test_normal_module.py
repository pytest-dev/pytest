# mypy: allow-untyped-defs
from __future__ import annotations


def test_doc():
    """
    >>> 10 > 5
    True
    """
    assert False
