import sys

import py
from py._code._assertionnew import interpret
import py._plugin.pytest_assertion as plugin


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


def test_functional(testdir):
    testdir.makepyfile("""
        def test_hello():
            x = 3
            assert x == 4
    """)
    result = testdir.runpytest()
    assert "3 == 4" in result.stdout.str()
    result = testdir.runpytest("--no-assert")
    assert "3 == 4" not in result.stdout.str()

def test_triple_quoted_string_issue113(testdir):
    testdir.makepyfile("""
        def test_hello():
            assert "" == '''
    '''""")
    result = testdir.runpytest("--fulltrace")
    result.stdout.fnmatch_lines([
        "*1 failed*",
    ])
    assert 'SyntaxError' not in result.stdout.str()

def test_traceback_failure(testdir):
    p1 = testdir.makepyfile("""
        def g():
            return 2
        def f(x):
            assert x == g()
        def test_onefails():
            f(3)
    """)
    result = testdir.runpytest(p1)
    result.stdout.fnmatch_lines([
        "*test_traceback_failure.py F",
        "====* FAILURES *====",
        "____*____",
        "",
        "    def test_onefails():",
        ">       f(3)",
        "",
        "*test_*.py:6: ",
        "_ _ _ *",
        #"",
        "    def f(x):",
        ">       assert x == g()",
        "E       assert 3 == 2",
        "E        +  where 2 = g()",
        "",
        "*test_traceback_failure.py:4: AssertionError"
    ])


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


class TestAssertCompare:
    def test_different_types(self):
        assert plugin.pytest_assert_compare('==', [0, 1], 'foo') is None

    def test_summary(self):
        summary = plugin.pytest_assert_compare('==', [0, 1], [0, 2])[0]
        assert len(summary) < 65

    def test_text_diff(self):
        diff = plugin.pytest_assert_compare('==', 'spam', 'eggs')[1:]
        assert '- spam' in diff
        assert '+ eggs' in diff

    def test_multiline_text_diff(self):
        left = 'foo\nspam\nbar'
        right = 'foo\neggs\nbar'
        diff = plugin.pytest_assert_compare('==', left, right)
        assert '- spam' in diff
        assert '+ eggs' in diff

    def test_list(self):
        expl = plugin.pytest_assert_compare('==', [0, 1], [0, 2])
        assert len(expl) > 1

    def test_dict(self):
        expl = plugin.pytest_assert_compare('==', {'a': 0}, {'a': 1})
        assert len(expl) > 1

    def test_set(self):
        expl = plugin.pytest_assert_compare('==', set([0, 1]), set([0, 2]))
        assert len(expl) > 1
