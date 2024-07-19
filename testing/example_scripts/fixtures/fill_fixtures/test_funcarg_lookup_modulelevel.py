# mypy: allow-untyped-defs
from __future__ import annotations

import pytest


@pytest.fixture
def something(request):
    return request.function.__name__


class TestClass:
    def test_method(self, something):
        assert something == "test_method"


def test_func(something):
    assert something == "test_func"
