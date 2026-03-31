# mypy: allow-untyped-defs
from __future__ import annotations

from collections.abc import Callable
import dataclasses
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from typing import Any
from typing import cast
import warnings

from _pytest import pathlib
from _pytest.config import Config
from _pytest.monkeypatch import MonkeyPatch
from _pytest.pathlib import cleanup_numbered_dir
from _pytest.pathlib import create_cleanup_lock
from _pytest.pathlib import make_numbered_dir
from _pytest.pathlib import maybe_delete_a_numbered_dir
from _pytest.pathlib import on_rm_rf_error
from _pytest.pathlib import register_cleanup_lock_removal
from _pytest.pathlib import rm_rf
from _pytest.pathlib import safe_rmtree
from _pytest.pytester import Pytester
from _pytest.tmpdir import _cleanup_old_rootdirs
from _pytest.tmpdir import _verify_ownership_and_tighten_permissions
from _pytest.tmpdir import get_user
from _pytest.tmpdir import pytest_sessionfinish
from _pytest.tmpdir import TempPathFactory
import pytest


skip_if_no_getuid = pytest.mark.skipif(
    not hasattr(os, "getuid"), reason="checks unix permissions"
)


def test_tmp_path_fixture(pytester: Pytester) -> None:
    p = pytester.copy_example("tmpdir/tmp_path_fixture.py")
    results = pytester.runpytest(p)
    results.stdout.fnmatch_lines(["*1 passed*"])


@dataclasses.dataclass
class FakeConfig:
    basetemp: str | Path

    @property
    def trace(self):
        return self

    def get(self, key):
        return lambda *k: None

    def getini(self, name):
        if name == "tmp_path_retention_count":
            return 3
        elif name == "tmp_path_retention_policy":
            return "all"
        else:
            assert False

    @property
    def option(self):
        return self


