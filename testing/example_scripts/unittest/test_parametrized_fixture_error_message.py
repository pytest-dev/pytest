# mypy: allow-untyped-defs
from __future__ import annotations

import unittest

import pytest


@pytest.fixture(params=[1, 2])
def two(request):
    return request.param


@pytest.mark.usefixtures("two")
class TestSomethingElse(unittest.TestCase):
    def test_two(self):
        pass
