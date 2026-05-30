from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Sequence

from _pytest.assertion._typing import _HighlightFunc


# Above this combined input size (in characters), ``difflib.ndiff`` becomes
# pathologically slow: its character-level "fancy replace" step is quadratic in
# the size of the differing region, so a few tens of kilobytes of differing text
# can hang for minutes (see issue #8998).
NDIFF_MAX_INPUT_SIZE = 10_000

# Above this number of lines, both ``ndiff`` and ``unified_diff`` get slow,
# since the underlying ``SequenceMatcher`` is quadratic in the number of lines
# (a large nested structure can pretty-print to hundreds of thousands of lines).
# We both fall back and cap the fallback's input at this many lines.
DIFF_MAX_LINES = 1_000


def ndiff_too_slow(left_lines: Sequence[str], right_lines: Sequence[str]) -> bool:
    """Return True if ``difflib.ndiff`` would likely be pathologically slow."""
    if len(left_lines) > DIFF_MAX_LINES or len(right_lines) > DIFF_MAX_LINES:
        return True
    size = sum(len(line) for line in left_lines) + sum(
        len(line) for line in right_lines
    )
    return size > NDIFF_MAX_INPUT_SIZE


def fast_unified_diff(
    left_lines: Sequence[str],
    right_lines: Sequence[str],
    highlighter: _HighlightFunc,
) -> Iterator[str]:
    """Yield a fast, coarse line-level diff for inputs too large for ``ndiff``.

    Unlike ``ndiff`` this does not produce character-level "?" guide lines, and
    it only diffs the first ``DIFF_MAX_LINES`` lines of each side, but it
    completes in milliseconds where ``ndiff`` would hang (see issue #8998).

    "right" is the expected base against which we compare "left",
    see https://github.com/pytest-dev/pytest/issues/3333.
    """
    from difflib import unified_diff

    yield (
        f"Diff too large to compute in full (over {NDIFF_MAX_INPUT_SIZE} "
        "characters); showing a faster line-level diff instead:"
    )
    left = [line.rstrip("\n") for line in left_lines[:DIFF_MAX_LINES]]
    right = [line.rstrip("\n") for line in right_lines[:DIFF_MAX_LINES]]
    hidden = max(len(left_lines), len(right_lines)) - DIFF_MAX_LINES
    if hidden > 0:
        yield f"Diffing only the first {DIFF_MAX_LINES} lines; {hidden} more hidden"
    diff = unified_diff(right, left, n=3, lineterm="")
    # The first two lines are the always-empty "--- "/"+++ " file headers.
    next(diff, None)
    next(diff, None)
    yield from highlighter("\n".join(diff), lexer="diff").splitlines()