class TestTmpPathHandler:
    def test_mktemp(self, tmp_path: Path) -> None:
        config = cast(Config, FakeConfig(tmp_path))
        t = TempPathFactory.from_config(config, _ispytest=True)
        tmp = t.mktemp("world")
        assert str(tmp.relative_to(t.getbasetemp())) == "world0"
        tmp = t.mktemp("this")
        assert str(tmp.relative_to(t.getbasetemp())).startswith("this")
        tmp2 = t.mktemp("this")
        assert str(tmp2.relative_to(t.getbasetemp())).startswith("this")
        assert tmp2 != tmp

    def test_tmppath_relative_basetemp_absolute(
        self, tmp_path: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """#4425"""
        monkeypatch.chdir(tmp_path)
        config = cast(Config, FakeConfig("hello"))
        t = TempPathFactory.from_config(config, _ispytest=True)
        assert t.getbasetemp().resolve() == (tmp_path / "hello").resolve()


class TestConfigTmpPath:
    def test_getbasetemp_custom_removes_old(self, pytester: Pytester) -> None:
        mytemp = pytester.path.joinpath("xyz")
        p = pytester.makepyfile(
            """
            def test_1(tmp_path):
                pass
        """
        )
        pytester.runpytest(p, f"--basetemp={mytemp}")
        assert mytemp.exists()
        mytemp.joinpath("hello").touch()

        pytester.runpytest(p, f"--basetemp={mytemp}")
        assert mytemp.exists()
        assert not mytemp.joinpath("hello").exists()

    def test_policy_failed_removes_only_passed_dir(self, pytester: Pytester) -> None:
        p = pytester.makepyfile(
            """
            def test_1(tmp_path):
                assert 0 == 0
            def test_2(tmp_path):
                assert 0 == 1
        """
        )
        pytester.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            tmp_path_retention_policy = "failed"
        """
        )

        pytester.inline_run(p)
        root = pytester._test_tmproot

        for child in root.iterdir():
            # basetemp IS the mkdtemp rootdir; test dirs are directly inside.
            test_dir = list(
                filter(lambda x: x.is_dir() and not x.is_symlink(), child.iterdir())
            )
            # Check only the failed one remains
            assert len(test_dir) == 1
            assert test_dir[0].name == "test_20"

    def test_policy_failed_removes_basedir_when_all_passed(
        self, pytester: Pytester
    ) -> None:
        p = pytester.makepyfile(
            """
            def test_1(tmp_path):
                assert 0 == 0
        """
        )
        pytester.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            tmp_path_retention_policy = "failed"
        """
        )

        pytester.inline_run(p)
        root = pytester._test_tmproot
        for child in root.iterdir():
            # basetemp IS the mkdtemp rootdir; with policy "failed" and
            # all tests passing, test dirs are removed directly.
            test_dirs = list(
                filter(lambda x: x.is_dir() and not x.is_symlink(), child.iterdir())
            )
            assert len(test_dirs) == 0

    # issue #10502
    def test_policy_failed_removes_dir_when_skipped_from_fixture(
        self, pytester: Pytester
    ) -> None:
        p = pytester.makepyfile(
            """
            import pytest

            @pytest.fixture
            def fixt(tmp_path):
                pytest.skip()

            def test_fixt(fixt):
                pass
        """
        )
        pytester.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            tmp_path_retention_policy = "failed"
        """
        )

        pytester.inline_run(p)

        # Check if the test directories are removed
        root = pytester._test_tmproot
        for child in root.iterdir():
            test_dirs = list(
                filter(lambda x: x.is_dir() and not x.is_symlink(), child.iterdir())
            )
            assert len(test_dirs) == 0

    # issue #10502
    def test_policy_all_keeps_dir_when_skipped_from_fixture(
        self, pytester: Pytester
    ) -> None:
        p = pytester.makepyfile(
            """
            import pytest

            @pytest.fixture
            def fixt(tmp_path):
                pytest.skip()

            def test_fixt(fixt):
                pass
        """
        )
        pytester.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            tmp_path_retention_policy = "all"
        """
        )
        pytester.inline_run(p)

        # Check if the test directory is kept
        root = pytester._test_tmproot
        for child in root.iterdir():
            # basetemp IS the mkdtemp rootdir; test dirs are directly inside.
            test_dir = list(
                filter(lambda x: x.is_dir() and not x.is_symlink(), child.iterdir())
            )
            assert len(test_dir) == 1


testdata = [
    ("mypath", True),
    ("/mypath1", False),
    ("./mypath1", True),
    ("../mypath3", False),
    ("../../mypath4", False),
    ("mypath5/..", False),
    ("mypath6/../mypath6", True),
    ("mypath7/../mypath7/..", False),
]


@pytest.mark.parametrize("basename, is_ok", testdata)
def test_mktemp(pytester: Pytester, basename: str, is_ok: bool) -> None:
    mytemp = pytester.mkdir("mytemp")
    p = pytester.makepyfile(
        f"""
        def test_abs_path(tmp_path_factory):
            tmp_path_factory.mktemp('{basename}', numbered=False)
        """
    )

    result = pytester.runpytest(p, f"--basetemp={mytemp}")
    if is_ok:
        assert result.ret == 0
        assert mytemp.joinpath(basename).exists()
    else:
        assert result.ret == 1
        result.stdout.fnmatch_lines("*ValueError*")


def test_tmp_path_always_is_realpath(pytester: Pytester, monkeypatch) -> None:
    # the reason why tmp_path should be a realpath is that
    # when you cd to it and do "os.getcwd()" you will anyway
    # get the realpath.  Using the symlinked path can thus
    # easily result in path-inequality
    # XXX if that proves to be a problem, consider using
    # os.environ["PWD"]
    realtemp = pytester.mkdir("myrealtemp")
    linktemp = pytester.path.joinpath("symlinktemp")
    attempt_symlink_to(linktemp, str(realtemp))
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(linktemp))
    pytester.makepyfile(
        """
        def test_1(tmp_path):
            assert tmp_path.resolve() == tmp_path
    """
    )
    reprec = pytester.inline_run()
    reprec.assertoutcome(passed=1)


