"""Plain-data results of matching an exception against an expectation.

``ExceptionInfo.match``, ``ExceptionInfo.group_contains``, :class:`pytest.RaisesExc`
and :class:`pytest.RaisesGroup` all answer the same question - "does this exception
satisfy these expectations?" - and used to answer it with ad-hoc strings stitched
together at the point of failure.

The primitives in this module (:func:`check_type`, :func:`check_regex`) are the one
shared implementation of that check, and they report failures as immutable
:class:`MatchFailure` objects. A failure can be rendered as plain text
(:meth:`MatchFailure.to_text`, byte-for-byte what ``fail_reason`` used to contain)
or as a ``rich`` renderable (:meth:`MatchFailure.__rich_console__`), where mismatches
of nested :class:`pytest.RaisesGroup` become a :class:`rich.tree.Tree`.

This module deliberately imports nothing from ``_pytest.raises`` or
``_pytest._code.code`` so both can depend on it.
"""

from __future__ import annotations

import dataclasses
import re
from re import Pattern
import sys
from textwrap import indent
from typing import ClassVar
from typing import Final
from typing import Literal
from typing import TYPE_CHECKING


if sys.version_info < (3, 11):
    from exceptiongroup import BaseExceptionGroup

if TYPE_CHECKING:
    from rich.console import Console
    from rich.console import ConsoleOptions
    from rich.console import RenderableType
    from rich.console import RenderResult


# String patterns default to including the unicode flag.
REGEX_NO_FLAGS: Final[int] = re.compile(r"").flags


def match_pattern(match: Pattern[str]) -> str | Pattern[str]:
    """Remove redundant ``re.compile`` calls when printing a regex."""
    return match.pattern if match.flags == REGEX_NO_FLAGS else match


def backquote(s: str) -> str:
    return "`" + s + "`"


def exception_type_name(
    e: type[BaseException] | tuple[type[BaseException], ...],
) -> str:
    if isinstance(e, type):
        return e.__name__
    if len(e) == 1:
        return e[0].__name__
    return "(" + ", ".join(ee.__name__ for ee in e) + ")"


@dataclasses.dataclass(frozen=True)
class MatchFailure:
    """Why an exception did not match an expectation.

    Instances are immutable and made of plain strings and nested
    :class:`MatchFailure` objects, so they can be stored, compared and
    re-rendered without access to the exceptions they describe.
    """

    def to_text(self) -> str:
        """The failure as plain text."""
        raise NotImplementedError

    def __str__(self) -> str:
        return self.to_text()

    def to_rich(self) -> RenderableType:
        """The failure as a ``rich`` renderable."""
        from rich.text import Text

        return Text(self.to_text())

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.to_rich()


@dataclasses.dataclass(frozen=True)
class NoException(MatchFailure):
    """``None`` was given where an exception was expected."""

    def to_text(self) -> str:
        return "exception is None"


@dataclasses.dataclass(frozen=True)
class TypeMismatch(MatchFailure):
    """The exception is not an instance of the expected type(s)."""

    actual: str
    expected: str
    # An exception group was found where a non-group type was expected.
    unexpected_nested_group: bool = False

    def to_text(self) -> str:
        actual = backquote(self.actual + "()")
        expected = backquote(self.expected)
        if self.unexpected_nested_group:
            return f"Unexpected nested {actual}, expected {expected}"
        return f"{actual} is not an instance of {expected}"


@dataclasses.dataclass(frozen=True)
class NotAnExceptionGroup(MatchFailure):
    """A non-group exception was given to a ``RaisesGroup``."""

    actual: str
    would_match_unwrapped: bool = False

    def to_text(self) -> str:
        # Only the type is printed, as the repr would likely be quite long.
        text = f"`{self.actual}()` is not an exception group"
        if self.would_match_unwrapped:
            text += ", but would match with `allow_unwrapped=True`"
        return text


@dataclasses.dataclass(frozen=True)
class RegexSuggestion:
    """A lone sub-exception matched the regex that the enclosing group did not."""

    expected: str
    type_name: str
    pattern: str


@dataclasses.dataclass(frozen=True)
class RegexMismatch(MatchFailure):
    """A regex did not match the stringified exception."""

    expected: str
    actual: str
    # e.g. "the `ExceptionGroup()`", to reduce confusion when a group is matched.
    subject: str | None = None
    # Set if the regex is a fully escaped literal, in which case a diff is shown.
    diff: str | None = None
    escape_hint: bool = False
    suggestion: RegexSuggestion | None = None

    def to_text(self) -> str:
        if self.diff is not None:
            text = self.diff
        else:
            subject = f" {self.subject}" if self.subject else ""
            text = (
                f"Regex pattern did not match{subject}.\n"
                f"  Expected regex: {self.expected}\n"
                f"  Actual message: {self.actual}"
            )
            if self.escape_hint:
                text += "\n Did you mean to `re.escape()` the regex?"
        if self.suggestion is not None:
            text += (
                f"\n"
                f" but matched the expected `{self.suggestion.expected}`.\n"
                f" You might want "
                f"`RaisesGroup(RaisesExc({self.suggestion.type_name}, match={self.suggestion.pattern}))`"
            )
        return text


