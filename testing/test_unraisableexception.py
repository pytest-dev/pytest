from __future__ import annotations

from collections.abc import Generator
import contextlib
import gc
import sys
from unittest import mock

from _pytest.pytester import Pytester
import pytest


PYPY = hasattr(sys, "pypy_version_info")


@pytest.mark.skipif(PYPY, reason="garbage-collection differences make this flaky")
@pytest.mark.filterwarnings("default::pytest.PytestUnraisableExceptionWarning")
def test_unraisable(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        class BrokenDel:
            def __del__(self):
                raise ValueError("del is broken")

        def test_it():
            obj = BrokenDel()
            del obj

        def test_2(): pass
        """
    )
    result = pytester.runpytest()
    assert result.ret == 0
    result.assert_outcomes(passed=2, warnings=1)
    result.stdout.fnmatch_lines(
        [
            "*= warnings summary =*",
            "test_it.py::test_it",
            "  * PytestUnraisableExceptionWarning: Exception ignored in: <function BrokenDel.__del__ at *>",
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: del is broken",
            "  ",
            "  Enable tracemalloc to get traceback where the object was allocated.",
            "  See https* for more info.",
            "    warnings.warn(pytest.PytestUnraisableExceptionWarning(msg))",
        ]
    )


@pytest.mark.skipif(PYPY, reason="garbage-collection differences make this flaky")
@pytest.mark.filterwarnings("default::pytest.PytestUnraisableExceptionWarning")
def test_unraisable_in_setup(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        import pytest

        class BrokenDel:
            def __del__(self):
                raise ValueError("del is broken")

        @pytest.fixture
        def broken_del():
            obj = BrokenDel()
            del obj

        def test_it(broken_del): pass
        def test_2(): pass
        """
    )
    result = pytester.runpytest()
    assert result.ret == 0
    result.assert_outcomes(passed=2, warnings=1)
    result.stdout.fnmatch_lines(
        [
            "*= warnings summary =*",
            "test_it.py::test_it",
            "  * PytestUnraisableExceptionWarning: Exception ignored in: <function BrokenDel.__del__ at *>",
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: del is broken",
            "  ",
            "  Enable tracemalloc to get traceback where the object was allocated.",
            "  See https* for more info.",
            "    warnings.warn(pytest.PytestUnraisableExceptionWarning(msg))",
        ]
    )


