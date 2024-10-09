# mypy: allow-untyped-defs
from __future__ import annotations

from test_1 import func


def test_2():
    func("foo")
