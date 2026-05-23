# mypy: allow-untyped-defs
from __future__ import annotations

from _pytest.fixtures import FixtureLookupError
import pytest


@pytest.fixture
def arg2(request):
    with pytest.raises(FixtureLookupError):
        request.getfixturevalue("arg1")
