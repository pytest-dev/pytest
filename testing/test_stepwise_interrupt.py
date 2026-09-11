# mypy: disallow-untyped-defs
"""--stepwise should resume after a debugger quit / pytest.exit (#10562)."""

from __future__ import annotations

from _pytest.pytester import Pytester


def test_stepwise_continues_after_pytest_exit(pytester: Pytester) -> None:
    """Pdb quit raises pytest.exit; --stepwise should start from that test next run."""
    pytester.makeini(
        """
        [pytest]
        cache_dir = .cache
        """
    )
    pytester.makepyfile(
        """
        def test_before():
            assert True

        def test_quit():
            import pytest

            pytest.exit("Quitting debugger")

        def test_after():
            assert True
        """
    )
    first = pytester.runpytest("-v", "--stepwise")
    stdout = first.stdout.str()
    assert "test_before PASSED" in stdout
    assert "test_quit" in stdout
    assert "test_after PASSED" not in stdout

    second = pytester.runpytest("-v", "--stepwise")
    stdout = second.stdout.str()
    assert "skipping 1 already passed items" in stdout
    assert "test_before PASSED" not in stdout
    assert "test_quit" in stdout
    assert "test_after PASSED" not in stdout


def test_stepwise_continues_after_bdbquit(pytester: Pytester) -> None:
    """A raised BdbQuit is already a failed report; keep that resume path."""
    pytester.makeini(
        """
        [pytest]
        cache_dir = .cache
        """
    )
    pytester.makepyfile(
        """
        def test_before():
            assert True

        def test_quit():
            import bdb

            raise bdb.BdbQuit()

        def test_after():
            assert True
        """
    )
    first = pytester.runpytest("-v", "--stepwise")
    stdout = first.stdout.str()
    assert "test_before PASSED" in stdout
    assert "test_quit FAILED" in stdout
    assert "test_after PASSED" not in stdout

    second = pytester.runpytest("-v", "--stepwise")
    stdout = second.stdout.str()
    assert "skipping 1 already passed items" in stdout
    assert "test_before PASSED" not in stdout
    assert "test_quit FAILED" in stdout
