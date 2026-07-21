from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar
from typing import Literal
from typing import Protocol
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from _pytest.config import Config


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

    @classmethod
    def from_config(cls, config: Config) -> TruncationBudget:
        """Build a budget from the ``truncation_limit_*`` ini options.

        Both options are registered with ``type=int | str`` for
        backward compatibility, so :meth:`~_pytest.config.Config.getini` may
        return an ``int`` (native TOML value) or a ``str`` (INI files, ``-o``
        overrides); it returns ``None`` when the option is unset, which falls
        back to the default limit.
        """
        max_lines = config.getini("truncation_limit_lines")
        max_chars = config.getini("truncation_limit_chars")
        return cls(
            max_lines=cls.DEFAULT_MAX_LINES if max_lines is None else int(max_lines),
            max_chars=cls.DEFAULT_MAX_CHARS if max_chars is None else int(max_chars),
        )


class _HighlightFunc(Protocol):  # noqa: PYI046
    def __call__(self, source: str, lexer: Literal["diff", "python"] = "python") -> str:
        """Apply highlighting to the given source."""
