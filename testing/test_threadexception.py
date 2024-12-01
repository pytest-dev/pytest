from __future__ import annotations

from _pytest.pytester import Pytester
import pytest


@pytest.mark.filterwarnings("default::pytest.PytestUnhandledThreadExceptionWarning")
def test_unhandled_thread_exception(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        import threading

        def test_it():
            def oops():
                raise ValueError("Oops")

            t = threading.Thread(target=oops, name="MyThread")
            t.start()
            t.join()

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
            "  * PytestUnhandledThreadExceptionWarning: Exception in thread MyThread",
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: Oops",
            "  ",
            "    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))",
        ]
    )


@pytest.mark.filterwarnings("default::pytest.PytestUnhandledThreadExceptionWarning")
def test_unhandled_thread_exception_in_setup(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        import threading
        import pytest

        @pytest.fixture
        def threadexc():
            def oops():
                raise ValueError("Oops")
            t = threading.Thread(target=oops, name="MyThread")
            t.start()
            t.join()

        def test_it(threadexc): pass
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
            "  * PytestUnhandledThreadExceptionWarning: Exception in thread MyThread",
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: Oops",
            "  ",
            "    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))",
        ]
    )


@pytest.mark.filterwarnings("default::pytest.PytestUnhandledThreadExceptionWarning")
def test_unhandled_thread_exception_in_teardown(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        import threading
        import pytest

        @pytest.fixture
        def threadexc():
            def oops():
                raise ValueError("Oops")
            yield
            t = threading.Thread(target=oops, name="MyThread")
            t.start()
            t.join()

        def test_it(threadexc): pass
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
            "  * PytestUnhandledThreadExceptionWarning: Exception in thread MyThread",
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: Oops",
            "  ",
            "    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))",
        ]
    )


@pytest.mark.filterwarnings("error::pytest.PytestUnhandledThreadExceptionWarning")
def test_unhandled_thread_exception_warning_error(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        import threading
        import pytest

        def test_it():
            def oops():
                raise ValueError("Oops")
            t = threading.Thread(target=oops, name="MyThread")
            t.start()
            t.join()

        def test_2(): pass
        """
    )
    result = pytester.runpytest()
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert result.parseoutcomes() == {"passed": 1, "failed": 1}


@pytest.mark.filterwarnings("error::pytest.PytestUnhandledThreadExceptionWarning")
def test_threadexception_warning_multiple_errors(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        import threading

        def test_it():
            def oops():
                raise ValueError("Oops")

            t = threading.Thread(target=oops, name="MyThread")
            t.start()
            t.join()

            t = threading.Thread(target=oops, name="MyThread2")
            t.start()
            t.join()

        def test_2(): pass
        """
    )
    result = pytester.runpytest()
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=1, failed=1)
    result.stdout.fnmatch_lines(
        ["  | *ExceptionGroup: multiple thread exception warnings (2 sub-exceptions)"]
    )


def test_unraisable_collection_failure(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        import threading

        class Thread(threading.Thread):
            @property
            def name(self):
                raise RuntimeError("oops!")

        def test_it():
            def oops():
                raise ValueError("Oops")

            t = Thread(target=oops, name="MyThread")
            t.start()
            t.join()

        def test_2(): pass
        """
    )

    result = pytester.runpytest()
    assert result.ret == 1
    result.assert_outcomes(passed=1, failed=1)
    result.stdout.fnmatch_lines(
        ["E               RuntimeError: Failed to process thread exception"]
    )


def test_unhandled_thread_exception_after_teardown(pytester: Pytester) -> None:
    # see: https://github.com/pytest-dev/pytest/issues/10404
    pytester.makepyfile(
        test_it="""
        import time
        import threading
        import pytest

        @pytest.fixture(scope="session")
        def thread():
            yield

            def oops():
                time.sleep(0.5)
                raise ValueError("Oops")

            t = threading.Thread(target=oops, name="MyThread")
            t.start()

        def test_it(thread):
            pass
        """
    )

    result = pytester.runpytest()

    # TODO: should be a test failure or error
    assert result.ret == pytest.ExitCode.INTERNAL_ERROR

    result.assert_outcomes(passed=1)
    result.stderr.fnmatch_lines("ValueError: Oops")
