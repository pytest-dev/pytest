from __future__ import annotations

from _pytest.pytester import Pytester


def test_generate_tests_discovery_in_test_module_and_not_other_hooks(
    pytester: Pytester,
) -> None:
    pytester.makepyfile(
        """
        def pytest_generate_tests(metafunc):
            if "x" in metafunc.fixturenames:
                metafunc.parametrize("x", [1, 2])

        def pytest_terminal_summary(terminalreporter):
            raise AssertionError("should not be called")

        def test_x(x):
            assert x in (1, 2)
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=2)
