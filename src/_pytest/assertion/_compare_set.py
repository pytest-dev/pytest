from __future__ import annotations

from collections.abc import Callable
from collections.abc import Set as AbstractSet
from typing import TypeAlias

from _pytest._io.saferepr import saferepr
from _pytest.assertion._typing import _HighlightFunc


def _set_one_sided_diff(
    posn: str,
    set1: AbstractSet[object],
    set2: AbstractSet[object],
    highlighter: _HighlightFunc,
) -> list[str]:
    explanation = []
    diff = set1 - set2
    if diff:
        explanation.append(f"Extra items in the {posn} set:")
        for item in diff:
            explanation.append(highlighter(saferepr(item)))
    return explanation


def _compare_eq_set(
    left: AbstractSet[object],
    right: AbstractSet[object],
    highlighter: _HighlightFunc,
    verbose: int = 0,
) -> list[str]:
    explanation = []
    explanation.extend(_set_one_sided_diff("left", left, right, highlighter))
    explanation.extend(_set_one_sided_diff("right", right, left, highlighter))
    return explanation


def _compare_gt_set(
    left: AbstractSet[object],
    right: AbstractSet[object],
    highlighter: _HighlightFunc,
    verbose: int = 0,
) -> list[str]:
    explanation = _compare_gte_set(left, right, highlighter)
    if not explanation:
        return ["Both sets are equal"]
    return explanation


def _compare_lt_set(
    left: AbstractSet[object],
    right: AbstractSet[object],
    highlighter: _HighlightFunc,
    verbose: int = 0,
) -> list[str]:
    explanation = _compare_lte_set(left, right, highlighter)
    if not explanation:
        return ["Both sets are equal"]
    return explanation


def _compare_gte_set(
    left: AbstractSet[object],
    right: AbstractSet[object],
    highlighter: _HighlightFunc,
    verbose: int = 0,
) -> list[str]:
    return _set_one_sided_diff("right", right, left, highlighter)


def _compare_lte_set(
    left: AbstractSet[object],
    right: AbstractSet[object],
    highlighter: _HighlightFunc,
    verbose: int = 0,
) -> list[str]:
    return _set_one_sided_diff("left", left, right, highlighter)


SetComparisonFunction: TypeAlias = Callable[
    [AbstractSet[object], AbstractSet[object], _HighlightFunc, int],
    list[str],
]

SET_COMPARISON_FUNCTIONS: dict[str, SetComparisonFunction] = {
    # == can't be done here without a prior refactor because there's an additional
    # explanation for iterable in _compare_eq_any
    # "==": _compare_eq_set,
    "!=": lambda *a, **kw: ["Both sets are equal"],
    ">=": _compare_gte_set,
    "<=": _compare_lte_set,
    ">": _compare_gt_set,
    "<": _compare_lt_set,
}
