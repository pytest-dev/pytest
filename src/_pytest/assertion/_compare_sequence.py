from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence

from _pytest._io.pprint import PrettyPrinter
from _pytest._io.saferepr import saferepr
from _pytest.assertion._typing import _HighlightFunc
from _pytest.assertion._typing import NO_TRUNCATION_BUDGET
from _pytest.assertion._typing import TruncationBudget
from _pytest.compat import running_on_ci


def _compare_eq_iterable(
    left: Iterable[object],
    right: Iterable[object],
    highlighter: _HighlightFunc,
    verbose: int = 0,
    truncation_budget: TruncationBudget = NO_TRUNCATION_BUDGET,
) -> Iterator[str]:
    if verbose <= 0 and not running_on_ci():
        yield "Use -v to get more diff"
        return
    # dynamic import to speedup pytest
    import difflib

    pp = PrettyPrinter()
    # ``pformat_lines`` spells an unbounded dimension ``None``; the budget spells it ``0``.
    max_lines = truncation_budget.max_lines or None
    max_chars = truncation_budget.max_chars or None
    left_formatting = pp.pformat_lines(left, max_lines=max_lines, max_chars=max_chars)
    right_formatting = pp.pformat_lines(right, max_lines=max_lines, max_chars=max_chars)

    yield ""
    yield "Full diff:"
    # "right" is the expected base against which we compare "left",
    # see https://github.com/pytest-dev/pytest/issues/3333
    # Highlight each ndiff line individually so the streaming truncator can
    # stop pulling from ``difflib.ndiff`` once its budget is full; the diff
    # lexer is line-oriented, so per-line highlighting is equivalent.
    for line in difflib.ndiff(right_formatting, left_formatting):
        yield highlighter(line.rstrip(), lexer="diff")


def _compare_eq_sequence(
    left: Sequence[object],
    right: Sequence[object],
    highlighter: _HighlightFunc,
    verbose: int = 0,
) -> Iterator[str]:
    comparing_bytes = isinstance(left, bytes) and isinstance(right, bytes)
    len_left = len(left)
    len_right = len(right)
    for i in range(min(len_left, len_right)):
        if left[i] != right[i]:
            if comparing_bytes:
                # when comparing bytes, we want to see their ascii representation
                # instead of their numeric values (#5260)
                # using a slice gives us the ascii representation:
                # >>> s = b'foo'
                # >>> s[0]
                # 102
                # >>> s[0:1]
                # b'f'
                left_value: object = left[i : i + 1]
                right_value: object = right[i : i + 1]
            else:
                left_value = left[i]
                right_value = right[i]

            yield (
                f"At index {i} diff:"
                f" {highlighter(repr(left_value))} != {highlighter(repr(right_value))}"
            )
            break

    if comparing_bytes:
        # when comparing bytes, it doesn't help to show the "sides contain one or more
        # items" longer explanation, so skip it
        return

    len_diff = len_left - len_right
    if len_diff:
        if len_diff > 0:
            dir_with_more = "Left"
            extra = saferepr(left[len_right])
        else:
            len_diff = 0 - len_diff
            dir_with_more = "Right"
            extra = saferepr(right[len_left])

        if len_diff == 1:
            yield f"{dir_with_more} contains one more item: {highlighter(extra)}"
        else:
            yield f"{dir_with_more} contains {len_diff} more items, first extra item: {highlighter(extra)}"
