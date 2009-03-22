from py.test import raises
import py

def otherfunc(a,b):
    assert a==b

def somefunc(x,y):
    otherfunc(x,y)

def otherfunc_multi(a,b): 
    assert (a == 
            b) 

class TestFailing(object):
    def test_simple(self):
        def f():
            return 42
        def g():
            return 43

        assert f() == g()

    def test_simple_multiline(self):
        otherfunc_multi(
                  42,
                  6*9)

    def test_not(self):
        def f():
            return 42
        assert not f()

    def test_complex_error(self):
        def f():
            return 44
        def g():
            return 43
        somefunc(f(), g())

    def test_z1_unpack_error(self):
        l = []
        a,b  = l

    def test_z2_type_error(self):
        l = 3
        a,b  = l

    def test_startswith(self):
        s = "123"
        g = "456"
        assert s.startswith(g)

    def test_startswith_nested(self):
        def f():
            return "123"
        def g():
            return "456"
        assert f().startswith(g())

    def test_global_func(self):
        assert isinstance(globf(42), float)

    def test_instance(self):
        self.x = 6*7
        assert self.x != 42

    def test_compare(self):
        assert globf(10) < 5

    def test_try_finally(self):
        x = 1
        try:
            assert x == 0
        finally:
            x = 0

    def test_raises(self):
        s = 'qwe'
        raises(TypeError, "int(s)")

    def test_raises_doesnt(self):
        raises(IOError, "int('3')")

    def test_raise(self):
        raise ValueError("demo error")

    def test_tupleerror(self):
        a,b = [1]

    def test_reinterpret_fails_with_print_for_the_fun_of_it(self):
        l = [1,2,3]
        print "l is", l
        a,b = l.pop()

    def test_some_error(self):
        if namenotexi:
            pass

    def test_generator(self):
        yield None

    def func1(self):
        assert 41 == 42

    def test_generator2(self):
        yield self.func1

# thanks to Matthew Scott for this test
def test_dynamic_compile_shows_nicely():
    src = 'def foo():\n assert 1 == 0\n'
    name = 'abc-123'
    module = py.std.imp.new_module(name)
    code = py.code.compile(src, name, 'exec')
    exec code in module.__dict__
    py.std.sys.modules[name] = module
    module.foo()


def globf(x):
    return x+1
