import sys
import py
import pytest

ast = pytest.importorskip("ast")

from _pytest.assertrewrite import rewrite_asserts


def setup_module(mod):
    mod._old_reprcompare = py.code._reprcompare
    py.code._reprcompare = None

def teardown_module(mod):
    py.code._reprcompare = mod._old_reprcompare
    del mod._old_reprcompare


def getmsg(f, extra_ns=None, must_pass=False):
    """Rewrite the assertions in f, run it, and get the failure message."""
    src = '\n'.join(py.code.Code(f).source().lines)
    mod = ast.parse(src)
    rewrite_asserts(mod)
    code = compile(mod, "<test>", "exec")
    ns = {}
    if extra_ns is not None:
        ns.update(extra_ns)
    exec code in ns
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
            f = True
            g = False
            assert f or g
        getmsg(f, must_pass=True)

    def test_short_circut_evaluation(self):
        pytest.xfail("complicated fix; I'm not sure if it's important")
        def f():
            assert True or explode
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
        assert getmsg(f, ns) == """assert False
 +  where False = g()"""
        def f():
            assert g(1)
        assert getmsg(f, ns) == """assert False
 +  where False = g(1)"""
        def f():
            assert g(1, 2)
        assert getmsg(f, ns) == """assert False
 +  where False = g(1, 2)"""
        def f():
            assert g(1, g=42)
        assert getmsg(f, ns) == """assert False
 +  where False = g(1, g=42)"""
        def f():
            assert g(1, 3, g=23)
        assert getmsg(f, ns) == """assert False
 +  where False = g(1, 3, g=23)"""

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
        assert getmsg(f, ns) == """assert False
 +  where False = x.a"""

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

    def test_len(self):
        def f():
            l = range(10)
            assert len(l) == 11
        assert getmsg(f).startswith("""assert 10 == 11
 +  where 10 = len([""")

    def test_custom_reprcompare(self, monkeypatch):
        def my_reprcompare(op, left, right):
            return "42"
        monkeypatch.setattr(py.code, "_reprcompare", my_reprcompare)
        def f():
            assert 42 < 3
        assert getmsg(f) == "assert 42"
        def my_reprcompare(op, left, right):
            return "%s %s %s" % (left, op, right)
        monkeypatch.setattr(py.code, "_reprcompare", my_reprcompare)
        def f():
            assert 1 < 3 < 5 <= 4 < 7
        assert getmsg(f) == "assert 5 <= 4"
