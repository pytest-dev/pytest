from __future__ import annotations

import gc
import sys
from unittest import mock

from _pytest.pytester import Pytester
import pytest


PYPY = hasattr(sys, "pypy_version_info")

UNRAISABLE_LINE = (
    (
        "  * PytestUnraisableExceptionWarning: Exception ignored while calling "
        "deallocator <function BrokenDel.__del__ at *>: None"
    )
    if sys.version_info >= (3, 14)
    else "  * PytestUnraisableExceptionWarning: Exception ignored in: <function BrokenDel.__del__ at *>"
)

TRACEMALLOC_LINES = (
    ()
    if sys.version_info >= (3, 14)
    else (
        "  Enable tracemalloc to get traceback where the object was allocated.",
        "  See https* for more info.",
    )
)


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
            UNRAISABLE_LINE,
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: del is broken",
            "  ",
            *TRACEMALLOC_LINES,
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
            UNRAISABLE_LINE,
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: del is broken",
            "  ",
            *TRACEMALLOC_LINES,
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
            UNRAISABLE_LINE,
            "  ",
            "  Traceback (most recent call last):",
            "  ValueError: del is broken",
            "  ",
            *TRACEMALLOC_LINES,
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


def test_refcycle_unraisable(pytester: Pytester) -> None:
    # see: https://github.com/pytest-dev/pytest/issues/10404
    pytester.makepyfile(
        test_it="""
        # Should catch the unraisable exception even if gc is disabled.
        import gc; gc.disable()

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

    result = pytester.runpytest_subprocess(
        "-Wdefault::pytest.PytestUnraisableExceptionWarning"
    )

    assert result.ret == 0

    result.assert_outcomes(passed=1)
    result.stderr.fnmatch_lines("ValueError: del is broken")


def test_refcycle_unraisable_warning_filter(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_it="""
        # Should catch the unraisable exception even if gc is disabled.
        import gc; gc.disable()

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

    result = pytester.runpytest_subprocess(
        "-Werror::pytest.PytestUnraisableExceptionWarning"
    )

    # TODO: Should be a test failure or error. Currently the exception
    # propagates all the way to the top resulting in exit code 1.
    assert result.ret == 1

    result.assert_outcomes(passed=1)
    result.stderr.fnmatch_lines("ValueError: del is broken")


def test_create_task_raises_unraisable_warning_filter(pytester: Pytester) -> None:
    # note that the host pytest warning filter is disabled and the pytester
    # warning filter applies during config teardown of unraisablehook.
    # see: https://github.com/pytest-dev/pytest/issues/10404
    # This is a dupe of the above test, but using the exact reproducer from
    # the issue
    pytester.makepyfile(
        test_it="""
        # Should catch the unraisable exception even if gc is disabled.
        import gc; gc.disable()

        import asyncio
        import pytest

        async def my_task():
            pass

        def test_scheduler_must_be_created_within_running_loop() -> None:
            with pytest.raises(RuntimeError) as _:
                asyncio.create_task(my_task())
        """
    )

    result = pytester.runpytest_subprocess("-Werror")

    # TODO: Should be a test failure or error. Currently the exception
    # propagates all the way to the top resulting in exit code 1.
    # Note: since #14263, the propagated class is the bare RuntimeWarning
    # rather than the wrapping PytestUnraisableExceptionWarning, because
    # -Werror activates an error filter that matches RuntimeWarning's
    # category and the new unwrap path in collect_unraisable fires.
    assert result.ret == 1

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


def test_refcycle_resource_warning_filter(pytester: Pytester) -> None:
    # Regression test for https://github.com/pytest-dev/pytest/issues/14263.
    # A reference cycle holds a file alive past test return; only the cyclic
    # GC at session end frees it. The file finalizer emits ResourceWarning.
    # With ``filterwarnings = error::ResourceWarning`` the user has expressed
    # intent that resource leaks should fail tests. Before the fix, the
    # ResourceWarning was captured by sys.unraisablehook (the timing piece
    # was already correct since #13057), but ``collect_unraisable`` wrapped
    # it in a ``PytestUnraisableExceptionWarning``. Since the user had no
    # error filter on the wrapping class, the failure was silently logged
    # as a warning and the test passed.
    pytester.makeini(
        """
        [pytest]
        filterwarnings =
            error::ResourceWarning
        """
    )
    pytester.makepyfile(
        test_it="""
        # Disable gc so the cycle survives until session-end gc_collect_harder.
        import gc; gc.disable()

        def test_it():
            f = open(__file__)
            cycle = [f]
            cycle.append(cycle)
        """
    )

    result = pytester.runpytest_subprocess()

    # TODO: should be a test failure or error. Currently the exception
    # propagates all the way to the top resulting in exit code 1.
    assert result.ret == 1
    result.assert_outcomes(passed=1)
    # The unwrap path: stderr shows the ResourceWarning directly, NOT wrapped
    # in PytestUnraisableExceptionWarning. The negative assertion is what
    # makes this a contract test for #14263 rather than an exit-code check.
    result.stderr.fnmatch_lines("*ResourceWarning: unclosed file*")
    result.stderr.no_fnmatch_line("*PytestUnraisableExceptionWarning*")


def test_refcycle_userwarning_filter(pytester: Pytester) -> None:
    # Companion to test_refcycle_resource_warning_filter. Covers the unwrap
    # path for a non-built-in Warning subclass (UserWarning here) and a
    # finalizer that calls ``warnings.warn(...)`` directly rather than
    # leaking a resource. Confirms the fix is not specific to ResourceWarning.
    pytester.makeini(
        """
        [pytest]
        filterwarnings =
            error::UserWarning
        """
    )
    pytester.makepyfile(
        test_it="""
        import gc; gc.disable()
        import warnings

        class Leaky:
            def __init__(self):
                self.self = self  # cycle so __del__ defers to session-end gc

            def __del__(self):
                warnings.warn("leak detected", UserWarning)

        def test_it():
            Leaky()
        """
    )

    result = pytester.runpytest_subprocess()

    # TODO: should be a test failure or error. Currently the exception
    # propagates all the way to the top resulting in exit code 1.
    assert result.ret == 1
    result.assert_outcomes(passed=1)
    result.stderr.fnmatch_lines("*UserWarning: leak detected*")
    result.stderr.no_fnmatch_line("*PytestUnraisableExceptionWarning*")


def test_unraisable_warning_without_filter_still_wraps(pytester: Pytester) -> None:
    # Regression guard for the scope of the #14263 fix. A Warning raised
    # from ``__del__`` *without* a matching error filter must still be
    # wrapped in PytestUnraisableExceptionWarning rather than propagated
    # directly. Otherwise the fix would change behavior for users who
    # haven't set any filter (suites that previously logged would start
    # failing unconditionally).
    pytester.makepyfile(
        test_it="""
        class RaisingDel:
            def __del__(self):
                raise UserWarning("oops")

        def test_it():
            obj = RaisingDel()
            del obj
        """
    )

    # Subprocess so we don't inherit the outer pytest's filterwarnings
    # (which is ``error`` in pyproject.toml; that would falsely trigger
    # the unwrap path). ``-Wdefault::pytest.PytestUnraisableExceptionWarning``
    # makes the wrapping warning visible on stderr regardless of whether
    # ``__del__`` fires inside the test or during later GC (PyPy).
    result = pytester.runpytest_subprocess(
        "-Wdefault::pytest.PytestUnraisableExceptionWarning"
    )

    assert result.ret == 0
    result.assert_outcomes(passed=1)
    # Wrap path fired: the unraisable hook emitted
    # PytestUnraisableExceptionWarning rather than propagating UserWarning.
    # The warning lands in the warnings-summary section of stdout on
    # CPython (where ``__del__`` fires inside the test) and on stderr on
    # PyPy (where it fires during later GC). Check both rather than the
    # outcomes counter, which is timing-dependent.
    combined = "\n".join(result.outlines + result.errlines)
    assert "PytestUnraisableExceptionWarning" in combined


@pytest.mark.skipif(sys.version_info < (3, 11), reason="add_note requires Python 3.11+")
def test_unraisable_warning_filter_add_note_dedups(pytester: Pytester) -> None:
    # Covers the duplicate-note guard in the unwrap path. When the same
    # Warning instance reaches sys.unraisablehook twice (which happens
    # for singleton/cached warnings), the cause note must be appended
    # once, not duplicated.
    pytester.makeini(
        """
        [pytest]
        filterwarnings =
            error::UserWarning
        """
    )
    pytester.makepyfile(
        test_it="""
        import sys
        import types

        cached = UserWarning("cached")

        def test_emit_same_instance_twice():
            for _ in range(2):
                sys.unraisablehook(
                    types.SimpleNamespace(
                        exc_type=UserWarning,
                        exc_value=cached,
                        exc_traceback=None,
                        err_msg=None,
                        object=None,
                    )
                )
        """
    )
    result = pytester.runpytest_subprocess()
    # The unwrap path raises the UserWarning, so the test fails.
    assert result.ret == 1
    # Two errors land in the ExceptionGroup (one per hook call). With the
    # dedup guard, ``cached.__notes__`` holds the cause note once, so the
    # formatted group prints it twice (once per entry). Without the
    # guard it would print four times.
    note_count = sum(
        1 for ln in result.outlines + result.errlines if "Exception ignored in" in ln
    )
    assert note_count == 2, f"expected 2 cause-note lines, saw {note_count}"


@pytest.mark.skipif(PYPY, reason="garbage-collection differences make this flaky")
def test_unraisable_decouples_from_cleanup_stack_order(pytester: Pytester) -> None:
    # Regression test for the structural fix. The garbage-collection step
    # that surfaces queued unraisables must run before _cleanup_stack.close()
    # so warning filters installed via cleanup-stack-managed contexts are
    # still in effect when finalizers fire. Otherwise correctness depends
    # on the order in which plugins register their cleanups under LIFO.
    #
    # The conftest uses ``@hookimpl(trylast=True)`` so its pytest_configure
    # runs after all built-in pytest_configures. Its
    # ``warnings.resetwarnings`` cleanup then lands on the cleanup stack
    # last and pops first under LIFO. Under the pre-fix layout, where
    # garbage collection runs inside unraisableexception's own cleanup
    # callback, that pop clears the user's ``error::ResourceWarning``
    # filter before the leaking finalizer fires; ``warnings.warn`` emits
    # the ResourceWarning silently rather than promoting it, and the suite
    # exits 0. Under the post-fix layout, ``pytest_unconfigure`` does the
    # garbage collection and queue processing before the cleanup stack
    # starts closing, so the conftest's reset has no effect.
    pytester.makeini(
        """
        [pytest]
        filterwarnings =
            error::ResourceWarning
        """
    )
    pytester.makeconftest(
        """
        import warnings
        import pytest

        @pytest.hookimpl(trylast=True)
        def pytest_configure(config):
            config.add_cleanup(warnings.resetwarnings)
        """
    )
    pytester.makepyfile(
        test_it="""
        import gc; gc.disable()

        def test_it():
            f = open(__file__)
            cycle = [f]
            cycle.append(cycle)
        """
    )

    result = pytester.runpytest_subprocess()

    assert result.ret == 1
    result.assert_outcomes(passed=1)
    result.stderr.fnmatch_lines("*ResourceWarning: unclosed file*")
    result.stderr.no_fnmatch_line("*PytestUnraisableExceptionWarning*")


def test_pytest_unconfigure_survives_failed_pytest_configure(
    pytester: Pytester,
) -> None:
    # Regression test for the guard against an unset stash key. When
    # another plugin's pytest_configure raises pytest.UsageError, pluggy
    # stops calling the remaining configure hooks; the unraisable plugin's
    # pytest_configure never runs and config.stash[unraisable_exceptions]
    # stays unset. pytest_unconfigure still fires for partially-configured
    # runs, so without a presence check the unraisable plugin's
    # pytest_unconfigure raises KeyError and pytest reports INTERNALERROR
    # instead of USAGE_ERROR.
    pytester.makeconftest(
        """
        import pytest

        def pytest_configure(config):
            raise pytest.UsageError("simulated bad config")
        """
    )
    pytester.makepyfile(test_it="def test_it(): pass")

    result = pytester.runpytest_subprocess()

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines("*ERROR: simulated bad config*")
    result.stderr.no_fnmatch_line("*INTERNALERROR*")
    result.stderr.no_fnmatch_line("*KeyError*")


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
