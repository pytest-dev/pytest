from __future__ import annotations

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
    assert result.parseoutcomes() == {"passed": 2, "warnings": 1}
    result.stdout.fnmatch_lines(
        [
            "*= warnings summary =*",
            "test_it.py::test_it",
            "  * PytestUnraisableExceptionWarning: Exception ignored in: <function BrokenDel.__del__ at *>",
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: del is broken",
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
    assert result.parseoutcomes() == {"passed": 2, "warnings": 1}
    result.stdout.fnmatch_lines(
        [
            "*= warnings summary =*",
            "test_it.py::test_it",
            "  * PytestUnraisableExceptionWarning: Exception ignored in: <function BrokenDel.__del__ at *>",
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: del is broken",
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
    assert result.parseoutcomes() == {"passed": 2, "warnings": 1}
    result.stdout.fnmatch_lines(
        [
            "*= warnings summary =*",
            "test_it.py::test_it",
            "  * PytestUnraisableExceptionWarning: Exception ignored in: <function BrokenDel.__del__ at *>",
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: del is broken",
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
    assert result.parseoutcomes() == {"passed": 1, "failed": 1}


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
    assert result.parseoutcomes() == {"passed": 1, "failed": 1}
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
    assert result.parseoutcomes() == {"passed": 1, "failed": 1}
    result.stdout.fnmatch_lines(
        ["E               RuntimeError: Failed to process unraisable exception"]
    )


def test_create_task_unraisable(pytester: Pytester) -> None:
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

    was_enabled = gc.isenabled()
    gc.disable()
    try:
        result = pytester.runpytest()
    finally:
        if was_enabled:
            gc.enable()

    # TODO: should be a test failure or error
    assert result.ret == pytest.ExitCode.INTERNAL_ERROR

    assert result.parseoutcomes() == {"passed": 1}
    result.stderr.fnmatch_lines("ValueError: del is broken")
