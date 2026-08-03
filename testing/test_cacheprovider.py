from __future__ import annotations

from collections.abc import Generator
from collections.abc import Sequence
from enum import auto
from enum import Enum
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any

from _pytest import cacheprovider
from _pytest.cacheprovider import _label
from _pytest.cacheprovider import _project_digest
from _pytest.cacheprovider import _scope_id
from _pytest.cacheprovider import Cache
from _pytest.cacheprovider import CACHE_INFO_NAME
from _pytest.cacheprovider import CACHE_INFO_SCHEMA
from _pytest.cacheprovider import CacheScope
from _pytest.cacheprovider import read_cache_info
from _pytest.compat import assert_never
from _pytest.config import ExitCode
from _pytest.monkeypatch import MonkeyPatch
from _pytest.pathlib import symlink_or_skip
from _pytest.pytester import Pytester
from _pytest.tmpdir import TempPathFactory
import pytest


pytest_plugins = ("pytester",)


@pytest.fixture
def unwritable_cache_dir(pytester: Pytester) -> Generator[Path]:
    cache_dir = pytester.path.joinpath(".pytest_cache")
    cache_dir.mkdir()
    mode = cache_dir.stat().st_mode
    cache_dir.chmod(0)
    if os.access(cache_dir, os.W_OK):
        pytest.skip("Failed to make cache dir unwritable")

    yield cache_dir
    cache_dir.chmod(mode)


def env_scope_values(cachedir: str | Path = ".pytest_cache") -> Path:
    """Path of the env-scoped value directory inside ``cachedir``."""
    scope_id = _scope_id(CacheScope.ENV)
    assert scope_id is not None
    return Path(cachedir, "s", scope_id, "v")


