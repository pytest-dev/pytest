"""Test case for issue #13817: AttributeError with invalid flag in pytest_addoption."""

from __future__ import annotations

from _pytest.config.argparsing import ArgumentError
from _pytest.config.argparsing import Parser
import pytest


# Suppress warning about using private pytest API (we're testing pytest itself)
@pytest.mark.filterwarnings("ignore::pytest.PytestDeprecationWarning")
class TestArgumentReprFix:
    """Test that Argument.__repr__ handles missing dest attribute."""

    def test_invalid_option_without_dashes(self) -> None:
        """Test that invalid option names produce helpful error messages."""
        parser = Parser()

        with pytest.raises(ArgumentError) as exc_info:
            parser.addoption("shuffle")  # Missing required -- prefix

        error_message = str(exc_info.value)
        assert "invalid long option string" in error_message
        assert "shuffle" in error_message
        assert "must start with --" in error_message

        # Ensure no AttributeError is mentioned
        assert "AttributeError" not in error_message
        assert "has no attribute 'dest'" not in error_message

    def test_invalid_short_option(self) -> None:
        """Test that invalid short option names produce helpful error messages."""
        parser = Parser()

        with pytest.raises(ArgumentError) as exc_info:
            parser.addoption("-ab")  # 3 chars, treated as invalid long option

        error_message = str(exc_info.value)
        # -ab is treated as invalid long option (3+ chars)
        assert (
            "invalid long option string" in error_message
            or "invalid short option string" in error_message
        )

    def test_valid_option_works(self) -> None:
        """Test that valid options still work correctly."""
        parser = Parser()
        parser.addoption("--shuffle", action="store_true", help="Shuffle tests")

        options = parser._anonymous.options
        assert len(options) > 0
        assert "--shuffle" in options[0].names()
