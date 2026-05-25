# mypy: allow-untyped-defs
"""Utilities for assertion debugging."""

from __future__ import annotations

import collections.abc
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
import dataclasses
import pprint
from typing import Literal
from typing import TypeGuard
from unicodedata import normalize

from _pytest import outcomes
import _pytest._code
from _pytest._io.saferepr import saferepr
from _pytest._io.saferepr import saferepr_unlimited
from _pytest.assertion._compare_mapping import _compare_eq_mapping
from _pytest.assertion._compare_sequence import _compare_eq_iterable
from _pytest.assertion._compare_sequence import _compare_eq_sequence
from _pytest.assertion._compare_set import _compare_eq_set
from _pytest.assertion._compare_set import SET_COMPARISON_FUNCTIONS
from _pytest.assertion._compare_text import _compare_eq_text
from _pytest.assertion._compare_text import _notin_text
from _pytest.assertion._typing import _AssertionTextDiffStyle
from _pytest.assertion._typing import _HighlightFunc
from _pytest.config import Config
from _pytest.config import UsageError


# The _reprcompare attribute on the util module is used by the new assertion
# interpretation code and assertion rewriter to detect this plugin was
# loaded and in turn call the hooks defined here as part of the
# DebugInterpreter.
_reprcompare: Callable[[str, object, object], str | None] | None = None

# Works similarly as _reprcompare attribute. Is populated with the hook call
# when pytest_runtest_setup is called.
_assertion_pass: Callable[[int, str, str], None] | None = None

# Config object which is assigned during pytest_runtest_protocol.
_config: Config | None = None

ASSERTION_TEXT_DIFF_STYLE_INI = "assertion_text_diff_style"
ASSERTION_TEXT_DIFF_STYLE_NDIFF: Literal["ndiff"] = "ndiff"
ASSERTION_TEXT_DIFF_STYLE_BLOCK: Literal["block"] = "block"
ASSERTION_TEXT_DIFF_STYLE_CHOICES = (
    ASSERTION_TEXT_DIFF_STYLE_NDIFF,
    ASSERTION_TEXT_DIFF_STYLE_BLOCK,
)


def dummy_highlighter(source: str, lexer: Literal["diff", "python"] = "python") -> str:
    """Dummy highlighter that returns the text unprocessed.

    Needed for _notin_text, as the diff gets post-processed to only show the "+" part.
    """
    return source


def get_assertion_text_diff_style(config: Config) -> _AssertionTextDiffStyle:
    style = str(config.getini(ASSERTION_TEXT_DIFF_STYLE_INI))
    match style:
        case "ndiff" | "block":
            return style
        case _:
            choices = ", ".join(
                repr(choice) for choice in ASSERTION_TEXT_DIFF_STYLE_CHOICES
            )
            raise UsageError(
                f"{ASSERTION_TEXT_DIFF_STYLE_INI} must be one of {choices}; got {style!r}"
            )


def validate_assertion_text_diff_style(config: Config) -> None:
    get_assertion_text_diff_style(config)


def format_explanation(explanation: str) -> str:
    r"""Format an explanation.

    Normally all embedded newlines are escaped, however there are
    three exceptions: \n{, \n} and \n~.  The first two are intended
    cover nested explanations, see function and attribute explanations
    for examples (.visit_Call(), visit_Attribute()).  The last one is
    for when one explanation needs to span multiple lines, e.g. when
    displaying diffs.
    """
    lines = _split_explanation(explanation)
    result = _format_lines(lines)
    return "\n".join(result)


def _split_explanation(explanation: str) -> list[str]:
    r"""Return a list of individual lines in the explanation.

    This will return a list of lines split on '\n{', '\n}' and '\n~'.
    Any other newlines will be escaped and appear in the line as the
    literal '\n' characters.
    """
    raw_lines = (explanation or "").split("\n")
    lines = [raw_lines[0]]
    for values in raw_lines[1:]:
        if values and values[0] in ["{", "}", "~", ">"]:
            lines.append(values)
        else:
            lines[-1] += "\\n" + values
    return lines


