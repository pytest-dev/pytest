# mypy: allow-untyped-defs
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from _pytest.config import ExitCode
from _pytest.fixtures import get_return_annotation
from _pytest.pytester import Pytester


class TestGetReturnAnnotation:
    def test_primitive_return_type(self):
        def six() -> int:
            return 6

        assert get_return_annotation(six) == "int"

    def test_compound_return_type(self):
        def two_sixes() -> tuple[int, str]:
            return (6, "six")

        assert get_return_annotation(two_sixes) == "tuple[int, str]"

    def test_callable_return_type(self):
        def callable_return() -> Callable[..., Any]:
            return self.test_compound_return_type

        assert get_return_annotation(callable_return) == "Callable[..., Any]"

    def test_no_annotation(self):
        def no_annotation():
            return 6

        assert get_return_annotation(no_annotation) == ""

    def test_none_return_type(self):
        def none_return() -> None:
            pass

        assert get_return_annotation(none_return) == "None"

    def test_custom_class_return_type(self):
        class T:
            pass

        def class_return() -> T:
            return T()

        assert get_return_annotation(class_return) == "T"

    def test_enum_return_type(self):
        def enum_return() -> ExitCode:
            return ExitCode(0)

        assert get_return_annotation(enum_return) == "ExitCode"

    def test_with_arg_annotations(self):
        def with_args(a: Callable[[], None], b: str) -> range:
            return range(2)

        assert get_return_annotation(with_args) == "range"

    def test_string_return_annotation(self):
        def string_return_annotation() -> int:
            return 6

        assert get_return_annotation(string_return_annotation) == "int"

    def test_invalid_return_type(self):
        def bad_annotation() -> 6:  # type: ignore
            return 6

        assert get_return_annotation(bad_annotation) == "6"

    def test_unobtainable_signature(self):
        assert get_return_annotation(len) == ""


def test_fixtures_return_annotation(pytester: Pytester) -> None:
    p = pytester.makepyfile(
        """
        import pytest
        @pytest.fixture
        def six() -> int:
            return 6
    """
    )
    result = pytester.runpytest("--fixtures", p)
    result.stdout.fnmatch_lines(
        """
        *fixtures defined from*
        *six -> int -- test_fixtures_return_annotation.py:3*
    """
    )


def test_fixtures_per_test_return_annotation(pytester: Pytester) -> None:
    p = pytester.makepyfile(
        """
        import pytest
        @pytest.fixture
        def five() -> int:
            return 5
        def test_five(five):
            pass
    """
    )

    result = pytester.runpytest("--fixtures-per-test", p)
    assert result.ret == 0

    result.stdout.fnmatch_lines(
        [
            "*fixtures used by test_five*",
            "*(test_fixtures_per_test_return_annotation.py:6)*",
            "five -> int -- test_fixtures_per_test_return_annotation.py:3",
        ]
    )
