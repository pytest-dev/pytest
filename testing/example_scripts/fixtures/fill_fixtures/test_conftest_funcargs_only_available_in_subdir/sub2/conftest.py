# mypy: allow-untyped-defs
from __future__ import annotations

import pytest


@pytest.fixture
def arg2(request):
    pytest.raises(Exception, request.getfixturevalue, "arg1")
