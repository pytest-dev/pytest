import sys

import pytest
from _pytest.compat import is_generator


def test_is_generator():
    def zap():
        yield

    def foo():
        pass

    assert is_generator(zap)
    assert not is_generator(foo)


def test_is_generator_asyncio(testdir):
    pytest.importorskip('asyncio')
    testdir.makepyfile("""
        from _pytest.compat import is_generator
        import asyncio
        @asyncio.coroutine
        def baz():
            yield from [1,2,3]

        def test_is_generator_asyncio():
            assert not is_generator(baz)
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*1 passed*'])


@pytest.mark.skipif(sys.version_info < (3, 5), reason='async syntax available in Python 3.5+')
def test_is_generator_async_syntax(testdir):
    testdir.makepyfile("""
        from _pytest.compat import is_generator
        def test_is_generator_py35():
            async def foo():
                await foo()

            async def bar():
                pass

            assert not is_generator(foo)
            assert not is_generator(bar)
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*1 passed*'])
