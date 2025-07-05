"""
Tests and examples for correct "+/-" usage in error diffs.

See https://github.com/pytest-dev/pytest/issues/3333 for details.

"""

from __future__ import annotations

from _pytest.pytester import Pytester
import pytest


TESTCASES = [
    pytest.param(
        """
        def test_this():
            result =   [1, 4, 3]
            expected = [1, 2, 3]
            assert result == expected
        """,
        """
        >       assert result == expected
        E       assert [1, 4, 3] == [1, 2, 3]
        E         At index 1 diff: 4 != 2
        E         Full diff:
        E           [
        E               1,
        E         -     2,
        E         ?     ^
        E         +     4,
        E         ?     ^
        E               3,
        E           ]
        """,
        id="Compare lists, one item differs",
    ),
    pytest.param(
        """
        def test_this():
            result =   [1, 2, 3]
            expected = [1, 2]
            assert result == expected
        """,
        """
        >       assert result == expected
        E       assert [1, 2, 3] == [1, 2]
        E         Left contains one more item: 3
        E         Full diff:
        E           [
        E               1,
        E               2,
        E         +     3,
        E           ]
        """,
        id="Compare lists, one extra item",
    ),
    pytest.param(
        """
        def test_this():
            result =   [1, 3]
            expected = [1, 2, 3]
            assert result == expected
        """,
        """
        >       assert result == expected
        E       assert [1, 3] == [1, 2, 3]
        E         At index 1 diff: 3 != 2
        E         Right contains one more item: 3
        E         Full diff:
        E           [
        E               1,
        E         -     2,
        E               3,
        E           ]
        """,
        id="Compare lists, one item missing",
    ),
    pytest.param(
        """
        def test_this():
            result =   (1, 4, 3)
            expected = (1, 2, 3)
            assert result == expected
        """,
        """
        >       assert result == expected
        E       assert (1, 4, 3) == (1, 2, 3)
        E         At index 1 diff: 4 != 2
        E         Full diff:
        E           (
        E               1,
        E         -     2,
        E         ?     ^
        E         +     4,
        E         ?     ^
        E               3,
        E           )
        """,
        id="Compare tuples",
    ),
    pytest.param(
        """
        def test_this():
            result =   {1, 3, 4}
            expected = {1, 2, 3}
            assert result == expected
        """,
        """
        >       assert result == expected
        E       assert {1, 3, 4} == {1, 2, 3}
        E         Extra items in the left set:
        E         4
        E         Extra items in the right set:
        E         2
        E         Full diff:
        E           {
        E               1,
        E         -     2,
        E               3,
        E         +     4,
        E           }
        """,
        id="Compare sets",
    ),
    pytest.param(
        """
        def test_this():
            result =   {1: 'spam', 3: 'eggs'}
            expected = {1: 'spam', 2: 'eggs'}
            assert result == expected
        """,
        """
        >       assert result == expected
        E       AssertionError: assert {1: 'spam', 3: 'eggs'} == {1: 'spam', 2: 'eggs'}
        E         Common items:
        E         {1: 'spam'}
        E         Left contains 1 more item:
        E         {3: 'eggs'}
        E         Right contains 1 more item:
        E         {2: 'eggs'}
        E         Full diff:
        E           {
        E               1: 'spam',
        E         -     2: 'eggs',
        E         ?     ^
        E         +     3: 'eggs',
        E         ?     ^
        E           }
        """,
        id="Compare dicts with differing keys",
    ),
    pytest.param(
        """
        def test_this():
            result =   {1: 'spam', 2: 'eggs'}
            expected = {1: 'spam', 2: 'bacon'}
            assert result == expected
        """,
        """
        >       assert result == expected
        E       AssertionError: assert {1: 'spam', 2: 'eggs'} == {1: 'spam', 2: 'bacon'}
        E         Common items:
        E         {1: 'spam'}
        E         Differing items:
        E         {2: 'eggs'} != {2: 'bacon'}
        E         Full diff:
        E           {
        E               1: 'spam',
        E         -     2: 'bacon',
        E         +     2: 'eggs',
        E           }
        """,
        id="Compare dicts with differing values",
    ),
    pytest.param(
        """
        def test_this():
            result =   {1: 'spam', 2: 'eggs'}
            expected = {1: 'spam', 3: 'bacon'}
            assert result == expected
        """,
        """
        >       assert result == expected
        E       AssertionError: assert {1: 'spam', 2: 'eggs'} == {1: 'spam', 3: 'bacon'}
        E         Common items:
        E         {1: 'spam'}
        E         Left contains 1 more item:
        E         {2: 'eggs'}
        E         Right contains 1 more item:
        E         {3: 'bacon'}
        E         Full diff:
        E           {
        E               1: 'spam',
        E         -     3: 'bacon',
        E         +     2: 'eggs',
        E           }
        """,
        id="Compare dicts with differing items",
    ),
    pytest.param(
        """
        def test_this():
            result = {'d': 4, 'c': 3, 'b': 2, 'a': 1}
            expected = {'d': 4, 'c': 3, 'e': 5}
            assert result == expected
        """,
        """
        >       assert result == expected
        E       AssertionError: assert {'d': 4, 'c': 3, 'b': 2, 'a': 1} == {'d': 4, 'c': 3, 'e': 5}
        E         Common items:
        E         {'d': 4, 'c': 3}
        E         Left contains 2 more items:
        E         {'b': 2, 'a': 1}
        E         Right contains 1 more item:
        E         {'e': 5}
        E         Full diff:
        E           {
        E               'd': 4,
        E               'c': 3,
        E         -     'e': 5,
        E         ?      ^   ^
        E         +     'b': 2,
        E         ?      ^   ^
        E         +     'a': 1,
        E           }
        """,
        id="Compare dicts and check order of diff",
    ),
    pytest.param(
        """
        def test_this():
            result = {'c': 3, 'd': 4, 'b': 2, 'a': 1}
            expected = {'d': 5, 'c': 3, 'b': 1}
            assert result == expected
        """,
        """
        >       assert result == expected
        E       AssertionError: assert {'c': 3, 'd': 4, 'b': 2, 'a': 1} == {'d': 5, 'c': 3, 'b': 1}
        E         Common items:
        E         {'c': 3}
        E         Differing items:
        E         {'d': 4} != {'d': 5}
        E         {'b': 2} != {'b': 1}
        E         Left contains 1 more item:
        E         {'a': 1}
        E         Full diff:
        E           {
        E         -     'd': 5,
        E               'c': 3,
        E         +     'd': 4,
        E         -     'b': 1,
        E         ?          ^
        E         +     'b': 2,
        E         ?          ^
        E         +     'a': 1,
        E           }
        """,
        id="Compare dicts with different order and values",
    ),
    pytest.param(
        """
        def test_this():
            result =   "spmaeggs"
            expected = "spameggs"
            assert result == expected
        """,
        """
        >       assert result == expected
        E       AssertionError: assert 'spmaeggs' == 'spameggs'
        E         - spameggs
        E         ?    -
        E         + spmaeggs
        E         ?   +
        """,
        id="Compare strings",
    ),
    pytest.param(
        """
        def test_this():
            result =   "spam bacon eggs"
            assert "bacon" not in result
        """,
        """
        >       assert "bacon" not in result
        E       AssertionError: assert 'bacon' not in 'spam bacon eggs'
        E         'bacon' is contained here:
        E           spam bacon eggs
        E         ?      +++++
        """,
        id='Test "not in" string',
    ),
    pytest.param(
        """
        from dataclasses import dataclass

        @dataclass
        class A:
            a: int
            b: str

        def test_this():
            result =   A(1, 'spam')
            expected = A(2, 'spam')
            assert result == expected
        """,
        """
        >       assert result == expected
        E       AssertionError: assert A(a=1, b='spam') == A(a=2, b='spam')
        E         Matching attributes:
        E         ['b']
        E         Differing attributes:
        E         ['a']
        E         Drill down into differing attribute a:
        E           a: 1 != 2
        """,
        id="Compare data classes",
    ),
    pytest.param(
        """
        import attr

        @attr.s(auto_attribs=True)
        class A:
            a: int
            b: str

        def test_this():
            result =   A(1, 'spam')
            expected = A(1, 'eggs')
            assert result == expected
        """,
        """
        >       assert result == expected
        E       AssertionError: assert A(a=1, b='spam') == A(a=1, b='eggs')
        E         Matching attributes:
        E         ['a']
        E         Differing attributes:
        E         ['b']
        E         Drill down into differing attribute b:
        E           b: 'spam' != 'eggs'
        E           - eggs
        E           + spam
        """,
        id="Compare attrs classes",
    ),
]


@pytest.mark.parametrize("code, expected", TESTCASES)
def test_error_diff(code: str, expected: str, pytester: Pytester) -> None:
    expected_lines = [line.lstrip() for line in expected.splitlines()]
    p = pytester.makepyfile(code)
    result = pytester.runpytest(p, "-vv")
    result.stdout.fnmatch_lines(expected_lines)
    assert result.ret == 1
