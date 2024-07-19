# mypy: allow-untyped-defs
"""Issue #7110"""

from __future__ import annotations

import asyncio

import asynctest


teardowns: list[None] = []


class Test(asynctest.TestCase):
    async def tearDown(self):
        teardowns.append(None)

    async def test_error(self):
        await asyncio.sleep(0)
        self.fail("failing on purpose")

    async def test_ok(self):
        await asyncio.sleep(0)

    def test_teardowns(self):
        assert len(teardowns) == 2