class TestNewAPI:
    def test_config_cache_mkdir(self, pytester: Pytester) -> None:
        pytester.makeini("[pytest]")
        config = pytester.parseconfigure()
        assert config.cache is not None
        with pytest.raises(ValueError):
            config.cache.mkdir("key/name")

        p = config.cache.mkdir("name")
        assert p.is_dir()

    def test_cache_dir_permissions(self, pytester: Pytester) -> None:
        """The .pytest_cache directory should have world-readable permissions
        (depending on umask).

        Regression test for #12308.
        """
        pytester.makeini("[pytest]")
        config = pytester.parseconfigure()
        assert config.cache is not None
        p = config.cache.mkdir("name")
        assert p.is_dir()
        # Instead of messing with umask, make sure .pytest_cache has the same
        # permissions as the default that `mkdir` gives `p`.
        assert (p.parent.stat().st_mode & 0o777) == (p.stat().st_mode & 0o777)

    def test_config_cache_dataerror(self, pytester: Pytester) -> None:
        pytester.makeini("[pytest]")
        config = pytester.parseconfigure()
        assert config.cache is not None
        cache = config.cache
        with pytest.raises(TypeError):
            cache.set("key/name", cache)
        config.cache.set("key/name", 0)
        config.cache._getvaluepath("key/name").write_bytes(b"123invalid")
        val = config.cache.get("key/name", -2)
        assert val == -2

    @pytest.mark.filterwarnings("ignore:could not create cache path")
    def test_cache_writefail_cachefile_silent(self, pytester: Pytester) -> None:
        pytester.makeini("[pytest]")
        pytester.path.joinpath(".pytest_cache").write_text(
            "gone wrong", encoding="utf-8"
        )
        config = pytester.parseconfigure()
        cache = config.cache
        assert cache is not None
        cache.set("test/broken", [])

    @pytest.mark.filterwarnings(
        "ignore:could not create cache path:pytest.PytestWarning"
    )
    def test_cache_writefail_permissions(
        self, unwritable_cache_dir: Path, pytester: Pytester
    ) -> None:
        pytester.makeini("[pytest]")
        config = pytester.parseconfigure()
        cache = config.cache
        assert cache is not None
        cache.set("test/broken", [])

    @pytest.mark.filterwarnings("default")
    def test_cache_failure_warns(
        self,
        pytester: Pytester,
        monkeypatch: MonkeyPatch,
        unwritable_cache_dir: Path,
    ) -> None:
        monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

        pytester.makepyfile("def test_error(): raise Exception")
        result = pytester.runpytest()
        assert result.ret == 1
        # warnings from nodeids and lastfailed
        result.stdout.fnmatch_lines(
            [
                # Validate location/stacklevel of warning from cacheprovider.
                "*= warnings summary =*",
                "*/cacheprovider.py:*",
                "  */cacheprovider.py:*: PytestCacheWarning: could not create cache path "
                f"{env_scope_values(unwritable_cache_dir)}/cache/nodeids: *",
                "    config.cache.set(",
                "*1 failed, 2 warnings in*",
            ]
        )

    def test_config_cache(self, pytester: Pytester) -> None:
        pytester.makeconftest(
            """
            def pytest_configure(config):
                # see that we get cache information early on
                assert hasattr(config, "cache")
        """
        )
        pytester.makepyfile(
            """
            def test_session(pytestconfig):
                assert hasattr(pytestconfig, "cache")
        """
        )
        result = pytester.runpytest()
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*1 passed*"])

    def test_cachefuncarg(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest
            def test_cachefuncarg(cache):
                val = cache.get("some/thing", None)
                assert val is None
                cache.set("some/thing", [1])
                with pytest.raises(TypeError):
                    cache.get("some/thing")
                val = cache.get("some/thing", [])
                assert val == [1]
        """
        )
        result = pytester.runpytest()
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*1 passed*"])

    def test_custom_rel_cache_dir(self, pytester: Pytester) -> None:
        rel_cache_dir = os.path.join("custom_cache_dir", "subdir")
        pytester.makeini(
            f"""
            [pytest]
            cache_dir = {rel_cache_dir}
        """
        )
        pytester.makepyfile(test_errored="def test_error():\n    assert False")
        pytester.runpytest()
        assert pytester.path.joinpath(rel_cache_dir).is_dir()

    def test_custom_abs_cache_dir(
        self, pytester: Pytester, tmp_path_factory: TempPathFactory
    ) -> None:
        tmp = tmp_path_factory.mktemp("tmp")
        abs_cache_dir = tmp / "custom_cache_dir"
        pytester.makeini(
            f"""
            [pytest]
            cache_dir = {abs_cache_dir}
        """
        )
        pytester.makepyfile(test_errored="def test_error():\n    assert False")
        pytester.runpytest()
        assert abs_cache_dir.is_dir()

    def test_custom_cache_dir_with_env_var(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setenv("env_var", "custom_cache_dir")
        pytester.makeini(
            """
            [pytest]
            cache_dir = {cache_dir}
        """.format(cache_dir="$env_var")
        )
        pytester.makepyfile(test_errored="def test_error():\n    assert False")
        pytester.runpytest()
        assert pytester.path.joinpath("custom_cache_dir").is_dir()


@pytest.mark.filterwarnings("ignore::pytest.PytestRemovedIn10Warning")
@pytest.mark.parametrize("env", ((), ("TOX_ENV_DIR", "mydir/tox-env")))
def test_cache_reportheader(
    env: Sequence[str], pytester: Pytester, monkeypatch: MonkeyPatch
) -> None:
    pytester.makepyfile("""def test_foo(): pass""")
    if env:
        monkeypatch.setenv(*env)
        expected = os.path.join(env[1], ".pytest_cache")
    else:
        monkeypatch.delenv("TOX_ENV_DIR", raising=False)
        expected = ".pytest_cache"
    result = pytester.runpytest("-v", "-W", "ignore::pytest.PytestRemovedIn10Warning")
    result.stdout.fnmatch_lines([f"cachedir: {expected}"])


class TestToxEnvDirDeprecation:
    def test_warns_when_the_legacy_default_is_used(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TOX_ENV_DIR", str(pytester.path / "tox-env"))
        pytester.makepyfile(test_a="def test_ok(): pass")
        result = pytester.runpytest("-W", "default")
        result.stdout.fnmatch_lines(
            [
                "*PytestRemovedIn10Warning: Defaulting the cache directory to "
                "$TOX_ENV_DIR/.pytest_cache is deprecated*",
                "*cache_dir = $TOX_ENV_DIR/.pytest_cache*",
            ]
        )

    def test_the_advice_reproduces_the_legacy_location(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        """The deprecation advice has to actually be true.

        It names the very expression the legacy default was built from, so it
        lands in the same place by construction - whatever TOX_ENV_DIR happens
        to point at.
        """
        monkeypatch.setenv("TOX_ENV_DIR", str(pytester.path / "tox-env"))
        pytester.makepyfile(test_a="def test_bad(): assert False")

        legacy = Cache.for_config(pytester.parseconfig(), _ispytest=True)._cachedir
        pytester.makeini("[pytest]\ncache_dir = $TOX_ENV_DIR/.pytest_cache\n")
        migrated = Cache.for_config(pytester.parseconfig(), _ispytest=True)._cachedir
        assert legacy == migrated == pytester.path / "tox-env" / ".pytest_cache"

    def test_silent_without_tox_env_dir(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.delenv("TOX_ENV_DIR", raising=False)
        pytester.makepyfile(test_a="def test_ok(): pass")
        result = pytester.runpytest("-W", "default")
        result.stdout.no_fnmatch_line("*TOX_ENV_DIR*")

    @pytest.mark.parametrize("ini", ["cache_policy = user", "cache_dir = elsewhere"])
    def test_silent_when_configured_explicitly(
        self, pytester: Pytester, monkeypatch: MonkeyPatch, tmp_path: Path, ini: str
    ) -> None:
        monkeypatch.setenv("PYTEST_CACHE_HOME", str(tmp_path / "user-cache"))
        monkeypatch.setenv("TOX_ENV_DIR", str(pytester.path / "tox-env"))
        pytester.makeini(f"[pytest]\n{ini}\n")
        pytester.makepyfile(test_a="def test_ok(): pass")
        result = pytester.runpytest("-W", "default")
        result.stdout.no_fnmatch_line("*TOX_ENV_DIR*")

    def test_configured_policy_is_not_overridden_by_tox(
        self, pytester: Pytester, monkeypatch: MonkeyPatch, tmp_path: Path
    ) -> None:
        """A configured cache_policy must win over the legacy tox location.

        The legacy path is only consulted by the `local` policy for exactly
        this reason - as a `cache_dir` default it would have silently beaten
        every policy, since cache_dir takes precedence.
        """
        user_cache = tmp_path / "user-cache"
        monkeypatch.setenv("PYTEST_CACHE_HOME", str(user_cache))
        monkeypatch.setenv("TOX_ENV_DIR", str(pytester.path / "tox-env"))
        pytester.makeini("[pytest]\ncache_policy = user\n")
        pytester.makepyfile(test_a="def test_bad(): assert False")
        pytester.runpytest("-q")

        assert list(user_cache.iterdir())
        assert not (pytester.path / "tox-env").exists()

    def test_local_policy_is_indistinguishable_from_the_default(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        """Writing `cache_policy = local` under tox still gets the legacy path.

        `local` is the default value, so there is nothing to tell an explicit
        setting apart from an absent one. The warning points at `cache_dir` for
        anyone who wants out.
        """
        monkeypatch.setenv("TOX_ENV_DIR", str(pytester.path / "tox-env"))
        pytester.makeini("[pytest]\ncache_policy = local\n")
        pytester.makepyfile(test_a="def test_bad(): assert False")
        pytester.runpytest("-q", "-W", "ignore::pytest.PytestRemovedIn10Warning")
        assert (pytester.path / "tox-env" / ".pytest_cache").is_dir()


def test_cache_reportheader_hidden_by_default(pytester: Pytester) -> None:
    pytester.makepyfile("""def test_foo(): pass""")
    result = pytester.runpytest()
    result.stdout.no_fnmatch_line("cachedir:*")


def test_cache_reportheader_hidden_for_explicit_default(pytester: Pytester) -> None:
    """Setting cache_dir to the default explicitly is still the default.

    The check compares the resolved path, rather than the configured string
    against a hardcoded ".pytest_cache".
    """
    pytester.makepyfile("""def test_foo(): pass""")
    pytester.makeini("[pytest]\ncache_dir = .pytest_cache\n")
    result = pytester.runpytest()
    result.stdout.no_fnmatch_line("cachedir:*")


def test_cache_reportheader_user_policy(
    pytester: Pytester, monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PYTEST_CACHE_HOME", str(tmp_path / "user-cache"))
    pytester.makepyfile("""def test_foo(): pass""")
    pytester.makeini("[pytest]\ncache_policy = user\n")
    result = pytester.runpytest("-v")
    # Outside the rootdir, so shown as an absolute path (#3745).
    result.stdout.fnmatch_lines([f"cachedir: {tmp_path / 'user-cache'}*"])


def test_cache_reportheader_hyperlinked(
    pytester: Pytester, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setenv("PY_COLORS", "1")
    monkeypatch.setenv("PYTEST_HYPERLINKS", "1")
    pytester.makepyfile("""def test_foo(): pass""")
    result = pytester.runpytest_subprocess("-v")
    result.stdout.fnmatch_lines(["*\x1b]8;;file://*.pytest_cache*"])


def test_cache_reportheader_external_abspath(
    pytester: Pytester, tmp_path_factory: TempPathFactory
) -> None:
    external_cache = tmp_path_factory.mktemp(
        "test_cache_reportheader_external_abspath_abs"
    )

    pytester.makepyfile("def test_hello(): pass")
    pytester.makeini(
        f"""
    [pytest]
    cache_dir = {external_cache}
    """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines([f"cachedir: {external_cache}"])


def test_cache_show(pytester: Pytester) -> None:
    result = pytester.runpytest("--cache-show")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*cache is empty*"])
    pytester.makeconftest(
        """
        def pytest_configure(config):
            config.cache.set("my/name", [1,2,3])
            config.cache.set("my/hello", "world")
            config.cache.set("other/some", {1:2})
            dp = config.cache.mkdir("mydb")
            dp.joinpath("hello").touch()
            dp.joinpath("world").touch()
    """
    )
    result = pytester.runpytest()
    assert result.ret == 5  # no tests executed

    result = pytester.runpytest("--cache-show")
    result.stdout.fnmatch_lines(
        [
            "*cachedir:*",
            "*- cache values for '[*]' -*",
            "my/name contains:",
            "  [1, 2, 3]",
            "other/some contains:",
            "  {*'1': 2}",
            # Env-scoped values are listed after the shared ones, tagged with
            # the scope they belong to.
            "cache/nodeids (env-*) contains:",
            "*- cache directories for '[*]' -*",
            "*mydb/hello*length 0*",
            "*mydb/world*length 0*",
        ]
    )
    assert result.ret == 0

    result = pytester.runpytest("--cache-show", "*/hello")
    result.stdout.fnmatch_lines(
        [
            "*cachedir:*",
            "*- cache values for '[*]/hello' -*",
            "my/hello contains:",
            "  *'world'",
            "*- cache directories for '[*]/hello' -*",
            "d/mydb/hello*length 0*",
        ]
    )
    stdout = result.stdout.str()
    assert "other/some" not in stdout
    assert "d/mydb/world" not in stdout
    assert result.ret == 0


class TestLastFailed:
    def test_lastfailed_usecase(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.dont_write_bytecode", True)
        p = pytester.makepyfile(
            """
            def test_1(): assert 0
            def test_2(): assert 0
            def test_3(): assert 1
            """
        )
        result = pytester.runpytest(str(p))
        result.stdout.fnmatch_lines(["*2 failed*"])
        p = pytester.makepyfile(
            """
            def test_1(): assert 1
            def test_2(): assert 1
            def test_3(): assert 0
            """
        )
        result = pytester.runpytest(str(p), "--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 3 items / 1 deselected / 2 selected",
                "run-last-failure: rerun previous 2 failures",
                "*= 2 passed, 1 deselected in *",
            ]
        )
        result = pytester.runpytest(str(p), "--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 3 items",
                "run-last-failure: no previously failed tests, not deselecting items.",
                "*1 failed*2 passed*",
            ]
        )
        pytester.path.joinpath(".pytest_cache", ".git").mkdir(parents=True)
        result = pytester.runpytest(str(p), "--lf", "--cache-clear")
        result.stdout.fnmatch_lines(["*1 failed*2 passed*"])
        assert pytester.path.joinpath(".pytest_cache", "README.md").is_file()
        assert pytester.path.joinpath(".pytest_cache", ".git").is_dir()

        # Run this again to make sure clear-cache is robust
        if os.path.isdir(".pytest_cache"):
            shutil.rmtree(".pytest_cache")
        result = pytester.runpytest("--lf", "--cache-clear")
        result.stdout.fnmatch_lines(["*1 failed*2 passed*"])

    def test_failedfirst_order(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            test_a="def test_always_passes(): pass",
            test_b="def test_always_fails(): assert 0",
        )
        result = pytester.runpytest()
        # Test order will be collection order; alphabetical
        result.stdout.fnmatch_lines(["test_a.py*", "test_b.py*"])
        result = pytester.runpytest("--ff")
        # Test order will be failing tests first
        result.stdout.fnmatch_lines(
            [
                "collected 2 items",
                "run-last-failure: rerun previous 1 failure first",
                "test_b.py*",
                "test_a.py*",
            ]
        )

    def test_lastfailed_failedfirst_order(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            test_a="def test_always_passes(): assert 1",
            test_b="def test_always_fails(): assert 0",
        )
        result = pytester.runpytest()
        # Test order will be collection order; alphabetical
        result.stdout.fnmatch_lines(["test_a.py*", "test_b.py*"])
        result = pytester.runpytest("--lf", "--ff")
        # Test order will be failing tests first
        result.stdout.fnmatch_lines(["test_b.py*"])
        result.stdout.no_fnmatch_line("*test_a.py*")

    def test_lastfailed_difference_invocations(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.dont_write_bytecode", True)
        pytester.makepyfile(
            test_a="""
                def test_a1(): assert 0
                def test_a2(): assert 1
            """,
            test_b="def test_b1(): assert 0",
        )
        p = pytester.path.joinpath("test_a.py")
        p2 = pytester.path.joinpath("test_b.py")

        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*2 failed*"])
        result = pytester.runpytest("--lf", p2)
        result.stdout.fnmatch_lines(["*1 failed*"])

        pytester.makepyfile(test_b="def test_b1(): assert 1")
        result = pytester.runpytest("--lf", p2)
        result.stdout.fnmatch_lines(["*1 passed*"])
        result = pytester.runpytest("--lf", p)
        result.stdout.fnmatch_lines(
            [
                "collected 2 items / 1 deselected / 1 selected",
                "run-last-failure: rerun previous 1 failure",
                "*= 1 failed, 1 deselected in *",
            ]
        )

    def test_lastfailed_usecase_splice(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.dont_write_bytecode", True)
        pytester.makepyfile(
            "def test_1(): assert 0", test_something="def test_2(): assert 0"
        )
        p2 = pytester.path.joinpath("test_something.py")
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*2 failed*"])
        result = pytester.runpytest("--lf", p2)
        result.stdout.fnmatch_lines(["*1 failed*"])
        result = pytester.runpytest("--lf")
        result.stdout.fnmatch_lines(["*2 failed*"])

    def test_lastfailed_xpass(self, pytester: Pytester) -> None:
        pytester.inline_runsource(
            """
            import pytest
            @pytest.mark.xfail
            def test_hello():
                assert 1
        """
        )
        config = pytester.parseconfigure()
        assert config.cache is not None
        lastfailed = config.cache.get("cache/lastfailed", -1, scope=CacheScope.ENV)
        assert lastfailed == -1

    def test_non_serializable_parametrize(self, pytester: Pytester) -> None:
        """Test that failed parametrized tests with unmarshable parameters
        don't break pytest-cache.
        """
        pytester.makepyfile(
            r"""
            import pytest

            @pytest.mark.parametrize('val', [
                b'\xac\x10\x02G',
            ])
            def test_fail(val):
                assert False
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*1 failed in*"])

    @pytest.mark.parametrize("parent", ("directory", "package"))
    def test_terminal_report_lastfailed(self, pytester: Pytester, parent: str) -> None:
        if parent == "package":
            pytester.makepyfile(
                __init__="",
            )

        test_a = pytester.makepyfile(
            test_a="""
            def test_a1(): pass
            def test_a2(): pass
        """
        )
        test_b = pytester.makepyfile(
            test_b="""
            def test_b1(): assert 0
            def test_b2(): assert 0
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["collected 4 items", "*2 failed, 2 passed in*"])

        result = pytester.runpytest("--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 2 items",
                "run-last-failure: rerun previous 2 failures (skipped 1 file)",
                "*2 failed in*",
            ]
        )

        result = pytester.runpytest(test_a, "--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 2 items",
                "run-last-failure: 2 known failures not in selected tests",
                "*2 passed in*",
            ]
        )

        result = pytester.runpytest(test_b, "--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 2 items",
                "run-last-failure: rerun previous 2 failures",
                "*2 failed in*",
            ]
        )

        result = pytester.runpytest("test_b.py::test_b1", "--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 1 item",
                "run-last-failure: rerun previous 1 failure",
                "*1 failed in*",
            ]
        )

    def test_terminal_report_failedfirst(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            test_a="""
            def test_a1(): assert 0
            def test_a2(): pass
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["collected 2 items", "*1 failed, 1 passed in*"])

        result = pytester.runpytest("--ff")
        result.stdout.fnmatch_lines(
            [
                "collected 2 items",
                "run-last-failure: rerun previous 1 failure first",
                "*1 failed, 1 passed in*",
            ]
        )

    def test_lastfailed_collectfailure(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        pytester.makepyfile(
            test_maybe="""
            import os
            env = os.environ
            if '1' == env['FAILIMPORT']:
                raise ImportError('fail')
            def test_hello():
                assert '0' == env['FAILTEST']
        """
        )

        def rlf(fail_import: int, fail_run: int) -> Any:
            monkeypatch.setenv("FAILIMPORT", str(fail_import))
            monkeypatch.setenv("FAILTEST", str(fail_run))

            pytester.runpytest("-q")
            config = pytester.parseconfigure()
            assert config.cache is not None
            lastfailed = config.cache.get("cache/lastfailed", -1, scope=CacheScope.ENV)
            return lastfailed

        lastfailed = rlf(fail_import=0, fail_run=0)
        assert lastfailed == -1

        lastfailed = rlf(fail_import=1, fail_run=0)
        assert list(lastfailed) == ["test_maybe.py"]

        lastfailed = rlf(fail_import=0, fail_run=1)
        assert list(lastfailed) == ["test_maybe.py::test_hello"]

    def test_lastfailed_failure_subset(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        pytester.makepyfile(
            test_maybe="""
            import os
            env = os.environ
            if '1' == env['FAILIMPORT']:
                raise ImportError('fail')
            def test_hello():
                assert '0' == env['FAILTEST']
        """
        )

        pytester.makepyfile(
            test_maybe2="""
            import os
            env = os.environ
            if '1' == env['FAILIMPORT']:
                raise ImportError('fail')

            def test_hello():
                assert '0' == env['FAILTEST']

            def test_pass():
                pass
        """
        )

        def rlf(
            fail_import: int, fail_run: int, args: Sequence[str] = ()
        ) -> tuple[Any, Any]:
            monkeypatch.setenv("FAILIMPORT", str(fail_import))
            monkeypatch.setenv("FAILTEST", str(fail_run))

            result = pytester.runpytest("-q", "--lf", *args)
            config = pytester.parseconfigure()
            assert config.cache is not None
            lastfailed = config.cache.get("cache/lastfailed", -1, scope=CacheScope.ENV)
            return result, lastfailed

        result, lastfailed = rlf(fail_import=0, fail_run=0)
        assert lastfailed == -1
        result.stdout.fnmatch_lines(["*3 passed*"])

        result, lastfailed = rlf(fail_import=1, fail_run=0)
        assert sorted(list(lastfailed)) == ["test_maybe.py", "test_maybe2.py"]

        result, lastfailed = rlf(fail_import=0, fail_run=0, args=("test_maybe2.py",))
        assert list(lastfailed) == ["test_maybe.py"]

        # edge case of test selection - even if we remember failures
        # from other tests we still need to run all tests if no test
        # matches the failures
        result, lastfailed = rlf(fail_import=0, fail_run=0, args=("test_maybe2.py",))
        assert list(lastfailed) == ["test_maybe.py"]
        result.stdout.fnmatch_lines(["*2 passed*"])

    def test_lastfailed_creates_cache_when_needed(self, pytester: Pytester) -> None:
        # Issue #1342
        lastfailed = env_scope_values() / "cache" / "lastfailed"

        pytester.makepyfile(test_empty="")
        pytester.runpytest("-q", "--lf")
        assert not lastfailed.exists()

        pytester.makepyfile(test_successful="def test_success():\n    assert True")
        pytester.runpytest("-q", "--lf")
        assert not lastfailed.exists()

        pytester.makepyfile(test_errored="def test_error():\n    assert False")
        pytester.runpytest("-q", "--lf")
        assert lastfailed.exists()

    def test_xfail_not_considered_failure(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest
            @pytest.mark.xfail
            def test(): assert 0
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*1 xfailed*"])
        assert self.get_cached_last_failed(pytester) == []

    def test_xfail_strict_considered_failure(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest
            @pytest.mark.xfail(strict=True)
            def test(): pass
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*1 failed*"])
        assert self.get_cached_last_failed(pytester) == [
            "test_xfail_strict_considered_failure.py::test"
        ]

    @pytest.mark.parametrize("mark", ["mark.xfail", "mark.skip"])
    def test_failed_changed_to_xfail_or_skip(
        self, pytester: Pytester, mark: str
    ) -> None:
        pytester.makepyfile(
            """
            import pytest
            def test(): assert 0
        """
        )
        result = pytester.runpytest()
        assert self.get_cached_last_failed(pytester) == [
            "test_failed_changed_to_xfail_or_skip.py::test"
        ]
        assert result.ret == 1

        pytester.makepyfile(
            f"""
            import pytest
            @pytest.{mark}
            def test(): assert 0
        """
        )
        result = pytester.runpytest()
        assert result.ret == 0
        assert self.get_cached_last_failed(pytester) == []
        assert result.ret == 0

    @pytest.mark.parametrize("quiet", [True, False])
    @pytest.mark.parametrize("opt", ["--ff", "--lf"])
    def test_lf_and_ff_prints_no_needless_message(
        self, quiet: bool, opt: str, pytester: Pytester
    ) -> None:
        # Issue 3853
        pytester.makepyfile("def test(): assert 0")
        args = [opt]
        if quiet:
            args.append("-q")
        result = pytester.runpytest(*args)
        result.stdout.no_fnmatch_line("*run all*")

        result = pytester.runpytest(*args)
        if quiet:
            result.stdout.no_fnmatch_line("*run all*")
        else:
            assert "rerun previous" in result.stdout.str()

    def get_cached_last_failed(self, pytester: Pytester) -> list[str]:
        config = pytester.parseconfigure()
        assert config.cache is not None
        return sorted(config.cache.get("cache/lastfailed", {}, scope=CacheScope.ENV))

    def test_cache_cumulative(self, pytester: Pytester) -> None:
        """Test workflow where user fixes errors gradually file by file using --lf."""
        # 1. initial run
        test_bar = pytester.makepyfile(
            test_bar="""
            def test_bar_1(): pass
            def test_bar_2(): assert 0
        """
        )
        test_foo = pytester.makepyfile(
            test_foo="""
            def test_foo_3(): pass
            def test_foo_4(): assert 0
        """
        )
        pytester.runpytest()
        assert self.get_cached_last_failed(pytester) == [
            "test_bar.py::test_bar_2",
            "test_foo.py::test_foo_4",
        ]

        # 2. fix test_bar_2, run only test_bar.py
        pytester.makepyfile(
            test_bar="""
            def test_bar_1(): pass
            def test_bar_2(): pass
        """
        )
        result = pytester.runpytest(test_bar)
        result.stdout.fnmatch_lines(["*2 passed*"])
        # ensure cache does not forget that test_foo_4 failed once before
        assert self.get_cached_last_failed(pytester) == ["test_foo.py::test_foo_4"]

        result = pytester.runpytest("--last-failed")
        result.stdout.fnmatch_lines(
            [
                "collected 1 item",
                "run-last-failure: rerun previous 1 failure (skipped 1 file)",
                "*= 1 failed in *",
            ]
        )
        assert self.get_cached_last_failed(pytester) == ["test_foo.py::test_foo_4"]

        # 3. fix test_foo_4, run only test_foo.py
        test_foo = pytester.makepyfile(
            test_foo="""
            def test_foo_3(): pass
            def test_foo_4(): pass
        """
        )
        result = pytester.runpytest(test_foo, "--last-failed")
        result.stdout.fnmatch_lines(
            [
                "collected 2 items / 1 deselected / 1 selected",
                "run-last-failure: rerun previous 1 failure",
                "*= 1 passed, 1 deselected in *",
            ]
        )
        assert self.get_cached_last_failed(pytester) == []

        result = pytester.runpytest("--last-failed")
        result.stdout.fnmatch_lines(["*4 passed*"])
        assert self.get_cached_last_failed(pytester) == []

    def test_lastfailed_no_failures_behavior_all_passed(
        self, pytester: Pytester
    ) -> None:
        pytester.makepyfile(
            """
            def test_1(): pass
            def test_2(): pass
        """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*2 passed*"])
        result = pytester.runpytest("--lf")
        result.stdout.fnmatch_lines(["*2 passed*"])
        result = pytester.runpytest("--lf", "--lfnf", "all")
        result.stdout.fnmatch_lines(["*2 passed*"])

        # Ensure the list passed to pytest_deselected is a copy,
        # and not a reference which is cleared right after.
        pytester.makeconftest(
            """
            deselected = []

            def pytest_deselected(items):
                global deselected
                deselected = items

            def pytest_sessionfinish():
                print("\\ndeselected={}".format(len(deselected)))
        """
        )

        result = pytester.runpytest("--lf", "--lfnf", "none")
        result.stdout.fnmatch_lines(
            [
                "collected 2 items / 2 deselected / 0 selected",
                "run-last-failure: no previously failed tests, deselecting all items.",
                "deselected=2",
                "* 2 deselected in *",
            ]
        )
        assert result.ret == ExitCode.NO_TESTS_COLLECTED

    def test_lastfailed_no_failures_behavior_empty_cache(
        self, pytester: Pytester
    ) -> None:
        pytester.makepyfile(
            """
            def test_1(): pass
            def test_2(): assert 0
        """
        )
        result = pytester.runpytest("--lf", "--cache-clear")
        result.stdout.fnmatch_lines(["*1 failed*1 passed*"])
        result = pytester.runpytest("--lf", "--cache-clear", "--lfnf", "all")
        result.stdout.fnmatch_lines(["*1 failed*1 passed*"])
        result = pytester.runpytest("--lf", "--cache-clear", "--lfnf", "none")
        result.stdout.fnmatch_lines(["*2 desel*"])

    def test_lastfailed_skip_collection(self, pytester: Pytester) -> None:
        """
        Test --lf behavior regarding skipping collection of files that are not marked as
        failed in the cache (#5172).
        """
        pytester.makepyfile(
            **{
                "pkg1/test_1.py": """
                import pytest

                @pytest.mark.parametrize('i', range(3))
                def test_1(i): pass
            """,
                "pkg2/test_2.py": """
                import pytest

                @pytest.mark.parametrize('i', range(5))
                def test_1(i):
                    assert i not in (1, 3)
            """,
            }
        )
        # first run: collects 8 items (test_1: 3, test_2: 5)
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["collected 8 items", "*2 failed*6 passed*"])
        # second run: collects only 5 items from test_2, because all tests from test_1 have passed
        result = pytester.runpytest("--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 2 items",
                "run-last-failure: rerun previous 2 failures (skipped 1 file)",
                "*= 2 failed in *",
            ]
        )

        # add another file and check if message is correct when skipping more than 1 file
        pytester.makepyfile(
            **{
                "pkg1/test_3.py": """
                def test_3(): pass
            """
            }
        )
        result = pytester.runpytest("--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 2 items",
                "run-last-failure: rerun previous 2 failures (skipped 2 files)",
                "*= 2 failed in *",
            ]
        )

    def test_lastfailed_skip_collection_with_nesting(self, pytester: Pytester) -> None:
        """Check that file skipping works even when the file with failures is
        nested at a different level of the collection tree."""
        pytester.makepyfile(
            **{
                "test_1.py": """
                    def test_1(): pass
                """,
                "pkg/__init__.py": "",
                "pkg/test_2.py": """
                    def test_2(): assert False
                """,
            }
        )
        # first run
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["collected 2 items", "*1 failed*1 passed*"])
        # second run - test_1.py is skipped.
        result = pytester.runpytest("--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 1 item",
                "run-last-failure: rerun previous 1 failure (skipped 1 file)",
                "*= 1 failed in *",
            ]
        )

    def test_lastfailed_with_known_failures_not_being_selected(
        self, pytester: Pytester
    ) -> None:
        pytester.makepyfile(
            **{
                "pkg1/test_1.py": """def test_1(): assert 0""",
                "pkg1/test_2.py": """def test_2(): pass""",
            }
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["collected 2 items", "* 1 failed, 1 passed in *"])

        Path("pkg1/test_1.py").unlink()
        result = pytester.runpytest("--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 1 item",
                "run-last-failure: 1 known failures not in selected tests",
                "* 1 passed in *",
            ]
        )

        # Recreate file with known failure.
        pytester.makepyfile(**{"pkg1/test_1.py": """def test_1(): assert 0"""})
        result = pytester.runpytest("--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 1 item",
                "run-last-failure: rerun previous 1 failure (skipped 1 file)",
                "* 1 failed in *",
            ]
        )

        # Remove/rename test: collects the file again.
        pytester.makepyfile(**{"pkg1/test_1.py": """def test_renamed(): assert 0"""})
        result = pytester.runpytest("--lf", "-rf")
        result.stdout.fnmatch_lines(
            [
                "collected 2 items",
                "run-last-failure: 1 known failures not in selected tests",
                "pkg1/test_1.py F *",
                "pkg1/test_2.py . *",
                "FAILED pkg1/test_1.py::test_renamed - assert 0",
                "* 1 failed, 1 passed in *",
            ]
        )

        result = pytester.runpytest("--lf", "--co")
        result.stdout.fnmatch_lines(
            [
                "collected 1 item",
                "run-last-failure: rerun previous 1 failure (skipped 1 file)",
                "",
                "<Dir *>",
                "  <Dir pkg1>",
                "    <Module test_1.py>",
                "      <Function test_renamed>",
            ]
        )

    def test_lastfailed_args_with_deselected(self, pytester: Pytester) -> None:
        """Test regression with --lf running into NoMatch error.

        This was caused by it not collecting (non-failed) nodes given as
        arguments.
        """
        pytester.makepyfile(
            **{
                "pkg1/test_1.py": """
                    def test_pass(): pass
                    def test_fail(): assert 0
                """,
            }
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["collected 2 items", "* 1 failed, 1 passed in *"])
        assert result.ret == 1

        result = pytester.runpytest("pkg1/test_1.py::test_pass", "--lf", "--co")
        assert result.ret == 0
        result.stdout.fnmatch_lines(
            [
                "*collected 1 item",
                "run-last-failure: 1 known failures not in selected tests",
                "",
                "<Dir *>",
                "  <Dir pkg1>",
                "    <Module test_1.py>",
                "      <Function test_pass>",
            ],
            consecutive=True,
        )

        result = pytester.runpytest(
            "pkg1/test_1.py::test_pass", "pkg1/test_1.py::test_fail", "--lf", "--co"
        )
        assert result.ret == 0
        result.stdout.fnmatch_lines(
            [
                "collected 2 items / 1 deselected / 1 selected",
                "run-last-failure: rerun previous 1 failure",
                "",
                "<Dir *>",
                "  <Dir pkg1>",
                "    <Module test_1.py>",
                "      <Function test_fail>",
                "*= 1/2 tests collected (1 deselected) in *",
            ],
        )

    def test_lastfailed_with_class_items(self, pytester: Pytester) -> None:
        """Test regression with --lf deselecting whole classes."""
        pytester.makepyfile(
            **{
                "pkg1/test_1.py": """
                    class TestFoo:
                        def test_pass(self): pass
                        def test_fail(self): assert 0

                    def test_other(): assert 0
                """,
            }
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["collected 3 items", "* 2 failed, 1 passed in *"])
        assert result.ret == 1

        result = pytester.runpytest("--lf", "--co")
        assert result.ret == 0
        result.stdout.fnmatch_lines(
            [
                "collected 3 items / 1 deselected / 2 selected",
                "run-last-failure: rerun previous 2 failures",
                "",
                "<Dir *>",
                "  <Dir pkg1>",
                "    <Module test_1.py>",
                "      <Class TestFoo>",
                "        <Function test_fail>",
                "      <Function test_other>",
                "",
                "*= 2/3 tests collected (1 deselected) in *",
            ],
            consecutive=True,
        )

    def test_lastfailed_with_all_filtered(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            **{
                "pkg1/test_1.py": """
                    def test_fail(): assert 0
                    def test_pass(): pass
                """,
            }
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["collected 2 items", "* 1 failed, 1 passed in *"])
        assert result.ret == 1

        # Remove known failure.
        pytester.makepyfile(
            **{
                "pkg1/test_1.py": """
                    def test_pass(): pass
                """,
            }
        )
        result = pytester.runpytest("--lf", "--co")
        result.stdout.fnmatch_lines(
            [
                "collected 1 item",
                "run-last-failure: 1 known failures not in selected tests",
                "",
                "<Dir *>",
                "  <Dir pkg1>",
                "    <Module test_1.py>",
                "      <Function test_pass>",
                "",
                "*= 1 test collected in*",
            ],
            consecutive=True,
        )
        assert result.ret == 0

    def test_packages(self, pytester: Pytester) -> None:
        """Regression test for #7758.

        The particular issue here was that Package nodes were included in the
        filtering, being themselves Modules for the __init__.py, even if they
        had failed Modules in them.

        The tests includes a test in an __init__.py file just to make sure the
        fix doesn't somehow regress that, it is not critical for the issue.
        """
        pytester.makepyfile(
            **{
                "__init__.py": "",
                "a/__init__.py": "def test_a_init(): assert False",
                "a/test_one.py": "def test_1(): assert False",
                "b/__init__.py": "",
                "b/test_two.py": "def test_2(): assert False",
            },
        )
        pytester.makeini(
            """
            [pytest]
            python_files = *.py
            """
        )
        result = pytester.runpytest()
        result.assert_outcomes(failed=3)
        result = pytester.runpytest("--lf")
        result.assert_outcomes(failed=3)

    def test_non_python_file_skipped(
        self,
        pytester: Pytester,
        dummy_yaml_custom_test: None,
    ) -> None:
        pytester.makepyfile(
            **{
                "test_bad.py": """def test_bad(): assert False""",
            },
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["collected 2 items", "* 1 failed, 1 passed in *"])

        result = pytester.runpytest("--lf")
        result.stdout.fnmatch_lines(
            [
                "collected 1 item",
                "run-last-failure: rerun previous 1 failure (skipped 1 file)",
                "* 1 failed in *",
            ]
        )


