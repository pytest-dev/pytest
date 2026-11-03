from __future__ import annotations

import io
import re
import sys

from _pytest._code import ExceptionInfo
from _pytest._code.matching import check_regex
from _pytest._code.matching import check_type
from _pytest._code.matching import CheckFailure
from _pytest._code.matching import FlattenHint
from _pytest._code.matching import MatchFailure
from _pytest._code.matching import Nested
from _pytest._code.matching import NoException
from _pytest._code.matching import NotAnExceptionGroup
from _pytest._code.matching import PairingDetails
from _pytest._code.matching import PartiallyMatched
from _pytest._code.matching import RegexMismatch
from _pytest._code.matching import TooFewExceptions
from _pytest._code.matching import TypeMismatch
from _pytest._code.matching import UnexpectedExceptions
import pytest
from pytest import RaisesExc
from pytest import RaisesGroup


if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup


def render_rich(renderable: object, width: int = 100) -> str:
    from rich.console import Console

    buf = io.StringIO()
    Console(file=buf, width=width, force_terminal=False, color_system=None).print(
        renderable
    )
    return buf.getvalue()


class TestCheckType:
    def test_match_and_accept_all(self) -> None:
        assert check_type(ValueError, ValueError()) is None
        assert check_type((KeyError, ValueError), ValueError()) is None
        # No expected type means any exception is fine.
        assert check_type(None, ValueError()) is None
        assert check_type((), ValueError()) is None

    def test_mismatch(self) -> None:
        failure = check_type(KeyError, ValueError())
        assert failure == TypeMismatch(actual="ValueError", expected="KeyError")
        assert failure.to_text() == "`ValueError()` is not an instance of `KeyError`"

    def test_unexpected_nested_group(self) -> None:
        failure = check_type(ValueError, ExceptionGroup("", [KeyError()]))
        assert failure is not None
        assert failure.unexpected_nested_group
        assert (
            failure.to_text()
            == "Unexpected nested `ExceptionGroup()`, expected `ValueError`"
        )


class TestCheckRegex:
    def test_match(self) -> None:
        assert check_regex("foo", "a foo b") is None
        assert check_regex(re.compile("FOO", re.IGNORECASE), "foo") is None

    def test_mismatch_text(self) -> None:
        failure = check_regex("foo", "bar")
        assert isinstance(failure, RegexMismatch)
        assert failure.to_text() == (
            "Regex pattern did not match.\n"
            "  Expected regex: 'foo'\n"
            "  Actual message: 'bar'"
        )

    def test_flagless_compiled_pattern_displays_like_str(self) -> None:
        assert check_regex(re.compile("foo"), "bar") == check_regex("foo", "bar")
        flagged = check_regex(re.compile("foo", re.IGNORECASE), "bar")
        assert flagged is not None
        assert "re.compile('foo', re.IGNORECASE)" in flagged.to_text()

    def test_escape_hint(self) -> None:
        failure = check_regex("a(b)", "a(b)")
        assert failure is not None
        assert failure.escape_hint
        assert failure.to_text().endswith("\n Did you mean to `re.escape()` the regex?")

    def test_subject(self) -> None:
        failure = check_regex("foo", "bar", subject="the `ExceptionGroup()`")
        assert failure is not None
        assert failure.to_text().startswith(
            "Regex pattern did not match the `ExceptionGroup()`.\n"
        )

    def test_diff_for_fully_escaped_literal(self) -> None:
        failure = check_regex("^foo$", "fob", rawmatch="foo")
        assert failure is not None
        assert failure.diff is not None
        assert failure.to_text() == failure.diff
        assert "foo" in failure.diff
        assert "fob" in failure.diff


class TestExceptionInfoSharesImplementation:
    def test_match_message_equals_raisesexc_message(self) -> None:
        try:
            raise ValueError("bar")
        except ValueError as e:
            exc = e
            excinfo = ExceptionInfo.from_exception(e)
        raiser = RaisesExc(ValueError, match="foo")
        assert not raiser.matches(exc)
        with pytest.raises(AssertionError) as ei:
            excinfo.match("foo")
        assert str(ei.value) == raiser.fail_reason

    def test_match_with_compiled_pattern(self) -> None:
        try:
            raise ValueError("bar")
        except ValueError as e:
            excinfo = ExceptionInfo.from_exception(e)
        with pytest.raises(AssertionError) as ei:
            excinfo.match(re.compile("foo"))
        assert "Expected regex: 'foo'" in str(ei.value)

    def test_group_contains_regex(self) -> None:
        try:
            raise ExceptionGroup("g", [ValueError("a foo"), KeyError("bar")])
        except ExceptionGroup as e:
            excinfo = ExceptionInfo.from_exception(e)
        assert excinfo.group_contains(ValueError, match="foo")
        assert not excinfo.group_contains(ValueError, match="bar")
        assert excinfo.group_contains(KeyError, match="bar")


