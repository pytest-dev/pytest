from _pytest.pytester import Pytester


def test_should_show_no_ouput_when_zero_items(pytester: Pytester) -> None:
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


def test_should_not_show_pseudo_fixtures(pytester: Pytester) -> None:
    """A fixture is considered pseudo if it was directly created using the
    @pytest.mark.parametrize decorator as part of internal pytest mechanisms
    to manage batch execution. These fixtures should not be included in the
    output because they don't satisfy user expectations for how fixtures are
    created and used."""

    p = pytester.makepyfile(
        """
        import pytest

        @pytest.mark.parametrize("x", [1])
        def test_pseudo_fixture(x):
            pass
    """
    )
    result = pytester.runpytest("--fixtures-per-test", p)
    result.stdout.no_fnmatch_line("*fixtures used by*")
    assert result.ret == 0


def test_should_show_parametrized_fixtures_used_by_test(pytester: Pytester) -> None:
    """A fixture with parameters should be included if it was created using
    the @pytest.fixture decorator, including those that are indirectly
    parametrized."""
    p = pytester.makepyfile(
        '''
        import pytest
        
        @pytest.fixture(params=['a', 'b'])
        def directly(request):
            """parametrized fixture"""
            return request.param
            
        @pytest.fixture
        def indirectly(request):
            """indirectly parametrized fixture"""
            return request.param
            
        def test_parametrized_fixture(directly):
            pass
            
        @pytest.mark.parametrize("indirectly", ["a", "b"], indirect=True)
        def test_indirectly_parametrized(indirectly):
            pass                    
        '''
    )
    result = pytester.runpytest("--fixtures-per-test", p)
    assert result.ret == 0

    expected_matches_for_parametrized_test = [
        "*fixtures used by test_parametrized_fixture*",
        "*(test_should_show_parametrized_fixtures_used_by_test.py:14)*",
        "directly -- test_should_show_parametrized_fixtures_used_by_test.py:4",
        "    parametrized fixture",
    ]

    expected_matches_for_indirectly_parametrized_test = [
        "*fixtures used by test_indirectly_parametrized*",
        "*(test_should_show_parametrized_fixtures_used_by_test.py:17)*",
        "indirectly -- test_should_show_parametrized_fixtures_used_by_test.py:9",
        "    indirectly parametrized fixture",
    ]

    expected_matches = (
        expected_matches_for_parametrized_test * 2
        + expected_matches_for_indirectly_parametrized_test * 2
    )

    result.stdout.fnmatch_lines(expected_matches)
