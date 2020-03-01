import warnings

import pytest


def func():
    warnings.warn(UserWarning("foo"))


@pytest.fixture(params=range(20), autouse=True)
def repeat_hack(request):
    return request.param


@pytest.mark.parametrize("i", range(5))
def test_foo(i):
    func()


def test_bar():
    func()
