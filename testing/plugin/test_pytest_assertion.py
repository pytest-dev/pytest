import sys

import py
import py._plugin.pytest_assertion as plugin

needsnewassert = py.test.mark.skipif("sys.version_info < (2,6)")

def interpret(expr):
    return py.code._reinterpret(expr, py.code.Frame(sys._getframe(1)))

class TestBinReprIntegration:
    pytestmark = needsnewassert

    def pytest_funcarg__hook(self, request):
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
        mockhook = MockHook()
        monkeypatch = request.getfuncargvalue("monkeypatch")
        monkeypatch.setattr(py.code, '_binrepr', mockhook)
        return mockhook

    def test_pytest_assert_binrepr_called(self, hook):
        interpret('assert 0 == 1')
        assert hook.called


    def test_pytest_assert_binrepr_args(self, hook):
        interpret('assert [0, 1] == [0, 2]')
        assert hook.op == '=='
        assert hook.left == [0, 1]
        assert hook.right == [0, 2]

    def test_configure_unconfigure(self, testdir, hook):
        assert hook == py.code._binrepr
        config = testdir.parseconfig()
        plugin.pytest_configure(config)
        assert hook != py.code._binrepr
        plugin.pytest_unconfigure(config)
        assert hook == py.code._binrepr

class TestAssert_binrepr:
    def test_different_types(self):
        assert plugin.pytest_assert_binrepr('==', [0, 1], 'foo') is None

    def test_summary(self):
        summary = plugin.pytest_assert_binrepr('==', [0, 1], [0, 2])[0]
        assert len(summary) < 65

    def test_text_diff(self):
        diff = plugin.pytest_assert_binrepr('==', 'spam', 'eggs')[1:]
        assert '- spam' in diff
        assert '+ eggs' in diff

    def test_multiline_text_diff(self):
        left = 'foo\nspam\nbar'
        right = 'foo\neggs\nbar'
        diff = plugin.pytest_assert_binrepr('==', left, right)
        assert '- spam' in diff
        assert '+ eggs' in diff

    def test_list(self):
        expl = plugin.pytest_assert_binrepr('==', [0, 1], [0, 2])
        assert len(expl) > 1

    def test_list_different_lenghts(self):
        expl = plugin.pytest_assert_binrepr('==', [0, 1], [0, 1, 2])
        assert len(expl) > 1
        expl = plugin.pytest_assert_binrepr('==', [0, 1, 2], [0, 1])
        assert len(expl) > 1

    def test_dict(self):
        expl = plugin.pytest_assert_binrepr('==', {'a': 0}, {'a': 1})
        assert len(expl) > 1

    def test_set(self):
        expl = plugin.pytest_assert_binrepr('==', set([0, 1]), set([0, 2]))
        assert len(expl) > 1

@needsnewassert
def test_pytest_assert_binrepr_integration(testdir):
    testdir.makepyfile("""
        def test_hello():
            x = set(range(100))
            y = x.copy()
            y.remove(50)
            assert x == y
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
        "*def test_hello():*",
        "*assert x == y*",
        "*E*Extra items*left*",
        "*E*50*",
    ])

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

