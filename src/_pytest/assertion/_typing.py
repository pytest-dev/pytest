from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from typing import Protocol


_AssertionTextDiffStyle = Literal["ndiff", "block"]


@dataclass(frozen=True, kw_only=True, slots=True)
class TruncationBudget:
    """Per-explanation budget for truncating assertion output.

    ``max_lines`` / ``max_chars`` mirror the ``truncation_limit_lines`` /
    ``truncation_limit_chars`` ini values: a positive limit bounds that
    dimension; ``0`` leaves it unbounded (the limit is disabled).
    """

    max_lines: int
    max_chars: int


class _HighlightFunc(Protocol):  # noqa: PYI046
    def __call__(self, source: str, lexer: Literal["diff", "python"] = "python") -> str:
        """Apply highlighting to the given source."""
