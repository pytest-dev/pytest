from __future__ import annotations

# several expected multi-line strings contain long lines. We don't wanna break them up
# as that makes it confusing to see where the line breaks are.
# ruff: noqa: E501
from contextlib import AbstractContextManager
import re
import sys

from _pytest._code import ExceptionInfo
from _pytest.outcomes import Failed
from _pytest.pytester import Pytester
from _pytest.raises import RaisesExc
from _pytest.raises import RaisesGroup
from _pytest.raises import repr_callable
import pytest


if sys.version_info < (3, 11):
    from exceptiongroup import BaseExceptionGroup
    from exceptiongroup import ExceptionGroup


def wrap_escape(s: str) -> str:
    return "^" + re.escape(s) + "$"


def fails_raises_group(msg: str, add_prefix: bool = True) -> RaisesExc[Failed]:
    assert msg[-1] != "\n", (
        "developer error, expected string should not end with newline"
    )
    prefix = "Raised exception group did not match: " if add_prefix else ""
    return pytest.raises(Failed, match=wrap_escape(prefix + msg))


def test_raises_group() -> None:
    with pytest.raises(
        TypeError,
        match=wrap_escape("expected exception must be a BaseException type, not 'int'"),
    ):
        RaisesExc(5)  # type: ignore[call-overload]
    with pytest.raises(
        ValueError,
        match=wrap_escape("expected exception must be a BaseException type, not 'int'"),
    ):
        RaisesExc(int)  # type: ignore[type-var]
    with pytest.raises(
        TypeError,
        # TODO: bad sentence structure
        match=wrap_escape(
            "expected exception must be a BaseException type, RaisesExc, or RaisesGroup, not an exception instance (ValueError)",
        ),
    ):
        RaisesGroup(ValueError())  # type: ignore[call-overload]
    with RaisesGroup(ValueError):
        raise ExceptionGroup("foo", (ValueError(),))

    with (
        fails_raises_group("`SyntaxError()` is not an instance of `ValueError`"),
        RaisesGroup(ValueError),
    ):
        raise ExceptionGroup("foo", (SyntaxError(),))

    # multiple exceptions
    with RaisesGroup(ValueError, SyntaxError):
        raise ExceptionGroup("foo", (ValueError(), SyntaxError()))

    # order doesn't matter
    with RaisesGroup(SyntaxError, ValueError):
        raise ExceptionGroup("foo", (ValueError(), SyntaxError()))

    # nested exceptions
    with RaisesGroup(RaisesGroup(ValueError)):
        raise ExceptionGroup("foo", (ExceptionGroup("bar", (ValueError(),)),))

    with RaisesGroup(
        SyntaxError,
        RaisesGroup(ValueError),
        RaisesGroup(RuntimeError),
    ):
        raise ExceptionGroup(
            "foo",
            (
                SyntaxError(),
                ExceptionGroup("bar", (ValueError(),)),
                ExceptionGroup("", (RuntimeError(),)),
            ),
        )


def test_incorrect_number_exceptions() -> None:
    # We previously gave an error saying the number of exceptions was wrong,
    # but we now instead indicate excess/missing exceptions
    with (
        fails_raises_group(
            "1 matched exception. Unexpected exception(s): [RuntimeError()]"
        ),
        RaisesGroup(ValueError),
    ):
        raise ExceptionGroup("", (RuntimeError(), ValueError()))

    # will error if there's missing exceptions
    with (
        fails_raises_group(
            "1 matched exception. Too few exceptions raised, found no match for: [SyntaxError]"
        ),
        RaisesGroup(ValueError, SyntaxError),
    ):
        raise ExceptionGroup("", (ValueError(),))

    with (
        fails_raises_group(
            "\n"
            "1 matched exception. \n"
            "Too few exceptions raised!\n"
            "The following expected exceptions did not find a match:\n"
            "  ValueError\n"
            "    It matches `ValueError()` which was paired with `ValueError`"
        ),
        RaisesGroup(ValueError, ValueError),
    ):
        raise ExceptionGroup("", (ValueError(),))

    with (
        fails_raises_group(
            "\n"
            "1 matched exception. \n"
            "Unexpected exception(s)!\n"
            "The following raised exceptions did not find a match\n"
            "  ValueError('b'):\n"
            "    It matches `ValueError` which was paired with `ValueError('a')`"
        ),
        RaisesGroup(ValueError),
    ):
        raise ExceptionGroup("", (ValueError("a"), ValueError("b")))

    with (
        fails_raises_group(
            "\n"
            "1 matched exception. \n"
            "The following expected exceptions did not find a match:\n"
            "  ValueError\n"
            "    It matches `ValueError()` which was paired with `ValueError`\n"
            "The following raised exceptions did not find a match\n"
            "  SyntaxError():\n"
            "    `SyntaxError()` is not an instance of `ValueError`"
        ),
        RaisesGroup(ValueError, ValueError),
    ):
        raise ExceptionGroup("", [ValueError(), SyntaxError()])


