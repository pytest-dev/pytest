from __future__ import annotations

from collections.abc import Iterator

from _pytest._io.saferepr import saferepr
from _pytest.assertion._typing import _AssertionTextDiffStyle
from _pytest.assertion._typing import _HighlightFunc
from _pytest.assertion._typing import NO_TRUNCATION_BUDGET
from _pytest.assertion._typing import TruncationBudget
from _pytest.assertion.highlight import dummy_highlighter
from _pytest.compat import assert_never


def _compare_eq_text(
    left: str,
    right: str,
    highlighter: _HighlightFunc,
    verbose: int,
    assertion_text_diff_style: _AssertionTextDiffStyle,
    truncation_budget: TruncationBudget = NO_TRUNCATION_BUDGET,
) -> Iterator[str]:
    match assertion_text_diff_style:
        case "block":
            yield from _diff_text_block(left, right)
        case "ndiff":
            yield from _diff_text(left, right, highlighter, verbose, truncation_budget)
        case unreachable:
            assert_never(unreachable)


def _diff_text_block(left: str, right: str) -> Iterator[str]:
    yield "Left:"
    yield from _format_text_block_lines(left)
    yield ""
    yield "Right:"
    yield from _format_text_block_lines(right)


def _format_text_block_lines(text: str) -> Iterator[str]:
    for line in text.split("\n"):
        yield f"  {line}"


def _diff_text(
    left: str,
    right: str,
    highlighter: _HighlightFunc,
    verbose: int = 0,
    truncation_budget: TruncationBudget = NO_TRUNCATION_BUDGET,
) -> Iterator[str]:
    """Yield the explanation for the diff between text.

    Unless --verbose is used this will skip leading and trailing
    characters which are identical to keep the diff minimal.

    When a truncation budget is set, the inputs to ``ndiff`` are capped
    first, so the truncated head may differ from the head of the
    unbounded diff.
    """
    from difflib import ndiff

    if verbose < 1:
        i = 0  # just in case left or right has zero length
        for i in range(min(len(left), len(right))):
            if left[i] != right[i]:
                break
        if i > 42:
            i -= 10  # Provide some context
            yield f"Skipping {i} identical leading characters in diff, use -v to show"
            left = left[i:]
            right = right[i:]
        if len(left) == len(right):
            for i in range(1, len(left) + 1):
                if left[-i] != right[-i]:
                    break
            if i > 42:
                i -= 10  # Provide some context
                yield (
                    f"Skipping {i} identical trailing "
                    "characters in diff, use -v to show"
                )
                left = left[:-i]
                right = right[:-i]
    keepends = True
    if left.isspace() or right.isspace():
        left = repr(str(left))
        right = repr(str(right))
        yield "Strings contain only whitespace, escaping them using repr()"
    left_lines = _cap_ndiff_input(left, keepends, truncation_budget)
    right_lines = _cap_ndiff_input(right, keepends, truncation_budget)
    # "right" is the expected base against which we compare "left",
    # see https://github.com/pytest-dev/pytest/issues/3333
    yield from highlighter(
        "\n".join(line.strip("\n") for line in ndiff(right_lines, left_lines)),
        lexer="diff",
    ).splitlines()


def _cap_ndiff_input(text: str, keepends: bool, budget: TruncationBudget) -> list[str]:
    """Cap an ``ndiff`` input to the truncation budget, as split lines.

    A char slice first (bounds a few huge lines, whose intraline diff is
    O(len^2)), then a line slice (bounds many lines). A ``0`` limit leaves
    that dimension unbounded.
    """
    if budget.max_chars > 0:
        text = text[: budget.max_chars]
    lines = text.splitlines(keepends)
    if budget.max_lines > 0:
        lines = lines[: budget.max_lines]
    return lines


def _notin_text(
    term: str,
    text: str,
    verbose: int = 0,
    truncation_budget: TruncationBudget = NO_TRUNCATION_BUDGET,
) -> Iterator[str]:
    index = text.find(term)
    head = text[:index]
    tail = text[index + len(term) :]
    correct_text = head + tail
    diff = _diff_text(text, correct_text, dummy_highlighter, verbose, truncation_budget)
    yield f"{saferepr(term, maxsize=42)} is contained here:"
    for line in diff:
        if line.startswith("Skipping"):
            continue
        if line.startswith("- "):
            continue
        if line.startswith("+ "):
            yield "  " + line[2:]
        else:
            yield line
