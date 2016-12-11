import pytest
from _pytest.compat import is_generator
try:
    import asyncio
except ImportError:
    asyncio = None


@pytest.mark.skipif(asyncio is None, reason='asyncio is not installed')
def test_is_generator():
    @asyncio.coroutine
    def baz():
        yield from [1,2,3]

    assert not is_generator(baz)
