""" support discovery and running of traditional "unittest.py" style tests. """
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
        loader = py.std.unittest.TestLoader()
        for name in loader.getTestCaseNames(self.obj):
            yield TestCaseFunction(name, parent=self)

    def setup(self):
        meth = getattr(self.obj, 'setUpClass', None)
        if meth is not None:
            meth()

    def teardown(self):
        meth = getattr(self.obj, 'tearDownClass', None)
        if meth is not None:
            meth()

class TestCaseFunction(py.test.collect.Function):
    def startTest(self, testcase):
        pass
    def addError(self, testcase, rawexcinfo):
        py.builtin._reraise(*rawexcinfo)
    def addFailure(self, testcase, rawexcinfo):
        py.builtin._reraise(*rawexcinfo)
    def addSuccess(self, testcase):
        pass
    def stopTest(self, testcase):
        pass
    def runtest(self):
        testcase = self.parent.obj(self.name)
        testcase(result=self)
