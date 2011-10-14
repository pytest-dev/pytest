import sys
import zipfile
import py
import pytest

ast = pytest.importorskip("ast")
if sys.platform.startswith("java"):
    # XXX should be xfail
    pytest.skip("assert rewrite does currently not work on jython")

from _pytest.assertion import util
from _pytest.assertion.rewrite import rewrite_asserts


def setup_module(mod):
    mod._old_reprcompare = util._reprcompare
    py.code._reprcompare = None

def teardown_module(mod):
    util._reprcompare = mod._old_reprcompare
    del mod._old_reprcompare


def rewrite(src):
    tree = ast.parse(src)
    rewrite_asserts(tree)
    return tree

def getmsg(f, extra_ns=None, must_pass=False):
    """Rewrite the assertions in f, run it, and get the failure message."""
    src = '\n'.join(py.code.Code(f).source().lines)
    mod = rewrite(src)
    code = compile(mod, "<test>", "exec")
    ns = {}
    if extra_ns is not None:
        ns.update(extra_ns)
    py.builtin.exec_(code, ns)
    func = ns[f.__name__]
    try:
        func()
    except AssertionError:
        if must_pass:
            pytest.fail("shouldn't have raised")
        s = str(sys.exc_info()[1])
        if not s.startswith("assert"):
            return "AssertionError: " + s
        return s
    else:
        if not must_pass:
            pytest.fail("function didn't raise at all")


