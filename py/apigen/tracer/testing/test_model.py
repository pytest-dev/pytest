
""" test_model - our (very simple) type system
model tests
"""

from py.__.apigen.tracer.model import *

import types
import py

def check_guess(val, t):
    assert isinstance(guess_type(val), t)

def test_basic():
    """ This tests checks every object that we might want
    to track
    """
    check_guess(3, SomeInt)
    check_guess(3., SomeFloat)
    check_guess(True, SomeBoolean)
    check_guess(lambda x: None, SomeFunction)

    class A:
        pass

    check_guess(A, SomeClass)
    check_guess(A(), SomeInstance)

    class B(object):
        def meth(self):
            pass
    
    class C(object):
        def __call__(self):
            pass

    check_guess(B, SomeClass)
    check_guess(B.meth, SomeFunction)
    check_guess(B(), SomeInstance)
    check_guess(B().meth, SomeMethod)
    check_guess([1], SomeList)
    check_guess(None, SomeNone)
    check_guess((1,), SomeTuple)
    check_guess(C(), SomeInstance)
    import sys
    check_guess(sys, SomeModule)
    check_guess({}, SomeDict)
    check_guess(sys.exc_info, SomeBuiltinFunction)

def test_anyof():
    def check_lst(lst):
        a = guess_type(lst[0])
        for i in lst[1:]:
            a = unionof(a, guess_type(i))
        d = dict([(i, True) for i in a.possibilities])
        assert len(a.possibilities) == len(d)
        for i in a.possibilities:
            assert not isinstance(i, SomeUnion)
        return a
        
    class C(object):
        pass
    
    ret = check_lst([3, 4, 3., "aa"])
    assert len(ret.possibilities) == 3
    ret = check_lst([3, 4, 3.])
    ret2 = check_lst([1, "aa"])
    ret3 = unionof(ret, ret2)
    assert len(ret3.possibilities) == 3
    ret = check_lst([3, 1.])
    ret = unionof(ret, guess_type("aa"))
    ret = unionof(guess_type("aa"), ret)
    ret = unionof(guess_type(C()), ret)
    ret = unionof(ret, guess_type("aa"))
    ret = unionof(ret, guess_type(C()))
    assert len(ret.possibilities) == 4

def test_union():
    class A(object):
        pass
    
    class B(object):
        pass
    
    f = guess_type(A).unionof(guess_type(A))
    assert isinstance(f, SomeClass)
    assert f.cls is A
    f = guess_type(A).unionof(guess_type(B)).unionof(guess_type(A))
    assert isinstance(f, SomeUnion)
    assert len(f.possibilities) == 2
    f = guess_type(A()).unionof(guess_type(A()))
    assert isinstance(f, SomeInstance)
    assert isinstance(f.classdef, SomeClass)
    assert f.classdef.cls is A
    f = guess_type(B()).unionof(guess_type(A())).unionof(guess_type(B()))
    assert isinstance(f, SomeInstance)
    assert isinstance(f.classdef, SomeUnion)
    assert len(f.classdef.possibilities) == 2
    
def test_striter():
    class A(object):
        pass
    
    class B(object):
        pass
    
    g = guess_type(A).unionof(guess_type(A()))
    l = py.builtin.sorted(list(g.striter()))
    assert l[4] == "AnyOf("
    assert isinstance(l[0], SomeClass)
    assert l[3] == ", "
    assert isinstance(l[1], SomeInstance)