def test_flatten_subgroups() -> None:
    # loose semantics, as with expect*
    with RaisesGroup(ValueError, flatten_subgroups=True):
        raise ExceptionGroup("", (ExceptionGroup("", (ValueError(),)),))

    with RaisesGroup(ValueError, TypeError, flatten_subgroups=True):
        raise ExceptionGroup("", (ExceptionGroup("", (ValueError(), TypeError())),))
    with RaisesGroup(ValueError, TypeError, flatten_subgroups=True):
        raise ExceptionGroup("", [ExceptionGroup("", [ValueError()]), TypeError()])

    # mixed loose is possible if you want it to be at least N deep
    with RaisesGroup(RaisesGroup(ValueError, flatten_subgroups=True)):
        raise ExceptionGroup("", (ExceptionGroup("", (ValueError(),)),))
    with RaisesGroup(RaisesGroup(ValueError, flatten_subgroups=True)):
        raise ExceptionGroup(
            "",
            (ExceptionGroup("", (ExceptionGroup("", (ValueError(),)),)),),
        )

    # but not the other way around
    with pytest.raises(
        ValueError,
        match=r"^You cannot specify a nested structure inside a RaisesGroup with",
    ):
        RaisesGroup(RaisesGroup(ValueError), flatten_subgroups=True)  # type: ignore[call-overload]

    # flatten_subgroups is not sufficient to catch fully unwrapped
    with (
        fails_raises_group(
            "`ValueError()` is not an exception group, but would match with `allow_unwrapped=True`"
        ),
        RaisesGroup(ValueError, flatten_subgroups=True),
    ):
        raise ValueError
    with (
        fails_raises_group(
            "RaisesGroup(ValueError, flatten_subgroups=True): `ValueError()` is not an exception group, but would match with `allow_unwrapped=True`"
        ),
        RaisesGroup(RaisesGroup(ValueError, flatten_subgroups=True)),
    ):
        raise ExceptionGroup("", (ValueError(),))

    # helpful suggestion if flatten_subgroups would make it pass
    with (
        fails_raises_group(
            "Raised exception group did not match: \n"
            "The following expected exceptions did not find a match:\n"
            "  ValueError\n"
            "  TypeError\n"
            "The following raised exceptions did not find a match\n"
            "  ExceptionGroup('', [ValueError(), TypeError()]):\n"
            "    Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "    Unexpected nested `ExceptionGroup()`, expected `TypeError`\n"
            "Did you mean to use `flatten_subgroups=True`?",
            add_prefix=False,
        ),
        RaisesGroup(ValueError, TypeError),
    ):
        raise ExceptionGroup("", [ExceptionGroup("", [ValueError(), TypeError()])])
    # but doesn't consider check (otherwise we'd break typing guarantees)
    with (
        fails_raises_group(
            "Raised exception group did not match: \n"
            "The following expected exceptions did not find a match:\n"
            "  ValueError\n"
            "  TypeError\n"
            "The following raised exceptions did not find a match\n"
            "  ExceptionGroup('', [ValueError(), TypeError()]):\n"
            "    Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "    Unexpected nested `ExceptionGroup()`, expected `TypeError`\n"
            "Did you mean to use `flatten_subgroups=True`?",
            add_prefix=False,
        ),
        RaisesGroup(
            ValueError,
            TypeError,
            check=lambda eg: len(eg.exceptions) == 1,
        ),
    ):
        raise ExceptionGroup("", [ExceptionGroup("", [ValueError(), TypeError()])])
    # correct number of exceptions, and flatten_subgroups would make it pass
    # This now doesn't print a repr of the caught exception at all, but that can be found in the traceback
    with (
        fails_raises_group(
            "Raised exception group did not match: Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "  Did you mean to use `flatten_subgroups=True`?",
            add_prefix=False,
        ),
        RaisesGroup(ValueError),
    ):
        raise ExceptionGroup("", [ExceptionGroup("", [ValueError()])])
    # correct number of exceptions, but flatten_subgroups wouldn't help, so we don't suggest it
    with (
        fails_raises_group(
            "Unexpected nested `ExceptionGroup()`, expected `ValueError`"
        ),
        RaisesGroup(ValueError),
    ):
        raise ExceptionGroup("", [ExceptionGroup("", [TypeError()])])

    # flatten_subgroups can be suggested if nested. This will implicitly ask the user to
    # do `RaisesGroup(RaisesGroup(ValueError, flatten_subgroups=True))` which is unlikely
    # to be what they actually want - but I don't think it's worth trying to special-case
    with (
        fails_raises_group(
            "RaisesGroup(ValueError): Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "  Did you mean to use `flatten_subgroups=True`?",
        ),
        RaisesGroup(RaisesGroup(ValueError)),
    ):
        raise ExceptionGroup(
            "",
            [ExceptionGroup("", [ExceptionGroup("", [ValueError()])])],
        )

    # Don't mention "unexpected nested" if expecting an ExceptionGroup.
    # Although it should perhaps be an error to specify `RaisesGroup(ExceptionGroup)` in
    # favor of doing `RaisesGroup(RaisesGroup(...))`.
    with (
        fails_raises_group(
            "`BaseExceptionGroup()` is not an instance of `ExceptionGroup`"
        ),
        RaisesGroup(ExceptionGroup),
    ):
        raise BaseExceptionGroup("", [BaseExceptionGroup("", [KeyboardInterrupt()])])


def test_catch_unwrapped_exceptions() -> None:
    # Catches lone exceptions with strict=False
    # just as except* would
    with RaisesGroup(ValueError, allow_unwrapped=True):
        raise ValueError

    # expecting multiple unwrapped exceptions is not possible
    with pytest.raises(
        ValueError,
        match=r"^You cannot specify multiple exceptions with",
    ):
        RaisesGroup(SyntaxError, ValueError, allow_unwrapped=True)  # type: ignore[call-overload]
    # if users want one of several exception types they need to use a RaisesExc
    # (which the error message suggests)
    with RaisesGroup(
        RaisesExc(check=lambda e: isinstance(e, (SyntaxError, ValueError))),
        allow_unwrapped=True,
    ):
        raise ValueError

    # Unwrapped nested `RaisesGroup` is likely a user error, so we raise an error.
    with pytest.raises(ValueError, match="has no effect when expecting"):
        RaisesGroup(RaisesGroup(ValueError), allow_unwrapped=True)  # type: ignore[call-overload]

    # But it *can* be used to check for nesting level +- 1 if they move it to
    # the nested RaisesGroup. Users should probably use `RaisesExc`s instead though.
    with RaisesGroup(RaisesGroup(ValueError, allow_unwrapped=True)):
        raise ExceptionGroup("", [ExceptionGroup("", [ValueError()])])
    with RaisesGroup(RaisesGroup(ValueError, allow_unwrapped=True)):
        raise ExceptionGroup("", [ValueError()])

    # with allow_unwrapped=False (default) it will not be caught
    with (
        fails_raises_group(
            "`ValueError()` is not an exception group, but would match with `allow_unwrapped=True`"
        ),
        RaisesGroup(ValueError),
    ):
        raise ValueError("value error text")

    # allow_unwrapped on its own won't match against nested groups
    with (
        fails_raises_group(
            "Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "  Did you mean to use `flatten_subgroups=True`?",
        ),
        RaisesGroup(ValueError, allow_unwrapped=True),
    ):
        raise ExceptionGroup("foo", [ExceptionGroup("bar", [ValueError()])])

    # you need both allow_unwrapped and flatten_subgroups to fully emulate except*
    with RaisesGroup(ValueError, allow_unwrapped=True, flatten_subgroups=True):
        raise ExceptionGroup("", [ExceptionGroup("", [ValueError()])])

    # code coverage
    with (
        fails_raises_group(
            "Raised exception (group) did not match: `TypeError()` is not an instance of `ValueError`",
            add_prefix=False,
        ),
        RaisesGroup(ValueError, allow_unwrapped=True),
    ):
        raise TypeError("this text doesn't show up in the error message")
    with (
        fails_raises_group(
            "Raised exception (group) did not match: RaisesExc(ValueError): `TypeError()` is not an instance of `ValueError`",
            add_prefix=False,
        ),
        RaisesGroup(RaisesExc(ValueError), allow_unwrapped=True),
    ):
        raise TypeError

    # check we don't suggest unwrapping with nested RaisesGroup
    with (
        fails_raises_group("`ValueError()` is not an exception group"),
        RaisesGroup(RaisesGroup(ValueError)),
    ):
        raise ValueError


