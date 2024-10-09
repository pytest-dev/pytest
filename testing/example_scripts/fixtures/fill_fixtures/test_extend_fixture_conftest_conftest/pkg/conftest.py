# mypy: allow-untyped-defs
from __future__ import annotations

import pytest


@pytest.fixture
def spam(spam):
    return spam * 2