@pytest.mark.skipif(PYPY, reason="garbage-collection differences make this flaky")
@pytest.mark.filterwarnings("default::pytest.PytestUnraisableExceptionWarning")
def test_unraisable_in_teardown(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        import pytest

        class BrokenDel:
            def __del__(self):
                raise ValueError("del is broken")

        @pytest.fixture
        def broken_del():
            yield
            obj = BrokenDel()
            del obj

        def test_it(broken_del): pass
        def test_2(): pass
        """
    )
    result = pytester.runpytest()
    assert result.ret == 0
    result.assert_outcomes(passed=2, warnings=1)
    result.stdout.fnmatch_lines(
        [
            "*= warnings summary =*",
            "test_it.py::test_it",
            "  * PytestUnraisableExceptionWarning: Exception ignored in: <function BrokenDel.__del__ at *>",
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: del is broken",
            "  ",
            "  Enable tracemalloc to get traceback where the object was allocated.",
            "  See https* for more info.",
            "    warnings.warn(pytest.PytestUnraisableExceptionWarning(msg))",
        ]
    )


@pytest.mark.filterwarnings("error::pytest.PytestUnraisableExceptionWarning")
def test_unraisable_warning_error(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it=f"""
        class BrokenDel:
            def __del__(self) -> None:
                raise ValueError("del is broken")

        def test_it() -> None:
            obj = BrokenDel()
            del obj
            {"import gc; gc.collect()" * PYPY}

        def test_2(): pass
        """
    )
    result = pytester.runpytest()
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=1, failed=1)


@pytest.mark.filterwarnings("error::pytest.PytestUnraisableExceptionWarning")
def test_unraisable_warning_multiple_errors(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it=f"""
        class BrokenDel:
            def __init__(self, msg: str):
                self.msg = msg

            def __del__(self) -> None:
                raise ValueError(self.msg)

        def test_it() -> None:
            BrokenDel("del is broken 1")
            BrokenDel("del is broken 2")
            {"import gc; gc.collect()" * PYPY}

        def test_2(): pass
        """
    )
    result = pytester.runpytest()
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=1, failed=1)
    result.stdout.fnmatch_lines(
        [
            "  | *ExceptionGroup: multiple unraisable exception warnings (2 sub-exceptions)"
        ]
    )


def test_unraisable_collection_failure(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it=f"""
        class BrokenDel:
            def __del__(self):
                raise ValueError("del is broken")

        def test_it():
            obj = BrokenDel()
            del obj
            {"import gc; gc.collect()" * PYPY}

        def test_2(): pass
        """
    )

    class MyError(BaseException):
        pass

    with mock.patch("traceback.format_exception", side_effect=MyError):
        result = pytester.runpytest()
    assert result.ret == 1
    result.assert_outcomes(passed=1, failed=1)
    result.stdout.fnmatch_lines(
        ["E               RuntimeError: Failed to process unraisable exception"]
    )


def _set_gc_state(enabled: bool) -> bool:
    was_enabled = gc.isenabled()
    if enabled:
        gc.enable()
    else:
        gc.disable()
    return was_enabled


@contextlib.contextmanager
def _disable_gc() -> Generator[None]:
    was_enabled = _set_gc_state(enabled=False)
    try:
        yield
    finally:
        _set_gc_state(enabled=was_enabled)


def test_refcycle_unraisable(pytester: Pytester) -> None:
    # see: https://github.com/pytest-dev/pytest/issues/10404
    pytester.makepyfile(
        test_it="""
        import pytest

        class BrokenDel:
            def __init__(self):
                self.self = self  # make a reference cycle

            def __del__(self):
                raise ValueError("del is broken")

        def test_it():
            BrokenDel()
        """
    )

    with _disable_gc():
        result = pytester.runpytest()

    # TODO: should be a test failure or error
    assert result.ret == pytest.ExitCode.INTERNAL_ERROR

    result.assert_outcomes(passed=1)
    result.stderr.fnmatch_lines("ValueError: del is broken")


@pytest.mark.filterwarnings("default::pytest.PytestUnraisableExceptionWarning")
def test_refcycle_unraisable_warning_filter(pytester: Pytester) -> None:
    # note that the host pytest warning filter is disabled and the pytester
    # warning filter applies during config teardown of unraisablehook.
    # see: https://github.com/pytest-dev/pytest/issues/10404
    pytester.makepyfile(
        test_it="""
        import pytest

        class BrokenDel:
            def __init__(self):
                self.self = self  # make a reference cycle

            def __del__(self):
                raise ValueError("del is broken")

        def test_it():
            BrokenDel()
        """
    )

    with _disable_gc():
        result = pytester.runpytest("-Werror")

    # TODO: should be a test failure or error
    assert result.ret == pytest.ExitCode.INTERNAL_ERROR

    result.assert_outcomes(passed=1)
    result.stderr.fnmatch_lines("ValueError: del is broken")


@pytest.mark.filterwarnings("default::pytest.PytestUnraisableExceptionWarning")
def test_create_task_raises_unraisable_warning_filter(pytester: Pytester) -> None:
    # note that the host pytest warning filter is disabled and the pytester
    # warning filter applies during config teardown of unraisablehook.
    # see: https://github.com/pytest-dev/pytest/issues/10404
    # This is a dupe of the above test, but using the exact reproducer from
    # the issue
    pytester.makepyfile(
        test_it="""
        import asyncio
        import pytest

        async def my_task():
            pass

        def test_scheduler_must_be_created_within_running_loop() -> None:
            with pytest.raises(RuntimeError) as _:
                asyncio.create_task(my_task())
        """
    )

    with _disable_gc():
        result = pytester.runpytest("-Werror")

    # TODO: should be a test failure or error
    assert result.ret == pytest.ExitCode.INTERNAL_ERROR

    result.assert_outcomes(passed=1)
    result.stderr.fnmatch_lines("RuntimeWarning: coroutine 'my_task' was never awaited")


def test_refcycle_unraisable_warning_filter_default(pytester: Pytester) -> None:
    # note this time we use a default warning filter for pytester
    # and run it in a subprocess, because the warning can only go to the
    # sys.stdout rather than the terminal reporter, which has already
    # finished.
    # see: https://github.com/pytest-dev/pytest/pull/13057#discussion_r1888396126
    pytester.makepyfile(
        test_it="""
        import gc
        gc.disable()

        import pytest

        class BrokenDel:
            def __init__(self):
                self.self = self  # make a reference cycle

            def __del__(self):
                raise ValueError("del is broken")

        def test_it():
            BrokenDel()
        """
    )

    # since we use subprocess we need to disable gc inside test_it
    result = pytester.runpytest_subprocess("-Wdefault")

    assert result.ret == pytest.ExitCode.OK

    # TODO: should be warnings=1, but the outcome has already come out
    # by the time the warning triggers
    result.assert_outcomes(passed=1)
    result.stderr.fnmatch_lines("ValueError: del is broken")


@pytest.mark.filterwarnings("error::pytest.PytestUnraisableExceptionWarning")
def test_possibly_none_excinfo(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        import sys
        import types

        def test_it():
            sys.unraisablehook(
                types.SimpleNamespace(
                    exc_type=RuntimeError,
                    exc_value=None,
                    exc_traceback=None,
                    err_msg=None,
                    object=None,
                )
            )
        """
    )

    result = pytester.runpytest()

    # TODO: should be a test failure or error
    assert result.ret == pytest.ExitCode.TESTS_FAILED

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        [
            "E                   pytest.PytestUnraisableExceptionWarning:"
            " Exception ignored in: None",
            "E                   ",
            "E                   NoneType: None",
        ]
    )
