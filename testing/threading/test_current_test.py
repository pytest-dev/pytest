from __future__ import annotations

from testing.threading.utils import threaded_conftest, n_conftest_threads


def test_current_test_envvar_shows_all_threads(pytester):
    pytester.makeconftest(threaded_conftest)

    # PYTEST_CURRENT_TEST should be popped from os.environ after pytest finishes
    pytester.makeconftest(
        """
        import os
        import pytest

        def pytest_sessionfinish():
            assert "PYTEST_CURRENT_TEST" not in os.environ
        """
    )

    pytester.makepyfile(
        f"""
        import os
        import pytest
        from threading import Barrier

        barrier = Barrier({n_conftest_threads})

        def test_1():
            assert "test_1 (call)" in os.environ["PYTEST_CURRENT_TEST"]

        def test_2():
            assert "test_2 (call)" in os.environ["PYTEST_CURRENT_TEST"]

        def test_3():
            assert "test_3 (call)" in os.environ["PYTEST_CURRENT_TEST"]
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=3)
