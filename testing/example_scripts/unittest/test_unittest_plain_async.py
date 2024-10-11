# mypy: allow-untyped-defs
from __future__ import annotations

import unittest


class Test(unittest.TestCase):
    async def test_foo(self):
        assert False
