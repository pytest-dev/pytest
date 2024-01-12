from _pytest.pytester import Pytester


class TestWarningAttributes:
    def test_raise_type_error(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest
            import warnings

            def test_example_one():
                with pytest.warns(UserWarning):
                    warnings.warn(1)
            """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["*1 failed*"])
