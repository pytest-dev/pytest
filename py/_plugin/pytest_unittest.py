"""
automatically discover and run traditional "unittest.py" style tests. 

Usage
----------------

This plugin collects and runs Python `unittest.py style`_ tests. 
It will automatically collect ``unittest.TestCase`` subclasses 
and their ``test`` methods from the test modules of a project
(usually following the ``test_*.py`` pattern). 

This plugin is enabled by default. 

.. _`unittest.py style`: http://docs.python.org/library/unittest.html
"""
import py
import sys

def pytest_pycollect_makeitem(collector, name, obj):
    if 'unittest' not in sys.modules:
        return # nobody derived unittest.TestCase
    try:
        isunit = issubclass(obj, py.std.unittest.TestCase)
    except KeyboardInterrupt:
        raise
    except Exception:
        pass
    else:
        if isunit:
            return UnitTestCase(name, parent=collector)

class UnitTestCase(py.test.collect.Class):
    def collect(self):
        return [UnitTestCaseInstance("()", self)]

    def setup(self):
        pass

    def teardown(self):
        pass

_dummy = object()
class UnitTestCaseInstance(py.test.collect.Instance):
    def collect(self):
        loader = py.std.unittest.TestLoader()
        names = loader.getTestCaseNames(self.obj.__class__)
        l = []
        for name in names:
            callobj = getattr(self.obj, name)
            if py.builtin.callable(callobj):
                l.append(UnitTestFunction(name, parent=self))
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
        if hasattr(self.parent, 'newinstance'):
            self.parent.newinstance()
            self.obj = self._getobj()

    def runtest(self):
        target = self.obj
        args = self._args
        target(*args)

    def setup(self):
        instance = py.builtin._getimself(self.obj)
        instance.setUp()

    def teardown(self):
        instance = py.builtin._getimself(self.obj)
        instance.tearDown()