def test_match() -> None:
    # supports match string
    with RaisesGroup(ValueError, match="bar"):
        raise ExceptionGroup("bar", (ValueError(),))

    # now also works with ^$
    with RaisesGroup(ValueError, match="^bar$"):
        raise ExceptionGroup("bar", (ValueError(),))

    # it also includes notes
    with RaisesGroup(ValueError, match="my note"):
        e = ExceptionGroup("bar", (ValueError(),))
        e.add_note("my note")
        raise e

    # and technically you can match it all with ^$
    # but you're probably better off using a RaisesExc at that point
    with RaisesGroup(ValueError, match="^bar\nmy note$"):
        e = ExceptionGroup("bar", (ValueError(),))
        e.add_note("my note")
        raise e

    with (
        fails_raises_group(
            "Regex pattern did not match the `ExceptionGroup()`.\n"
            " Regex: 'foo'\n"
            " Input: 'bar'"
        ),
        RaisesGroup(ValueError, match="foo"),
    ):
        raise ExceptionGroup("bar", (ValueError(),))

    # Suggest a fix for easy pitfall of adding match to the RaisesGroup instead of
    # using a RaisesExc.
    # This requires a single expected & raised exception, the expected is a type,
    # and `isinstance(raised, expected_type)`.
    with (
        fails_raises_group(
            "Regex pattern did not match the `ExceptionGroup()`.\n"
            " Regex: 'foo'\n"
            " Input: 'bar'\n"
            " but matched the expected `ValueError`.\n"
            " You might want `RaisesGroup(RaisesExc(ValueError, match='foo'))`"
        ),
        RaisesGroup(ValueError, match="foo"),
    ):
        raise ExceptionGroup("bar", [ValueError("foo")])


def test_check() -> None:
    exc = ExceptionGroup("", (ValueError(),))

    def is_exc(e: ExceptionGroup[ValueError]) -> bool:
        return e is exc

    is_exc_repr = repr_callable(is_exc)
    with RaisesGroup(ValueError, check=is_exc):
        raise exc

    with (
        fails_raises_group(
            f"check {is_exc_repr} did not return True on the ExceptionGroup"
        ),
        RaisesGroup(ValueError, check=is_exc),
    ):
        raise ExceptionGroup("", (ValueError(),))

    def is_value_error(e: BaseException) -> bool:
        return isinstance(e, ValueError)

    # helpful suggestion if the user thinks the check is for the sub-exception
    with (
        fails_raises_group(
            f"check {is_value_error} did not return True on the ExceptionGroup, but did return True for the expected ValueError. You might want RaisesGroup(RaisesExc(ValueError, check=<...>))"
        ),
        RaisesGroup(ValueError, check=is_value_error),
    ):
        raise ExceptionGroup("", (ValueError(),))


def test_unwrapped_match_check() -> None:
    def my_check(e: object) -> bool:  # pragma: no cover
        return True

    msg = (
        "`allow_unwrapped=True` bypasses the `match` and `check` parameters"
        " if the exception is unwrapped. If you intended to match/check the"
        " exception you should use a `RaisesExc` object. If you want to match/check"
        " the exceptiongroup when the exception *is* wrapped you need to"
        " do e.g. `if isinstance(exc.value, ExceptionGroup):"
        " assert RaisesGroup(...).matches(exc.value)` afterwards."
    )
    with pytest.raises(ValueError, match=re.escape(msg)):
        RaisesGroup(ValueError, allow_unwrapped=True, match="foo")  # type: ignore[call-overload]
    with pytest.raises(ValueError, match=re.escape(msg)):
        RaisesGroup(ValueError, allow_unwrapped=True, check=my_check)  # type: ignore[call-overload]

    # Users should instead use a RaisesExc
    rg = RaisesGroup(RaisesExc(ValueError, match="^foo$"), allow_unwrapped=True)
    with rg:
        raise ValueError("foo")
    with rg:
        raise ExceptionGroup("", [ValueError("foo")])

    # or if they wanted to match/check the group, do a conditional `.matches()`
    with RaisesGroup(ValueError, allow_unwrapped=True) as exc:
        raise ExceptionGroup("bar", [ValueError("foo")])
    if isinstance(exc.value, ExceptionGroup):  # pragma: no branch
        assert RaisesGroup(ValueError, match="bar").matches(exc.value)


def test_matches() -> None:
    rg = RaisesGroup(ValueError)
    assert not rg.matches(None)
    assert not rg.matches(ValueError())
    assert rg.matches(ExceptionGroup("", (ValueError(),)))

    re = RaisesExc(ValueError)
    assert not re.matches(None)
    assert re.matches(ValueError())


def test_message() -> None:
    def check_message(
        message: str,
        body: RaisesGroup[BaseException],
    ) -> None:
        with (
            pytest.raises(
                Failed,
                match=f"^DID NOT RAISE any exception, expected `{re.escape(message)}`$",
            ),
            body,
        ):
            ...

    # basic
    check_message("ExceptionGroup(ValueError)", RaisesGroup(ValueError))
    # multiple exceptions
    check_message(
        "ExceptionGroup(ValueError, ValueError)",
        RaisesGroup(ValueError, ValueError),
    )
    # nested
    check_message(
        "ExceptionGroup(ExceptionGroup(ValueError))",
        RaisesGroup(RaisesGroup(ValueError)),
    )

    # RaisesExc
    check_message(
        "ExceptionGroup(RaisesExc(ValueError, match='my_str'))",
        RaisesGroup(RaisesExc(ValueError, match="my_str")),
    )
    check_message(
        "ExceptionGroup(RaisesExc(match='my_str'))",
        RaisesGroup(RaisesExc(match="my_str")),
    )
    # one-size tuple is printed as not being a tuple
    check_message(
        "ExceptionGroup(RaisesExc(ValueError))",
        RaisesGroup(RaisesExc((ValueError,))),
    )
    check_message(
        "ExceptionGroup(RaisesExc((ValueError, IndexError)))",
        RaisesGroup(RaisesExc((ValueError, IndexError))),
    )

    # BaseExceptionGroup
    check_message(
        "BaseExceptionGroup(KeyboardInterrupt)",
        RaisesGroup(KeyboardInterrupt),
    )
    # BaseExceptionGroup with type inside RaisesExc
    check_message(
        "BaseExceptionGroup(RaisesExc(KeyboardInterrupt))",
        RaisesGroup(RaisesExc(KeyboardInterrupt)),
    )
    check_message(
        "BaseExceptionGroup(RaisesExc((ValueError, KeyboardInterrupt)))",
        RaisesGroup(RaisesExc((ValueError, KeyboardInterrupt))),
    )
    # Base-ness transfers to parent containers
    check_message(
        "BaseExceptionGroup(BaseExceptionGroup(KeyboardInterrupt))",
        RaisesGroup(RaisesGroup(KeyboardInterrupt)),
    )
    # but not to child containers
    check_message(
        "BaseExceptionGroup(BaseExceptionGroup(KeyboardInterrupt), ExceptionGroup(ValueError))",
        RaisesGroup(RaisesGroup(KeyboardInterrupt), RaisesGroup(ValueError)),
    )


