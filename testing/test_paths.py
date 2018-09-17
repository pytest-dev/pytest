import sys

import py

import pytest

from _pytest.paths import fnmatch_ex


class TestPort:
    """Test that our port of py.common.FNMatcher (fnmatch_ex) produces the same results as the
    original py.path.local.fnmatch method.
    """

    @pytest.fixture(params=["pathlib", "py.path"])
    def match(self, request):
        if request.param == "py.path":

            def match_(pattern, path):
                return py.path.local(path).fnmatch(pattern)

        else:
            assert request.param == "pathlib"

            def match_(pattern, path):
                return fnmatch_ex(pattern, path)

        return match_

    if sys.platform == "win32":
        drv1 = "c:"
        drv2 = "d:"
    else:
        drv1 = "/c"
        drv2 = "/d"

    @pytest.mark.parametrize(
        "pattern, path",
        [
            ("*.py", "foo.py"),
            ("*.py", "bar/foo.py"),
            ("test_*.py", "foo/test_foo.py"),
            ("tests/*.py", "tests/foo.py"),
            (drv1 + "/*.py", drv1 + "/foo.py"),
            (drv1 + "/foo/*.py", drv1 + "/foo/foo.py"),
            ("tests/**/test*.py", "tests/foo/test_foo.py"),
            ("tests/**/doc/test*.py", "tests/foo/bar/doc/test_foo.py"),
            ("tests/**/doc/**/test*.py", "tests/foo/doc/bar/test_foo.py"),
        ],
    )
    def test_matching(self, match, pattern, path):
        assert match(pattern, path)

    @pytest.mark.parametrize(
        "pattern, path",
        [
            ("*.py", "foo.pyc"),
            ("*.py", "foo/foo.pyc"),
            ("tests/*.py", "foo/foo.py"),
            (drv1 + "/*.py", drv2 + "/foo.py"),
            (drv1 + "/foo/*.py", drv2 + "/foo/foo.py"),
            ("tests/**/test*.py", "tests/foo.py"),
            ("tests/**/test*.py", "foo/test_foo.py"),
            ("tests/**/doc/test*.py", "tests/foo/bar/doc/foo.py"),
            ("tests/**/doc/test*.py", "tests/foo/bar/test_foo.py"),
        ],
    )
    def test_not_matching(self, match, pattern, path):
        assert not match(pattern, path)
