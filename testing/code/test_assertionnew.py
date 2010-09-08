import sys

import py
from py._code._assertionnew import interpret


def getframe():
    """Return the frame of the caller as a py.code.Frame object"""
    return py.code.Frame(sys._getframe(1))


def pytest_funcarg__hook(request):
    class MockHook(object):
        def __init__(self):
            self.called = False
            self.args = tuple()
            self.kwargs = dict()

        def __call__(self, op, left, right):
            self.called = True
            self.op = op
            self.left = left
            self.right = right
    return MockHook()


def test_pytest_assert_compare_called(monkeypatch, hook):
    monkeypatch.setattr(py._plugin.pytest_assertion,
                        'pytest_assert_compare', hook)
    interpret('assert 0 == 1', getframe())
    assert hook.called


def test_pytest_assert_compare_args(monkeypatch, hook):
    print hook.called
    monkeypatch.setattr(py._plugin.pytest_assertion,
                        'pytest_assert_compare', hook)
    interpret('assert [0, 1] == [0, 2]', getframe())
    print hook.called
    print hook.left
    print hook.right
    assert hook.op == '=='
    assert hook.left == [0, 1]
    assert hook.right == [0, 2]
