# mypy: allow-untyped-defs
from __future__ import annotations

from unittest import IsolatedAsyncioTestCase


teardowns: list[None] = []


class AsyncArguments(IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        teardowns.append(None)

    async def test_something_async(self):
        async def addition(x, y):
            return x + y

        self.assertEqual(await addition(2, 2), 4)

    async def test_something_async_fails(self):
        async def addition(x, y):
            return x + y

        self.assertEqual(await addition(2, 2), 3)

    def test_teardowns(self):
        assert len(teardowns) == 2
