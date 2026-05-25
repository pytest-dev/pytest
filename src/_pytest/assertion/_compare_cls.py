from __future__ import annotations

import dataclasses
import pprint

from _pytest.assertion._typing import _AssertionTextDiffStyle
from _pytest.assertion._typing import _HighlightFunc


def _compare_eq_cls(
    left: object,
    right: object,
    highlighter: _HighlightFunc,
    verbose: int,
    assertion_text_diff_style: _AssertionTextDiffStyle,
) -> list[str]:
    # Deferred import to avoid a cycle: util.py imports from this module.
    from _pytest.assertion.util import _compare_eq_any
    from _pytest.assertion.util import has_default_eq
    from _pytest.assertion.util import isattrs
    from _pytest.assertion.util import isdatacls
    from _pytest.assertion.util import isnamedtuple

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
