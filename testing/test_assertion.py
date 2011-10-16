import sys

import py, pytest
import _pytest.assertion as plugin
from _pytest.assertion import reinterpret, util

needsnewassert = pytest.mark.skipif("sys.version_info < (2,6)")

def interpret(expr):
    return reinterpret.reinterpret(expr, py.code.Frame(sys._getframe(1)))

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
        monkeypatch.setattr(util, '_reprcompare', mockhook)
        return mockhook

    def test_pytest_assertrepr_compare_called(self, hook):
        interpret('assert 0 == 1')
        assert hook.called


    def test_pytest_assertrepr_compare_args(self, hook):
        interpret('assert [0, 1] == [0, 2]')
        assert hook.op == '=='
        assert hook.left == [0, 1]
        assert hook.right == [0, 2]

def callequal(left, right):
    return plugin.pytest_assertrepr_compare('==', left, right)

class TestAssert_reprcompare:
    def test_different_types(self):
        assert callequal([0, 1], 'foo') is None

    def test_summary(self):
        summary = callequal([0, 1], [0, 2])[0]
        assert len(summary) < 65

    def test_text_diff(self):
        diff = callequal('spam', 'eggs')[1:]
        assert '- spam' in diff
        assert '+ eggs' in diff

    def test_multiline_text_diff(self):
        left = 'foo\nspam\nbar'
        right = 'foo\neggs\nbar'
        diff = callequal(left, right)
        assert '- spam' in diff
        assert '+ eggs' in diff

    def test_list(self):
        expl = callequal([0, 1], [0, 2])
        assert len(expl) > 1

    def test_list_different_lenghts(self):
        expl = callequal([0, 1], [0, 1, 2])
        assert len(expl) > 1
        expl = callequal([0, 1, 2], [0, 1])
        assert len(expl) > 1

    def test_dict(self):
        expl = callequal({'a': 0}, {'a': 1})
        assert len(expl) > 1

    def test_set(self):
        expl = callequal(set([0, 1]), set([0, 2]))
        assert len(expl) > 1

    def test_list_tuples(self):
        expl = callequal([], [(1,2)])
        assert len(expl) > 1
        expl = callequal([(1,2)], [])
        assert len(expl) > 1

    def test_list_bad_repr(self):
        class A:
            def __repr__(self):
                raise ValueError(42)
        expl = callequal([], [A()])
        assert 'ValueError' in "".join(expl)
        expl = callequal({}, {'1': A()})
        assert 'faulty' in "".join(expl)

    def test_one_repr_empty(self):
        """
        the faulty empty string repr did trigger
        a unbound local error in _diff_text
        """
        class A(str):
            def __repr__(self):
                return ''
        expl = callequal(A(), '')
        assert not expl

    def test_repr_no_exc(self):
        expl = ' '.join(callequal('foo', 'bar'))
        assert 'raised in repr()' not in expl

@needsnewassert
def test_rewritten(testdir):
    testdir.makepyfile("""
        def test_rewritten():
            assert "@py_builtins" in globals()
    """)
    assert testdir.runpytest().ret == 0

def test_reprcompare_notin():
    detail = plugin.pytest_assertrepr_compare('not in', 'foo', 'aaafoobbb')[1:]
    assert detail == ["'foo' is contained here:", '  aaafoobbb', '?    +++']

@needsnewassert
def test_pytest_assertrepr_compare_integration(testdir):
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

@needsnewassert
def test_sequence_comparison_uses_repr(testdir):
    testdir.makepyfile("""
        def test_hello():
            x = set("hello x")
            y = set("hello y")
            assert x == y
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
        "*def test_hello():*",
        "*assert x == y*",
        "*E*Extra items*left*",
        "*E*'x'*",
        "*E*Extra items*right*",
        "*E*'y'*",
    ])

@needsnewassert
def test_assertrepr_loaded_per_dir(testdir):
    testdir.makepyfile(test_base=['def test_base(): assert 1 == 2'])
    a = testdir.mkdir('a')
    a_test = a.join('test_a.py')
    a_test.write('def test_a(): assert 1 == 2')
    a_conftest = a.join('conftest.py')
    a_conftest.write('def pytest_assertrepr_compare(): return ["summary a"]')
    b = testdir.mkdir('b')
    b_test = b.join('test_b.py')
    b_test.write('def test_b(): assert 1 == 2')
    b_conftest = b.join('conftest.py')
    b_conftest.write('def pytest_assertrepr_compare(): return ["summary b"]')
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
            '*def test_base():*',
            '*E*assert 1 == 2*',
            '*def test_a():*',
            '*E*assert summary a*',
            '*def test_b():*',
            '*E*assert summary b*'])


def test_assertion_options(testdir):
    testdir.makepyfile("""
        def test_hello():
            x = 3
            assert x == 4
    """)
    result = testdir.runpytest()
    assert "3 == 4" in result.stdout.str()
    off_options = (("--no-assert",),
                   ("--nomagic",),
                   ("--no-assert", "--nomagic"),
                   ("--assert=plain",),
                   ("--assert=plain", "--no-assert"),
                   ("--assert=plain", "--nomagic"),
                   ("--assert=plain", "--no-assert", "--nomagic"))
    for opt in off_options:
        result = testdir.runpytest(*opt)
        assert "3 == 4" not in result.stdout.str()

def test_old_assert_mode(testdir):
    testdir.makepyfile("""
        def test_in_old_mode():
            assert "@py_builtins" not in globals()
    """)
    result = testdir.runpytest("--assert=reinterp")
    assert result.ret == 0

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

@pytest.mark.skipif("sys.version_info < (2,5) or '__pypy__' in sys.builtin_module_names or sys.platform.startswith('java')" )
def test_warn_missing(testdir):
    p1 = testdir.makepyfile("")
    result = testdir.run(sys.executable, "-OO", "-m", "pytest", "-h")
    result.stderr.fnmatch_lines([
        "*WARNING*assert statements are not executed*",
    ])
    result = testdir.run(sys.executable, "-OO", "-m", "pytest", "--no-assert")
    result.stderr.fnmatch_lines([
        "*WARNING*assert statements are not executed*",
    ])
