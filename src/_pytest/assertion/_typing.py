from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar
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

    #: Default limits applied when the corresponding ini option is left unset.
    DEFAULT_MAX_LINES: ClassVar[int] = 8
    DEFAULT_MAX_CHARS: ClassVar[int] = DEFAULT_MAX_LINES * 80

    max_lines: int = DEFAULT_MAX_LINES
    max_chars: int = DEFAULT_MAX_CHARS


# Reusable "no cap" budget, used as a default argument (B008).
NO_TRUNCATION_BUDGET = TruncationBudget(max_lines=0, max_chars=0)


class _HighlightFunc(Protocol):  # noqa: PYI046
    def __call__(self, source: str, lexer: Literal["diff", "python"] = "python") -> str:
        """Apply highlighting to the given source."""
