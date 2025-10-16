"""Test for issue #13816 - better error messages for dict key mismatches in pytest.approx()"""
import pytest


def test_approx_dicts_with_different_keys_clear_error():
    """Test that pytest.approx() gives a clear error when dict keys don't match."""
    expected = {"a": 1, "c": 3}
    actual = {"a": 1, "b": 4}
    
    with pytest.raises(AssertionError) as exc_info:
        assert pytest.approx(actual) == expected
    
    error_message = str(exc_info.value)
    # Should mention "different keys" clearly
    assert "different keys" in error_message.lower()
    # Should NOT have the confusing KeyError message
    assert "KeyError" not in error_message
    # Should NOT mention "faulty __repr__"
    assert "faulty __repr__" not in error_message


def test_approx_dicts_with_extra_key_in_expected():
    """Test error message when expected has extra keys."""
    expected = {"a": 1, "b": 2, "c": 3}
    actual = {"a": 1, "b": 2}
    
    with pytest.raises(AssertionError) as exc_info:
        assert pytest.approx(actual) == expected
    
    error_message = str(exc_info.value)
    assert "different keys" in error_message.lower()


def test_approx_dicts_with_extra_key_in_actual():
    """Test error message when actual has extra keys."""
    expected = {"a": 1, "b": 2}
    actual = {"a": 1, "b": 2, "c": 3}
    
    with pytest.raises(AssertionError) as exc_info:
        assert pytest.approx(actual) == expected
    
    error_message = str(exc_info.value)
    assert "different keys" in error_message.lower()


def test_approx_dicts_matching_keys_still_works():
    """Test that dicts with matching keys still work normally."""
    expected = {"a": 1.0001, "b": 2.0001}
    actual = {"a": 1.0, "b": 2.0}
    
    assert pytest.approx(actual, rel=1e-3) == expected