def test_tmp_path_too_long_on_parametrization(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        @pytest.mark.parametrize("arg", ["1"*1000])
        def test_some(arg, tmp_path):
            tmp_path.joinpath("hello").touch()
    """
    )
    reprec = pytester.inline_run()
    reprec.assertoutcome(passed=1)


def test_tmp_path_factory(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        @pytest.fixture(scope='session')
        def session_dir(tmp_path_factory):
            return tmp_path_factory.mktemp('data', numbered=False)
        def test_some(session_dir):
            assert session_dir.is_dir()
    """
    )
    reprec = pytester.inline_run()
    reprec.assertoutcome(passed=1)


def test_tmp_path_fallback_tox_env(pytester: Pytester, monkeypatch) -> None:
    """Test that tmp_path works even if environment variables required by getpass
    module are missing (#1010).
    """
    monkeypatch.delenv("USER", raising=False)
    monkeypatch.delenv("USERNAME", raising=False)
    pytester.makepyfile(
        """
        def test_some(tmp_path):
            assert tmp_path.is_dir()
    """
    )
    reprec = pytester.inline_run()
    reprec.assertoutcome(passed=1)


@pytest.fixture
def break_getuser(monkeypatch):
    monkeypatch.setattr("os.getuid", lambda: -1)
    # taken from python 2.7/3.4
    for envvar in ("LOGNAME", "USER", "LNAME", "USERNAME"):
        monkeypatch.delenv(envvar, raising=False)


@pytest.mark.usefixtures("break_getuser")
@pytest.mark.skipif(sys.platform.startswith("win"), reason="no os.getuid on windows")
def test_tmp_path_fallback_uid_not_found(pytester: Pytester) -> None:
    """Test that tmp_path works even if the current process's user id does not
    correspond to a valid user.
    """
    pytester.makepyfile(
        """
        def test_some(tmp_path):
            assert tmp_path.is_dir()
    """
    )
    reprec = pytester.inline_run()
    reprec.assertoutcome(passed=1)


@pytest.mark.usefixtures("break_getuser")
@pytest.mark.skipif(sys.platform.startswith("win"), reason="no os.getuid on windows")
def test_get_user_uid_not_found():
    """Test that get_user() function works even if the current process's
    user id does not correspond to a valid user (e.g. running pytest in a
    Docker container with 'docker run -u'.
    """
    assert get_user() is None


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="win only")
def test_get_user(monkeypatch):
    """Test that get_user() function works even if environment variables
    required by getpass module are missing from the environment on Windows
    (#1010).
    """
    monkeypatch.delenv("USER", raising=False)
    monkeypatch.delenv("USERNAME", raising=False)
    assert get_user() is None


