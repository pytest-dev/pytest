import os
import pytest
import shutil
import py

pytest_plugins = "pytester",

class TestNewAPI:
    def test_config_cache_makedir(self, testdir):
        testdir.makeini("[pytest]")
        config = testdir.parseconfigure()
        with pytest.raises(ValueError):
            config.cache.makedir("key/name")

        p = config.cache.makedir("name")
        assert p.check()

    def test_config_cache_dataerror(self, testdir):
        testdir.makeini("[pytest]")
        config = testdir.parseconfigure()
        cache = config.cache
        pytest.raises(TypeError, lambda: cache.set("key/name", cache))
        config.cache.set("key/name", 0)
        config.cache._getvaluepath("key/name").write("123invalid")
        val = config.cache.get("key/name", -2)
        assert val == -2

    def test_config_cache(self, testdir):
        testdir.makeconftest("""
            def pytest_configure(config):
                # see that we get cache information early on
                assert hasattr(config, "cache")
        """)
        testdir.makepyfile("""
            def test_session(pytestconfig):
                assert hasattr(pytestconfig, "cache")
        """)
        result = testdir.runpytest()
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*1 passed*"])

    def XXX_test_cachefuncarg(self, testdir):
        testdir.makepyfile("""
            import pytest
            def test_cachefuncarg(cache):
                val = cache.get("some/thing", None)
                assert val is None
                cache.set("some/thing", [1])
                pytest.raises(TypeError, lambda: cache.get("some/thing"))
                val = cache.get("some/thing", [])
                assert val == [1]
        """)
        result = testdir.runpytest()
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*1 passed*"])



def test_cache_reportheader(testdir):
    p = testdir.makepyfile("""
        def test_hello():
            pass
    """)
    result = testdir.runpytest("-v")
    result.stdout.fnmatch_lines([
        "cachedir: .cache"
    ])

def test_cache_show(testdir):
    result = testdir.runpytest("--show-cache")
    assert result.ret == 0
    result.stdout.fnmatch_lines([
        "*cache is empty*"
    ])
    p = testdir.makeconftest("""
        def pytest_configure(config):
            config.cache.set("my/name", [1,2,3])
            config.cache.set("other/some", {1:2})
            dp = config.cache.makedir("mydb")
            dp.ensure("hello")
            dp.ensure("world")
    """)
    result = testdir.runpytest()
    assert result.ret == 0
    result = testdir.runpytest("--show-cache")
    result.stdout.fnmatch_lines_random([
        "*cachedir:*",
        "-*cache values*-",
        "*my/name contains:",
        "  [1, 2, 3]",
        "*other/some contains*",
        "  {*1*: 2}",
        "-*cache directories*-",
        "*mydb/hello*length 0*",
        "*mydb/world*length 0*",
    ])