class TestNewFirst:
    def test_newfirst_usecase(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            **{
                "test_1/test_1.py": """
                def test_1(): assert 1
            """,
                "test_2/test_2.py": """
                def test_1(): assert 1
            """,
            }
        )

        p1 = pytester.path.joinpath("test_1/test_1.py")
        os.utime(p1, ns=(p1.stat().st_atime_ns, int(1e9)))

        result = pytester.runpytest("-v")
        result.stdout.fnmatch_lines(
            ["*test_1/test_1.py::test_1 PASSED*", "*test_2/test_2.py::test_1 PASSED*"]
        )

        result = pytester.runpytest("-v", "--nf")
        result.stdout.fnmatch_lines(
            ["*test_2/test_2.py::test_1 PASSED*", "*test_1/test_1.py::test_1 PASSED*"]
        )

        p1.write_text(
            "def test_1(): assert 1\ndef test_2(): assert 1\n", encoding="utf-8"
        )
        os.utime(p1, ns=(p1.stat().st_atime_ns, int(1e9)))

        result = pytester.runpytest("--nf", "--collect-only", "-q")
        result.stdout.fnmatch_lines(
            [
                "test_1/test_1.py::test_2",
                "test_2/test_2.py::test_1",
                "test_1/test_1.py::test_1",
            ]
        )

        # Newest first with (plugin) pytest_collection_modifyitems hook.
        pytester.makepyfile(
            myplugin="""
            def pytest_collection_modifyitems(items):
                items[:] = sorted(items, key=lambda item: item.nodeid)
                print("new_items:", [x.nodeid for x in items])
            """
        )
        pytester.syspathinsert()
        result = pytester.runpytest("--nf", "-p", "myplugin", "--collect-only", "-q")
        result.stdout.fnmatch_lines(
            [
                "new_items: *test_1.py*test_1.py*test_2.py*",
                "test_1/test_1.py::test_2",
                "test_2/test_2.py::test_1",
                "test_1/test_1.py::test_1",
            ]
        )

    def test_newfirst_parametrize(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            **{
                "test_1/test_1.py": """
                import pytest
                @pytest.mark.parametrize('num', [1, 2])
                def test_1(num): assert num
            """,
                "test_2/test_2.py": """
                import pytest
                @pytest.mark.parametrize('num', [1, 2])
                def test_1(num): assert num
            """,
            }
        )

        p1 = pytester.path.joinpath("test_1/test_1.py")
        os.utime(p1, ns=(p1.stat().st_atime_ns, int(1e9)))

        result = pytester.runpytest("-v")
        result.stdout.fnmatch_lines(
            [
                "*test_1/test_1.py::test_1[1*",
                "*test_1/test_1.py::test_1[2*",
                "*test_2/test_2.py::test_1[1*",
                "*test_2/test_2.py::test_1[2*",
            ]
        )

        result = pytester.runpytest("-v", "--nf")
        result.stdout.fnmatch_lines(
            [
                "*test_2/test_2.py::test_1[1*",
                "*test_2/test_2.py::test_1[2*",
                "*test_1/test_1.py::test_1[1*",
                "*test_1/test_1.py::test_1[2*",
            ]
        )

        p1.write_text(
            "import pytest\n"
            "@pytest.mark.parametrize('num', [1, 2, 3])\n"
            "def test_1(num): assert num\n",
            encoding="utf-8",
        )
        os.utime(p1, ns=(p1.stat().st_atime_ns, int(1e9)))

        # Running only a subset does not forget about existing ones.
        result = pytester.runpytest("-v", "--nf", "test_2/test_2.py")
        result.stdout.fnmatch_lines(
            ["*test_2/test_2.py::test_1[1*", "*test_2/test_2.py::test_1[2*"]
        )

        result = pytester.runpytest("-v", "--nf")
        result.stdout.fnmatch_lines(
            [
                "*test_1/test_1.py::test_1[3*",
                "*test_2/test_2.py::test_1[1*",
                "*test_2/test_2.py::test_1[2*",
                "*test_1/test_1.py::test_1[1*",
                "*test_1/test_1.py::test_1[2*",
            ]
        )