@dataclasses.dataclass(frozen=True)
class CheckFailure(MatchFailure):
    """The ``check`` callable did not return ``True``."""

    # Empty to suppress repeated printing of the callable when nested.
    check_repr: str = ""
    # Set when the check was run against an exception group.
    on_type: str | None = None
    # Set when the check does pass for the lone expected sub-exception.
    suggestion: tuple[str, str] | None = None

    def to_text(self) -> str:
        check = f" {self.check_repr}" if self.check_repr else ""
        text = f"check{check} did not return True"
        if self.on_type is not None:
            text += f" on the {self.on_type}"
        if self.suggestion is not None:
            expected, name = self.suggestion
            text += (
                f", but did return True for the expected {expected}."
                f" You might want RaisesGroup(RaisesExc({name}, check=<...>))"
            )
        return text


@dataclasses.dataclass(frozen=True)
class Nested(MatchFailure):
    """A failure of a nested expectation, labelled with that expectation's repr."""

    label: str
    reason: MatchFailure

    def to_text(self) -> str:
        reason = self.reason.to_text()
        if reason.startswith("\n"):
            return f"\n{self.label}: {indent(reason, '  ')}"
        return f"{self.label}: {reason}"

    def to_rich(self) -> RenderableType:
        from rich.text import Text
        from rich.tree import Tree

        tree = Tree(Text(self.label))
        tree.add(self.reason.to_rich())
        return tree


@dataclasses.dataclass(frozen=True)
class FlattenHint(MatchFailure):
    """The match would succeed with ``flatten_subgroups=True``."""

    inner: MatchFailure

    def to_text(self) -> str:
        text = self.inner.to_text()
        # Only indent if it's a single-line reason. In a multi-line there's already
        # indented lines that this does not belong to.
        pad = "  " if "\n" not in text else ""
        return f"{text}\n{pad}Did you mean to use `flatten_subgroups=True`?"

    def to_rich(self) -> RenderableType:
        from rich.console import Group
        from rich.text import Text

        return Group(
            self.inner.to_rich(), Text("Did you mean to use `flatten_subgroups=True`?")
        )


def _matched_prefix(matched: int) -> str:
    if not matched:
        return ""
    return f"{matched} matched exception{'s' if matched > 1 else ''}. "


@dataclasses.dataclass(frozen=True)
class UnexpectedExceptions(MatchFailure):
    """Every expectation was met, but there are raised exceptions left over."""

    matched: int
    actual: tuple[str, ...]

    def to_text(self) -> str:
        return (
            f"{_matched_prefix(self.matched)}Unexpected exception(s):"
            f" [{', '.join(self.actual)}]"
        )


@dataclasses.dataclass(frozen=True)
class TooFewExceptions(MatchFailure):
    """Every raised exception was expected, but some expectations are unmet."""

    matched: int
    expected: tuple[str, ...]

    def to_text(self) -> str:
        return (
            f"{_matched_prefix(self.matched)}Too few exceptions raised,"
            f" found no match for: [{', '.join(self.expected)}]"
        )


@dataclasses.dataclass(frozen=True)
class PartiallyMatched(MatchFailure):
    """Some exceptions were paired up successfully, the remaining pair did not match."""

    matched: int
    inner: MatchFailure

    def to_text(self) -> str:
        return f"{_matched_prefix(self.matched)}{self.inner.to_text()}"

    def to_rich(self) -> RenderableType:
        from rich.console import Group
        from rich.text import Text

        if not self.matched:
            return self.inner.to_rich()
        return Group(Text(_matched_prefix(self.matched).rstrip()), self.inner.to_rich())


@dataclasses.dataclass(frozen=True)
class PairedWith(MatchFailure):
    """``matched`` also satisfies an expectation, but was already paired with ``partner``."""

    matched: str
    partner: str

    def to_text(self) -> str:
        return (
            f"It matches {backquote(self.matched)}"
            f" which was paired with {backquote(self.partner)}"
        )


@dataclasses.dataclass(frozen=True)
class UnmatchedExpected:
    """An expectation that no raised exception was paired with."""

    label: str
    paired_elsewhere: tuple[PairedWith, ...] = ()


@dataclasses.dataclass(frozen=True)
class UnmatchedActual:
    """A raised exception that no expectation was paired with.

    ``entries`` holds, for each expectation of interest, either the
    reason it did not match or the other exception it was paired with.
    """

    actual: str
    entries: tuple[MatchFailure, ...] = ()


