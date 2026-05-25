from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Mapping
from collections.abc import Sequence
from collections.abc import Set as AbstractSet
import dataclasses
import pprint

from _pytest.assertion._compare_mapping import _compare_eq_mapping
from _pytest.assertion._compare_sequence import _compare_eq_iterable
from _pytest.assertion._compare_sequence import _compare_eq_sequence
from _pytest.assertion._compare_set import _compare_eq_set
from _pytest.assertion._compare_set import SET_COMPARISON_FUNCTIONS
from _pytest.assertion._guards import has_default_eq
from _pytest.assertion._guards import isattrs
from _pytest.assertion._guards import isdatacls
from _pytest.assertion._guards import isiterable
from _pytest.assertion._guards import isnamedtuple
from _pytest.assertion._guards import issequence
from _pytest.assertion._typing import _AssertionTextDiffStyle
from _pytest.assertion._typing import _HighlightFunc
from _pytest.assertion.compare_text import _compare_eq_text
from _pytest.assertion.compare_text import _notin_text


def _compare_eq_any(
    op: str,
    left: object,
    right: object,
    highlighter: _HighlightFunc,
    verbose: int,
    assertion_text_diff_style: _AssertionTextDiffStyle,
) -> list[str] | None:
    """Return the per-line explanation for ``left op right`` (without summary).

    Returns ``None`` when no specialised explanation applies.
    """
    from _pytest.python_api import ApproxBase

    explanation: list[str]
    match (left, op, right):
        case (str(), "==", str()):
            explanation = list(
                _compare_eq_text(
                    left, right, highlighter, verbose, assertion_text_diff_style
                )
            )
        # Although the common order should be obtained == approx(...), allow both ways.
        case (_, "==", ApproxBase() as approx):
            explanation = approx._repr_compare(left)
        case (ApproxBase() as approx, "==", _):
            explanation = approx._repr_compare(right)
        case (_, "==", _) if type(left) is type(right) and (
            isdatacls(left) or isattrs(left) or isnamedtuple(left)
        ):
            # Note: unlike dataclasses/attrs, namedtuples compare only the
            # field values, not the type or field names. But this branch
            # intentionally only handles the same-type case, which was often
            # used in older code bases before dataclasses/attrs were available.
            explanation = list(
                _compare_eq_cls(
                    left, right, highlighter, verbose, assertion_text_diff_style
                )
            )
        # ``Sequence`` matches ``str`` too; the guard excludes those after the
        # ``(str(), "==", str())`` case above has handled the text case.
        case (Sequence(), "==", Sequence()) if issequence(left) and issequence(right):
            explanation = list(_compare_eq_sequence(left, right, highlighter, verbose))
        case (AbstractSet(), "==", AbstractSet()):
            explanation = _compare_eq_set(left, right, highlighter, verbose)
        case (Mapping(), "==", Mapping()):
            explanation = list(_compare_eq_mapping(left, right, highlighter, verbose))
        case (_, "==", _):
            # No specialised ``==`` diff, but the iterable extension below may
            # still apply.
            explanation = []
        case (str(), "not in", str()):
            return list(_notin_text(left, right, verbose))
        case (AbstractSet(), "!=" | ">=" | "<=" | ">" | "<", AbstractSet()):
            return SET_COMPARISON_FUNCTIONS[op](left, right, highlighter, verbose)
        case _:
            return None

    # Only the ``==`` cases reach here (others returned above); add the iterable
    # extension when applicable.
    if isiterable(left) and isiterable(right):
        explanation.extend(_compare_eq_iterable(left, right, highlighter, verbose))
    return explanation


def _compare_eq_cls(
    left: object,
    right: object,
    highlighter: _HighlightFunc,
    verbose: int,
    assertion_text_diff_style: _AssertionTextDiffStyle,
) -> Iterator[str]:
    if not has_default_eq(left):
        return
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

    if same or diff:
        yield ""
    if same and verbose < 2:
        yield f"Omitting {len(same)} identical items, use -vv to show"
    elif same:
        yield "Matching attributes:"
        yield from highlighter(pprint.pformat(same)).splitlines()
    if diff:
        yield "Differing attributes:"
        yield from highlighter(pprint.pformat(diff)).splitlines()
        for field in diff:
            field_left = getattr(left, field)
            field_right = getattr(right, field)
            yield ""
            yield f"Drill down into differing attribute {field}:"
            yield f"{indent}{field}: {highlighter(repr(field_left))} != {highlighter(repr(field_right))}"
            for line in (
                _compare_eq_any(
                    "==",
                    field_left,
                    field_right,
                    highlighter,
                    verbose,
                    assertion_text_diff_style,
                )
                or []
            ):
                yield indent + line
