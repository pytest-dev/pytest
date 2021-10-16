from pathlib import Path

import pytest
from _pytest.compat import LEGACY_PATH
from _pytest.legacypath import TempdirFactory
from _pytest.legacypath import Testdir


def test_testdir_testtmproot(testdir: Testdir) -> None:
    """Check test_tmproot is a py.path attribute for backward compatibility."""
    assert testdir.test_tmproot.check(dir=1)


def test_testdir_makefile_dot_prefixes_extension_silently(
    testdir: Testdir,
) -> None:
    """For backwards compat #8192"""
    p1 = testdir.makefile("foo.bar", "")
    assert ".foo.bar" in str(p1)


def test_testdir_makefile_ext_none_raises_type_error(testdir: Testdir) -> None:
    """For backwards compat #8192"""
    with pytest.raises(TypeError):
        testdir.makefile(None, "")


def test_testdir_makefile_ext_empty_string_makes_file(testdir: Testdir) -> None:
    """For backwards compat #8192"""
    p1 = testdir.makefile("", "")
    assert "test_testdir_makefile" in str(p1)


def attempt_symlink_to(path: str, to_path: str) -> None:
    """Try to make a symlink from "path" to "to_path", skipping in case this platform
    does not support it or we don't have sufficient privileges (common on Windows)."""
    try:
        Path(path).symlink_to(Path(to_path))
    except OSError:
        pytest.skip("could not create symbolic link")


def test_tmpdir_factory(
    tmpdir_factory: TempdirFactory,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    assert str(tmpdir_factory.getbasetemp()) == str(tmp_path_factory.getbasetemp())
    dir = tmpdir_factory.mktemp("foo")
    assert dir.exists()


def test_tmpdir_equals_tmp_path(tmpdir: LEGACY_PATH, tmp_path: Path) -> None:
    assert Path(tmpdir) == tmp_path


def test_tmpdir_always_is_realpath(pytester: pytest.Pytester) -> None:
    # See test_tmp_path_always_is_realpath.
    realtemp = pytester.mkdir("myrealtemp")
    linktemp = pytester.path.joinpath("symlinktemp")
    attempt_symlink_to(str(linktemp), str(realtemp))
    p = pytester.makepyfile(
        """
        def test_1(tmpdir):
            import os
            assert os.path.realpath(str(tmpdir)) == str(tmpdir)
    """
    )
    result = pytester.runpytest("-s", p, "--basetemp=%s/bt" % linktemp)
    assert not result.ret
