from textwrap import dedent

import pytest
from _pytest.pytester import Pytester


@pytest.fixture()
def file_structure(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_foo="""
        from foo import foo

        def test_foo():
            assert foo() == 1
        """
    )

    pytester.makepyfile(
        test_bar="""
        from bar import bar

        def test_bar():
            assert bar() == 2
        """
    )

    foo_py = pytester.mkdir("sub") / "foo.py"
    content = dedent(
        """
        def foo():
            return 1
        """
    )
    foo_py.write_text(content, encoding="utf-8")

    bar_py = pytester.mkdir("sub2") / "bar.py"
    content = dedent(
        """
        def bar():
            return 2
        """
    )
    bar_py.write_text(content, encoding="utf-8")


def test_one_dir(pytester: Pytester, file_structure) -> None:
    pytester.makefile(".ini", pytest="[pytest]\npythonpath=sub\n")
    result = pytester.runpytest("test_foo.py")
    result.assert_outcomes(passed=1)


def test_two_dirs(pytester: Pytester, file_structure) -> None:
    pytester.makefile(".ini", pytest="[pytest]\npythonpath=sub sub2\n")
    result = pytester.runpytest("test_foo.py", "test_bar.py")
    result.assert_outcomes(passed=2)


def test_module_not_found(pytester: Pytester, file_structure) -> None:
    """Without the pythonpath setting, the module should not be found."""
    pytester.makefile(".ini", pytest="[pytest]\n")
    result = pytester.runpytest("test_foo.py")
    result.assert_outcomes(errors=1)
    expected_error = "E   ModuleNotFoundError: No module named 'foo'"
    result.stdout.fnmatch_lines([expected_error])


def test_no_ini(pytester: Pytester, file_structure) -> None:
    """If no ini file, test should error."""
    result = pytester.runpytest("test_foo.py")
    result.assert_outcomes(errors=1)
    expected_error = "E   ModuleNotFoundError: No module named 'foo'"
    result.stdout.fnmatch_lines([expected_error])
