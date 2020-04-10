from unittest import IsolatedAsyncioTestCase  # type: ignore


class AsyncArguments(IsolatedAsyncioTestCase):
    async def test_something_async(self):
        async def addition(x, y):
            return x + y

        self.assertEqual(await addition(2, 2), 4)

    async def test_something_async_fails(self):
        async def addition(x, y):
            return x + y

        self.assertEqual(await addition(2, 2), 3)
