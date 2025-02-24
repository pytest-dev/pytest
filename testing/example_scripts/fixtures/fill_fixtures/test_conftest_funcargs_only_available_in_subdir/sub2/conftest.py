# mypy: allow-untyped-defs
from __future__ import annotations

import pytest


@pytest.fixture
def arg2(request):
    with pytest.raises(Exception):  # noqa: B017  # too general exception
        request.getfixturevalue("arg1")
