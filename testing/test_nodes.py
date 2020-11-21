from typing import List

import py

import pytest
from _pytest import nodes
from _pytest.config import ExitCode
from _pytest.pytester import Pytester


@pytest.mark.parametrize(
    ("nodeid", "expected"),
    (
        ("", [""]),
        ("a", ["", "a"]),
        ("aa/b", ["", "aa", "aa/b"]),
        ("a/b/c", ["", "a", "a/b", "a/b/c"]),
        ("a/bbb/c::D", ["", "a", "a/bbb", "a/bbb/c", "a/bbb/c::D"]),
        ("a/b/c::D::eee", ["", "a", "a/b", "a/b/c", "a/b/c::D", "a/b/c::D::eee"]),
        # :: considered only at the last component.
        ("::xx", ["", "::xx"]),
        ("a/b/c::D/d::e", ["", "a", "a/b", "a/b/c::D", "a/b/c::D/d", "a/b/c::D/d::e"]),
        # : alone is not a separator.
        ("a/b::D:e:f::g", ["", "a", "a/b", "a/b::D:e:f", "a/b::D:e:f::g"]),
    ),
)
def test_iterparentnodeids(nodeid: str, expected: List[str]) -> None:
    result = list(nodes.iterparentnodeids(nodeid))
    assert result == expected


def test_node_from_parent_disallowed_arguments() -> None:
    with pytest.raises(TypeError, match="session is"):
        nodes.Node.from_parent(None, session=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="config is"):
        nodes.Node.from_parent(None, config=None)  # type: ignore[arg-type]


def test_std_warn_not_pytestwarning(pytester: Pytester) -> None:
    items = pytester.getitems(
        """
        def test():
            pass
    """
    )
    with pytest.raises(ValueError, match=".*instance of PytestWarning.*"):
        items[0].warn(UserWarning("some warning"))  # type: ignore[arg-type]


def test__check_initialpaths_for_relpath() -> None:
    """Ensure that it handles dirs, and does not always use dirname."""
    cwd = py.path.local()

    class FakeSession1:
        _initialpaths = [cwd]

    assert nodes._check_initialpaths_for_relpath(FakeSession1, cwd) == ""

    sub = cwd.join("file")

    class FakeSession2:
        _initialpaths = [cwd]

    assert nodes._check_initialpaths_for_relpath(FakeSession2, sub) == "file"

    outside = py.path.local("/outside")
    assert nodes._check_initialpaths_for_relpath(FakeSession2, outside) is None


def test_failure_with_changed_cwd(pytester: Pytester) -> None:
    """
    Test failure lines should use absolute paths if cwd has changed since
    invocation, so the path is correct (#6428).
    """
    p = pytester.makepyfile(
        """
        import os
        import pytest

        @pytest.fixture
        def private_dir():
            out_dir = 'ddd'
            os.mkdir(out_dir)
            old_dir = os.getcwd()
            os.chdir(out_dir)
            yield out_dir
            os.chdir(old_dir)

        def test_show_wrong_path(private_dir):
            assert False
    """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines([str(p) + ":*: AssertionError", "*1 failed in *"])


def test_node_qual_name_package_func(pytester: Pytester) -> None:
    pkg = pytester.mkpydir("mypkg")
    pkg.joinpath("test_mod.py").write_text(
        """
def test_it(request):
    assert request.node.qual_name == 'test_node_qual_name_package_func0/mypkg::test_mod.py::test_it'"""
    )
    result = pytester.runpytest()
    assert result.ret == ExitCode.OK


def test_node_qual_name_module_func(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        def test_qual_name(request):
            expected = 'test_node_qual_name_module_func0/test_node_qual_name_module_func.py::test_qual_name'
            assert request.node.qual_name == expected
        """
    )
    result = pytester.runpytest()
    assert result.ret == ExitCode.OK


def test_node_qual_name_class_func(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        class TestQual:
            def test_clazz(self, request):
                expected = 'test_node_qual_name_class_func0/test_node_qual_name_class_func.py::TestQual::test_clazz'
                assert request.node.qual_name == expected
        """
    )
    result = pytester.runpytest()
    assert result.ret == ExitCode.OK