def _format_lines(lines: Sequence[str]) -> list[str]:
    """Format the individual lines.

    This will replace the '{', '}' and '~' characters of our mini formatting
    language with the proper 'where ...', 'and ...' and ' + ...' text, taking
    care of indentation along the way.

    Return a list of formatted lines.
    """
    result = list(lines[:1])
    stack = [0]
    stackcnt = [0]
    for line in lines[1:]:
        if line.startswith("{"):
            if stackcnt[-1]:
                s = "and   "
            else:
                s = "where "
            stack.append(len(result))
            stackcnt[-1] += 1
            stackcnt.append(0)
            result.append(" +" + "  " * (len(stack) - 1) + s + line[1:])
        elif line.startswith("}"):
            stack.pop()
            stackcnt.pop()
            result[stack[-1]] += line[1:]
        else:
            assert line[0] in ["~", ">"]
            stack[-1] += 1
            indent = len(stack) if line.startswith("~") else len(stack) - 1
            result.append("  " * indent + line[1:])
    assert len(stack) == 1
    return result


def issequence(x: object) -> TypeGuard[collections.abc.Sequence[object]]:
    return isinstance(x, collections.abc.Sequence) and not isinstance(x, str)


def istext(x: object) -> TypeGuard[str]:
    return isinstance(x, str)


def ismapping(x: object) -> TypeGuard[Mapping[object, object]]:
    return isinstance(x, Mapping)


def isset(x: object) -> TypeGuard[set[object] | frozenset[object]]:
    return isinstance(x, set | frozenset)


def isnamedtuple(obj: object) -> bool:
    return isinstance(obj, tuple) and getattr(obj, "_fields", None) is not None


isdatacls = dataclasses.is_dataclass


def isattrs(obj: object) -> bool:
    return getattr(obj, "__attrs_attrs__", None) is not None


def isiterable(obj: object) -> TypeGuard[collections.abc.Iterable[object]]:
    try:
        iter(obj)  # type: ignore[call-overload]
        return not istext(obj)
    except Exception:
        return False


def has_default_eq(obj: object) -> bool:
    """Check if an instance of an object contains the default eq

    First, we check if the object's __eq__ attribute has __code__,
    if so, we check the equally of the method code filename (__code__.co_filename)
    to the default one generated by the dataclass and attr module
    for dataclasses the default co_filename is <string>, for attrs class, the __eq__ should contain "attrs eq generated"
    """
    # inspired from https://github.com/willmcgugan/rich/blob/07d51ffc1aee6f16bd2e5a25b4e82850fb9ed778/rich/pretty.py#L68
    if hasattr(obj.__eq__, "__code__") and hasattr(obj.__eq__.__code__, "co_filename"):
        code_filename = obj.__eq__.__code__.co_filename

        if isattrs(obj):
            return "attrs generated " in code_filename

        return code_filename == "<string>"  # data class
    return True


def assertrepr_compare(
    op: str,
    left: object,
    right: object,
    *,
    verbose: int,
    highlighter: _HighlightFunc,
    assertion_text_diff_style: _AssertionTextDiffStyle,
) -> list[str] | None:
    """Return specialised explanations for some operators/operands."""
    # Strings which normalize equal are often hard to distinguish when printed; use ascii() to make this easier.
    # See issue #3246.
    use_ascii = (
        isinstance(left, str)
        and isinstance(right, str)
        and normalize("NFD", left) == normalize("NFD", right)
    )

    if verbose > 1:
        left_repr = saferepr_unlimited(left, use_ascii=use_ascii)
        right_repr = saferepr_unlimited(right, use_ascii=use_ascii)
    else:
        # XXX: "15 chars indentation" is wrong
        #      ("E       AssertionError: assert "); should use term width.
        maxsize = (
            80 - 15 - len(op) - 2
        ) // 2  # 15 chars indentation, 1 space around op

        left_repr = saferepr(left, maxsize=maxsize, use_ascii=use_ascii)
        right_repr = saferepr(right, maxsize=maxsize, use_ascii=use_ascii)

    summary = f"{left_repr} {op} {right_repr}"

    explanation = None
    try:
        if op == "==":
            explanation = _compare_eq_any(
                left,
                right,
                highlighter,
                verbose,
                assertion_text_diff_style,
            )
        elif op == "not in":
            if istext(left) and istext(right):
                explanation = _notin_text(left, right, verbose)
        elif op in {"!=", ">=", "<=", ">", "<"}:
            if isset(left) and isset(right):
                explanation = SET_COMPARISON_FUNCTIONS[op](
                    left, right, highlighter, verbose
                )

    except outcomes.Exit:
        raise
    except Exception:
        repr_crash = _pytest._code.ExceptionInfo.from_current()._getreprcrash()
        explanation = [
            f"(pytest_assertion plugin: representation of details failed: {repr_crash}.",
            " Probably an object has a faulty __repr__.)",
        ]

    if not explanation:
        return None

    if explanation[0] != "":
        explanation = ["", *explanation]
    return [summary, *explanation]


