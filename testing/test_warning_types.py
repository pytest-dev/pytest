# mypy: allow-untyped-defs
from __future__ import annotations

import inspect
import warnings

from _pytest import warning_types
from _pytest.pytester import Pytester
import pytest


@pytest.mark.parametrize(
    "warning_class",
    [
        w
        for n, w in vars(warning_types).items()
        if inspect.isclass(w) and issubclass(w, Warning)
    ],
)
def test_warning_types(warning_class: UserWarning) -> None:
    """Make sure all warnings declared in _pytest.warning_types are displayed as coming
    from 'pytest' instead of the internal module (#5452).
    """
    assert warning_class.__module__ == "pytest"


@pytest.mark.filterwarnings("error::pytest.PytestWarning")
def test_pytest_warnings_repr_integration_test(pytester: Pytester) -> None:
    """Small integration test to ensure our small hack of setting the __module__ attribute
    of our warnings actually works (#5452).
    """
    pytester.makepyfile(
        """
        import pytest
        import warnings

        def test():
            warnings.warn(pytest.PytestWarning("some warning"))
    """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["E       pytest.PytestWarning: some warning"])


@pytest.mark.filterwarnings("error")
def test_warn_explicit_for_annotates_errors_with_location():
    with pytest.raises(Warning, match=r"(?m)test\n at .*raises.py:\d+"):
        warning_types.warn_explicit_for(
            pytest.raises,  # type: ignore[arg-type]
            warning_types.PytestWarning("test"),
        )


class TestWarningTemplate:
    """A template must build a fresh warning per emission (#14912)."""

    template: warning_types.WarningTemplate[warning_types.PytestWarning] = (
        warning_types.WarningTemplate(warning_types.PytestWarning, "a message")
    )

    def test_format_returns_a_new_instance_each_call(self) -> None:
        first = self.template.format()
        second = self.template.format()

        assert first is not second
        assert isinstance(first, warning_types.PytestWarning)
        assert str(first) == str(second) == "a message"

    def test_constant_message_keeps_literal_braces(self) -> None:
        """Messages without placeholders are not run through str.format()."""
        template = warning_types.WarningTemplate(
            warning_types.PytestWarning, "a {literal} brace and a }} one"
        )

        assert str(template.format()) == "a {literal} brace and a }} one"

    def test_format_substitutes_kwargs(self) -> None:
        template = warning_types.WarningTemplate(
            warning_types.PytestWarning, "hello {name}"
        )

        assert str(template.format(name="world")) == "hello world"

    def test_warn_reports_the_callers_location(self) -> None:
        with warnings.catch_warnings(record=True) as records:
            warnings.simplefilter("always")
            lineno = inspect.currentframe().f_lineno + 1  # type: ignore[union-attr]
            self.template.warn(stacklevel=1)

        [record] = records
        assert record.filename == __file__
        assert record.lineno == lineno

    def test_warn_stacklevel_skips_the_helper(self) -> None:
        def helper() -> None:
            self.template.warn(stacklevel=2)

        with warnings.catch_warnings(record=True) as records:
            warnings.simplefilter("always")
            lineno = inspect.currentframe().f_lineno + 1  # type: ignore[union-attr]
            helper()

        [record] = records
        assert record.filename == __file__
        assert record.lineno == lineno