@dataclasses.dataclass(frozen=True)
class PairingDetails(MatchFailure):
    """The full table of why expected and raised exceptions could not be paired up."""

    matched: int
    problem: Literal["too_few", "unexpected", "both"]
    unmatched_expected: tuple[UnmatchedExpected, ...]
    unmatched_actual: tuple[UnmatchedActual, ...]
    greedy_hint: bool = False

    _HEADINGS: ClassVar[dict[str, str]] = {
        "too_few": "Too few exceptions raised!",
        "unexpected": "Unexpected exception(s)!",
        "both": "",
    }
    _GREEDY_HINT: ClassVar[str] = (
        "There exist a possible match when attempting an exhaustive check,"
        " but RaisesGroup uses a greedy algorithm. "
        "Please make your expected exceptions more stringent with `RaisesExc` etc"
        " so the greedy algorithm can function."
    )

    def to_text(self) -> str:
        indent_1 = " " * 2
        indent_2 = " " * 4
        s = ""
        if self.matched:
            s += f"\n{_matched_prefix(self.matched)}"
        heading = self._HEADINGS[self.problem]
        if heading:
            s += f"\n{heading}"

        if self.unmatched_expected:
            s += "\nThe following expected exceptions did not find a match:"
        for exp in self.unmatched_expected:
            s += f"\n{indent_1}{exp.label}"
            for paired in exp.paired_elsewhere:
                s += f"\n{indent_2}{paired.to_text()}"

        if self.unmatched_actual:
            s += "\nThe following raised exceptions did not find a match"
        for act in self.unmatched_actual:
            s += f"\n{indent_1}{act.actual}:"
            for entry in act.entries:
                if isinstance(entry, PairedWith):
                    s += f"\n{indent_2}{entry.to_text()}"
                else:
                    text = entry.to_text()
                    if text[0] != "\n":
                        s += "\n"
                    s += indent(text, indent_2)

        if self.greedy_hint:
            s += f"\n{self._GREEDY_HINT}"
        return s

    def to_rich(self) -> RenderableType:
        from rich.text import Text
        from rich.tree import Tree

        heading = self._HEADINGS[self.problem]
        label = _matched_prefix(self.matched).rstrip()
        if heading:
            label = f"{label} {heading}".strip()
        tree = Tree(Text(label or "Exceptions could not be paired up"))

        if self.unmatched_expected:
            branch = tree.add(Text("Expected exceptions without a match", "bold"))
            for exp in self.unmatched_expected:
                node = branch.add(Text(exp.label))
                for paired in exp.paired_elsewhere:
                    node.add(paired.to_rich())
        if self.unmatched_actual:
            branch = tree.add(Text("Raised exceptions without a match", "bold"))
            for act in self.unmatched_actual:
                node = branch.add(Text(act.actual))
                for entry in act.entries:
                    node.add(entry.to_rich())
        if self.greedy_hint:
            tree.add(Text(self._GREEDY_HINT, "italic"))
        return tree


def check_type(
    expected_type: type[BaseException] | tuple[type[BaseException], ...] | None,
    exception: BaseException,
) -> TypeMismatch | None:
    """Check that ``exception`` is an instance of ``expected_type``.

    ``None`` and ``()`` accept any exception.
    """
    if expected_type is None or expected_type == ():
        return None

    if isinstance(exception, expected_type):
        return None

    return TypeMismatch(
        actual=exception_type_name(type(exception)),
        expected=exception_type_name(expected_type),
        unexpected_nested_group=(
            isinstance(exception, BaseExceptionGroup)
            and isinstance(expected_type, type)
            and not issubclass(expected_type, BaseExceptionGroup)
        ),
    )


def check_regex(
    pattern: str | Pattern[str],
    actual: str,
    *,
    rawmatch: str | None = None,
    subject: str | None = None,
) -> RegexMismatch | None:
    """Check that ``pattern`` is found in ``actual`` using :func:`re.search`.

    :param rawmatch:
        If ``pattern`` is a fully escaped literal (anchored with ``^`` and ``$``),
        its unescaped text, which makes a failure show a diff.
    :param subject:
        What was matched, if not a plain exception. Reduces confusion when a
        group is matched instead of one of its sub-exceptions.
    """
    if re.search(pattern, actual):
        return None

    display = pattern if isinstance(pattern, str) else match_pattern(pattern)
    diff = None
    if rawmatch is not None:
        diff = _diff_literal(rawmatch, actual)
    return RegexMismatch(
        expected=repr(display),
        actual=repr(actual),
        subject=subject,
        diff=diff,
        escape_hint=display == actual,
    )


def _diff_literal(expected: str, actual: str) -> str:
    from _pytest.assertion.compare_text import _diff_text
    from _pytest.assertion.highlight import dummy_highlighter
    from _pytest.assertion.util import _config
    from _pytest.config import Config

    verbose = (
        _config.get_verbosity(Config.VERBOSITY_ASSERTIONS) if _config is not None else 0
    )
    diff = list(_diff_text(expected, actual, dummy_highlighter, verbose))
    return ("\n" if diff[0][0] == "-" else "") + "\n".join(diff)
