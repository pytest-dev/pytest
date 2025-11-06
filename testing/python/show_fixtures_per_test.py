from __future__ import annotations

from _pytest.pytester import Pytester


def test_no_items_should_not_show_output(pytester: Pytester) -> None:
    result = pytester.runpytest("--fixtures-per-test")
    result.stdout.no_fnmatch_line("*fixtures used by*")
    assert result.ret == 0


def test_fixtures_in_module(pytester: Pytester) -> None:
    p = pytester.makepyfile(
        '''
        import pytest
        @pytest.fixture
        def _arg0():
            """hidden arg0 fixture"""
        @pytest.fixture
        def arg1():
            """arg1 docstring"""
        def test_arg1(arg1):
            pass
    '''
    )

    result = pytester.runpytest("--fixtures-per-test", p)
    assert result.ret == 0

    result.stdout.fnmatch_lines(
        [
            "*fixtures used by test_arg1*",
            "*(test_fixtures_in_module.py:9)*",
            "arg1 -- test_fixtures_in_module.py:6",
            "    arg1 docstring",
        ]
    )
    result.stdout.no_fnmatch_line("*_arg0*")


def test_fixtures_in_conftest(pytester: Pytester) -> None:
    pytester.makeconftest(
        '''
        import pytest
        @pytest.fixture
        def arg1():
            """arg1 docstring"""
        @pytest.fixture
        def arg2():
            """arg2 docstring"""
        @pytest.fixture
        def arg3(arg1, arg2):
            """arg3
            docstring
            """
    '''
    )
    p = pytester.makepyfile(
        """
        def test_arg2(arg2):
            pass
        def test_arg3(arg3):
            pass
    """
    )
    result = pytester.runpytest("--fixtures-per-test", p)
    assert result.ret == 0

    result.stdout.fnmatch_lines(
        [
            "*fixtures used by test_arg2*",
            "*(test_fixtures_in_conftest.py:2)*",
            "arg2 -- conftest.py:6",
            "    arg2 docstring",
            "*fixtures used by test_arg3*",
            "*(test_fixtures_in_conftest.py:4)*",
            "arg1 -- conftest.py:3",
            "    arg1 docstring",
            "arg2 -- conftest.py:6",
            "    arg2 docstring",
            "arg3 -- conftest.py:9",
            "    arg3",
        ]
    )


def test_should_show_fixtures_used_by_test(pytester: Pytester) -> None:
    pytester.makeconftest(
        '''
        import pytest
        @pytest.fixture
        def arg1():
            """arg1 from conftest"""
        @pytest.fixture
        def arg2():
            """arg2 from conftest"""
    '''
    )
    p = pytester.makepyfile(
        '''
        import pytest
        @pytest.fixture
        def arg1():
            """arg1 from testmodule"""
        def test_args(arg1, arg2):
            pass
    '''
    )
    result = pytester.runpytest("--fixtures-per-test", p)
    assert result.ret == 0

    result.stdout.fnmatch_lines(
        [
            "*fixtures used by test_args*",
            "*(test_should_show_fixtures_used_by_test.py:6)*",
            "arg1 -- test_should_show_fixtures_used_by_test.py:3",
            "    arg1 from testmodule",
            "arg2 -- conftest.py:6",
            "    arg2 from conftest",
        ]
    )


def test_verbose_include_private_fixtures_and_loc(pytester: Pytester) -> None:
    pytester.makeconftest(
        '''
        import pytest
        @pytest.fixture
        def _arg1():
            """_arg1 from conftest"""
        @pytest.fixture
        def arg2(_arg1):
            """arg2 from conftest"""
    '''
    )
    p = pytester.makepyfile(
        '''
        import pytest
        @pytest.fixture
        def arg3():
            """arg3 from testmodule"""
        def test_args(arg2, arg3):
            pass
    '''
    )
    result = pytester.runpytest("--fixtures-per-test", "-v", p)
    assert result.ret == 0

    result.stdout.fnmatch_lines(
        [
            "*fixtures used by test_args*",
            "*(test_verbose_include_private_fixtures_and_loc.py:6)*",
            "_arg1 -- conftest.py:3",
            "    _arg1 from conftest",
            "arg2 -- conftest.py:6",
            "    arg2 from conftest",
            "arg3 -- test_verbose_include_private_fixtures_and_loc.py:3",
            "    arg3 from testmodule",
        ]
    )


