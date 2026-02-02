from __future__ import annotations

import sys

from testing.threading.utils import threaded_conftest

from _pytest.pytester import Pytester
import pytest


def test_invalid_thread_name_raises(pytester: Pytester) -> None:
    # note that there's a race condition if a thread switch happens at
    # exactly the right time in the runtestprotocol thread registration / error
    # checking that would make this test flaky. We force thread 0 to finish before
    # starting thread 1 to deflake this.
    #
    # This race is not a practical concern since this warning is a proactive one
    # for misguided users.

    pytester.makeconftest(
        """
import threading
from threading import Event, Barrier
from concurrent.futures import ThreadPoolExecutor

def pytest_runtestloop(session):
    thread_0_ran = Event()
    barrier = Barrier(2, timeout=5)

    def worker(worker_id, item):
        threading.current_thread().name = (
            f"pytest-thread-{worker_id}"
            if worker_id == 0
            else "invalid_thread_name"
        )

        barrier.wait()
        if worker_id == 1:
            thread_0_ran.wait(timeout=5)

        item.config.hook.pytest_runtest_protocol(item=item, nextitem=None)

        if worker_id == 0:
            thread_0_ran.set()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(worker, worker_id=i, item=session.items[i])
            for i in range(2)
        ]
        for future in futures:
            future.result()
    return True
"""
    )

    pytester.makepyfile(
        """
def test_1(): pass
def test_2(): pass
"""
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        ["*pytest threads must follow the naming convention pytest-thread-*"]
    )


def test_concurrent(pytester: Pytester) -> None:
    pytester.makeconftest(threaded_conftest)
    pytester.makepyfile(
        """
        import pytest

        def do_work():
            # arbitrary moderately-expensive work
            for x in range(500):
                _y = x**x

        def test1(): do_work()
        def test2(): do_work()
        def test3(): do_work()
        def test4(): do_work()

        @pytest.fixture
        def a_fixture():
            yield

        def test_fixture1(a_fixture): do_work()
        def test_fixture2(a_fixture): do_work()
        def test_fixture3(a_fixture): do_work()
        def test_fixture4(a_fixture): do_work()

        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=8)


def test_each_thread_gets_fresh_fixture_value(pytester: Pytester) -> None:
    pytester.makeconftest(threaded_conftest)
    pytester.makepyfile(
        """
        import itertools
        import pytest
        import threading

        seen_values = set()
        seen_values_lock = threading.Lock()
        counter = itertools.count()

        @pytest.fixture
        def a_fixture():
            value = next(counter)
            with seen_values_lock:
                assert value not in seen_values
                seen_values.add(value)
            return value

        def test1(a_fixture): pass
        def test2(a_fixture): pass
        def test3(a_fixture): pass
        def test4(a_fixture): pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=4)


def test_child_thread_gets_cached_fixture(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import threading
        import pytest
        import itertools

        counter = itertools.count()
        @pytest.fixture
        def my_fixture():
            return next(counter)

        def test_child_thread_shares_fixture(request):
            main_value = request.getfixturevalue("my_fixture")
            child_value = None

            def child_work():
                nonlocal child_value
                child_value = request.getfixturevalue("my_fixture")

            child = threading.Thread(target=child_work)
            child.start()
            child.join()

            assert child_value is main_value
        """
    )
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)


@pytest.mark.skipif(
    # - thread_inherit_context is new in 3.14
    # - thread_inherit_context defaults to 1 on 3.14t+ if not passed
    # - thread_inherit_context defaults to 0 on 3.14+ if not passed
    (
        sys.version_info < (3, 14)
        or (
            sys._xoptions["thread_inherit_context"] != "1"
            if "thread_inherit_context" in sys._xoptions
            else sys._is_gil_enabled()
        )
    ),
    reason="requires thread_inherit_context=1",
)
def test_child_thread_gets_cached_value_threaded(pytester: Pytester) -> None:
    # Threads spawned under threaded execution should still inherit the fixture
    # caching of the parent thread.
    pytester.makeconftest(threaded_conftest)
    pytester.makepyfile(
        """
        import threading
        import pytest
        import itertools

        counter = itertools.count()
        @pytest.fixture
        def my_fixture():
            return next(counter)

        def test_child_thread_shares_fixture(request):
            main_value = request.getfixturevalue("my_fixture")

            child_value = None

            def child_work():
                nonlocal child_value
                child_value = request.getfixturevalue("my_fixture")

            child = threading.Thread(target=child_work)
            child.start()
            child.join()

            assert child_value is main_value
        """
    )
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)
