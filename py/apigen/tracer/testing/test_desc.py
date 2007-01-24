
""" Some additional tests about descriptions
"""

from py.__.apigen.tracer.description import *

class A:
    pass

class B(object):
    def __init__(self):
        pass

class C(object):
    pass

class D:
    def __init__(self):
        pass

def test_getcode():
    assert hash(ClassDesc("a", A).code)
    assert hash(ClassDesc("b", B).code)
    assert hash(ClassDesc("c", C).code)
    assert hash(ClassDesc("d", D).code)

def test_eq():
    assert ClassDesc('a', A) == ClassDesc('a', A)
