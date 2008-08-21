import py

def setup_module(mod):
    py.magic.invoke(assertion=1)

def teardown_module(mod):
    py.magic.revoke(assertion=1)

def f():
    return 2

def test_assert():
    try:
        assert f() == 3
    except AssertionError, e:
        s = str(e)
        assert s.startswith('assert 2 == 3\n')

def test_assert_with_explicit_message():
    try:
        assert f() == 3, "hello"
    except AssertionError, e:
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
    except AssertionError, e:
        s = str(e)
        assert s.startswith('assert 2 == 3\n')

def test_assert_multiline_2():
    try:
        assert (f() == (4,
                   3)[-1])
    except AssertionError, e:
        s = str(e)
        assert s.startswith('assert 2 ==')

def test_assert_non_string_message(): 
    class A: 
        def __str__(self): 
            return "hello"
    try:
        assert 0 == 1, A()
    except AssertionError, e: 
        assert e.msg == "hello"


# These tests should both fail, but should fail nicely...
class WeirdRepr:
    def __repr__(self):
        return '<WeirdRepr\nsecond line>'
            
def bug_test_assert_repr():
    v = WeirdRepr()
    try: 
        assert v == 1
    except AssertionError, e: 
        assert e.msg.find('WeirdRepr') != -1
        assert e.msg.find('second line') != -1
        assert 0
        
def test_assert_non_string():
    try: 
        assert 0, ['list']
    except AssertionError, e: 
        assert e.msg.find("list") != -1 

def test_assert_implicit_multiline():
    try:
        x = [1,2,3]
        assert x != [1,
           2, 3]
    except AssertionError, e:
        assert e.msg.find('assert [1, 2, 3] !=') != -1


def test_assert_with_brokenrepr_arg():
    class BrokenRepr:
        def __repr__(self): 0 / 0
    e = AssertionError(BrokenRepr())
    if e.msg.find("broken __repr__") == -1:
        py.test.fail("broken __repr__ not handle correctly")

