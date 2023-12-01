from typing import TYPE_CHECKING

import pytest
from _pytest.python_api import ExpectedExceptionGroup
from _pytest.python_api import Matcher

# TODO: make a public export

if TYPE_CHECKING:
    from typing_extensions import assert_type


class TestExpectedExceptionGroup:
    def test_expected_exception_group(self) -> None:
        with pytest.raises(
            ValueError,
            match="^Invalid argument {exc} must be exception type, Matcher, or ExpectedExceptionGroup.$",
        ):
            ExpectedExceptionGroup(ValueError())

        with pytest.raises(ExpectedExceptionGroup(ValueError)):
            raise ExceptionGroup("foo", (ValueError(),))

        with pytest.raises(ExpectedExceptionGroup(SyntaxError)):
            with pytest.raises(ExpectedExceptionGroup(ValueError)):
                raise ExceptionGroup("foo", (SyntaxError(),))

        # multiple exceptions
        with pytest.raises(ExpectedExceptionGroup(ValueError, SyntaxError)):
            raise ExceptionGroup("foo", (ValueError(), SyntaxError()))

        # order doesn't matter
        with pytest.raises(ExpectedExceptionGroup(SyntaxError, ValueError)):
            raise ExceptionGroup("foo", (ValueError(), SyntaxError()))

        # nested exceptions
        with pytest.raises(ExpectedExceptionGroup(ExpectedExceptionGroup(ValueError))):
            raise ExceptionGroup("foo", (ExceptionGroup("bar", (ValueError(),)),))

        with pytest.raises(
            ExpectedExceptionGroup(
                SyntaxError,
                ExpectedExceptionGroup(ValueError),
                ExpectedExceptionGroup(RuntimeError),
            )
        ):
            raise ExceptionGroup(
                "foo",
                (
                    SyntaxError(),
                    ExceptionGroup("bar", (ValueError(),)),
                    ExceptionGroup("", (RuntimeError(),)),
                ),
            )

        # will error if there's excess exceptions
        with pytest.raises(ExceptionGroup):
            with pytest.raises(ExpectedExceptionGroup(ValueError)):
                raise ExceptionGroup("", (ValueError(), ValueError()))

        with pytest.raises(ExceptionGroup):
            with pytest.raises(ExpectedExceptionGroup(ValueError)):
                raise ExceptionGroup("", (RuntimeError(), ValueError()))

        # will error if there's missing exceptions
        with pytest.raises(ExceptionGroup):
            with pytest.raises(ExpectedExceptionGroup(ValueError, ValueError)):
                raise ExceptionGroup("", (ValueError(),))

        with pytest.raises(ExceptionGroup):
            with pytest.raises(ExpectedExceptionGroup(ValueError, SyntaxError)):
                raise ExceptionGroup("", (ValueError(),))

        # loose semantics, as with expect*
        with pytest.raises(ExpectedExceptionGroup(ValueError, strict=False)):
            raise ExceptionGroup("", (ExceptionGroup("", (ValueError(),)),))

        # mixed loose is possible if you want it to be at least N deep
        with pytest.raises(
            ExpectedExceptionGroup(ExpectedExceptionGroup(ValueError, strict=True))
        ):
            raise ExceptionGroup("", (ExceptionGroup("", (ValueError(),)),))
        with pytest.raises(
            ExpectedExceptionGroup(ExpectedExceptionGroup(ValueError, strict=False))
        ):
            raise ExceptionGroup(
                "", (ExceptionGroup("", (ExceptionGroup("", (ValueError(),)),)),)
            )

        # but not the other way around
        with pytest.raises(
            ValueError,
            match="^You cannot specify a nested structure inside an ExpectedExceptionGroup with strict=False$",
        ):
            ExpectedExceptionGroup(ExpectedExceptionGroup(ValueError), strict=False)

        # currently not fully identical in behaviour to expect*, which would also catch an unwrapped exception
        with pytest.raises(ValueError):
            with pytest.raises(ExpectedExceptionGroup(ValueError, strict=False)):
                raise ValueError

    def test_match(self) -> None:
        # supports match string
        with pytest.raises(ExpectedExceptionGroup(ValueError), match="bar"):
            raise ExceptionGroup("bar", (ValueError(),))

        try:
            with pytest.raises(ExpectedExceptionGroup(ValueError), match="foo"):
                raise ExceptionGroup("bar", (ValueError(),))
        except AssertionError as e:
            assert str(e).startswith("Regex pattern did not match.")
        else:
            raise AssertionError("Expected pytest.raises.Exception")

    def test_ExpectedExceptionGroup_matches(self) -> None:
        eeg = ExpectedExceptionGroup(ValueError)
        assert not eeg.matches(None)
        assert not eeg.matches(ValueError())
        assert eeg.matches(ExceptionGroup("", (ValueError(),)))

    def test_message(self) -> None:

        try:
            with pytest.raises(ExpectedExceptionGroup(ValueError)):
                ...
        except pytest.fail.Exception as e:
            assert e.msg == f"DID NOT RAISE ExceptionGroup({repr(ValueError)},)"
        else:
            assert False, "Expected pytest.raises.Exception"
        try:
            with pytest.raises(
                ExpectedExceptionGroup(ExpectedExceptionGroup(ValueError))
            ):
                ...
        except pytest.fail.Exception as e:
            assert (
                e.msg
                == f"DID NOT RAISE ExceptionGroup(ExceptionGroup({repr(ValueError)},),)"
            )
        else:
            assert False, "Expected pytest.raises.Exception"

    def test_matcher(self) -> None:
        with pytest.raises(
            ValueError, match="^You must specify at least one parameter to match on.$"
        ):
            Matcher()

        with pytest.raises(ExpectedExceptionGroup(Matcher(ValueError))):
            raise ExceptionGroup("", (ValueError(),))
        try:
            with pytest.raises(ExpectedExceptionGroup(Matcher(TypeError))):
                raise ExceptionGroup("", (ValueError(),))
        except ExceptionGroup:
            pass
        else:
            assert False, "Expected pytest.raises.Exception"

    def test_matcher_match(self) -> None:
        with pytest.raises(ExpectedExceptionGroup(Matcher(ValueError, "foo"))):
            raise ExceptionGroup("", (ValueError("foo"),))
        try:
            with pytest.raises(ExpectedExceptionGroup(Matcher(ValueError, "foo"))):
                raise ExceptionGroup("", (ValueError("bar"),))
        except ExceptionGroup:
            pass
        else:
            assert False, "Expected pytest.raises.Exception"

        # Can be used without specifying the type
        with pytest.raises(ExpectedExceptionGroup(Matcher(match="foo"))):
            raise ExceptionGroup("", (ValueError("foo"),))
        try:
            with pytest.raises(ExpectedExceptionGroup(Matcher(match="foo"))):
                raise ExceptionGroup("", (ValueError("bar"),))
        except ExceptionGroup:
            pass
        else:
            assert False, "Expected pytest.raises.Exception"

    def test_Matcher_check(self) -> None:
        def check_oserror_and_errno_is_5(e: BaseException) -> bool:
            return isinstance(e, OSError) and e.errno == 5

        with pytest.raises(
            ExpectedExceptionGroup(Matcher(check=check_oserror_and_errno_is_5))
        ):
            raise ExceptionGroup("", (OSError(5, ""),))

        # specifying exception_type narrows the parameter type to the callable
        def check_errno_is_5(e: OSError) -> bool:
            return e.errno == 5

        with pytest.raises(
            ExpectedExceptionGroup(Matcher(OSError, check=check_errno_is_5))
        ):
            raise ExceptionGroup("", (OSError(5, ""),))

        try:
            with pytest.raises(
                ExpectedExceptionGroup(Matcher(OSError, check=check_errno_is_5))
            ):
                raise ExceptionGroup("", (OSError(6, ""),))
        except ExceptionGroup:
            pass
        else:
            assert False, "Expected pytest.raises.Exception"

    if TYPE_CHECKING:
        # getting the typing working satisfactory is very tricky
        # but with ExpectedExceptionGroup being seen as a subclass of BaseExceptionGroup
        # most end-user cases of checking excinfo.value.foobar should work fine now.
        def test_types_0(self) -> None:
            _: BaseExceptionGroup[ValueError] = ExpectedExceptionGroup(ValueError)
            _ = ExpectedExceptionGroup(ExpectedExceptionGroup(ValueError))  # type: ignore[arg-type]
            a: BaseExceptionGroup[BaseExceptionGroup[ValueError]]
            a = ExpectedExceptionGroup(ExpectedExceptionGroup(ValueError))
            a = BaseExceptionGroup("", (BaseExceptionGroup("", (ValueError(),)),))
            assert a

        def test_types_1(self) -> None:
            with pytest.raises(ExpectedExceptionGroup(ValueError)) as e:
                raise ExceptionGroup("foo", (ValueError(),))
            assert_type(e.value, ExpectedExceptionGroup[ValueError])

        def test_types_2(self) -> None:
            exc: ExceptionGroup[ValueError] | ValueError = ExceptionGroup(
                "", (ValueError(),)
            )
            if ExpectedExceptionGroup(ValueError).matches(exc):
                assert_type(exc, BaseExceptionGroup[ValueError])

        def test_types_3(self) -> None:
            e: BaseExceptionGroup[KeyboardInterrupt] = BaseExceptionGroup(
                "", (KeyboardInterrupt(),)
            )
            if ExpectedExceptionGroup(ValueError).matches(e):
                assert_type(e, BaseExceptionGroup[ValueError])

        def test_types_4(self) -> None:
            with pytest.raises(ExpectedExceptionGroup(Matcher(ValueError))) as e:
                ...
            _: BaseExceptionGroup[ValueError] = e.value
            assert_type(e.value, ExpectedExceptionGroup[ValueError])

        def test_types_5(self) -> None:
            with pytest.raises(
                ExpectedExceptionGroup(ExpectedExceptionGroup(ValueError))
            ) as excinfo:
                raise ExceptionGroup("foo", (ValueError(),))
            _: BaseExceptionGroup[BaseExceptionGroup[ValueError]] = excinfo.value
            assert_type(
                excinfo.value,
                ExpectedExceptionGroup[ExpectedExceptionGroup[ValueError]],
            )
            print(excinfo.value.exceptions[0].exceptions[0])

        def test_types_6(self) -> None:
            exc: ExceptionGroup[ExceptionGroup[ValueError]] = ...  # type: ignore[assignment]
            if ExpectedExceptionGroup(ExpectedExceptionGroup(ValueError)).matches(exc):  # type: ignore[arg-type]
                # ugly
                assert_type(exc, BaseExceptionGroup[ExpectedExceptionGroup[ValueError]])