class TestReadme:
    def check_readme(self, pytester: Pytester) -> bool:
        config = pytester.parseconfigure()
        assert config.cache is not None
        readme = config.cache._cachedir.joinpath("README.md")
        return readme.is_file()

    def test_readme_passed(self, pytester: Pytester) -> None:
        pytester.makepyfile("def test_always_passes(): pass")
        pytester.runpytest()
        assert self.check_readme(pytester) is True

    def test_readme_failed(self, pytester: Pytester) -> None:
        pytester.makepyfile("def test_always_fails(): assert 0")
        pytester.runpytest()
        assert self.check_readme(pytester) is True


class Action(Enum):
    """Action to perform on the cache directory."""

    MKDIR = auto()
    SET = auto()


@pytest.mark.parametrize("action", list(Action))
def test_gitignore(
    pytester: Pytester,
    action: Action,
) -> None:
    """Ensure we automatically create .gitignore file in the pytest_cache directory (#3286)."""
    from _pytest.cacheprovider import Cache

    config = pytester.parseconfig()
    cache = Cache.for_config(config, _ispytest=True)
    if action == Action.MKDIR:
        cache.mkdir("foo")
    elif action == Action.SET:
        cache.set("foo", "bar")
    else:
        assert_never(action)
    msg = "# Created by pytest automatically.\n*\n"
    gitignore_path = cache._cachedir.joinpath(".gitignore")
    assert gitignore_path.read_text(encoding="UTF-8") == msg

    # Does not overwrite existing/custom one.
    gitignore_path.write_text("custom", encoding="utf-8")
    if action == Action.MKDIR:
        cache.mkdir("something")
    elif action == Action.SET:
        cache.set("something", "else")
    else:
        assert_never(action)
    assert gitignore_path.read_text(encoding="UTF-8") == "custom"