def test_doctest_items(pytester: Pytester) -> None:
    pytester.makepyfile(
        '''
        def foo():
            """
            >>> 1 + 1
            2
            """
    '''
    )
    pytester.maketxtfile(
        """
        >>> 1 + 1
        2
    """
    )
    result = pytester.runpytest(
        "--fixtures-per-test", "--doctest-modules", "--doctest-glob=*.txt", "-v"
    )
    assert result.ret == 0

    result.stdout.fnmatch_lines(["*collected 2 items*"])


def test_multiline_docstring_in_module(pytester: Pytester) -> None:
    p = pytester.makepyfile(
        '''
        import pytest
        @pytest.fixture
        def arg1():
            """Docstring content that spans across multiple lines,
            through second line,
            and through third line.

            Docstring content that extends into a second paragraph.

            Docstring content that extends into a third paragraph.
            """
        def test_arg1(arg1):
            pass
    '''
    )

    result = pytester.runpytest("--fixtures-per-test", p)
    assert result.ret == 0

    result.stdout.fnmatch_lines(
        [
            "*fixtures used by test_arg1*",
            "*(test_multiline_docstring_in_module.py:13)*",
            "arg1 -- test_multiline_docstring_in_module.py:3",
            "    Docstring content that spans across multiple lines,",
            "    through second line,",
            "    and through third line.",
        ]
    )


def test_verbose_include_multiline_docstring(pytester: Pytester) -> None:
    p = pytester.makepyfile(
        '''
        import pytest
        @pytest.fixture
        def arg1():
            """Docstring content that spans across multiple lines,
            through second line,
            and through third line.

            Docstring content that extends into a second paragraph.

            Docstring content that extends into a third paragraph.
            """
        def test_arg1(arg1):
            pass
    '''
    )

    result = pytester.runpytest("--fixtures-per-test", "-v", p)
    assert result.ret == 0

    result.stdout.fnmatch_lines(
        [
            "*fixtures used by test_arg1*",
            "*(test_verbose_include_multiline_docstring.py:13)*",
            "arg1 -- test_verbose_include_multiline_docstring.py:3",
            "    Docstring content that spans across multiple lines,",
            "    through second line,",
            "    and through third line.",
            "    ",
            "    Docstring content that extends into a second paragraph.",
            "    ",
            "    Docstring content that extends into a third paragraph.",
        ]
    )


def test_parametrize_pseudo_fixtures_excluded(pytester: Pytester) -> None:
    """Test that parametrize arguments are not shown as fixtures.

    Regression test for issue #11295.
    """
    p = pytester.makepyfile(
        '''
        import pytest
        @pytest.fixture
        def real_fixture():
            """A real fixture with a proper definition."""
            return "real_value"

        @pytest.mark.parametrize("x", [1, 2])
        def test_with_parametrize(x, real_fixture):
            """Test with both a parameter and a real fixture."""
            assert x > 0
            assert real_fixture == "real_value"

        @pytest.mark.parametrize("y,z", [(1, 2), (3, 4)])
        def test_with_multiple_parametrize(y, z):
            """Test with multiple parameters and no real fixtures."""
            assert y > 0
            assert z > 0
    '''
    )

    result = pytester.runpytest("--fixtures-per-test", p)
    assert result.ret == 0

    # Verify that real_fixture is shown for test_with_parametrize
    result.stdout.fnmatch_lines(
        [
            "*fixtures used by test_with_parametrize*1*",
            "*(test_parametrize_pseudo_fixtures_excluded.py:8)*",
            "real_fixture -- test_parametrize_pseudo_fixtures_excluded.py:3",
            "    A real fixture with a proper definition.",
        ]
    )

    # Verify that pseudo-fixtures (x, y, z) are NOT shown
    # Use more specific patterns to avoid matching header lines
    result.stdout.no_fnmatch_line("x -- *.py:*")
    result.stdout.no_fnmatch_line("y -- *.py:*")
    result.stdout.no_fnmatch_line("z -- *.py:*")

    # Verify that test_with_multiple_parametrize shows no fixtures section
    # (since it only has pseudo-fixtures, which should be excluded)
    output = result.stdout.str()
    # Count how many times "fixtures used by test_with_multiple_parametrize" appears
    # It should appear in the separator line but have no fixtures listed
    assert "fixtures used by test_with_multiple_parametrize" in output
