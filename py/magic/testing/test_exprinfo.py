
import sys
import py
from py.__.magic.exprinfo import getmsg, interpret

def getexcinfo(exc, obj, *args, **kwargs):
    try:
        obj(*args, **kwargs)
    except KeyboardInterrupt:
        raise
    except exc:
        return sys.exc_info()
    else:
        raise AssertionError, "%r(*%r, **%r) did not raise" %(
            obj, args, kwargs)

def test_assert_exprinfo():
    def g():
        a = 1
        b = 2
        assert a == b
    excinfo = getexcinfo(AssertionError, g)
    msg = getmsg(excinfo)
    assert msg == 'assert 1 == 2'

def test_nested_scopes():
    def g():
        a = 1
        def h():
            return a
        b = 2
        assert h() == b
    excinfo = getexcinfo(AssertionError, g)
    msg = getmsg(excinfo)
    assert msg.startswith('assert 1 == 2\n +  where 1 = ')

def test_nested_scopes_2():
    a = 1
    def g():
        b = 2
        assert a == b
    excinfo = getexcinfo(AssertionError, g)
    msg = getmsg(excinfo)
    assert msg == 'assert 1 == 2'

def test_assert_func_argument_type_error():
    def f ():
        pass
    def g():
        f(1)
    excinfo = getexcinfo(TypeError, g)
    msg = getmsg(excinfo)
    assert msg.find("takes no argument") != -1

    class A:
        def f():
            pass
    def g():
        A().f()
    excinfo = getexcinfo(TypeError, g)
    msg = getmsg(excinfo)
    assert msg.find("takes no argument") != -1

    def g():
        A.f()
    excinfo = getexcinfo(TypeError, g)
    msg = getmsg(excinfo)
    assert msg.find("must be called with A") != -1

def global_f(u=6, v=7):
    return u*v

def test_exprinfo_funccall():
    def g():
        assert global_f() == 43
    excinfo = getexcinfo(AssertionError, g)
    msg = getmsg(excinfo)
    assert msg == 'assert 42 == 43\n +  where 42 = global_f()'

def test_exprinfo_funccall_keywords():
    def g():
        assert global_f(v=11) == 67
    excinfo = getexcinfo(AssertionError, g)
    msg = getmsg(excinfo)
    assert msg == 'assert 66 == 67\n +  where 66 = global_f(v=11)'

def test_interpretable_escapes_newlines():
    class X(object):
        def __repr__(self):
            return '1\n2'
    def g():
        assert X() == 'XXX'

    excinfo = getexcinfo(AssertionError, g)
    msg = getmsg(excinfo)
    assert msg == "assert 1\\n2 == 'XXX'\n +  where 1\\n2 = <class 'py.__.magic.testing.test_exprinfo.X'>()"

def test_keyboard_interrupt():
    # XXX this test is slightly strange because it is not
    # clear that "interpret" should execute "raise" statements
    # ... but it apparently currently does and it's nice to
    # exercise the code because the exprinfo-machinery is
    # not much executed when all tests pass ...

    class DummyCode:
        co_filename = 'dummy'
        co_firstlineno = 0
        co_name = 'dummy'
    class DummyFrame:
        f_globals = f_locals = {}
        f_code = DummyCode
        f_lineno = 0

    for exstr in "SystemExit", "KeyboardInterrupt", "MemoryError":
        ex = eval(exstr)
        try:
            interpret("raise %s" % exstr, py.code.Frame(DummyFrame))
        except ex:
            pass
        else:
            raise AssertionError, "ex %s didn't pass through" %(exstr, )
