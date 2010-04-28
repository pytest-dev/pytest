import py

def exvalue():
    return py.std.sys.exc_info()[1]

def setup_module(mod):
    py.code.patch_builtins(assertion=True, compile=False)

def teardown_module(mod):
    py.code.unpatch_builtins(assertion=True, compile=False)

def f():
    return 2

def test_assert():
    try:
        assert f() == 3
    except AssertionError:
        e = exvalue()
        s = str(e)
        assert s.startswith('assert 2 == 3\n')

def test_assert_with_explicit_message():
    try:
        assert f() == 3, "hello"
    except AssertionError:
        e = exvalue()
        assert e.msg == 'hello'

def test_assert_within_finally():
    class A:
        def f():
            pass
    excinfo = py.test.raises(TypeError, """
        try:
            A().f()
        finally:
            i = 42
    """)
    s = excinfo.exconly() 
    assert s.find("takes no argument") != -1

    #def g():
    #    A.f()
    #excinfo = getexcinfo(TypeError, g)
    #msg = getmsg(excinfo)
    #assert msg.find("must be called with A") != -1


def test_assert_multiline_1():
    try:
        assert (f() ==
                3)
    except AssertionError:
        e = exvalue()
        s = str(e)
        assert s.startswith('assert 2 == 3\n')

def test_assert_multiline_2():
    try:
        assert (f() == (4,
                   3)[-1])
    except AssertionError:
        e = exvalue()
        s = str(e)
        assert s.startswith('assert 2 ==')

def test_in():
    try:
        assert "hi" in [1, 2]
    except AssertionError:
        e = exvalue()
        s = str(e)
        assert s.startswith("assert 'hi' in")

def test_is():
    try:
        assert 1 is 2
    except AssertionError:
        e = exvalue()
        s = str(e)
        assert s.startswith("assert 1 is 2")

def test_assert_non_string_message(): 
    class A: 
        def __str__(self): 
            return "hello"
    try:
        assert 0 == 1, A()
    except AssertionError:
        e = exvalue()
        assert e.msg == "hello"

def test_assert_keyword_arg():
    def f(x=3):
        return False
    try:
        assert f(x=5)
    except AssertionError:
        e = exvalue()
        assert "x=5" in e.msg

# These tests should both fail, but should fail nicely...
class WeirdRepr:
    def __repr__(self):
        return '<WeirdRepr\nsecond line>'
            
def bug_test_assert_repr():
    v = WeirdRepr()
    try: 
        assert v == 1
    except AssertionError:
        e = exvalue()
        assert e.msg.find('WeirdRepr') != -1
        assert e.msg.find('second line') != -1
        assert 0
        
def test_assert_non_string():
    try: 
        assert 0, ['list']
    except AssertionError:
        e = exvalue()
        assert e.msg.find("list") != -1 

def test_assert_implicit_multiline():
    try:
        x = [1,2,3]
        assert x != [1,
           2, 3]
    except AssertionError:
        e = exvalue()
        assert e.msg.find('assert [1, 2, 3] !=') != -1


def test_assert_with_brokenrepr_arg():
    class BrokenRepr:
        def __repr__(self): 0 / 0
    e = AssertionError(BrokenRepr())
    if e.msg.find("broken __repr__") == -1:
        py.test.fail("broken __repr__ not handle correctly")


class TestView:

    def setup_class(cls):
        cls.View = py.test.importorskip("py._code._assertionold").View

    def test_class_dispatch(self):
        ### Use a custom class hierarchy with existing instances

        class Picklable(self.View):
            pass

        class Simple(Picklable):
            __view__ = object
            def pickle(self):
                return repr(self.__obj__)

        class Seq(Picklable):
            __view__ = list, tuple, dict
            def pickle(self):
                return ';'.join(
                    [Picklable(item).pickle() for item in self.__obj__])

        class Dict(Seq):
            __view__ = dict
            def pickle(self):
                return Seq.pickle(self) + '!' + Seq(self.values()).pickle()

        assert Picklable(123).pickle() == '123'
        assert Picklable([1,[2,3],4]).pickle() == '1;2;3;4'
        assert Picklable({1:2}).pickle() == '1!2'

    def test_viewtype_class_hierarchy(self):
        # Use a custom class hierarchy based on attributes of existing instances
        class Operation:
            "Existing class that I don't want to change."
            def __init__(self, opname, *args):
                self.opname = opname
                self.args = args

        existing = [Operation('+', 4, 5),
                    Operation('getitem', '', 'join'),
                    Operation('setattr', 'x', 'y', 3),
                    Operation('-', 12, 1)]

        class PyOp(self.View):
            def __viewkey__(self):
                return self.opname
            def generate(self):
                return '%s(%s)' % (self.opname, ', '.join(map(repr, self.args)))

        class PyBinaryOp(PyOp):
            __view__ = ('+', '-', '*', '/')
            def generate(self):
                return '%s %s %s' % (self.args[0], self.opname, self.args[1])

        codelines = [PyOp(op).generate() for op in existing]
        assert codelines == ["4 + 5", "getitem('', 'join')", 
            "setattr('x', 'y', 3)", "12 - 1"]

def test_underscore_api():
    py.code._AssertionError
    py.code._reinterpret_old # used by pypy
    py.code._reinterpret
