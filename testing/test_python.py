import pytest


@pytest.mark.parametrize("a", [1, 2, 10, 11, 2, 1, 12, 11, 2_1])
def test_params(a):
    print("a:", a)
    assert a > 0


@pytest.mark.parametrize("a", [1, 2, 10, 11, 2, 1, 12, 11])
def test_params(a):
    print("a:", a)
    assert a > 0