def test_assert_message() -> None:
    # the message does not need to list all parameters to RaisesGroup, nor all exceptions
    # in the exception group, as those are both visible in the traceback.
    # first fails to match
    with (
        fails_raises_group("`TypeError()` is not an instance of `ValueError`"),
        RaisesGroup(ValueError),
    ):
        raise ExceptionGroup("a", [TypeError()])
    with (
        fails_raises_group(
            "Raised exception group did not match: \n"
            "The following expected exceptions did not find a match:\n"
            "  RaisesGroup(ValueError)\n"
            "  RaisesGroup(ValueError, match='a')\n"
            "The following raised exceptions did not find a match\n"
            "  ExceptionGroup('', [RuntimeError()]):\n"
            "    RaisesGroup(ValueError): `RuntimeError()` is not an instance of `ValueError`\n"
            "    RaisesGroup(ValueError, match='a'): Regex pattern did not match the `ExceptionGroup()`.\n"
            "     Regex: 'a'\n"
            "     Input: ''\n"
            "  RuntimeError():\n"
            "    RaisesGroup(ValueError): `RuntimeError()` is not an exception group\n"
            "    RaisesGroup(ValueError, match='a'): `RuntimeError()` is not an exception group",
            add_prefix=False,  # to see the full structure
        ),
        RaisesGroup(RaisesGroup(ValueError), RaisesGroup(ValueError, match="a")),
    ):
        raise ExceptionGroup(
            "",
            [ExceptionGroup("", [RuntimeError()]), RuntimeError()],
        )

    with (
        fails_raises_group(
            "Raised exception group did not match: \n"
            "2 matched exceptions. \n"
            "The following expected exceptions did not find a match:\n"
            "  RaisesGroup(RuntimeError)\n"
            "  RaisesGroup(ValueError)\n"
            "The following raised exceptions did not find a match\n"
            "  RuntimeError():\n"
            "    RaisesGroup(RuntimeError): `RuntimeError()` is not an exception group, but would match with `allow_unwrapped=True`\n"
            "    RaisesGroup(ValueError): `RuntimeError()` is not an exception group\n"
            "  ValueError('bar'):\n"
            "    It matches `ValueError` which was paired with `ValueError('foo')`\n"
            "    RaisesGroup(RuntimeError): `ValueError()` is not an exception group\n"
            "    RaisesGroup(ValueError): `ValueError()` is not an exception group, but would match with `allow_unwrapped=True`",
            add_prefix=False,  # to see the full structure
        ),
        RaisesGroup(
            ValueError,
            RaisesExc(TypeError),
            RaisesGroup(RuntimeError),
            RaisesGroup(ValueError),
        ),
    ):
        raise ExceptionGroup(
            "a",
            [RuntimeError(), TypeError(), ValueError("foo"), ValueError("bar")],
        )

    with (
        fails_raises_group(
            "1 matched exception. `AssertionError()` is not an instance of `TypeError`"
        ),
        RaisesGroup(ValueError, TypeError),
    ):
        raise ExceptionGroup("a", [ValueError(), AssertionError()])

    with (
        fails_raises_group(
            "RaisesExc(ValueError): `TypeError()` is not an instance of `ValueError`"
        ),
        RaisesGroup(RaisesExc(ValueError)),
    ):
        raise ExceptionGroup("a", [TypeError()])

    # suggest escaping
    with (
        fails_raises_group(
            # TODO: did not match Exceptiongroup('h(ell)o', ...) ?
            "Raised exception group did not match: Regex pattern did not match the `ExceptionGroup()`.\n"
            " Regex: 'h(ell)o'\n"
            " Input: 'h(ell)o'\n"
            " Did you mean to `re.escape()` the regex?",
            add_prefix=False,  # to see the full structure
        ),
        RaisesGroup(ValueError, match="h(ell)o"),
    ):
        raise ExceptionGroup("h(ell)o", [ValueError()])
    with (
        fails_raises_group(
            "RaisesExc(match='h(ell)o'): Regex pattern did not match.\n"
            " Regex: 'h(ell)o'\n"
            " Input: 'h(ell)o'\n"
            " Did you mean to `re.escape()` the regex?",
        ),
        RaisesGroup(RaisesExc(match="h(ell)o")),
    ):
        raise ExceptionGroup("", [ValueError("h(ell)o")])

    with (
        fails_raises_group(
            "Raised exception group did not match: \n"
            "The following expected exceptions did not find a match:\n"
            "  ValueError\n"
            "  ValueError\n"
            "  ValueError\n"
            "  ValueError\n"
            "The following raised exceptions did not find a match\n"
            "  ExceptionGroup('', [ValueError(), TypeError()]):\n"
            "    Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "    Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "    Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "    Unexpected nested `ExceptionGroup()`, expected `ValueError`",
            add_prefix=False,  # to see the full structure
        ),
        RaisesGroup(ValueError, ValueError, ValueError, ValueError),
    ):
        raise ExceptionGroup("", [ExceptionGroup("", [ValueError(), TypeError()])])