def test_preserve_keys_order(pytester: Pytester) -> None:
    """Ensure keys order is preserved when saving dicts (#9205)."""
    from _pytest.cacheprovider import Cache

    config = pytester.parseconfig()
    cache = Cache.for_config(config, _ispytest=True)
    cache.set("foo", {"z": 1, "b": 2, "a": 3, "d": 10})
    read_back = cache.get("foo", None)
    assert list(read_back.items()) == [("z", 1), ("b", 2), ("a", 3), ("d", 10)]


def test_does_not_create_boilerplate_in_existing_dirs(pytester: Pytester) -> None:
    from _pytest.cacheprovider import Cache

    pytester.makeini(
        """
        [pytest]
        cache_dir = .
        """
    )
    config = pytester.parseconfig()
    cache = Cache.for_config(config, _ispytest=True)
    cache.set("foo", "bar")

    assert os.path.isdir("v")  # cache contents
    assert not os.path.exists(".gitignore")
    assert not os.path.exists("README.md")


def test_cachedir_tag(pytester: Pytester) -> None:
    """Ensure we automatically create CACHEDIR.TAG file in the pytest_cache directory (#4278)."""
    from _pytest.cacheprovider import Cache
    from _pytest.cacheprovider import CACHEDIR_FILES

    config = pytester.parseconfig()
    cache = Cache.for_config(config, _ispytest=True)
    cache.set("foo", "bar")
    cachedir_tag_path = cache._cachedir.joinpath("CACHEDIR.TAG")
    assert cachedir_tag_path.read_bytes() == CACHEDIR_FILES["CACHEDIR.TAG"]


