from __future__ import annotations

from collections.abc import Callable
from typing import cast

from _pytest.mark import MarkMatcher
from _pytest.mark.expression import Expression
from _pytest.mark.expression import MatcherCall
from _pytest.mark.expression import ParseError
import pytest


def evaluate(input: str, matcher: Callable[[str], bool]) -> bool:
    return Expression.compile(input).evaluate(cast(MatcherCall, matcher))


def test_empty_is_false() -> None:
    assert not evaluate("", lambda ident: False)
    assert not evaluate("", lambda ident: True)
    assert not evaluate("   ", lambda ident: False)
    assert not evaluate("\t", lambda ident: False)


@pytest.mark.parametrize(
    ("expr", "expected"),
    (
        ("true", True),
        ("true", True),
        ("false", False),
        ("not true", False),
        ("not false", True),
        ("not not true", True),
        ("not not false", False),
        ("true and true", True),
        ("true and false", False),
        ("false and true", False),
        ("true and true and true", True),
        ("true and true and false", False),
        ("true and true and not true", False),
        ("false or false", False),
        ("false or true", True),
        ("true or true", True),
        ("true or true or false", True),
        ("true and true or false", True),
        ("not true or true", True),
        ("(not true) or true", True),
        ("not (true or true)", False),
        ("true and true or false and false", True),
        ("true and (true or false) and false", False),
        ("true and (true or (not (not false))) and false", False),
    ),
)
def test_basic(expr: str, expected: bool) -> None:
    matcher = {"true": True, "false": False}.__getitem__
    assert evaluate(expr, matcher) is expected


@pytest.mark.parametrize(
    ("expr", "expected"),
    (
        ("               true           ", True),
        ("               ((((((true))))))           ", True),
        ("     (         ((\t  (((true)))))  \t   \t)", True),
        ("(     true     and   (((false))))", False),
        ("not not not not true", True),
        ("not not not not not true", False),
    ),
)
def test_syntax_oddities(expr: str, expected: bool) -> None:
    matcher = {"true": True, "false": False}.__getitem__
    assert evaluate(expr, matcher) is expected


def test_backslash_not_treated_specially() -> None:
    r"""When generating nodeids, if the source name contains special characters
    like a newline, they are escaped into two characters like \n. Therefore, a
    user will never need to insert a literal newline, only \n (two chars). So
    mark expressions themselves do not support escaping, instead they treat
    backslashes as regular identifier characters."""
    matcher = {r"\nfoo\n"}.__contains__

    assert evaluate(r"\nfoo\n", matcher)
    assert not evaluate(r"foo", matcher)
    with pytest.raises(ParseError):
        evaluate("\nfoo\n", matcher)


@pytest.mark.parametrize(
    ("expr", "column", "message"),
    (
        ("(", 2, "expected not OR left parenthesis OR identifier; got end of input"),
        (
            " (",
            3,
            "expected not OR left parenthesis OR identifier; got end of input",
        ),
        (
            ")",
            1,
            "expected not OR left parenthesis OR identifier; got right parenthesis",
        ),
        (
            ") ",
            1,
            "expected not OR left parenthesis OR identifier; got right parenthesis",
        ),
        (
            "not",
            4,
            "expected not OR left parenthesis OR identifier; got end of input",
        ),
        (
            "not not",
            8,
            "expected not OR left parenthesis OR identifier; got end of input",
        ),
        (
            "(not)",
            5,
            "expected not OR left parenthesis OR identifier; got right parenthesis",
        ),
        ("and", 1, "expected not OR left parenthesis OR identifier; got and"),
        (
            "ident and",
            10,
            "expected not OR left parenthesis OR identifier; got end of input",
        ),
        (
            "ident and or",
            11,
            "expected not OR left parenthesis OR identifier; got or",
        ),
        ("ident ident", 7, "expected end of input; got identifier"),
    ),
)
def test_syntax_errors(expr: str, column: int, message: str) -> None:
    with pytest.raises(ParseError) as excinfo:
        evaluate(expr, lambda ident: True)
    assert excinfo.value.column == column
    assert excinfo.value.message == message


@pytest.mark.parametrize(
    "ident",
    (
        ".",
        "...",
        ":::",
        "a:::c",
        "a+-b",
        r"\nhe\\l\lo\n\t\rbye",
        "a/b",
        "אבגד",
        "aaאבגדcc",
        "a[bcd]",
        "1234",
        "1234abcd",
        "1234and",
        "1234or",
        "1234not",
        "notandor",
        "not_and_or",
        "not[and]or",
        "1234+5678",
        "123.232",
        "True",
        "False",
        "None",
        "if",
        "else",
        "while",
    ),
)
def test_valid_idents(ident: str) -> None:
    assert evaluate(ident, {ident: True}.__getitem__)


@pytest.mark.parametrize(
    "ident",
    (
        "^",
        "*",
        "=",
        "&",
        "%",
        "$",
        "#",
        "@",
        "!",
        "~",
        "{",
        "}",
        '"',
        "'",
        "|",
        ";",
        "←",
    ),
)
def test_invalid_idents(ident: str) -> None:
    with pytest.raises(ParseError):
        evaluate(ident, lambda ident: True)