class TestAssertionRewrite:

    def test_place_initial_imports(self):
        s = """'Doc string'\nother = stuff"""
        m = rewrite(s)
        assert isinstance(m.body[0], ast.Expr)
        assert isinstance(m.body[0].value, ast.Str)
        for imp in m.body[1:3]:
            assert isinstance(imp, ast.Import)
            assert imp.lineno == 2
            assert imp.col_offset == 0
        assert isinstance(m.body[3], ast.Assign)
        s = """from __future__ import with_statement\nother_stuff"""
        m = rewrite(s)
        assert isinstance(m.body[0], ast.ImportFrom)
        for imp in m.body[1:3]:
            assert isinstance(imp, ast.Import)
            assert imp.lineno == 2
            assert imp.col_offset == 0
        assert isinstance(m.body[3], ast.Expr)
        s = """'doc string'\nfrom __future__ import with_statement\nother"""
        m = rewrite(s)
        assert isinstance(m.body[0], ast.Expr)
        assert isinstance(m.body[0].value, ast.Str)
        assert isinstance(m.body[1], ast.ImportFrom)
        for imp in m.body[2:4]:
            assert isinstance(imp, ast.Import)
            assert imp.lineno == 3
            assert imp.col_offset == 0
        assert isinstance(m.body[4], ast.Expr)
        s = """from . import relative\nother_stuff"""
        m = rewrite(s)
        for imp in m.body[0:2]:
            assert isinstance(imp, ast.Import)
            assert imp.lineno == 1
            assert imp.col_offset == 0
        assert isinstance(m.body[3], ast.Expr)

    def test_dont_rewrite(self):
        s = """'PYTEST_DONT_REWRITE'\nassert 14"""
        m = rewrite(s)
        assert len(m.body) == 2
        assert isinstance(m.body[0].value, ast.Str)
        assert isinstance(m.body[1], ast.Assert)
        assert m.body[1].msg is None

    def test_name(self):
        def f():
            assert False
        assert getmsg(f) == "assert False"
        def f():
            f = False
            assert f
        assert getmsg(f) == "assert False"
        def f():
            assert a_global
        assert getmsg(f, {"a_global" : False}) == "assert a_global"

    def test_assert_already_has_message(self):
        def f():
            assert False, "something bad!"
        assert getmsg(f) == "AssertionError: something bad!"

    def test_boolop(self):
        def f():
            f = g = False
            assert f and g
        assert getmsg(f) == "assert (False)"
        def f():
            f = True
            g = False
            assert f and g
        assert getmsg(f) == "assert (True and False)"
        def f():
            f = False
            g = True
            assert f and g
        assert getmsg(f) == "assert (False)"
        def f():
            f = g = False
            assert f or g
        assert getmsg(f) == "assert (False or False)"
        def f():
            f = g = False
            assert not f and not g
        getmsg(f, must_pass=True)
        def x():
            return False
        def f():
            assert x() and x()
        assert getmsg(f, {"x" : x}) == "assert (x())"
        def f():
            assert False or x()
        assert getmsg(f, {"x" : x}) == "assert (False or x())"
        def f():
            assert 1 in {} and 2 in {}
        assert getmsg(f) == "assert (1 in {})"
        def f():
            x = 1
            y = 2
            assert x in {1 : None} and y in {}
        assert getmsg(f) == "assert (1 in {1: None} and 2 in {})"
        def f():
            f = True
            g = False
            assert f or g
        getmsg(f, must_pass=True)
        def f():
            f = g = h = lambda: True
            assert f() and g() and h()
        getmsg(f, must_pass=True)

    def test_short_circut_evaluation(self):
        def f():
            assert True or explode
        getmsg(f, must_pass=True)
        def f():
            x = 1
            assert x == 1 or x == 2
        getmsg(f, must_pass=True)

    def test_unary_op(self):
        def f():
            x = True
            assert not x
        assert getmsg(f) == "assert not True"
        def f():
            x = 0
            assert ~x + 1
        assert getmsg(f) == "assert (~0 + 1)"
        def f():
            x = 3
            assert -x + x
        assert getmsg(f) == "assert (-3 + 3)"
        def f():
            x = 0
            assert +x + x
        assert getmsg(f) == "assert (+0 + 0)"

    def test_binary_op(self):
        def f():
            x = 1
            y = -1
            assert x + y
        assert getmsg(f) == "assert (1 + -1)"

    def test_call(self):
        def g(a=42, *args, **kwargs):
            return False
        ns = {"g" : g}
        def f():
            assert g()
        assert getmsg(f, ns) == """assert g()"""
        def f():
            assert g(1)
        assert getmsg(f, ns) == """assert g(1)"""
        def f():
            assert g(1, 2)
        assert getmsg(f, ns) == """assert g(1, 2)"""
        def f():
            assert g(1, g=42)
        assert getmsg(f, ns) == """assert g(1, g=42)"""
        def f():
            assert g(1, 3, g=23)
        assert getmsg(f, ns) == """assert g(1, 3, g=23)"""
        def f():
            seq = [1, 2, 3]
            assert g(*seq)
        assert getmsg(f, ns) == """assert g(*[1, 2, 3])"""
        def f():
            x = "a"
            assert g(**{x : 2})
        assert getmsg(f, ns) == """assert g(**{'a': 2})"""

    def test_attribute(self):
        class X(object):
            g = 3
        ns = {"X" : X, "x" : X()}
        def f():
            assert not x.g
        assert getmsg(f, ns) == """assert not 3
 +  where 3 = x.g"""
        def f():
            x.a = False
            assert x.a
        assert getmsg(f, ns) == """assert x.a"""

    def test_comparisons(self):
        def f():
            a, b = range(2)
            assert b < a
        assert getmsg(f) == """assert 1 < 0"""
        def f():
            a, b, c = range(3)
            assert a > b > c
        assert getmsg(f) == """assert 0 > 1"""
        def f():
            a, b, c = range(3)
            assert a < b > c
        assert getmsg(f) == """assert 1 > 2"""
        def f():
            a, b, c = range(3)
            assert a < b <= c
        getmsg(f, must_pass=True)
        def f():
            a, b, c = range(3)
            assert a < b
            assert b < c
        getmsg(f, must_pass=True)

    def test_len(self):
        def f():
            l = list(range(10))
            assert len(l) == 11
        assert getmsg(f).startswith("""assert 10 == 11
 +  where 10 = len([""")

    def test_custom_reprcompare(self, monkeypatch):
        def my_reprcompare(op, left, right):
            return "42"
        monkeypatch.setattr(util, "_reprcompare", my_reprcompare)
        def f():
            assert 42 < 3
        assert getmsg(f) == "assert 42"
        def my_reprcompare(op, left, right):
            return "%s %s %s" % (left, op, right)
        monkeypatch.setattr(util, "_reprcompare", my_reprcompare)
        def f():
            assert 1 < 3 < 5 <= 4 < 7
        assert getmsg(f) == "assert 5 <= 4"

    def test_assert_raising_nonzero_in_comparison(self):
        def f():
            class A(object):
                def __nonzero__(self):
                    raise ValueError(42)
                def __lt__(self, other):
                    return A()
                def __repr__(self):
                    return "<MY42 object>"
            def myany(x):
                return False
            assert myany(A() < 0)
        assert "<MY42 object> < 0" in getmsg(f)

    def test_formatchar(self):
        def f():
            assert "%test" == "test"
        assert getmsg(f).startswith("assert '%test' == 'test'")


