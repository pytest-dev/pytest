import pytest

def test_basic_math():
    assert 1 + 1 == 2

def test_pytest_raises():
    with pytest.raises(ZeroDivisionError):
        1 / 0