def _compare_eq_any(
    left: object,
    right: object,
    highlighter: _HighlightFunc,
    verbose: int,
    assertion_text_diff_style: _AssertionTextDiffStyle,
) -> list[str]:
    explanation = []
    if istext(left) and istext(right):
        explanation = _compare_eq_text(
            left,
            right,
            highlighter,
            verbose,
            assertion_text_diff_style,
        )
    else:
        from _pytest.python_api import ApproxBase

        # Although the common order should be obtained == approx(...), allow both ways.
        if isinstance(right, ApproxBase):
            explanation = right._repr_compare(left)
        elif isinstance(left, ApproxBase):
            explanation = left._repr_compare(right)
        elif type(left) is type(right) and (
            isdatacls(left) or isattrs(left) or isnamedtuple(left)
        ):
            # Note: unlike dataclasses/attrs, namedtuples compare only the
            # field values, not the type or field names. But this branch
            # intentionally only handles the same-type case, which was often
            # used in older code bases before dataclasses/attrs were available.
            explanation = _compare_eq_cls(
                left,
                right,
                highlighter,
                verbose,
                assertion_text_diff_style,
            )
        elif issequence(left) and issequence(right):
            explanation = _compare_eq_sequence(left, right, highlighter, verbose)
        elif isset(left) and isset(right):
            explanation = _compare_eq_set(left, right, highlighter, verbose)
        elif ismapping(left) and ismapping(right):
            explanation = _compare_eq_mapping(left, right, highlighter, verbose)

        if isiterable(left) and isiterable(right):
            expl = _compare_eq_iterable(left, right, highlighter, verbose)
            explanation.extend(expl)

    return explanation


def _compare_eq_cls(
    left: object,
    right: object,
    highlighter: _HighlightFunc,
    verbose: int,
    assertion_text_diff_style: _AssertionTextDiffStyle,
) -> list[str]:
    if not has_default_eq(left):
        return []
    if isdatacls(left):
        all_fields = dataclasses.fields(left)
        fields_to_check = [info.name for info in all_fields if info.compare]
    elif isattrs(left):
        all_fields = left.__attrs_attrs__  # type: ignore[attr-defined]
        fields_to_check = [field.name for field in all_fields if getattr(field, "eq")]
    elif isnamedtuple(left):
        fields_to_check = left._fields  # type: ignore[attr-defined]
    else:
        assert False

    indent = "  "
    same = []
    diff = []
    for field in fields_to_check:
        if getattr(left, field) == getattr(right, field):
            same.append(field)
        else:
            diff.append(field)

    explanation = []
    if same or diff:
        explanation += [""]
    if same and verbose < 2:
        explanation.append(f"Omitting {len(same)} identical items, use -vv to show")
    elif same:
        explanation += ["Matching attributes:"]
        explanation += highlighter(pprint.pformat(same)).splitlines()
    if diff:
        explanation += ["Differing attributes:"]
        explanation += highlighter(pprint.pformat(diff)).splitlines()
        for field in diff:
            field_left = getattr(left, field)
            field_right = getattr(right, field)
            explanation += [
                "",
                f"Drill down into differing attribute {field}:",
                f"{indent}{field}: {highlighter(repr(field_left))} != {highlighter(repr(field_right))}",
            ]
            explanation += [
                indent + line
                for line in _compare_eq_any(
                    field_left,
                    field_right,
                    highlighter,
                    verbose,
                    assertion_text_diff_style,
                )
            ]
    return explanation
