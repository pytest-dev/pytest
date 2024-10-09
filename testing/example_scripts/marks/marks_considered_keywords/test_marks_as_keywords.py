# mypy: allow-untyped-defs
from __future__ import annotations

import pytest


@pytest.mark.foo
def test_mark():
    pass
