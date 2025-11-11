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

    def test_repr_with_dest_set(self) -> None:
        """Test that __repr__ works correctly when dest is set."""
        parser = Parser()
        parser.addoption("--valid-option", dest="valid_dest", help="A valid option")

        # Get the argument object and check its repr
        option = parser._anonymous.options[0]
        repr_str = repr(option)

        # Should contain the dest
        assert "dest: 'valid_dest'" in repr_str
        assert "NOT_SET" not in repr_str

    def test_repr_without_dest(self) -> None:
        """Test that __repr__ works when dest is not set due to error."""
        from _pytest.config.argparsing import Argument

        # Create an Argument that will fail during initialization
        # This triggers the code path where dest is not set
        try:
            Argument("invalid")  # No dashes, will fail
        except ArgumentError as exc:
            # The repr was called during error creation
            # Verify it contains NOT_SET representation
            assert "dest:" in str(exc)
            assert "NOT_SET" in str(exc) or "<notset>" in str(exc)