class TestCachePolicy:
    @pytest.fixture
    def user_cache(self, monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
        root = tmp_path / "user-cache"
        monkeypatch.setenv("PYTEST_CACHE_HOME", str(root))
        return root

    def resolve(self, pytester: Pytester, **ini: str) -> Path:
        body = "".join(f"{k} = {v}\n" for k, v in ini.items())
        pytester.makeini(f"[pytest]\n{body}")
        return Cache.for_config(pytester.parseconfig(), _ispytest=True)._cachedir

    def test_local_is_the_default(self, pytester: Pytester) -> None:
        assert self.resolve(pytester) == pytester.path / ".pytest_cache"

    def test_user_policy(self, pytester: Pytester, user_cache: Path) -> None:
        cachedir = self.resolve(pytester, cache_policy="user")
        assert cachedir.parent == user_cache
        assert cachedir.name.startswith(f"{pytester.path.name}-")

    def test_cache_dir_wins_over_policy(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        cachedir = self.resolve(pytester, cache_policy="user", cache_dir="explicit")
        assert cachedir == pytester.path / "explicit"

    def test_unknown_policy_is_a_usage_error(self, pytester: Pytester) -> None:
        pytester.makeini("[pytest]\ncache_policy = bogus\n")
        pytester.makepyfile(test_a="def test_ok(): pass")
        result = pytester.runpytest()
        assert result.ret == ExitCode.USAGE_ERROR
        result.stderr.fnmatch_lines(["*cache_policy*expects one of*got 'bogus'*"])

    def test_env_var_sets_the_default(
        self, pytester: Pytester, user_cache: Path, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PYTEST_CACHE_POLICY", "user")
        assert self.resolve(pytester).parent == user_cache

    def test_explicit_setting_beats_the_env_var(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PYTEST_CACHE_POLICY", "user")
        assert self.resolve(pytester, cache_policy="local") == (
            pytester.path / ".pytest_cache"
        )

    def test_project_key_is_stable(self, pytester: Pytester, user_cache: Path) -> None:
        first = self.resolve(pytester, cache_policy="user")
        second = self.resolve(pytester, cache_policy="user")
        assert first == second
        assert re.fullmatch(r"[A-Za-z0-9._-]{1,32}-[0-9a-f]{16}", first.name)

    def test_project_key_ignores_the_environment(
        self, pytester: Pytester, user_cache: Path, monkeypatch: MonkeyPatch
    ) -> None:
        # The whole point of scopes: one project gets one directory, however
        # many interpreters run it.
        before = self.resolve(pytester, cache_policy="user")
        monkeypatch.setattr(sys, "prefix", "/somewhere/else")
        monkeypatch.setattr(sys, "version_info", (9, 9, 9))
        assert self.resolve(pytester, cache_policy="user") == before

    def test_project_key_resolves_symlinks(
        self, pytester: Pytester, user_cache: Path, tmp_path: Path
    ) -> None:
        real = self.resolve(pytester, cache_policy="user")

        link = tmp_path / "link"
        symlink_or_skip(pytester.path, link)
        pytester.makeini("[pytest]\ncache_policy = user\n")
        config = pytester.parseconfig(f"--rootdir={link}", str(link))
        assert Cache.for_config(config, _ispytest=True)._cachedir == real

    def test_project_key_collision_extends_the_name(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        cachedir = self.resolve(pytester, cache_policy="user")
        # Squat the short name with a directory belonging to something else.
        cachedir.mkdir(parents=True)
        (cachedir / CACHE_INFO_NAME).write_text(
            json.dumps({"schema": 1, "digest": "f" * 64}), encoding="UTF-8"
        )

        extended = self.resolve(pytester, cache_policy="user")
        assert extended != cachedir
        assert extended.name.endswith(_project_digest(pytester.path)[:32])

    def test_user_policy_records_the_digest(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        cache = Cache.for_config(
            pytester.parseconfig("-o", "cache_policy=user"), _ispytest=True
        )
        cache.set("foo", 1)
        info = read_cache_info(cache._cachedir)
        assert info is not None
        assert info["policy"] == "user"
        assert info["digest"] == _project_digest(pytester.path)

    def test_user_policy_creates_nothing_when_unused(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        pytester.makeini("[pytest]\ncache_policy = user\n")
        pytester.makepyfile(test_a="def test_ok(): pass")
        pytester.runpytest("--collect-only")
        assert not user_cache.exists()

    def test_lastfailed_round_trips(self, pytester: Pytester, user_cache: Path) -> None:
        pytester.makeini("[pytest]\ncache_policy = user\n")
        pytester.makepyfile(
            test_a="def test_ok(): pass\ndef test_bad(): assert False\n"
        )
        pytester.runpytest("-q").assert_outcomes(passed=1, failed=1)
        assert not (pytester.path / ".pytest_cache").exists()

        result = pytester.runpytest("-q", "--lf")
        result.assert_outcomes(failed=1)

    def test_user_policy_without_platformdirs(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTEST_CACHE_HOME", raising=False)
        pytester.makeini("[pytest]\ncache_policy = user\n")
        pytester.makepyfile(test_a="def test_ok(): pass")
        pytester.syspathinsert()
        # Hide platformdirs from the inner run.
        pytester.makepyfile(platformdirs="raise ImportError('hidden')")

        result = pytester.runpytest_subprocess()
        assert result.ret == ExitCode.USAGE_ERROR
        result.stderr.fnmatch_lines(["*pip install pytest?xdg?*"])


class TestCacheList:
    @pytest.fixture
    def user_cache(self, monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
        root = tmp_path / "user-cache"
        monkeypatch.setenv("PYTEST_CACHE_HOME", str(root))
        return root

    def populate(self, pytester: Pytester, name: str) -> Path:
        """Run a failing test in a fresh project, returning its rootdir."""
        project = pytester.path / name
        project.mkdir()
        project.joinpath("test_x.py").write_text(
            "def test_bad(): assert False\n", encoding="UTF-8"
        )
        project.joinpath("tox.ini").write_text(
            "[pytest]\ncache_policy = user\n", encoding="UTF-8"
        )
        pytester.runpytest_subprocess(str(project), "--rootdir", str(project))
        return project

    def test_empty(self, pytester: Pytester, user_cache: Path) -> None:
        result = pytester.runpytest("--cache-list")
        assert result.ret == 0
        result.stdout.fnmatch_lines(
            [
                f"user cache directory: {user_cache}",
                "no managed cache directories found",
            ]
        )

    def test_lists_entries_with_scopes(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        project = self.populate(pytester, "alpha")

        result = pytester.runpytest("--cache-list")
        assert result.ret == 0
        result.stdout.fnmatch_lines(
            [
                "*DIRECTORY*SIZE*LAST USED*STATUS*ORIGIN*",
                f"  alpha-*  * ok  *{project}",
                "    env-*  *  ok  *",
                "1 directories, 1 scopes, * total",
            ]
        )

    def test_marks_orphaned_when_the_origin_is_gone(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        project = self.populate(pytester, "alpha")
        shutil.rmtree(project)

        result = pytester.runpytest("--cache-list")
        result.stdout.fnmatch_lines([f"  alpha-*orphaned*{project}"])

    def test_marks_scope_stale_when_the_env_is_gone(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        self.populate(pytester, "alpha")
        cachedir = next(user_cache.iterdir())
        info = json.loads((cachedir / CACHE_INFO_NAME).read_text(encoding="UTF-8"))
        for scope in info["scopes"].values():
            scope["prefix"] = str(pytester.path / "deleted-venv")
        (cachedir / CACHE_INFO_NAME).write_text(json.dumps(info), encoding="UTF-8")

        result = pytester.runpytest("--cache-list")
        # The directory itself stays fine; only the scope is collectable.
        result.stdout.fnmatch_lines(["  alpha-*  ok  *", "    env-*  stale  *"])

    @pytest.mark.parametrize("content", ["", "{not json", '{"schema": 99}'])
    def test_tolerates_unusable_metadata(
        self, pytester: Pytester, user_cache: Path, content: str
    ) -> None:
        # A directory we cannot understand must still be listed, or it becomes
        # invisible but undeletable.
        cachedir = user_cache / "mystery-0123456789abcdef"
        cachedir.mkdir(parents=True)
        if content:
            (cachedir / CACHE_INFO_NAME).write_text(content, encoding="UTF-8")

        result = pytester.runpytest("--cache-list")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["  mystery-*broken*"])

    def test_works_regardless_of_this_project_policy(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        # Listing must work after switching back to the local policy, or you
        # could never clean up what you left behind.
        self.populate(pytester, "alpha")
        pytester.makeini("[pytest]\ncache_policy = local\n")

        result = pytester.runpytest("--cache-list")
        result.stdout.fnmatch_lines(["  alpha-*"])

    def test_creates_nothing(self, pytester: Pytester, user_cache: Path) -> None:
        pytester.makeini("[pytest]\ncache_policy = user\n")
        pytester.makepyfile(test_a="def test_ok(): pass")
        pytester.runpytest("--cache-list")
        assert not user_cache.exists()

    def test_does_not_collect_or_run_tests(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        pytester.makepyfile(test_a="raise RuntimeError('should not be collected')")
        result = pytester.runpytest("--cache-list")
        assert result.ret == 0
        result.stdout.no_fnmatch_line("*RuntimeError*")

    def test_does_not_clobber_the_cache(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        """Listing must not rewrite the state being listed.

        LFPlugin/NFPlugin write on pytest_sessionfinish, which is why this
        command deliberately runs without a Session.
        """
        self.populate(pytester, "alpha")
        cachedir = next(user_cache.iterdir())
        lastfailed = next(cachedir.glob("s/*/v/cache/lastfailed"))
        before = lastfailed.read_bytes()

        pytester.runpytest("--cache-list")
        assert lastfailed.read_bytes() == before

    def test_with_help(self, pytester: Pytester, user_cache: Path) -> None:
        result = pytester.runpytest("--cache-list", "--help")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*--cache-list*"])

    def test_hyperlinks(
        self, pytester: Pytester, user_cache: Path, monkeypatch: MonkeyPatch
    ) -> None:
        project = self.populate(pytester, "alpha")
        # Pytester forces PY_COLORS=0 for inner runs, so ask explicitly.
        monkeypatch.setenv("PY_COLORS", "1")
        monkeypatch.setenv("PYTEST_HYPERLINKS", "1")

        result = pytester.runpytest_subprocess("--cache-list")
        assert result.ret == 0
        cachedir = next(user_cache.iterdir())
        stdout = result.stdout.str()
        assert f"\x1b]8;;{cachedir.as_uri()}\x1b\\" in stdout
        assert f"\x1b]8;;{project.as_uri()}\x1b\\" in stdout

    def test_no_hyperlinks_when_piped(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        self.populate(pytester, "alpha")
        result = pytester.runpytest_subprocess("--cache-list")
        assert "\x1b]8;;" not in result.stdout.str()


class TestCachePrune:
    @pytest.fixture
    def user_cache(self, monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
        root = tmp_path / "user-cache"
        monkeypatch.setenv("PYTEST_CACHE_HOME", str(root))
        return root

    def populate(self, pytester: Pytester, name: str) -> Path:
        project = pytester.path / name
        project.mkdir()
        project.joinpath("test_x.py").write_text(
            "def test_bad(): assert False\n", encoding="UTF-8"
        )
        project.joinpath("tox.ini").write_text(
            "[pytest]\ncache_policy = user\n", encoding="UTF-8"
        )
        pytester.runpytest_subprocess(str(project), "--rootdir", str(project))
        return project

    def names(self, user_cache: Path) -> set[str]:
        return {p.name for p in user_cache.iterdir()}

    def test_requires_a_selector(self, pytester: Pytester, user_cache: Path) -> None:
        # No default, so a bare invocation can never be destructive.
        result = pytester.runpytest("--cache-prune")
        assert result.ret == ExitCode.USAGE_ERROR
        result.stderr.fnmatch_lines(["*--cache-prune: expected one argument*"])

    def test_all(self, pytester: Pytester, user_cache: Path) -> None:
        self.populate(pytester, "alpha")
        self.populate(pytester, "beta")

        result = pytester.runpytest("--cache-prune=all")
        assert result.ret == ExitCode.OK
        result.stdout.fnmatch_lines(["removing alpha-*", "reclaimed *"])
        assert self.names(user_cache) == set()

    def test_all_skips_the_current_directory(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        self.populate(pytester, "alpha")
        pytester.makeini("[pytest]\ncache_policy = user\n")
        # Give this project a cache directory of its own to protect.
        pytester.makepyfile(test_a="def test_bad(): assert False")
        pytester.runpytest("-q")
        mine = _label(pytester.path.name)

        pytester.runpytest("--cache-prune=all")
        remaining = self.names(user_cache)
        assert not any(n.startswith("alpha-") for n in remaining)
        assert any(n.startswith(f"{mine}-") for n in remaining)

    def test_orphaned(self, pytester: Pytester, user_cache: Path) -> None:
        alpha = self.populate(pytester, "alpha")
        self.populate(pytester, "beta")
        shutil.rmtree(alpha)

        pytester.runpytest("--cache-prune=orphaned")
        assert not any(n.startswith("alpha-") for n in self.names(user_cache))
        assert any(n.startswith("beta-") for n in self.names(user_cache))

    def test_orphaned_removes_broken_directories(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        user_cache.mkdir(parents=True, exist_ok=True)
        (user_cache / "mystery-0123456789abcdef").mkdir()

        pytester.runpytest("--cache-prune=orphaned")
        assert self.names(user_cache) == set()

    def test_stale_removes_only_the_scope(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        self.populate(pytester, "alpha")
        cachedir = next(user_cache.iterdir())
        info = json.loads((cachedir / CACHE_INFO_NAME).read_text(encoding="UTF-8"))
        for scope in info["scopes"].values():
            scope["prefix"] = str(pytester.path / "deleted-venv")
        (cachedir / CACHE_INFO_NAME).write_text(json.dumps(info), encoding="UTF-8")

        result = pytester.runpytest("--cache-prune=stale")
        assert result.ret == ExitCode.OK
        result.stdout.fnmatch_lines(["removing alpha-*/env-*"])
        # The project's own cache directory survives; only the dead
        # environment's state goes.
        assert cachedir.is_dir()
        assert not list((cachedir / "s").iterdir())

    def test_stale_applies_to_the_current_project_too(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        """Self-exclusion must not block pruning your own stale scopes.

        It guards whole-directory removal; a stale scope can never be the one
        in use, since the running environment exists by definition - and
        clearing out a deleted virtualenv of the project you are standing in
        is the most likely reason to run this at all.
        """
        pytester.makeini("[pytest]\ncache_policy = user\n")
        pytester.makepyfile(test_a="def test_bad(): assert False")
        pytester.runpytest("-q")

        cachedir = next(user_cache.iterdir())
        info = json.loads((cachedir / CACHE_INFO_NAME).read_text(encoding="UTF-8"))
        for scope in info["scopes"].values():
            scope["prefix"] = str(pytester.path / "deleted-venv")
        (cachedir / CACHE_INFO_NAME).write_text(json.dumps(info), encoding="UTF-8")

        result = pytester.runpytest("--cache-prune=stale")
        result.stdout.fnmatch_lines(["removing *env-*"])
        assert cachedir.is_dir()
        assert not list((cachedir / "s").iterdir())

    def test_glob_matches_name_or_origin(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        self.populate(pytester, "alpha")
        self.populate(pytester, "beta")

        pytester.runpytest("--cache-prune=alpha-*")
        assert not any(n.startswith("alpha-") for n in self.names(user_cache))
        assert any(n.startswith("beta-") for n in self.names(user_cache))

        pytester.runpytest(f"--cache-prune={pytester.path}/beta")
        assert self.names(user_cache) == set()

    def test_selectors_are_repeatable(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        self.populate(pytester, "alpha")
        self.populate(pytester, "beta")
        self.populate(pytester, "gamma")

        pytester.runpytest("--cache-prune=alpha-*", "--cache-prune=beta-*")
        assert {n.split("-")[0] for n in self.names(user_cache)} == {"gamma"}

    def test_no_match_removes_nothing(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        self.populate(pytester, "alpha")
        result = pytester.runpytest("--cache-prune=nothing-matches-this")
        assert result.ret == ExitCode.OK
        assert any(n.startswith("alpha-") for n in self.names(user_cache))

    def test_does_not_clobber_the_cache(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        """Pruning must not rewrite the caches it leaves alone.

        The direct regression test for the LFPlugin/NFPlugin sessionfinish
        hazard: a no-match prune has to be a complete no-op.
        """
        project = self.populate(pytester, "alpha")
        cachedir = next(user_cache.iterdir())
        values = {
            p: p.read_bytes() for p in cachedir.glob("s/*/v/cache/*") if p.is_file()
        }
        assert values

        pytester.runpytest("--cache-prune=nothing-matches-this")
        assert {p: p.read_bytes() for p in values} == values

        # ... and --lf still works afterwards.
        result = pytester.runpytest_subprocess(
            str(project), "--rootdir", str(project), "--lf", "-v"
        )
        result.stdout.fnmatch_lines(["*rerun previous 1 failure*"])

    def test_with_help(self, pytester: Pytester, user_cache: Path) -> None:
        result = pytester.runpytest("--cache-prune=all", "--help")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*--cache-prune*"])

    @pytest.mark.skipif(sys.platform == "win32", reason="no chmod on win32")
    def test_reports_failures_and_continues(
        self, pytester: Pytester, user_cache: Path
    ) -> None:
        self.populate(pytester, "alpha")
        self.populate(pytester, "beta")
        alpha = next(p for p in user_cache.iterdir() if p.name.startswith("alpha-"))
        user_cache.chmod(0o500)
        try:
            result = pytester.runpytest("--cache-prune=all")
        finally:
            user_cache.chmod(0o700)

        assert result.ret == ExitCode.USAGE_ERROR
        result.stdout.fnmatch_lines(["*failed: *"])
        assert alpha.exists()


class TestCacheInfo:
    @pytest.fixture
    def cache(self, pytester: Pytester) -> Cache:
        return Cache.for_config(pytester.parseconfig(), _ispytest=True)

    def info(self, cache: Cache) -> dict[str, Any]:
        info = read_cache_info(cache._cachedir)
        assert info is not None
        return info

    def test_written_on_creation(self, pytester: Pytester) -> None:
        pytester.makeini("[pytest]")
        cache = Cache.for_config(pytester.parseconfig(), _ispytest=True)
        cache.set("foo", 1)
        info = self.info(cache)

        assert info["schema"] == CACHE_INFO_SCHEMA
        assert info["origin"] == {
            "rootdir": str(pytester.path),
            "inipath": str(pytester.path / "tox.ini"),
        }
        assert info["pytest_version"] == pytest.__version__
        assert info["created_at"] == info["last_used_at"]
        assert info["scopes"] == {}

    def test_origin_inipath_is_null_without_a_config_file(self, cache: Cache) -> None:
        cache.set("foo", 1)
        assert self.info(cache)["origin"]["inipath"] is None

    def test_not_written_when_cache_is_unused(self, cache: Cache) -> None:
        # A run which never writes to the cache must still not create it.
        assert not cache._cachedir.exists()

    def test_records_scopes_as_they_are_used(self, cache: Cache) -> None:
        cache.set("foo", 1)
        assert self.info(cache)["scopes"] == {}

        cache.set("foo", 1, scope=CacheScope.ENV)
        scopes = self.info(cache)["scopes"]
        scope_id = _scope_id(CacheScope.ENV)
        assert set(scopes) == {scope_id}
        assert scopes[scope_id]["scope"] == "env"
        assert scopes[scope_id]["prefix"] == sys.prefix

        cache.set("foo", 1, scope=CacheScope.PYTHON)
        assert set(self.info(cache)["scopes"]) == {
            scope_id,
            _scope_id(CacheScope.PYTHON),
        }

    def test_last_used_at_refreshed_but_created_at_kept(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cacheprovider, "_now", lambda: 1000.0)
        first = Cache.for_config(pytester.parseconfig(), _ispytest=True)
        first.set("foo", 1)

        monkeypatch.setattr(cacheprovider, "_now", lambda: 2000.0)
        second = Cache.for_config(pytester.parseconfig(), _ispytest=True)
        second.set("foo", 2)

        info = self.info(second)
        assert info["created_at"] == 1000.0
        assert info["last_used_at"] == 2000.0

    def test_preserves_unknown_keys(self, cache: Cache) -> None:
        # A newer pytest's fields must survive an older pytest touching the
        # same directory.
        cache.set("foo", 1)
        path = cache._cachedir / CACHE_INFO_NAME
        info = json.loads(path.read_text(encoding="UTF-8"))
        info["from_the_future"] = {"hello": "world"}
        path.write_text(json.dumps(info), encoding="UTF-8")

        cache.set("foo", 1, scope=CacheScope.ENV)
        assert self.info(cache)["from_the_future"] == {"hello": "world"}

    def test_backfilled_into_a_preexisting_dir(self, cache: Cache) -> None:
        cache.set("foo", 1)
        (cache._cachedir / CACHE_INFO_NAME).unlink()

        later = Cache.for_config(cache._config, _ispytest=True)
        later.set("foo", 2)
        assert self.info(later)["schema"] == CACHE_INFO_SCHEMA

    def test_survives_cache_clear(self, pytester: Pytester) -> None:
        # Like README.md and CACHEDIR.TAG, the metadata is a supporting file:
        # clearing a cache must not make it anonymous (#6290).
        pytester.makepyfile(test_a="def test_error(): assert False")
        pytester.runpytest("-q")
        cachedir = pytester.path / ".pytest_cache"
        before = read_cache_info(cachedir)
        assert before is not None

        pytester.runpytest("-q", "--cache-clear")

        after = read_cache_info(cachedir)
        assert after is not None
        assert after["created_at"] == before["created_at"]

    def test_unreadable_metadata_is_tolerated(self, cache: Cache) -> None:
        cache.set("foo", 1)
        (cache._cachedir / CACHE_INFO_NAME).write_text("{not json", encoding="UTF-8")
        assert read_cache_info(cache._cachedir) is None

        # ... and gets rewritten rather than making the run fail.
        later = Cache.for_config(cache._config, _ispytest=True)
        later.set("foo", 2)
        assert self.info(later)["schema"] == CACHE_INFO_SCHEMA

    @pytest.mark.filterwarnings("default")
    def test_write_failure_is_silent(
        self, pytester: Pytester, unwritable_cache_dir: Path
    ) -> None:
        # The value writes warn about the same cause already; a second warning
        # for the metadata would be noise.
        pytester.makepyfile(test_a="def test_ok(): pass")
        result = pytester.runpytest()
        assert result.ret == 0
        result.stdout.no_fnmatch_line("*cache metadata*")


class TestEnvScopedBuiltins:
    """The built-in cache keys are pinned to the environment.

    Which environment collected which tests is not portable, so `--lf`, `--nf`
    and `--sw` state must not be shared between them. Previously the only way
    to get that was to move the whole cache directory, which is what the
    TOX_ENV_DIR special case does.
    """

    def test_lastfailed_lives_in_the_env_scope(self, pytester: Pytester) -> None:
        pytester.makepyfile(test_a="def test_error(): assert False")
        pytester.runpytest("-q")

        assert (env_scope_values() / "cache" / "lastfailed").is_file()
        assert not (Path(".pytest_cache") / "v" / "cache" / "lastfailed").exists()

    def test_nodeids_lives_in_the_env_scope(self, pytester: Pytester) -> None:
        pytester.makepyfile(test_a="def test_ok(): pass")
        pytester.runpytest("-q")

        assert (env_scope_values() / "cache" / "nodeids").is_file()
        assert not (Path(".pytest_cache") / "v" / "cache" / "nodeids").exists()

    def test_environments_do_not_clobber_each_other(
        self, pytester: Pytester, monkeypatch: MonkeyPatch
    ) -> None:
        pytester.makepyfile(
            test_a="""
            import os
            def test_one(): assert not os.environ.get("FAIL_ONE")
            def test_two(): assert not os.environ.get("FAIL_TWO")
            """
        )
        # Two runs which fail different tests, as two different environments.
        # Patched at conftest import time, i.e. before cacheprovider's
        # tryfirst pytest_configure builds the Cache.
        pytester.makeconftest(
            """
            import os, sys
            sys.prefix = os.environ["FAKE_PREFIX"]
            """
        )

        monkeypatch.setenv("FAKE_PREFIX", str(pytester.path / "venv-one"))
        monkeypatch.setenv("FAIL_ONE", "1")
        pytester.runpytest_subprocess("-q").assert_outcomes(passed=1, failed=1)

        monkeypatch.delenv("FAIL_ONE")
        monkeypatch.setenv("FAKE_PREFIX", str(pytester.path / "venv-two"))
        monkeypatch.setenv("FAIL_TWO", "1")
        pytester.runpytest_subprocess("-q").assert_outcomes(passed=1, failed=1)

        # Each environment still remembers its own failure, rather than the
        # second run having overwritten the first.
        monkeypatch.delenv("FAIL_TWO")
        monkeypatch.setenv("FAKE_PREFIX", str(pytester.path / "venv-one"))
        result = pytester.runpytest_subprocess("--lf", "-v")
        result.stdout.fnmatch_lines(
            ["*rerun previous 1 failure*", "*test_a.py::test_one*PASSED*"]
        )
        result.assert_outcomes(passed=1)


class TestCacheScopes:
    @pytest.fixture
    def cache(self, pytester: Pytester) -> Cache:
        return Cache.for_config(pytester.parseconfig(), _ispytest=True)

    def test_shared_scope_keeps_the_flat_layout(self, cache: Cache) -> None:
        # The shared scope must stay where it has always been, so that existing
        # caches and third-party plugins need no migration.
        cache.set("foo/bar", 1)
        assert (cache._cachedir / "v" / "foo" / "bar").is_file()
        assert not (cache._cachedir / "s").exists()

    @pytest.mark.parametrize("scope", [CacheScope.PYTHON, CacheScope.ENV])
    def test_scoped_values_round_trip(self, cache: Cache, scope: CacheScope) -> None:
        cache.set("foo/bar", 1, scope=scope)
        assert cache.get("foo/bar", None, scope=scope) == 1

        scope_id = _scope_id(scope)
        assert scope_id is not None
        assert (cache._cachedir / "s" / scope_id / "v" / "foo" / "bar").is_file()

    def test_scopes_do_not_see_each_other(self, cache: Cache) -> None:
        for scope in CacheScope:
            cache.set("foo", scope.value, scope=scope)
        for scope in CacheScope:
            assert cache.get("foo", None, scope=scope) == scope.value

    def test_mkdir_is_scoped(self, cache: Cache) -> None:
        shared = cache.mkdir("name")
        scoped = cache.mkdir("name", scope=CacheScope.ENV)
        assert shared.is_dir() and scoped.is_dir()
        assert shared != scoped

    def test_mkdir_rejects_separators_in_any_scope(self, cache: Cache) -> None:
        with pytest.raises(ValueError):
            cache.mkdir("key/name", scope=CacheScope.ENV)

    def test_clear_cache_removes_scopes(self, cache: Cache) -> None:
        cache.set("foo", 1)
        cache.set("foo", 1, scope=CacheScope.ENV)
        Cache.clear_cache(cache._cachedir, _ispytest=True)
        assert not (cache._cachedir / "s").exists()
        assert not (cache._cachedir / "v").exists()
        # ... but the supporting files survive, as for `d` and `v` (#6290).
        assert (cache._cachedir / "CACHEDIR.TAG").is_file()

    def test_scope_ids_are_stable(self) -> None:
        assert _scope_id(CacheScope.SHARED) is None
        for scope in (CacheScope.PYTHON, CacheScope.ENV):
            assert _scope_id(scope) == _scope_id(scope)

    def test_python_scope_id_tracks_minor_version_only(
        self, monkeypatch: MonkeyPatch
    ) -> None:
        before = _scope_id(CacheScope.PYTHON)

        # A patch release upgrade must not invalidate the cache.
        major, minor, micro = sys.version_info[:3]
        monkeypatch.setattr(sys, "version_info", (major, minor, micro + 1))
        assert _scope_id(CacheScope.PYTHON) == before

        monkeypatch.setattr(sys, "version_info", (major, minor + 1, 0))
        assert _scope_id(CacheScope.PYTHON) != before

    def test_env_scope_id_tracks_sys_prefix(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "prefix", "/somewhere/one/.venv")
        one = _scope_id(CacheScope.ENV)
        monkeypatch.setattr(sys, "prefix", "/somewhere/two/.venv")
        two = _scope_id(CacheScope.ENV)

        assert one != two
        # Both stay readable, and the leading dot is stripped so they are not
        # hidden directories.
        assert one is not None and two is not None
        assert one.startswith("env-venv-") and two.startswith("env-venv-")

    def test_env_scope_id_ignores_python_version(
        self, monkeypatch: MonkeyPatch
    ) -> None:
        before = _scope_id(CacheScope.ENV)
        monkeypatch.setattr(sys, "version_info", (99, 9, 9))
        assert _scope_id(CacheScope.ENV) == before

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("myproj", "myproj"),
            ("my project (v2)", "my-project-v2"),
            (".hidden", "hidden"),
            ("with/sep", "with-sep"),
            ("ünïcode", "n-code"),
            ("", "root"),
            ("/", "root"),
            ("!!!", "root"),
            ("x" * 60, "x" * 32),
        ],
    )
    def test_label_sanitisation(self, name: str, expected: str) -> None:
        assert _label(name) == expected


def test_clioption_with_cacheshow_and_help(pytester: Pytester) -> None:
    result = pytester.runpytest("--cache-show", "--help")
    assert result.ret == 0


def test_make_cachedir_cleans_up_on_base_exception(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    """Ensure _make_cachedir cleans up the temp directory on BaseException.

    When a BaseException (like KeyboardInterrupt) is raised during cache
    directory creation, the temporary directory should be cleaned up before
    re-raising the exception.
    """
    from _pytest.cacheprovider import _make_cachedir

    target = tmp_path / ".pytest_cache"

    def raise_keyboard_interrupt(self: Path, target: Path) -> None:
        raise KeyboardInterrupt("simulated interrupt")

    # Patch Path.rename only for the duration of the _make_cachedir call
    with monkeypatch.context() as m:
        m.setattr(Path, "rename", raise_keyboard_interrupt)

        # Verify the exception is re-raised
        with pytest.raises(KeyboardInterrupt, match="simulated interrupt"):
            _make_cachedir(target)

    # Verify no temp directories were left behind
    temp_dirs = list(tmp_path.glob("pytest-cache-files-*"))
    assert temp_dirs == [], f"Temp directories not cleaned up: {temp_dirs}"

    # Verify the target directory was not created
    assert not target.exists()
