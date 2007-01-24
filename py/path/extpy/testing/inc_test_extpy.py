from __future__ import generators

class A:
    x1 = 42
    def func(self):
        pass

    def genfunc(self):
        yield 2

class B:
    x2 = 23

class Nested:
    class Class:
        def borgfunc(self): pass


