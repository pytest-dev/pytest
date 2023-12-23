import pytest


def test_pass():
    print("in test_pass")


def test_fail():
    print("in test_fail")
    a, b = 1, 2
    assert a == b


@pytest.mark.xfail
def test_xfail():
    print("in test_xfail")
    a, b = 1, 2
    assert a == b


@pytest.mark.xfail(reason="reason 1")
def test_xfail_reason():
    print("in test_xfail")
    a, b = 1, 2
    assert a == b


@pytest.mark.xfail(reason="reason 2")
def test_xpass():
    print("in test_xpass")
    a, b = 1, 1
    assert a == b
