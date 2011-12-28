""" discovery and running of std-library "unittest" style tests. """
import pytest, py
import sys, pdb

# for transfering markers
from _pytest.python import transfer_markers

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
        module = self.getparent(pytest.Module).obj
        cls = self.obj
        for name in loader.getTestCaseNames(self.obj):
            x = getattr(self.obj, name)
            funcobj = getattr(x, 'im_func', x)
            transfer_markers(funcobj, cls, module)
            if hasattr(funcobj, 'todo'):
                pytest.mark.xfail(reason=str(funcobj.todo))(funcobj)
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
        self._testcase = self.parent.obj(self.name)
        self._obj = getattr(self._testcase, self.name)
        if hasattr(self._testcase, 'skip'):
            pytest.skip(self._testcase.skip)
        if hasattr(self._obj, 'skip'):
            pytest.skip(self._obj.skip)
        if hasattr(self._testcase, 'setup_method'):
            self._testcase.setup_method(self._obj)

    def teardown(self):
        if hasattr(self._testcase, 'teardown_method'):
            self._testcase.teardown_method(self._obj)

    def startTest(self, testcase):
        pass

    def _addexcinfo(self, rawexcinfo):
        # unwrap potential exception info (see twisted trial support below)
        rawexcinfo = getattr(rawexcinfo, '_rawexcinfo', rawexcinfo)
        try:
            excinfo = py.code.ExceptionInfo(rawexcinfo)
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
            except KeyboardInterrupt:
                raise
            except pytest.fail.Exception:
                excinfo = py.code.ExceptionInfo()
        self.__dict__.setdefault('_excinfo', []).append(excinfo)

    def addError(self, testcase, rawexcinfo):
        self._addexcinfo(rawexcinfo)
    def addFailure(self, testcase, rawexcinfo):
        self._addexcinfo(rawexcinfo)
    def addSkip(self, testcase, reason):
        try:
            pytest.skip(reason)
        except pytest.skip.Exception:
            self._addexcinfo(sys.exc_info())
    def addExpectedFailure(self, testcase, rawexcinfo, reason):
        try:
            pytest.xfail(str(reason))
        except pytest.xfail.Exception:
            self._addexcinfo(sys.exc_info())
    def addUnexpectedSuccess(self, testcase, reason):
        pass
    def addSuccess(self, testcase):
        pass
    def stopTest(self, testcase):
        pass
    def runtest(self):
        self._testcase(result=self)

    def _prunetraceback(self, excinfo):
        pytest.Function._prunetraceback(self, excinfo)
        traceback = excinfo.traceback.filter(
            lambda x:not x.frame.f_globals.get('__unittest'))
        if traceback:
            excinfo.traceback = traceback

@pytest.mark.tryfirst
def pytest_runtest_makereport(item, call):
    if isinstance(item, TestCaseFunction):
        if item._excinfo:
            call.excinfo = item._excinfo.pop(0)
            del call.result

# twisted trial support
def pytest_runtest_protocol(item, __multicall__):
    if isinstance(item, TestCaseFunction):
        if 'twisted.trial.unittest' in sys.modules:
            ut = sys.modules['twisted.python.failure']
            Failure__init__ = ut.Failure.__init__.im_func
            check_testcase_implements_trial_reporter()
            def excstore(self, exc_value=None, exc_type=None, exc_tb=None,
                captureVars=None):
                if exc_value is None:
                    self._rawexcinfo = sys.exc_info()
                else:
                    if exc_type is None:
                        exc_type = type(exc_value)
                    self._rawexcinfo = (exc_type, exc_value, exc_tb)
                try:
                    Failure__init__(self, exc_value, exc_type, exc_tb,
                        captureVars=captureVars)
                except TypeError:
                    Failure__init__(self, exc_value, exc_type, exc_tb)
            ut.Failure.__init__ = excstore
            try:
                return __multicall__.execute()
            finally:
                ut.Failure.__init__ = Failure__init__

def check_testcase_implements_trial_reporter(done=[]):
    if done:
        return
    from zope.interface import classImplements
    from twisted.trial.itrial import IReporter
    classImplements(TestCaseFunction, IReporter)
    done.append(1)
