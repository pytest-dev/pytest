import pytest


def test_pass():
    ...


def test_fail():
    a, b = 1, 2
    assert a == b


@pytest.mark.xfail
def test_xfail():
    a, b = 1, 2
    assert a == b


@pytest.mark.xfail
def test_xpass():
    a, b = 1, 1
    assert a == b
