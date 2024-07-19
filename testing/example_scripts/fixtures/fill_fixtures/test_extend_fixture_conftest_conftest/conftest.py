# mypy: allow-untyped-defs
from __future__ import annotations

import pytest


@pytest.fixture
def spam():
    return "spam"
