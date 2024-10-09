# mypy: allow-untyped-defs
from __future__ import annotations

import pytest


def test_foo():
    assert True


@pytest.mark.parametrize("i", range(3))
def test_bar(i):
    assert True
