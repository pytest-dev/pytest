from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Sequence
from itertools import chain

from _pytest.assertion._typing import _HighlightFunc


# Past these limits ``difflib.ndiff`` becomes pathologically slow: its
# character-level "fancy replace" step compares every pair of similar lines in a
# differing block, so its cost grows with the *product* of the line count and
# the character count. A few hundred similar lines can already take seconds, and
# the pretty-printed form of a large list/dataclass takes minutes (see issue
# #8998). The limits below keep ``ndiff`` under roughly a second in the worst
# case. Above them we still run ``ndiff`` -- so the detailed diff is kept -- but
# only over a bounded prefix of the input.
NDIFF_MAX_INPUT_SIZE = 10_000  # characters (left + right)
DIFF_MAX_LINES = 100  # lines (left + right)


def ndiff_too_slow_for_text(left: str, right: str) -> bool:
    """Whether ``ndiff`` would be pathologically slow for these strings.

    Counts line separators instead of splitting into lines, so the check stays
    cheap even for huge inputs.
    """
    if left.count("\n") + right.count("\n") > DIFF_MAX_LINES:
        return True
    return len(left) + len(right) > NDIFF_MAX_INPUT_SIZE


def ndiff_too_slow_for_lines(
    left_lines: Sequence[str], right_lines: Sequence[str]
) -> bool:
    """Whether ``ndiff`` would be pathologically slow for these lines.

    Exits as soon as a limit is exceeded instead of measuring the whole input.
    """
    if len(left_lines) + len(right_lines) > DIFF_MAX_LINES:
        return True
    size = 0
    for line in chain(left_lines, right_lines):
        size += len(line)
        if size > NDIFF_MAX_INPUT_SIZE:
            return True
    return False


def truncated_ndiff(
    left_lines: Sequence[str],
    right_lines: Sequence[str],
    highlighter: _HighlightFunc,
) -> Iterator[str]:
    """Yield an ``ndiff`` over a bounded prefix of the input (issue #8998).

    The character-level diff is kept, but only for a slice small enough to
    compute quickly; the rest of the input is dropped.
    """
    from difflib import ndiff

    left = _bounded_prefix(left_lines, DIFF_MAX_LINES // 2, NDIFF_MAX_INPUT_SIZE // 2)
    right = _bounded_prefix(right_lines, DIFF_MAX_LINES // 2, NDIFF_MAX_INPUT_SIZE // 2)
    yield (
        f"Diff too large to show in full (over {NDIFF_MAX_INPUT_SIZE} characters "
        f"or {DIFF_MAX_LINES} lines); showing a truncated diff:"
    )
    # "right" is the expected base against which we compare "left",
    # see https://github.com/pytest-dev/pytest/issues/3333
    yield from highlighter(
        "\n".join(line.rstrip("\n") for line in ndiff(right, left)),
        lexer="diff",
    ).splitlines()


def _bounded_prefix(lines: Sequence[str], max_lines: int, max_chars: int) -> list[str]:
    """Return the longest prefix of ``lines`` within both limits.

    The line that would cross the character limit is included truncated, so a
    single huge line still yields some (bounded) output.
    """
    kept: list[str] = []
    chars = 0
    for line in lines:
        if len(kept) >= max_lines:
            break
        room = max_chars - chars
        if len(line) > room:
            if room > 0:
                kept.append(line[:room])
            break
        kept.append(line)
        chars += len(line)
    return kept
