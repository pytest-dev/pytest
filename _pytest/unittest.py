""" discovery and running of std-library "unittest" style tests. """
import pytest, py
import sys

def pytest_pycollect_makeitem(collector, name, obj):
    unittest = sys.modules.get('unittest')
    if unittest is None:
        return # nobody can have derived unittest.TestCase
    try:
        isunit = issubclass(obj, unittest.TestCase)
    except KeyboardInterrupt:
        raise
    except Exception:
        pass
    else:
        if isunit:
            return UnitTestCase(name, parent=collector)

class UnitTestCase(pytest.Class):
    def collect(self):
        loader = py.std.unittest.TestLoader()
        for name in loader.getTestCaseNames(self.obj):
            yield TestCaseFunction(name, parent=self)

    def setup(self):
        meth = getattr(self.obj, 'setUpClass', None)
        if meth is not None:
            meth()
        super(UnitTestCase, self).setup()

    def teardown(self):
        meth = getattr(self.obj, 'tearDownClass', None)
        if meth is not None:
            meth()
        super(UnitTestCase, self).teardown()

class TestCaseFunction(pytest.Function):
    _excinfo = None
    def setup(self):
        pass
    def teardown(self):
        pass
    def startTest(self, testcase):
        pass

    def _addexcinfo(self, rawexcinfo):
        #__tracebackhide__ = True
        assert rawexcinfo
        try:
            self._excinfo = py.code.ExceptionInfo(rawexcinfo)
        except TypeError:
            try:
                try:
                    l = py.std.traceback.format_exception(*rawexcinfo)
                    l.insert(0, "NOTE: Incompatible Exception Representation, "
                        "displaying natively:\n\n")
                    pytest.fail("".join(l), pytrace=False)
                except (pytest.fail.Exception, KeyboardInterrupt):
                    raise
                except:
                    pytest.fail("ERROR: Unknown Incompatible Exception "
                        "representation:\n%r" %(rawexcinfo,), pytrace=False)
            except pytest.fail.Exception:
                self._excinfo = py.code.ExceptionInfo()
            except KeyboardInterrupt:
                raise

    def addError(self, testcase, rawexcinfo):
        self._addexcinfo(rawexcinfo)
    def addFailure(self, testcase, rawexcinfo):
        self._addexcinfo(rawexcinfo)
    def addSuccess(self, testcase):
        pass
    def stopTest(self, testcase):
        pass
    def runtest(self):
        testcase = self.parent.obj(self.name)
        testcase(result=self)

@pytest.mark.tryfirst
def pytest_runtest_makereport(item, call):
    if isinstance(item, TestCaseFunction):
        if item._excinfo:
            call.excinfo = item._excinfo
            item._excinfo = None
            del call.result