class TestRewriteOnImport:

    def test_pycache_is_a_file(self, testdir):
        testdir.tmpdir.join("__pycache__").write("Hello")
        testdir.makepyfile("""
def test_rewritten():
    assert "@py_builtins" in globals()""")
        assert testdir.runpytest().ret == 0

    def test_zipfile(self, testdir):
        z = testdir.tmpdir.join("myzip.zip")
        z_fn = str(z)
        f = zipfile.ZipFile(z_fn, "w")
        try:
            f.writestr("test_gum/__init__.py", "")
            f.writestr("test_gum/test_lizard.py", "")
        finally:
            f.close()
        z.chmod(256)
        testdir.makepyfile("""
import sys
sys.path.append(%r)
import test_gum.test_lizard""" % (z_fn,))
        assert testdir.runpytest().ret == 0

    def test_readonly(self, testdir):
        sub = testdir.mkdir("testing")
        sub.join("test_readonly.py").write(
        py.builtin._totext("""
def test_rewritten():
    assert "@py_builtins" in globals()
""").encode("utf-8"), "wb")
        sub.chmod(320)
        assert testdir.runpytest().ret == 0

    def test_dont_write_bytecode(self, testdir, monkeypatch):
        testdir.makepyfile("""
import os
def test_no_bytecode():
    assert "__pycache__" in __cached__
    assert not os.path.exists(__cached__)
    assert not os.path.exists(os.path.dirname(__cached__))""")
        monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
        assert testdir.runpytest().ret == 0

    def test_pyc_vs_pyo(self, testdir, monkeypatch):
        testdir.makepyfile("""
import pytest
def test_optimized():
    "hello"
    assert test_optimized.__doc__ is None""")
        p = py.path.local.make_numbered_dir(prefix="runpytest-", keep=None,
                                            rootdir=testdir.tmpdir)
        tmp = "--basetemp=%s" % p
        monkeypatch.setenv("PYTHONOPTIMIZE", "2")
        assert testdir.runpybin("py.test", tmp).ret == 0
        monkeypatch.undo()
        assert testdir.runpybin("py.test", tmp).ret == 1

    def test_package(self, testdir):
        pkg = testdir.tmpdir.join("pkg")
        pkg.mkdir()
        pkg.join("__init__.py").ensure()
        pkg.join("test_blah.py").write("""
def test_rewritten():
    assert "@py_builtins" in globals()""")
        assert testdir.runpytest().ret == 0

    def test_translate_newlines(self, testdir):
        content = "def test_rewritten():\r\n assert '@py_builtins' in globals()"
        b = content.encode("utf-8")
        testdir.tmpdir.join("test_newlines.py").write(b, "wb")
        assert testdir.runpytest().ret == 0
