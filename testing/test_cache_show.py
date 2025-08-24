from __future__ import annotations

from textwrap import dedent

from _pytest.pytester import Pytester


def test_cache_show_lists_keys(pytester: Pytester) -> None:
    conftest = """
        def pytest_configure(config):
            config.cache.set("example/key", "42")
    """
    pytester.makeconftest(dedent(conftest))

    result = pytester.runpytest("--cache-show")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*example/key*"])


def test_cache_show_glob_filter(pytester: Pytester) -> None:
    conftest = """
        def pytest_configure(config):
            config.cache.set("alpha/key", "1")
            config.cache.set("beta/key", "2")
    """
    pytester.makeconftest(dedent(conftest))

    result = pytester.runpytest("--cache-show=alpha/*")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*alpha/key*"])
    assert "beta/key" not in result.stdout.str()
