import sys

import pytest


@pytest.mark.skipif(sys.version_info < (3, 5), reason='async syntax available in Python 3.5+')
def test_async_function(testdir):
    testdir.makepyfile("""
        async def test_async_function_py35():
            assert False
    """)
    # avoid importing asyncio into pytest's own process, which in turn imports logging (#8)
    result = testdir.runpytest_subprocess()
    result.stdout.fnmatch_lines(['*1 failed*'])