def test_message_indent() -> None:
    with (
        fails_raises_group(
            "Raised exception group did not match: \n"
            "The following expected exceptions did not find a match:\n"
            "  RaisesGroup(ValueError, ValueError)\n"
            "  ValueError\n"
            "The following raised exceptions did not find a match\n"
            "  ExceptionGroup('', [TypeError(), RuntimeError()]):\n"
            "    RaisesGroup(ValueError, ValueError): \n"
            "      The following expected exceptions did not find a match:\n"
            "        ValueError\n"
            "        ValueError\n"
            "      The following raised exceptions did not find a match\n"
            "        TypeError():\n"
            "          `TypeError()` is not an instance of `ValueError`\n"
            "          `TypeError()` is not an instance of `ValueError`\n"
            "        RuntimeError():\n"
            "          `RuntimeError()` is not an instance of `ValueError`\n"
            "          `RuntimeError()` is not an instance of `ValueError`\n"
            # TODO: this line is not great, should maybe follow the same format as the other and say
            # ValueError: Unexpected nested `ExceptionGroup()` (?)
            "    Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "  TypeError():\n"
            "    RaisesGroup(ValueError, ValueError): `TypeError()` is not an exception group\n"
            "    `TypeError()` is not an instance of `ValueError`",
            add_prefix=False,
        ),
        RaisesGroup(
            RaisesGroup(ValueError, ValueError),
            ValueError,
        ),
    ):
        raise ExceptionGroup(
            "",
            [
                ExceptionGroup("", [TypeError(), RuntimeError()]),
                TypeError(),
            ],
        )
    with (
        fails_raises_group(
            "Raised exception group did not match: \n"
            "RaisesGroup(ValueError, ValueError): \n"
            "  The following expected exceptions did not find a match:\n"
            "    ValueError\n"
            "    ValueError\n"
            "  The following raised exceptions did not find a match\n"
            "    TypeError():\n"
            "      `TypeError()` is not an instance of `ValueError`\n"
            "      `TypeError()` is not an instance of `ValueError`\n"
            "    RuntimeError():\n"
            "      `RuntimeError()` is not an instance of `ValueError`\n"
            "      `RuntimeError()` is not an instance of `ValueError`",
            add_prefix=False,
        ),
        RaisesGroup(
            RaisesGroup(ValueError, ValueError),
        ),
    ):
        raise ExceptionGroup(
            "",
            [
                ExceptionGroup("", [TypeError(), RuntimeError()]),
            ],
        )


def test_suggestion_on_nested_and_brief_error() -> None:
    # Make sure "Did you mean" suggestion gets indented iff it follows a single-line error
    with (
        fails_raises_group(
            "\n"
            "The following expected exceptions did not find a match:\n"
            "  RaisesGroup(ValueError)\n"
            "  ValueError\n"
            "The following raised exceptions did not find a match\n"
            "  ExceptionGroup('', [ExceptionGroup('', [ValueError()])]):\n"
            "    RaisesGroup(ValueError): Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "      Did you mean to use `flatten_subgroups=True`?\n"
            "    Unexpected nested `ExceptionGroup()`, expected `ValueError`",
        ),
        RaisesGroup(RaisesGroup(ValueError), ValueError),
    ):
        raise ExceptionGroup(
            "",
            [ExceptionGroup("", [ExceptionGroup("", [ValueError()])])],
        )
    # if indented here it would look like another raised exception
    with (
        fails_raises_group(
            "\n"
            "The following expected exceptions did not find a match:\n"
            "  RaisesGroup(ValueError, ValueError)\n"
            "  ValueError\n"
            "The following raised exceptions did not find a match\n"
            "  ExceptionGroup('', [ValueError(), ExceptionGroup('', [ValueError()])]):\n"
            "    RaisesGroup(ValueError, ValueError): \n"
            "      1 matched exception. \n"
            "      The following expected exceptions did not find a match:\n"
            "        ValueError\n"
            "          It matches `ValueError()` which was paired with `ValueError`\n"
            "      The following raised exceptions did not find a match\n"
            "        ExceptionGroup('', [ValueError()]):\n"
            "          Unexpected nested `ExceptionGroup()`, expected `ValueError`\n"
            "      Did you mean to use `flatten_subgroups=True`?\n"
            "    Unexpected nested `ExceptionGroup()`, expected `ValueError`"
        ),
        RaisesGroup(RaisesGroup(ValueError, ValueError), ValueError),
    ):
        raise ExceptionGroup(
            "",
            [ExceptionGroup("", [ValueError(), ExceptionGroup("", [ValueError()])])],
        )

    # re.escape always comes after single-line errors
    with (
        fails_raises_group(
            "\n"
            "The following expected exceptions did not find a match:\n"
            "  RaisesGroup(Exception, match='^hello')\n"
            "  ValueError\n"
            "The following raised exceptions did not find a match\n"
            "  ExceptionGroup('^hello', [Exception()]):\n"
            "    RaisesGroup(Exception, match='^hello'): Regex pattern did not match the `ExceptionGroup()`.\n"
            "     Regex: '^hello'\n"
            "     Input: '^hello'\n"
            "     Did you mean to `re.escape()` the regex?\n"
            "    Unexpected nested `ExceptionGroup()`, expected `ValueError`"
        ),
        RaisesGroup(RaisesGroup(Exception, match="^hello"), ValueError),
    ):
        raise ExceptionGroup("", [ExceptionGroup("^hello", [Exception()])])


