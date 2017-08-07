import pytest


def test_success():
    assert True


def test_fails():
    assert False


@pytest.mark.parametrize("number", list(range(3)))
def test_fixtures(number):
    assert number % 2 == 0


def test_error():
    1/0