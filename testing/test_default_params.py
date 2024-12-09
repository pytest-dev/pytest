from _pytest.pytester import Pytester

def test_no_default_argument(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        def test_with_default_param(param):
            assert param == 42
        """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines([
        "*fixture 'param' not found*"
    ])


def test_default_argument_warning(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        def test_with_default_param(param=42):
            assert param == 42
        """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines([
        "*PytestDefaultArgumentWarning: Test function 'test_with_default_param' has a default argument 'param=42'.*"
    ])


def test_no_warning_for_no_default_param(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        def test_without_default_param(param):
            assert param is None
        """
    )
    result = pytester.runpytest()
    assert "PytestDefaultArgumentWarning" not in result.stdout.str()
    

def test_warning_for_multiple_default_params(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        def test_with_multiple_defaults(param1=42, param2="default"):
            assert param1 == 42
            assert param2 == "default"
        """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines([
        "*PytestDefaultArgumentWarning: Test function 'test_with_multiple_defaults' has a default argument 'param1=42'.*",
        "*PytestDefaultArgumentWarning: Test function 'test_with_multiple_defaults' has a default argument 'param2=default'.*"
    ])