@pytest.mark.parametrize(
    "expr, expected_error_msg",
    (
        ("mark(True=False)", "unexpected reserved python keyword `True`"),
        ("mark(def=False)", "unexpected reserved python keyword `def`"),
        ("mark(class=False)", "unexpected reserved python keyword `class`"),
        ("mark(if=False)", "unexpected reserved python keyword `if`"),
        ("mark(else=False)", "unexpected reserved python keyword `else`"),
        ("mark(valid=False, def=1)", "unexpected reserved python keyword `def`"),
        ("mark(1)", "not a valid python identifier 1"),
        ("mark(var:=False", "not a valid python identifier var:"),
        ("mark(1=2)", "not a valid python identifier 1"),
        ("mark(/=2)", "not a valid python identifier /"),
        ("mark(var==", "expected identifier; got ="),
        ("mark(var)", "expected =; got right parenthesis"),
        ("mark(var=none)", 'unexpected character/s "none"'),
        ("mark(var=1.1)", 'unexpected character/s "1.1"'),
        ("mark(var=')", """closing quote "'" is missing"""),
        ('mark(var=")', 'closing quote """ is missing'),
        ("""mark(var="')""", 'closing quote """ is missing'),
        ("""mark(var='")""", """closing quote "'" is missing"""),
        (
            r"mark(var='\hugo')",
            r'escaping with "\\" not supported in marker expression',
        ),
        ("mark(empty_list=[])", r'unexpected character/s "\[\]"'),
        ("'str'", "expected not OR left parenthesis OR identifier; got string literal"),
    ),
)
def test_invalid_kwarg_name_or_value(
    expr: str, expected_error_msg: str, mark_matcher: MarkMatcher
) -> None:
    with pytest.raises(ParseError, match=expected_error_msg):
        assert evaluate(expr, mark_matcher)


@pytest.fixture(scope="session")
def mark_matcher() -> MarkMatcher:
    markers = [
        pytest.mark.number_mark(a=1, b=2, c=3, d=999_999).mark,
        pytest.mark.builtin_matchers_mark(x=True, y=False, z=None).mark,
        pytest.mark.str_mark(  # pylint: disable-next=non-ascii-name
            m="M", space="with space", empty="", aaאבגדcc="aaאבגדcc", אבגד="אבגד"
        ).mark,
    ]

    return MarkMatcher.from_markers(markers)


@pytest.mark.parametrize(
    "expr, expected",
    (
        # happy cases
        ("number_mark(a=1)", True),
        ("number_mark(b=2)", True),
        ("number_mark(a=1,b=2)", True),
        ("number_mark(a=1,     b=2)", True),
        ("number_mark(d=999999)", True),
        ("number_mark(a   =   1,b= 2,     c = 3)", True),
        # sad cases
        ("number_mark(a=6)", False),
        ("number_mark(b=6)", False),
        ("number_mark(a=1,b=6)", False),
        ("number_mark(a=6,b=2)", False),
        ("number_mark(a   =   1,b= 2,     c = 6)", False),
        ("number_mark(a='1')", False),
    ),
)
def test_keyword_expressions_with_numbers(
    expr: str, expected: bool, mark_matcher: MarkMatcher
) -> None:
    assert evaluate(expr, mark_matcher) is expected


@pytest.mark.parametrize(
    "expr, expected",
    (
        ("builtin_matchers_mark(x=True)", True),
        ("builtin_matchers_mark(x=False)", False),
        ("builtin_matchers_mark(y=True)", False),
        ("builtin_matchers_mark(y=False)", True),
        ("builtin_matchers_mark(z=None)", True),
        ("builtin_matchers_mark(z=False)", False),
        ("builtin_matchers_mark(z=True)", False),
        ("builtin_matchers_mark(z=0)", False),
        ("builtin_matchers_mark(z=1)", False),
    ),
)
def test_builtin_matchers_keyword_expressions(
    expr: str, expected: bool, mark_matcher: MarkMatcher
) -> None:
    assert evaluate(expr, mark_matcher) is expected


@pytest.mark.parametrize(
    "expr, expected",
    (
        ("str_mark(m='M')", True),
        ('str_mark(m="M")', True),
        ("str_mark(aaאבגדcc='aaאבגדcc')", True),
        ("str_mark(אבגד='אבגד')", True),
        ("str_mark(space='with space')", True),
        ("str_mark(empty='')", True),
        ('str_mark(empty="")', True),
        ("str_mark(m='wrong')", False),
        ("str_mark(aaאבגדcc='wrong')", False),
        ("str_mark(אבגד='wrong')", False),
        ("str_mark(m='')", False),
        ('str_mark(m="")', False),
    ),
)
def test_str_keyword_expressions(
    expr: str, expected: bool, mark_matcher: MarkMatcher
) -> None:
    assert evaluate(expr, mark_matcher) is expected