class TestNumberedDir:
    PREFIX = "fun-"

    def test_make(self, tmp_path):
        for i in range(10):
            d = make_numbered_dir(root=tmp_path, prefix=self.PREFIX)
            assert d.name.startswith(self.PREFIX)
            assert d.name.endswith(str(i))

        symlink = tmp_path.joinpath(self.PREFIX + "current")
        if symlink.exists():
            # unix
            assert symlink.is_symlink()
            assert symlink.resolve() == d.resolve()

    def test_cleanup_lock_create(self, tmp_path):
        d = tmp_path.joinpath("test")
        d.mkdir()
        lockfile = create_cleanup_lock(d)
        with pytest.raises(OSError, match=r"cannot create lockfile in .*"):
            create_cleanup_lock(d)

        lockfile.unlink()

    def test_lock_register_cleanup_removal(self, tmp_path: Path) -> None:
        lock = create_cleanup_lock(tmp_path)

        registry: list[Callable[..., None]] = []
        register_cleanup_lock_removal(lock, register=registry.append)

        (cleanup_func,) = registry

        assert lock.is_file()

        cleanup_func(original_pid="intentionally_different")

        assert lock.is_file()

        cleanup_func()

        assert not lock.exists()

        cleanup_func()

        assert not lock.exists()

    def _do_cleanup(self, tmp_path: Path, keep: int = 2) -> None:
        self.test_make(tmp_path)
        cleanup_numbered_dir(
            root=tmp_path,
            prefix=self.PREFIX,
            keep=keep,
            consider_lock_dead_if_created_before=0,
        )

    def test_cleanup_keep(self, tmp_path):
        self._do_cleanup(tmp_path)
        a, b = (x for x in tmp_path.iterdir() if not x.is_symlink())
        print(a, b)

    def test_cleanup_keep_0(self, tmp_path: Path):
        self._do_cleanup(tmp_path, 0)
        dir_num = len(list(tmp_path.iterdir()))
        assert dir_num == 0

    def test_make_no_symlink(self, tmp_path):
        """make_numbered_dir with create_symlink=False must not create a
        ``{prefix}current`` symlink."""
        d = make_numbered_dir(root=tmp_path, prefix=self.PREFIX, create_symlink=False)
        assert d.is_dir()
        symlink = tmp_path / (self.PREFIX + "current")
        assert not symlink.exists()

    def test_cleanup_locked(self, tmp_path):
        p = make_numbered_dir(root=tmp_path, prefix=self.PREFIX)

        create_cleanup_lock(p)

        assert not pathlib.ensure_deletable(
            p, consider_lock_dead_if_created_before=p.stat().st_mtime - 1
        )
        assert pathlib.ensure_deletable(
            p, consider_lock_dead_if_created_before=p.stat().st_mtime + 1
        )

    def test_cleanup_ignores_symlink(self, tmp_path):
        the_symlink = tmp_path / (self.PREFIX + "current")
        attempt_symlink_to(the_symlink, tmp_path / (self.PREFIX + "5"))
        self._do_cleanup(tmp_path)

    def test_removal_accepts_lock(self, tmp_path):
        dir = make_numbered_dir(root=tmp_path, prefix=self.PREFIX)
        create_cleanup_lock(dir)
        maybe_delete_a_numbered_dir(dir)
        assert dir.is_dir()


class TestRmRf:
    def test_rm_rf(self, tmp_path):
        adir = tmp_path / "adir"
        adir.mkdir()
        rm_rf(adir)

        assert not adir.exists()

        adir.mkdir()
        afile = adir / "afile"
        afile.write_bytes(b"aa")

        rm_rf(adir)
        assert not adir.exists()

    def test_rm_rf_with_read_only_file(self, tmp_path):
        """Ensure rm_rf can remove directories with read-only files in them (#5524)"""
        fn = tmp_path / "dir/foo.txt"
        fn.parent.mkdir()

        fn.touch()

        self.chmod_r(fn)

        rm_rf(fn.parent)

        assert not fn.parent.is_dir()

    def chmod_r(self, path):
        mode = os.stat(str(path)).st_mode
        os.chmod(str(path), mode & ~stat.S_IWRITE)

    def test_rm_rf_with_read_only_directory(self, tmp_path):
        """Ensure rm_rf can remove read-only directories (#5524)"""
        adir = tmp_path / "dir"
        adir.mkdir()

        (adir / "foo.txt").touch()
        self.chmod_r(adir)

        rm_rf(adir)

        assert not adir.is_dir()

    def test_on_rm_rf_error(self, tmp_path: Path) -> None:
        adir = tmp_path / "dir"
        adir.mkdir()

        fn = adir / "foo.txt"
        fn.touch()
        self.chmod_r(fn)

        # unknown exception
        with pytest.warns(pytest.PytestWarning):
            exc_info1 = (RuntimeError, RuntimeError(), None)
            on_rm_rf_error(os.unlink, str(fn), exc_info1, start_path=tmp_path)
            assert fn.is_file()

        # we ignore FileNotFoundError
        exc_info2 = (FileNotFoundError, FileNotFoundError(), None)
        assert not on_rm_rf_error(None, str(fn), exc_info2, start_path=tmp_path)

        # unknown function
        with pytest.warns(
            pytest.PytestWarning,
            match=r"^\(rm_rf\) unknown function None when removing .*foo.txt:\n<class 'PermissionError'>: ",
        ):
            exc_info3 = (PermissionError, PermissionError(), None)
            on_rm_rf_error(None, str(fn), exc_info3, start_path=tmp_path)
            assert fn.is_file()

        # ignored function
        with warnings.catch_warnings(record=True) as w:
            exc_info4 = PermissionError()
            on_rm_rf_error(os.open, str(fn), exc_info4, start_path=tmp_path)
            assert fn.is_file()
            assert not [x.message for x in w]

        exc_info5 = PermissionError()
        on_rm_rf_error(os.unlink, str(fn), exc_info5, start_path=tmp_path)
        assert not fn.is_file()