class TestRaiserFailures:
    def test_raisesexc_failure_kinds(self) -> None:
        raiser = RaisesExc(ValueError, match="foo", check=lambda e: False)

        def failure() -> MatchFailure | None:
            # A function, so that mypy does not narrow ``raiser._failure`` across calls.
            return raiser._failure

        assert failure() is None
        assert raiser.fail_reason is None

        assert not raiser.matches(None)
        assert failure() == NoException()

        assert not raiser.matches(KeyError())
        assert isinstance(failure(), TypeMismatch)

        assert not raiser.matches(ValueError("bar"))
        assert isinstance(failure(), RegexMismatch)

        assert not raiser.matches(ValueError("foo"))
        last = failure()
        assert isinstance(last, CheckFailure)
        assert raiser.fail_reason == last.to_text()

    def test_failure_is_cleared_on_success(self) -> None:
        raiser = RaisesExc(ValueError)
        assert not raiser.matches(KeyError())
        assert raiser.fail_reason is not None
        assert raiser.matches(ValueError())
        assert raiser._failure is None
        assert raiser.fail_reason is None

    def test_group_not_a_group(self) -> None:
        raiser = RaisesGroup(ValueError)
        assert not raiser.matches(ValueError())
        assert raiser._failure == NotAnExceptionGroup(
            "ValueError", would_match_unwrapped=True
        )

    def test_group_too_few_and_unexpected(self) -> None:
        raiser = RaisesGroup(ValueError, TypeError)
        assert not raiser.matches(ExceptionGroup("", [ValueError()]))
        assert raiser._failure == TooFewExceptions(matched=1, expected=("TypeError",))

        raiser = RaisesGroup(ValueError)
        assert not raiser.matches(ExceptionGroup("", [ValueError(), KeyError()]))
        assert isinstance(raiser._failure, UnexpectedExceptions)
        assert raiser._failure.matched == 1

    def test_group_single_pair_is_nested_failure(self) -> None:
        raiser = RaisesGroup(RaisesExc(ValueError, match="foo"))
        assert not raiser.matches(ExceptionGroup("", [ValueError("bar")]))
        failure = raiser._failure
        assert isinstance(failure, Nested)
        assert failure.label == "RaisesExc(ValueError, match='foo')"
        assert isinstance(failure.reason, RegexMismatch)

    def test_group_partially_matched(self) -> None:
        raiser = RaisesGroup(ValueError, RaisesExc(TypeError, match="foo"))
        assert not raiser.matches(
            ExceptionGroup("", [ValueError(), TypeError("bar")]),
        )
        failure = raiser._failure
        assert isinstance(failure, PartiallyMatched)
        assert failure.matched == 1
        assert isinstance(failure.inner, Nested)

    def test_group_pairing_details(self) -> None:
        raiser = RaisesGroup(ValueError, TypeError)
        assert not raiser.matches(ExceptionGroup("", [KeyError(), IndexError()]))
        failure = raiser._failure
        assert isinstance(failure, PairingDetails)
        assert failure.problem == "both"
        assert [e.label for e in failure.unmatched_expected] == [
            "ValueError",
            "TypeError",
        ]
        assert [a.actual for a in failure.unmatched_actual] == [
            "KeyError()",
            "IndexError()",
        ]
        assert all(
            isinstance(entry, TypeMismatch)
            for a in failure.unmatched_actual
            for entry in a.entries
        )

    def test_group_flatten_hint(self) -> None:
        raiser = RaisesGroup(ValueError)
        inner = ExceptionGroup("", [ValueError()])
        assert not raiser.matches(ExceptionGroup("", [inner]))
        assert isinstance(raiser._failure, FlattenHint)

    def test_group_check_failure_on_group(self) -> None:
        raiser = RaisesGroup(ValueError, check=lambda e: isinstance(e, ValueError))
        assert not raiser.matches(ExceptionGroup("", [ValueError()]))
        failure = raiser._failure
        assert isinstance(failure, CheckFailure)
        assert failure.on_type == "ExceptionGroup"
        # The check would have passed for the lone sub-exception.
        assert failure.suggestion == ("ValueError", "ValueError")

        raiser = RaisesGroup(ValueError, check=lambda e: False)
        assert not raiser.matches(ExceptionGroup("", [ValueError()]))
        assert isinstance(raiser._failure, CheckFailure)
        assert raiser._failure.suggestion is None


class TestRichRendering:
    def test_leaf_failure_renders_its_text(self) -> None:
        failure = check_regex("foo", "bar")
        assert failure is not None
        out = render_rich(failure)
        assert "Regex pattern did not match." in out
        assert "Expected regex: 'foo'" in out

    def test_pairing_details_is_a_tree(self) -> None:
        from rich.tree import Tree

        raiser = RaisesGroup(ValueError, RaisesExc(TypeError, match="foo"))
        assert not raiser.matches(
            ExceptionGroup("", [KeyError(), TypeError("bar"), IndexError()])
        )
        failure = raiser._failure
        assert isinstance(failure, MatchFailure)
        assert isinstance(failure.to_rich(), Tree)
        out = render_rich(failure)
        assert "Expected exceptions without a match" in out
        assert "Raised exceptions without a match" in out
        assert "ValueError" in out
        assert "KeyError()" in out
        assert "RaisesExc(TypeError, match='foo')" in out

    def test_nested_failure_is_a_tree(self) -> None:
        from rich.tree import Tree

        raiser = RaisesGroup(RaisesExc(ValueError, match="foo"))
        assert not raiser.matches(ExceptionGroup("", [ValueError("bar")]))
        failure = raiser._failure
        assert isinstance(failure, Nested)
        assert isinstance(failure.to_rich(), Tree)
        out = render_rich(failure)
        assert "RaisesExc(ValueError, match='foo')" in out
        assert "Regex pattern did not match." in out
