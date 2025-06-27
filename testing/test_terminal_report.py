from __future__ import annotations

from _pytest.pytester import Pytester


def test_console_output_style_times_with_skipped_and_passed(pytester: Pytester) -> None:
    pytester.makepyfile(
        test_repro="""
            def test_hello():
                pass
        """,
        test_repro_skip="""
            import pytest
            pytest.importorskip("fakepackage_does_not_exist")
        """,
    )

    result = pytester.runpytest(
        "test_repro.py",
        "test_repro_skip.py",
        "-o",
        "console_output_style=times",
    )

    print("Captured stdout:")
    print(result.stdout.str())
    print("Captured stderr:")
    print(result.stderr.str())

    combined = result.stdout.lines + result.stderr.lines
    assert any(
        "'CollectReport' object has no attribute 'duration'" in line
        for line in combined
    )