def test_assert_message_nested() -> None:
    # we only get one instance of aaaaaaaaaa... and bbbbbb..., but we do get multiple instances of ccccc... and dddddd..
    # but I think this now only prints the full repr when that is necessary to disambiguate exceptions
    with (
        fails_raises_group(
            "Raised exception group did not match: \n"
            "The following expected exceptions did not find a match:\n"
            "  RaisesGroup(ValueError)\n"
            "  RaisesGroup(RaisesGroup(ValueError))\n"
            "  RaisesGroup(RaisesExc(TypeError, match='foo'))\n"
            "  RaisesGroup(TypeError, ValueError)\n"
            "The following raised exceptions did not find a match\n"
            "  TypeError('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'):\n"
            "    RaisesGroup(ValueError): `TypeError()` is not an exception group\n"
            "    RaisesGroup(RaisesGroup(ValueError)): `TypeError()` is not an exception group\n"
            "    RaisesGroup(RaisesExc(TypeError, match='foo')): `TypeError()` is not an exception group\n"
            "    RaisesGroup(TypeError, ValueError): `TypeError()` is not an exception group\n"
            "  ExceptionGroup('Exceptions from Trio nursery', [TypeError('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb')]):\n"
            "    RaisesGroup(ValueError): `TypeError()` is not an instance of `ValueError`\n"
            "    RaisesGroup(RaisesGroup(ValueError)): RaisesGroup(ValueError): `TypeError()` is not an exception group\n"
            "    RaisesGroup(RaisesExc(TypeError, match='foo')): RaisesExc(TypeError, match='foo'): Regex pattern did not match.\n"
            "     Regex: 'foo'\n"
            "     Input: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'\n"
            "    RaisesGroup(TypeError, ValueError): 1 matched exception. Too few exceptions raised, found no match for: [ValueError]\n"
            "  ExceptionGroup('Exceptions from Trio nursery', [TypeError('cccccccccccccccccccccccccccccc'), TypeError('dddddddddddddddddddddddddddddd')]):\n"
            "    RaisesGroup(ValueError): \n"
            "      The following expected exceptions did not find a match:\n"
            "        ValueError\n"
            "      The following raised exceptions did not find a match\n"
            "        TypeError('cccccccccccccccccccccccccccccc'):\n"
            "          `TypeError()` is not an instance of `ValueError`\n"
            "        TypeError('dddddddddddddddddddddddddddddd'):\n"
            "          `TypeError()` is not an instance of `ValueError`\n"
            "    RaisesGroup(RaisesGroup(ValueError)): \n"
            "      The following expected exceptions did not find a match:\n"
            "        RaisesGroup(ValueError)\n"
            "      The following raised exceptions did not find a match\n"
            "        TypeError('cccccccccccccccccccccccccccccc'):\n"
            "          RaisesGroup(ValueError): `TypeError()` is not an exception group\n"
            "        TypeError('dddddddddddddddddddddddddddddd'):\n"
            "          RaisesGroup(ValueError): `TypeError()` is not an exception group\n"
            "    RaisesGroup(RaisesExc(TypeError, match='foo')): \n"
            "      The following expected exceptions did not find a match:\n"
            "        RaisesExc(TypeError, match='foo')\n"
            "      The following raised exceptions did not find a match\n"
            "        TypeError('cccccccccccccccccccccccccccccc'):\n"
            "          RaisesExc(TypeError, match='foo'): Regex pattern did not match.\n"
            "           Regex: 'foo'\n"
            "           Input: 'cccccccccccccccccccccccccccccc'\n"
            "        TypeError('dddddddddddddddddddddddddddddd'):\n"
            "          RaisesExc(TypeError, match='foo'): Regex pattern did not match.\n"
            "           Regex: 'foo'\n"
            "           Input: 'dddddddddddddddddddddddddddddd'\n"
            "    RaisesGroup(TypeError, ValueError): \n"
            "      1 matched exception. \n"
            "      The following expected exceptions did not find a match:\n"
            "        ValueError\n"
            "      The following raised exceptions did not find a match\n"
            "        TypeError('dddddddddddddddddddddddddddddd'):\n"
            "          It matches `TypeError` which was paired with `TypeError('cccccccccccccccccccccccccccccc')`\n"
            "          `TypeError()` is not an instance of `ValueError`",
            add_prefix=False,  # to see the full structure
        ),
        RaisesGroup(
            RaisesGroup(ValueError),
            RaisesGroup(RaisesGroup(ValueError)),
            RaisesGroup(RaisesExc(TypeError, match="foo")),
            RaisesGroup(TypeError, ValueError),
        ),
    ):
        raise ExceptionGroup(
            "",
            [
                TypeError("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
                ExceptionGroup(
                    "Exceptions from Trio nursery",
                    [TypeError("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")],
                ),
                ExceptionGroup(
                    "Exceptions from Trio nursery",
                    [
                        TypeError("cccccccccccccccccccccccccccccc"),
                        TypeError("dddddddddddddddddddddddddddddd"),
                    ],
                ),
            ],
        )


# CI always runs with hypothesis, but this is not a critical test - it overlaps
# with several others
@pytest.mark.skipif(
    "hypothesis" in sys.modules,
    reason="hypothesis may have monkeypatched _check_repr",
)
def test_check_no_patched_repr() -> None:  # pragma: no cover
    # We make `_check_repr` monkeypatchable to avoid this very ugly and verbose
    # repr. The other tests that use `check` make use of `_check_repr` so they'll
    # continue passing in case it is patched - but we have this one test that
    # demonstrates just how nasty it gets otherwise.
    match_str = (
        r"^Raised exception group did not match: \n"
        r"The following expected exceptions did not find a match:\n"
        r"  RaisesExc\(check=<function test_check_no_patched_repr.<locals>.<lambda> at .*>\)\n"
        r"  TypeError\n"
        r"The following raised exceptions did not find a match\n"
        r"  ValueError\('foo'\):\n"
        r"    RaisesExc\(check=<function test_check_no_patched_repr.<locals>.<lambda> at .*>\): check did not return True\n"
        r"    `ValueError\(\)` is not an instance of `TypeError`\n"
        r"  ValueError\('bar'\):\n"
        r"    RaisesExc\(check=<function test_check_no_patched_repr.<locals>.<lambda> at .*>\): check did not return True\n"
        r"    `ValueError\(\)` is not an instance of `TypeError`$"
    )
    with (
        pytest.raises(Failed, match=match_str),
        RaisesGroup(RaisesExc(check=lambda x: False), TypeError),
    ):
        raise ExceptionGroup("", [ValueError("foo"), ValueError("bar")])


def test_misordering_example() -> None:
    with (
        fails_raises_group(
            "\n"
            "3 matched exceptions. \n"
            "The following expected exceptions did not find a match:\n"
            "  RaisesExc(ValueError, match='foo')\n"
            "    It matches `ValueError('foo')` which was paired with `ValueError`\n"
            "    It matches `ValueError('foo')` which was paired with `ValueError`\n"
            "    It matches `ValueError('foo')` which was paired with `ValueError`\n"
            "The following raised exceptions did not find a match\n"
            "  ValueError('bar'):\n"
            "    It matches `ValueError` which was paired with `ValueError('foo')`\n"
            "    It matches `ValueError` which was paired with `ValueError('foo')`\n"
            "    It matches `ValueError` which was paired with `ValueError('foo')`\n"
            "    RaisesExc(ValueError, match='foo'): Regex pattern did not match.\n"
            "     Regex: 'foo'\n"
            "     Input: 'bar'\n"
            "There exist a possible match when attempting an exhaustive check, but RaisesGroup uses a greedy algorithm. Please make your expected exceptions more stringent with `RaisesExc` etc so the greedy algorithm can function."
        ),
        RaisesGroup(
            ValueError, ValueError, ValueError, RaisesExc(ValueError, match="foo")
        ),
    ):
        raise ExceptionGroup(
            "",
            [
                ValueError("foo"),
                ValueError("foo"),
                ValueError("foo"),
                ValueError("bar"),
            ],
        )


def test_brief_error_on_one_fail() -> None:
    """If only one raised and one expected fail to match up, we print a full table iff
    the raised exception would match one of the expected that previously got matched"""
    # no also-matched
    with (
        fails_raises_group(
            "1 matched exception. `TypeError()` is not an instance of `RuntimeError`"
        ),
        RaisesGroup(ValueError, RuntimeError),
    ):
        raise ExceptionGroup("", [ValueError(), TypeError()])

    # raised would match an expected
    with (
        fails_raises_group(
            "\n"
            "1 matched exception. \n"
            "The following expected exceptions did not find a match:\n"
            "  RuntimeError\n"
            "The following raised exceptions did not find a match\n"
            "  TypeError():\n"
            "    It matches `Exception` which was paired with `ValueError()`\n"
            "    `TypeError()` is not an instance of `RuntimeError`"
        ),
        RaisesGroup(Exception, RuntimeError),
    ):
        raise ExceptionGroup("", [ValueError(), TypeError()])

    # expected would match a raised
    with (
        fails_raises_group(
            "\n"
            "1 matched exception. \n"
            "The following expected exceptions did not find a match:\n"
            "  ValueError\n"
            "    It matches `ValueError()` which was paired with `ValueError`\n"
            "The following raised exceptions did not find a match\n"
            "  TypeError():\n"
            "    `TypeError()` is not an instance of `ValueError`"
        ),
        RaisesGroup(ValueError, ValueError),
    ):
        raise ExceptionGroup("", [ValueError(), TypeError()])


def test_identity_oopsies() -> None:
    # it's both possible to have several instances of the same exception in the same group
    # and to expect multiple of the same type
    # this previously messed up the logic

    with (
        fails_raises_group(
            "3 matched exceptions. `RuntimeError()` is not an instance of `TypeError`"
        ),
        RaisesGroup(ValueError, ValueError, ValueError, TypeError),
    ):
        raise ExceptionGroup(
            "", [ValueError(), ValueError(), ValueError(), RuntimeError()]
        )

    e = ValueError("foo")
    m = RaisesExc(match="bar")
    with (
        fails_raises_group(
            "\n"
            "The following expected exceptions did not find a match:\n"
            "  RaisesExc(match='bar')\n"
            "  RaisesExc(match='bar')\n"
            "  RaisesExc(match='bar')\n"
            "The following raised exceptions did not find a match\n"
            "  ValueError('foo'):\n"
            "    RaisesExc(match='bar'): Regex pattern did not match.\n"
            "     Regex: 'bar'\n"
            "     Input: 'foo'\n"
            "    RaisesExc(match='bar'): Regex pattern did not match.\n"
            "     Regex: 'bar'\n"
            "     Input: 'foo'\n"
            "    RaisesExc(match='bar'): Regex pattern did not match.\n"
            "     Regex: 'bar'\n"
            "     Input: 'foo'\n"
            "  ValueError('foo'):\n"
            "    RaisesExc(match='bar'): Regex pattern did not match.\n"
            "     Regex: 'bar'\n"
            "     Input: 'foo'\n"
            "    RaisesExc(match='bar'): Regex pattern did not match.\n"
            "     Regex: 'bar'\n"
            "     Input: 'foo'\n"
            "    RaisesExc(match='bar'): Regex pattern did not match.\n"
            "     Regex: 'bar'\n"
            "     Input: 'foo'\n"
            "  ValueError('foo'):\n"
            "    RaisesExc(match='bar'): Regex pattern did not match.\n"
            "     Regex: 'bar'\n"
            "     Input: 'foo'\n"
            "    RaisesExc(match='bar'): Regex pattern did not match.\n"
            "     Regex: 'bar'\n"
            "     Input: 'foo'\n"
            "    RaisesExc(match='bar'): Regex pattern did not match.\n"
            "     Regex: 'bar'\n"
            "     Input: 'foo'"
        ),
        RaisesGroup(m, m, m),
    ):
        raise ExceptionGroup("", [e, e, e])


def test_raisesexc() -> None:
    with pytest.raises(
        ValueError,
        match=r"^You must specify at least one parameter to match on.$",
    ):
        RaisesExc()  # type: ignore[call-overload]
    with pytest.raises(
        ValueError,
        match=wrap_escape(
            "expected exception must be a BaseException type, not 'object'"
        ),
    ):
        RaisesExc(object)  # type: ignore[type-var]

    with RaisesGroup(RaisesExc(ValueError)):
        raise ExceptionGroup("", (ValueError(),))
    with (
        fails_raises_group(
            "RaisesExc(TypeError): `ValueError()` is not an instance of `TypeError`"
        ),
        RaisesGroup(RaisesExc(TypeError)),
    ):
        raise ExceptionGroup("", (ValueError(),))

    with RaisesExc(ValueError):
        raise ValueError

    # FIXME: leaving this one formatted differently for now to not change
    # tests in python/raises.py
    with pytest.raises(Failed, match=wrap_escape("DID NOT RAISE <class 'ValueError'>")):
        with RaisesExc(ValueError):
            ...

    with pytest.raises(Failed, match=wrap_escape("DID NOT RAISE any exception")):
        with RaisesExc(match="foo"):
            ...

    with pytest.raises(
        # FIXME: do we want repr(type) or type.__name__ ?
        Failed,
        match=wrap_escape(
            "DID NOT RAISE any of (<class 'ValueError'>, <class 'TypeError'>)"
        ),
    ):
        with RaisesExc((ValueError, TypeError)):
            ...

    # currently RaisesGroup says "Raised exception did not match" but RaisesExc doesn't...
    with pytest.raises(
        AssertionError,
        match=wrap_escape("Regex pattern did not match.\n Regex: 'foo'\n Input: 'bar'"),
    ):
        with RaisesExc(TypeError, match="foo"):
            raise TypeError("bar")


def test_raisesexc_match() -> None:
    with RaisesGroup(RaisesExc(ValueError, match="foo")):
        raise ExceptionGroup("", (ValueError("foo"),))
    with (
        fails_raises_group(
            "RaisesExc(ValueError, match='foo'): Regex pattern did not match.\n"
            " Regex: 'foo'\n"
            " Input: 'bar'"
        ),
        RaisesGroup(RaisesExc(ValueError, match="foo")),
    ):
        raise ExceptionGroup("", (ValueError("bar"),))

    # Can be used without specifying the type
    with RaisesGroup(RaisesExc(match="foo")):
        raise ExceptionGroup("", (ValueError("foo"),))
    with (
        fails_raises_group(
            "RaisesExc(match='foo'): Regex pattern did not match.\n"
            " Regex: 'foo'\n"
            " Input: 'bar'"
        ),
        RaisesGroup(RaisesExc(match="foo")),
    ):
        raise ExceptionGroup("", (ValueError("bar"),))

    # check ^$
    with RaisesGroup(RaisesExc(ValueError, match="^bar$")):
        raise ExceptionGroup("", [ValueError("bar")])
    with (
        fails_raises_group(
            "\nRaisesExc(ValueError, match='^bar$'): \n  - barr\n  ?    -\n  + bar"
        ),
        RaisesGroup(RaisesExc(ValueError, match="^bar$")),
    ):
        raise ExceptionGroup("", [ValueError("barr")])


def test_RaisesExc_check() -> None:
    def check_oserror_and_errno_is_5(e: BaseException) -> bool:
        return isinstance(e, OSError) and e.errno == 5

    with RaisesGroup(RaisesExc(check=check_oserror_and_errno_is_5)):
        raise ExceptionGroup("", (OSError(5, ""),))

    # specifying exception_type narrows the parameter type to the callable
    def check_errno_is_5(e: OSError) -> bool:
        return e.errno == 5

    with RaisesGroup(RaisesExc(OSError, check=check_errno_is_5)):
        raise ExceptionGroup("", (OSError(5, ""),))

    # avoid printing overly verbose repr multiple times
    with (
        fails_raises_group(
            f"RaisesExc(OSError, check={check_errno_is_5!r}): check did not return True"
        ),
        RaisesGroup(RaisesExc(OSError, check=check_errno_is_5)),
    ):
        raise ExceptionGroup("", (OSError(6, ""),))

    # in nested cases you still get it multiple times though
    # to address this you'd need logic in RaisesExc.__repr__ and RaisesGroup.__repr__
    with (
        fails_raises_group(
            f"RaisesGroup(RaisesExc(OSError, check={check_errno_is_5!r})): RaisesExc(OSError, check={check_errno_is_5!r}): check did not return True"
        ),
        RaisesGroup(RaisesGroup(RaisesExc(OSError, check=check_errno_is_5))),
    ):
        raise ExceptionGroup("", [ExceptionGroup("", [OSError(6, "")])])


def test_raisesexc_tostring() -> None:
    assert str(RaisesExc(ValueError)) == "RaisesExc(ValueError)"
    assert str(RaisesExc(match="[a-z]")) == "RaisesExc(match='[a-z]')"
    pattern_no_flags = re.compile(r"noflag", 0)
    assert str(RaisesExc(match=pattern_no_flags)) == "RaisesExc(match='noflag')"
    pattern_flags = re.compile(r"noflag", re.IGNORECASE)
    assert str(RaisesExc(match=pattern_flags)) == f"RaisesExc(match={pattern_flags!r})"
    assert (
        str(RaisesExc(ValueError, match="re", check=bool))
        == f"RaisesExc(ValueError, match='re', check={bool!r})"
    )


def test_raisesgroup_tostring() -> None:
    def check_str_and_repr(s: str) -> None:
        evaled = eval(s)
        assert s == str(evaled) == repr(evaled)

    check_str_and_repr("RaisesGroup(ValueError)")
    check_str_and_repr("RaisesGroup(RaisesGroup(ValueError))")
    check_str_and_repr("RaisesGroup(RaisesExc(ValueError))")
    check_str_and_repr("RaisesGroup(ValueError, allow_unwrapped=True)")
    check_str_and_repr("RaisesGroup(ValueError, match='aoeu')")

    assert (
        str(RaisesGroup(ValueError, match="[a-z]", check=bool))
        == f"RaisesGroup(ValueError, match='[a-z]', check={bool!r})"
    )


def test_assert_matches() -> None:
    e = ValueError()

    # it's easy to do this
    assert RaisesExc(ValueError).matches(e)

    # but you don't get a helpful error
    with pytest.raises(AssertionError, match=r"assert False\n \+  where False = .*"):
        assert RaisesExc(TypeError).matches(e)

    with pytest.raises(
        AssertionError,
        match=wrap_escape(
            "`ValueError()` is not an instance of `TypeError`\n"
            "assert False\n"
            " +  where False = matches(ValueError())\n"
            " +    where matches = RaisesExc(TypeError).matches"
        ),
    ):
        # you'd need to do this arcane incantation
        assert (m := RaisesExc(TypeError)).matches(e), m.fail_reason

    # but even if we add assert_matches, will people remember to use it?
    # other than writing a linter rule, I don't think we can catch `assert RaisesExc(...).matches`
    # ... no wait pytest catches other asserts ... so we probably can??


# https://github.com/pytest-dev/pytest/issues/12504
def test_xfail_raisesgroup(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import sys
        import pytest
        if sys.version_info < (3, 11):
            from exceptiongroup import ExceptionGroup
        @pytest.mark.xfail(raises=pytest.RaisesGroup(ValueError))
        def test_foo() -> None:
            raise ExceptionGroup("foo", [ValueError()])
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(xfailed=1)


def test_xfail_RaisesExc(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        @pytest.mark.xfail(raises=pytest.RaisesExc(ValueError))
        def test_foo() -> None:
            raise ValueError
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(xfailed=1)


@pytest.mark.parametrize(
    "wrap_in_group,handler",
    [
        (False, pytest.raises(ValueError)),
        (True, RaisesGroup(ValueError)),
    ],
)
def test_parametrizing_conditional_raisesgroup(
    wrap_in_group: bool, handler: AbstractContextManager[ExceptionInfo[BaseException]]
) -> None:
    with handler:
        if wrap_in_group:
            raise ExceptionGroup("", [ValueError()])
        raise ValueError()


def test_annotated_group() -> None:
    # repr depends on if exceptiongroup backport is being used or not
    t = repr(ExceptionGroup[ValueError])
    msg = "Only `ExceptionGroup[Exception]` or `BaseExceptionGroup[BaseExeption]` are accepted as generic types but got `{}`. As `raises` will catch all instances of the specified group regardless of the generic argument specific nested exceptions has to be checked with `RaisesGroup`."

    fail_msg = wrap_escape(msg.format(t))
    with pytest.raises(ValueError, match=fail_msg):
        RaisesGroup(ExceptionGroup[ValueError])
    with pytest.raises(ValueError, match=fail_msg):
        RaisesExc(ExceptionGroup[ValueError])
    with pytest.raises(
        ValueError,
        match=wrap_escape(msg.format(repr(BaseExceptionGroup[KeyboardInterrupt]))),
    ):
        with RaisesExc(BaseExceptionGroup[KeyboardInterrupt]):
            raise BaseExceptionGroup("", [KeyboardInterrupt()])

    with RaisesGroup(ExceptionGroup[Exception]):
        raise ExceptionGroup(
            "", [ExceptionGroup("", [ValueError(), ValueError(), ValueError()])]
        )
    with RaisesExc(BaseExceptionGroup[BaseException]):
        raise BaseExceptionGroup("", [KeyboardInterrupt()])


def test_tuples() -> None:
    # raises has historically supported one of several exceptions being raised
    with pytest.raises((ValueError, IndexError)):
        raise ValueError
    # so now RaisesExc also does
    with RaisesExc((ValueError, IndexError)):
        raise IndexError
    # but RaisesGroup currently doesn't. There's an argument it shouldn't because
    # it can be confusing - RaisesGroup((ValueError, TypeError)) looks a lot like
    # RaisesGroup(ValueError, TypeError), and the former might be interpreted as the latter.
    with pytest.raises(
        TypeError,
        match=wrap_escape(
            "expected exception must be a BaseException type, RaisesExc, or RaisesGroup, not 'tuple'.\n"
            "RaisesGroup does not support tuples of exception types when expecting one of "
            "several possible exception types like RaisesExc.\n"
            "If you meant to expect a group with multiple exceptions, list them as separate arguments."
        ),
    ):
        RaisesGroup((ValueError, IndexError))  # type: ignore[call-overload]
