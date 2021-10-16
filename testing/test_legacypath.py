import pytest
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
