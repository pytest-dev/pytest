import re
import sys
from typing import TYPE_CHECKING

import pytest
from _pytest.outcomes import Failed
from pytest import RaisesGroup

if TYPE_CHECKING:
    from typing_extensions import assert_type

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup


def test_raises_group() -> None:
    # wrong type to constructor
    with pytest.raises(
        TypeError,
        match="^expected exception must be a BaseException type, not ValueError$",
    ):
        RaisesGroup(ValueError())  # type: ignore[arg-type]

    # working example
    with RaisesGroup(ValueError):
        raise ExceptionGroup("foo", (ValueError(),))

    with RaisesGroup(ValueError, check=lambda x: True):
        raise ExceptionGroup("foo", (ValueError(),))

    # wrong subexception
    with pytest.raises(
        AssertionError,
        match="Wrong type in group: got <class 'SyntaxError'>, expected <class 'ValueError'>",
    ):
        with RaisesGroup(ValueError):
            raise ExceptionGroup("foo", (SyntaxError(),))

    # will error if there's excess exceptions
    with pytest.raises(
        AssertionError, match="Wrong number of exceptions: got 2, expected 1"
    ):
        with RaisesGroup(ValueError):
            raise ExceptionGroup("", (ValueError(), ValueError()))

    # double nested exceptions is not (currently) supported (contrary to expect*)
    with pytest.raises(
        AssertionError,
        match="Wrong type in group: got <class '(exceptiongroup.)?ExceptionGroup'>, expected <class 'ValueError'>",
    ):
        with RaisesGroup(ValueError):
            raise ExceptionGroup("", (ExceptionGroup("", (ValueError(),)),))

    # you'd need to write
    with RaisesGroup(ExceptionGroup) as excinfo:
        raise ExceptionGroup("", (ExceptionGroup("", (ValueError(),)),))
    RaisesGroup(ValueError).assert_matches(excinfo.value.exceptions[0])

    # unwrapped exceptions are not accepted (contrary to expect*)
    with pytest.raises(
        AssertionError, match="Expected an ExceptionGroup, not <class 'ValueError'."
    ):
        with RaisesGroup(ValueError):
            raise ValueError

    with pytest.raises(
        AssertionError,
        match=re.escape("Check failed on ExceptionGroup('foo', (ValueError(),))."),
    ):
        with RaisesGroup(ValueError, check=lambda x: False):
            raise ExceptionGroup("foo", (ValueError(),))


def test_RaisesGroup_matches() -> None:
    eeg = RaisesGroup(ValueError)
    # exc_val is None
    assert not eeg.matches(None)
    # exc_val is not an exceptiongroup
    assert not eeg.matches(ValueError())
    # wrong length
    assert not eeg.matches(ExceptionGroup("", (ValueError(), ValueError())))
    # wrong type
    assert not eeg.matches(ExceptionGroup("", (TypeError(),)))
    # check fails
    assert not RaisesGroup(ValueError, check=lambda _: False).matches(
        ExceptionGroup("", (ValueError(),))
    )
    # success
    assert eeg.matches(ExceptionGroup("", (ValueError(),)))


def test_RaisesGroup_assert_matches() -> None:
    """Check direct use of RaisesGroup.assert_matches, without a context manager"""
    eeg = RaisesGroup(ValueError)
    with pytest.raises(AssertionError):
        eeg.assert_matches(None)
    with pytest.raises(AssertionError):
        eeg.assert_matches(ValueError())
    eeg.assert_matches(ExceptionGroup("", (ValueError(),)))


def test_message() -> None:
    with pytest.raises(
        Failed,
        match=re.escape(
            f"DID NOT RAISE ANY EXCEPTION, expected ExceptionGroup({repr(ValueError)})"
        ),
    ):
        with RaisesGroup(ValueError):
            ...

    with pytest.raises(
        Failed,
        match=re.escape(
            f"DID NOT RAISE ANY EXCEPTION, expected BaseExceptionGroup({repr(KeyboardInterrupt)})"
        ),
    ):
        with RaisesGroup(KeyboardInterrupt):
            ...


if TYPE_CHECKING:

    def test_types_1() -> None:
        with RaisesGroup(ValueError) as e:
            raise ExceptionGroup("foo", (ValueError(),))
        assert_type(e.value, BaseExceptionGroup[ValueError])

    def test_types_2() -> None:
        exc: ExceptionGroup[ValueError] | ValueError = ExceptionGroup(
            "", (ValueError(),)
        )
        if RaisesGroup(ValueError).assert_matches(exc):
            assert_type(exc, BaseExceptionGroup[ValueError])

    def test_types_3() -> None:
        e: BaseExceptionGroup[KeyboardInterrupt] = BaseExceptionGroup(
            "", (KeyboardInterrupt(),)
        )
        if RaisesGroup(ValueError).matches(e):
            assert_type(e, BaseExceptionGroup[ValueError])

    def test_types_4() -> None:
        e: BaseExceptionGroup[KeyboardInterrupt] = BaseExceptionGroup(
            "", (KeyboardInterrupt(),)
        )
        # not currently possible: https://github.com/python/typing/issues/930
        RaisesGroup(ValueError).assert_matches(e)
        assert_type(e, BaseExceptionGroup[ValueError])  # type: ignore[assert-type]
