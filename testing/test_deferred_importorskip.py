from __future__ import annotations

from _pytest.pytester import Pytester
import pytest


def test_deferred_collects_all_tests(pytester: Pytester) -> None:
    pytester.makepyfile("""
        import pytest
        missing = pytest.importorskip("missing_deferred_dependency", defer=True)
        @pytest.mark.parametrize("value", [1, 2])
        def test_dependent(value):
            missing.work(value)
    """)
    result = pytester.runpytest("--collect-only", "-q")
    result.stdout.fnmatch_lines(
        ["*test_dependent[[]1[]]", "*test_dependent[[]2[]]", "*2 tests collected*"]
    )
    result = pytester.runpytest("-rs")
    result.assert_outcomes(skipped=2)
    result.stdout.fnmatch_lines(["*missing_deferred_dependency*"])


def test_deferred_conftest_scopes_to_directory(pytester: Pytester) -> None:
    pytester.makepyfile(
        **{
            "gated/conftest.py": """
            import pytest
            missing = pytest.importorskip("missing_deferred_dependency", defer=True)
            @pytest.fixture
            def dependency():
                return missing.value
        """,
            "gated/test_a.py": "def test_gated(dependency): pass",
            "test_b.py": "def test_unrelated(): pass",
        }
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, skipped=1)


@pytest.mark.parametrize(
    "tail", ["value = missing.value", "import another_missing_dependency"]
)
def test_deferred_eager_use_falls_back_to_module_skip(
    pytester: Pytester, tail: str
) -> None:
    pytester.makepyfile(
        "import pytest\n"
        'missing = pytest.importorskip("missing_deferred_dependency", defer=True)\n'
        + tail
        + "\ndef test_example(): pass"
    )
    result = pytester.runpytest()
    result.assert_outcomes(skipped=1)


def test_deferred_available_returns_real_module(pytester: Pytester) -> None:
    pytester.makepyfile("""
        import pytest
        import sys
        actual = pytest.importorskip("sys", defer=True)
        def test_available():
            assert actual is sys
    """)
    pytester.runpytest().assert_outcomes(passed=1)


def test_deferred_inside_test_skips_immediately(pytester: Pytester) -> None:
    pytester.makepyfile("""
        import pytest
        def test_missing():
            pytest.importorskip("missing_deferred_dependency", defer=True)
            pytest.fail("must not continue")
    """)
    result = pytester.runpytest("-rs")
    result.assert_outcomes(skipped=1)
    result.stdout.fnmatch_lines(
        ["SKIPPED [[]1[]] test_deferred_inside_test_skips_immediately.py:3: *"]
    )


def test_unrelated_import_errors_still_reported(pytester: Pytester) -> None:
    pytester.makepyfile("import another_missing_dependency\ndef test_example(): pass")
    pytester.runpytest().assert_outcomes(errors=1)


def test_deferred_minversion_and_original_location(pytester: Pytester) -> None:
    pytester.makepyfile(dependency='__version__ = "1.0"')
    pytester.makepyfile(
        test_version="""
        import pytest
        dependency = pytest.importorskip("dependency", minversion="2.0", defer=True)
        def test_first(): pass
        def test_second(): pass
    """
    )
    result = pytester.runpytest("-rs")
    result.assert_outcomes(skipped=2)
    result.stdout.fnmatch_lines(
        ["SKIPPED [[]2[]] test_version.py:2: *required is: '2.0'"]
    )


def test_deferred_preserves_existing_markers(pytester: Pytester) -> None:
    pytester.makepyfile("""
        import pytest
        pytestmark = pytest.mark.slow
        pytest.importorskip("missing_deferred_dependency", defer=True)
        def test_marked(): pass
    """)
    result = pytester.runpytest("-m", "not slow", "-o", "markers=slow: slow tests")
    result.assert_outcomes(deselected=1)


def test_deferred_custom_reason(pytester: Pytester) -> None:
    pytester.makepyfile("""
        import pytest
        pytest.importorskip("missing_deferred_dependency", defer=True, reason="needs extra")
        def test_first(): pass
        def test_second(): pass
    """)
    result = pytester.runpytest("-rs")
    result.assert_outcomes(skipped=2)
    result.stdout.fnmatch_lines(["SKIPPED [[]2[]] *: needs extra"])