class TestSafeRmtree:
    """Tests for safe_rmtree (#13669)."""

    def test_removes_real_directory(self, tmp_path: Path) -> None:
        """safe_rmtree removes a real (non-symlink) directory."""
        target = tmp_path / "real"
        target.mkdir()
        (target / "file.txt").write_text("data", encoding="utf-8")
        safe_rmtree(target)
        assert not target.exists()

    def test_refuses_symlink_raises(self, tmp_path: Path) -> None:
        """safe_rmtree raises OSError when path is a symlink."""
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real)
        except OSError:
            pytest.skip("could not create symbolic link")

        with pytest.raises(OSError, match="Refusing to recursively remove"):
            safe_rmtree(link)
        # The real directory must be untouched.
        assert real.is_dir()

    def test_refuses_symlink_ignore_errors(self, tmp_path: Path) -> None:
        """safe_rmtree silently skips a symlink when ignore_errors=True."""
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real)
        except OSError:
            pytest.skip("could not create symbolic link")

        # Should not raise; should silently skip.
        safe_rmtree(link, ignore_errors=True)
        # Both the symlink and the real directory must still exist.
        assert link.is_symlink()
        assert real.is_dir()

    def test_rm_rf_refuses_symlink(self, tmp_path: Path) -> None:
        """rm_rf also refuses to remove a symlink after the guard was added."""
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real)
        except OSError:
            pytest.skip("could not create symbolic link")

        with pytest.raises(OSError, match="Refusing to recursively remove"):
            rm_rf(link)
        assert real.is_dir()

    def test_no_warning_when_avoids_symlink_attacks_is_false(
        self, tmp_path: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """No warning is emitted regardless of avoids_symlink_attacks value.

        The is_symlink() root check is the defense; warnings about
        avoids_symlink_attacks were removed because they are unactionable
        for users (they cannot upgrade their kernel from pytest config).
        """
        target = tmp_path / "dir"
        target.mkdir()

        monkeypatch.setattr(shutil.rmtree, "avoids_symlink_attacks", False)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            safe_rmtree(target)
        symlink_warnings = [
            x for x in w if "avoids_symlink_attacks" in str(x.message)
        ]
        assert symlink_warnings == []
        assert not target.exists()


def attempt_symlink_to(path, to_path):
    """Try to make a symlink from "path" to "to_path", skipping in case this platform
    does not support it or we don't have sufficient privileges (common on Windows)."""
    try:
        Path(path).symlink_to(Path(to_path))
    except OSError:
        pytest.skip("could not create symbolic link")


def test_basetemp_with_read_only_files(pytester: Pytester) -> None:
    """Integration test for #5524"""
    pytester.makepyfile(
        """
        import os
        import stat

        def test(tmp_path):
            fn = tmp_path / 'foo.txt'
            fn.write_text('hello', encoding='utf-8')
            mode = os.stat(str(fn)).st_mode
            os.chmod(str(fn), mode & ~stat.S_IREAD)
    """
    )
    result = pytester.runpytest("--basetemp=tmp")
    assert result.ret == 0
    # running a second time and ensure we don't crash
    result = pytester.runpytest("--basetemp=tmp")
    assert result.ret == 0


def test_tmp_path_factory_handles_invalid_dir_characters(
    tmp_path_factory: TempPathFactory, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr("getpass.getuser", lambda: "os/<:*?;>agnostic")
    # _basetemp / _given_basetemp are cached / set in parallel runs, patch them
    monkeypatch.setattr(tmp_path_factory, "_basetemp", None)
    monkeypatch.setattr(tmp_path_factory, "_given_basetemp", None)
    p = tmp_path_factory.getbasetemp()
    assert "pytest-of-unknown" in str(p)


@skip_if_no_getuid
def test_tmp_path_factory_defense_in_depth_fchmod(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Defense-in-depth: even if os.chmod after mkdtemp somehow leaves
    world-readable permissions, the fchmod inside _verify_ownership_and_tighten_permissions corrects
    them."""
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(tmp_path))

    # Sabotage os.chmod so it *widens* permissions instead of tightening;
    # the fd-based fchmod should still correct them.
    original_chmod = os.chmod

    def _widen_chmod(path: Any, mode: int, **kw: Any) -> None:
        original_chmod(path, 0o755)

    monkeypatch.setattr(os, "chmod", _widen_chmod)

    tmp_factory = TempPathFactory(None, 3, "all", lambda *args: None, _ispytest=True)
    basetemp = tmp_factory.getbasetemp()

    # The fchmod defense should have corrected the permissions on basetemp (= rootdir).
    assert (basetemp.stat().st_mode & 0o077) == 0


@skip_if_no_getuid
def test_tmp_path_factory_rejects_symlink_rootdir(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """CVE-2025-71176: defense-in-depth — if the mkdtemp-created rootdir is
    somehow replaced by a symlink before _verify_ownership_and_tighten_permissions runs, it must be
    rejected."""
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(tmp_path))

    attacker_dir = tmp_path / "attacker-controlled"
    attacker_dir.mkdir(mode=0o700)

    original_mkdtemp = tempfile.mkdtemp

    def _mkdtemp_then_replace_with_symlink(**kwargs: Any) -> str:
        """Create the dir normally, then swap it for a symlink."""
        path: str = original_mkdtemp(**kwargs)
        os.rmdir(path)
        os.symlink(str(attacker_dir), path)
        return path

    monkeypatch.setattr(tempfile, "mkdtemp", _mkdtemp_then_replace_with_symlink)

    tmp_factory = TempPathFactory(None, 3, "all", lambda *args: None, _ispytest=True)
    with pytest.raises(OSError, match="could not be safely opened"):
        tmp_factory.getbasetemp()


@skip_if_no_getuid
def test_tmp_path_factory_nofollow_flag_missing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """CVE-2025-71176: verify that the code still works when O_NOFOLLOW or
    O_DIRECTORY flags are not available on the platform."""
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(tmp_path))
    monkeypatch.delattr(os, "O_NOFOLLOW", raising=False)
    monkeypatch.delattr(os, "O_DIRECTORY", raising=False)

    tmp_factory = TempPathFactory(None, 3, "all", lambda *args: None, _ispytest=True)
    basetemp = tmp_factory.getbasetemp()

    # Should still create the directory with safe permissions.
    assert basetemp.is_dir()
    assert (basetemp.stat().st_mode & 0o077) == 0


@pytest.mark.parametrize(
    "ini_overrides, match",
    [
        ({"tmp_path_retention_count": -1}, "tmp_path_retention_count must be >= 0"),
        (
            {"tmp_path_retention_count": 3, "tmp_path_retention_policy": "invalid"},
            "tmp_path_retention_policy must be either",
        ),
    ],
    ids=["negative_count", "invalid_policy"],
)
def test_tmp_path_factory_from_config_rejects_bad_ini(
    tmp_path: Path, ini_overrides: dict[str, Any], match: str
) -> None:
    """Verify that invalid ini options raise ValueError."""

    @dataclasses.dataclass
    class FakeIniConfig:
        basetemp: str | Path = ""

        def getini(self, name):
            if name in ini_overrides:
                return ini_overrides[name]
            if name == "tmp_path_retention_count":
                return 3
            if name == "tmp_path_retention_policy":
                return "all"
            raise KeyError(name)

    config = cast(Config, FakeIniConfig(tmp_path))
    with pytest.raises(ValueError, match=match):
        TempPathFactory.from_config(config, _ispytest=True)


def test_tmp_path_factory_none_policy_sets_keep_zero(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Verify that retention_policy='none' sets keep=0."""
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(tmp_path))
    tmp_factory = TempPathFactory(None, 3, "none", lambda *args: None, _ispytest=True)
    basetemp = tmp_factory.getbasetemp()
    assert basetemp.is_dir()


def test_pytest_sessionfinish_noop_when_no_basetemp(
    pytester: Pytester,
) -> None:
    """Verify that pytest_sessionfinish returns early when basetemp is None."""
    p = pytester.makepyfile(
        """
        def test_no_tmp():
            pass
    """
    )
    result = pytester.runpytest(p)
    result.assert_outcomes(passed=1)


def test_pytest_sessionfinish_handles_missing_basetemp_dir() -> None:
    """Cover the branch where basetemp is set but the directory no longer
    exists when pytest_sessionfinish runs."""
    factory = TempPathFactory(None, 3, "failed", lambda *args: None, _ispytest=True)
    # Point _basetemp at a path that does not exist on disk.
    factory._basetemp = Path("/nonexistent/already-gone")

    class FakeSession:
        class config:
            _tmp_path_factory = factory

    # exitstatus=0 + policy="failed" + _given_basetemp=None enters the
    # cleanup block; basetemp.is_dir() is False so rmtree is skipped.
    pytest_sessionfinish(FakeSession, exitstatus=0)


# -- Tests for mkdtemp-based rootdir creation (DoS mitigation, #13669) --


def test_getbasetemp_uses_mkdtemp_rootdir(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Verify that getbasetemp always creates a randomly-named rootdir
    via mkdtemp, not a predictable pytest-of-<user> directory."""
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(tmp_path))
    factory = TempPathFactory(None, 3, "all", lambda *args: None, _ispytest=True)
    basetemp = factory.getbasetemp()
    user = get_user() or "unknown"
    # basetemp IS the mkdtemp rootdir — no numbered subdir inside it.
    assert basetemp.name.startswith(f"pytest-of-{user}-")
    assert basetemp.name != f"pytest-of-{user}"
    assert basetemp.is_dir()


def test_getbasetemp_immune_to_predictable_path_dos(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """An attacker pre-creating files at /tmp/pytest-of-<user> cannot DoS
    pytest because we no longer use predictable paths (#13669)."""
    temproot = tmp_path / "temproot"
    temproot.mkdir()
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(temproot))

    user = get_user() or "unknown"
    # Simulate the attack: touch /tmp/pytest-of-$user for every user.
    (temproot / f"pytest-of-{user}").touch()
    (temproot / "pytest-of-unknown").touch()

    factory = TempPathFactory(None, 3, "all", lambda *args: None, _ispytest=True)
    basetemp = factory.getbasetemp()
    assert basetemp.is_dir()
    # The blocking files are simply ignored; mkdtemp picks a unique name.
    assert basetemp.name.startswith(f"pytest-of-{user}-")


# -- Unit tests for _cleanup_old_rootdirs --


class TestCleanupOldRootdirs:
    """Tests for cross-session cleanup of mkdtemp-created rootdirs."""

    def test_removes_excess_rootdirs(self, tmp_path: Path) -> None:
        prefix = "pytest-of-testuser-"
        dirs = []
        for i in range(5):
            d = tmp_path / f"{prefix}{i:08}"
            d.mkdir()
            dirs.append(d)

        current = dirs[-1]
        _cleanup_old_rootdirs(tmp_path, prefix, keep=2, current=current)

        remaining = sorted(p for p in tmp_path.iterdir() if p.name.startswith(prefix))
        # current + 2 most recent old dirs = 3 total
        assert len(remaining) == 3
        assert current in remaining

    def test_never_removes_current(self, tmp_path: Path) -> None:
        prefix = "pytest-of-testuser-"
        current = tmp_path / f"{prefix}only"
        current.mkdir()
        _cleanup_old_rootdirs(tmp_path, prefix, keep=0, current=current)
        assert current.is_dir()

    def test_tolerates_missing_temproot(self) -> None:
        _cleanup_old_rootdirs(
            Path("/nonexistent"), "pytest-of-x-", keep=3, current=Path("/x")
        )

    def test_ignores_non_matching_entries(self, tmp_path: Path) -> None:
        prefix = "pytest-of-testuser-"
        current = tmp_path / f"{prefix}current"
        current.mkdir()
        unrelated = tmp_path / "some-other-dir"
        unrelated.mkdir()
        _cleanup_old_rootdirs(tmp_path, prefix, keep=0, current=current)
        assert unrelated.is_dir()

    def test_skips_symlinks_under_temproot(self, tmp_path: Path) -> None:
        """CVE-2025-71176 defense-in-depth: symlinks under temproot that match
        the prefix must be silently skipped, not followed or removed."""
        prefix = "pytest-of-testuser-"
        current = tmp_path / f"{prefix}current"
        current.mkdir()

        # Real old dir that should be cleaned up.
        old_real = tmp_path / f"{prefix}old-real"
        old_real.mkdir()

        # Attacker-planted symlink matching the prefix.
        attacker_target = tmp_path / "attacker-controlled"
        attacker_target.mkdir()
        symlink = tmp_path / f"{prefix}evil-link"
        try:
            symlink.symlink_to(attacker_target)
        except OSError:
            pytest.skip("could not create symbolic link")

        _cleanup_old_rootdirs(tmp_path, prefix, keep=0, current=current)

        # The symlink itself must be untouched (not followed, not removed).
        assert symlink.is_symlink()
        # The attacker's target directory must be untouched.
        assert attacker_target.is_dir()
        # The real old directory should have been cleaned up.
        assert not old_real.exists()
        # Current is always preserved.
        assert current.is_dir()


# -- Direct unit tests for _verify_ownership_and_tighten_permissions context manager --


class TestVerifyOwnershipAndTightenPermissions:
    """Unit tests for _verify_ownership_and_tighten_permissions (CVE-2025-71176)."""

    @skip_if_no_getuid
    def test_accepts_real_directory_owned_by_current_user(self, tmp_path: Path) -> None:
        """Happy path: no error for a real directory owned by us."""
        d = tmp_path / "owned"
        d.mkdir(mode=0o700)
        _verify_ownership_and_tighten_permissions(d, os.getuid())

    @skip_if_no_getuid
    def test_rejects_symlink(self, tmp_path: Path) -> None:
        """A symlink must be rejected with a clear error message."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real_dir)

        with pytest.raises(OSError, match="could not be safely opened"):
            _verify_ownership_and_tighten_permissions(link, os.getuid())

    @skip_if_no_getuid
    def test_rejects_nonexistent_path(self, tmp_path: Path) -> None:
        """A non-existent path must be rejected with a clear error message."""
        missing = tmp_path / "does-not-exist"
        with pytest.raises(OSError, match="could not be safely opened"):
            _verify_ownership_and_tighten_permissions(missing, os.getuid())

    @skip_if_no_getuid
    def test_rejects_wrong_owner(self, tmp_path: Path) -> None:
        """A directory owned by someone else must be rejected."""
        d = tmp_path / "dir"
        d.mkdir(mode=0o700)
        with pytest.raises(OSError, match="not owned by the current user"):
            _verify_ownership_and_tighten_permissions(d, os.getuid() + 1)

    @skip_if_no_getuid
    def test_tightens_loose_permissions(self, tmp_path: Path) -> None:
        """World-readable permissions must be tightened to 0o700."""
        d = tmp_path / "loose"
        d.mkdir(mode=0o755)
        _verify_ownership_and_tighten_permissions(d, os.getuid())
        assert (d.stat().st_mode & 0o077) == 0
