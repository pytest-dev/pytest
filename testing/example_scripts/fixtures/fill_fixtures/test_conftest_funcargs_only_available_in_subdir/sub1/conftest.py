# mypy: allow-untyped-defs
from __future__ import annotations

import pytest


@pytest.fixture
def arg1(request):
    with pytest.raises(pytest.FixtureLookupError):
        request.getfixturevalue("arg2")
