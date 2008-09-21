"""
collect and run traditional "unittest.py" style tests. 

drop this conftest.py into your project directory so that
all testing directories are below it. 

you can mix unittest TestCase subclasses and 
py.test style tests (discovery based on name). 

user-extensions such as a custom test_suite() 
will not be considered (see XXX). 

$HeadURL: https://codespeak.net/svn/py/trunk/contrib/py_unittest/conftest.py $
$Id: conftest.py 58286 2008-09-21 07:18:39Z hpk $
"""
import py
import unittest
import sys

__version__ = "$Rev: 58286 $".split()[1]

def configproperty(name):
    def fget(self):
        ret = self._config.getvalue(name, self.fspath)
        return ret
    return property(fget)

class Module(py.test.collect.Module):
    UnitTestCase = configproperty('UnitTestCase')
    def makeitem(self, name, obj, usefilters=True):
        # XXX add generic test_suite() support(?)
        if py.std.inspect.isclass(obj) and issubclass(obj, unittest.TestCase):
            return self.UnitTestCase(name, parent=self)
        elif callable(obj) and getattr(obj, 'func_name', '') == 'test_suite':
            return None
        return super(Module, self).makeitem(name, obj, usefilters)

class UnitTestCase(py.test.collect.Class):
    TestCaseInstance = configproperty('TestCaseInstance')
    def collect(self):
        return [self.TestCaseInstance("()", self)]

    def setup(self):
        pass

    def teardown(self):
        pass

_dummy = object()
class TestCaseInstance(py.test.collect.Instance):
    UnitTestFunction = configproperty('UnitTestFunction')
    def collect(self):
        loader = unittest.TestLoader()
        names = loader.getTestCaseNames(self.obj.__class__)
        l = []
        for name in names:
            callobj = getattr(self.obj, name)
            if callable(callobj):
                l.append(self.UnitTestFunction(name, parent=self))
        return l

    def _getobj(self):
        x = self.parent.obj
        return self.parent.obj(methodName='run')
        
class UnitTestFunction(py.test.collect.Function):
    def __init__(self, name, parent, args=(), obj=_dummy, sort_value=None):
        super(UnitTestFunction, self).__init__(name, parent)
        self._args = args
        if obj is not _dummy:
            self._obj = obj
        self._sort_value = sort_value

    def runtest(self):
        target = self.obj
        args = self._args
        target(*args)

    def setup(self):
        instance = self.obj.im_self
        instance.setUp()

    def teardown(self):
        instance = self.obj.im_self
        instance.tearDown()

