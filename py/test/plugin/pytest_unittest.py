"""
automatically collect and run traditional "unittest.py" style tests. 

you can mix unittest TestCase subclasses and 
py.test style tests in one test module. 

XXX consider user-specified test_suite() 

this code is somewhat derived from Guido Wesdorps 

    http://johnnydebris.net/svn/projects/py_unittest

$HeadURL: https://codespeak.net/svn/py/branch/pytestplugin/contrib/py_unittest/conftest.py $
$Id: conftest.py 60979 2009-01-14 22:29:32Z hpk $
"""
import py

class UnittestPlugin:
    """ discover and integrate traditional ``unittest.py`` tests. 
    """
    def pytest_pymodule_makeitem(self, modcol, name, obj):
        if py.std.inspect.isclass(obj) and issubclass(obj, py.std.unittest.TestCase):
            return UnitTestCase(name, parent=modcol)

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
            if callable(callobj):
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


def test_generic(plugintester):
    plugintester.apicheck(UnittestPlugin)

def test_simple_unittest(testdir):
    testpath = testdir.makepyfile("""
        import unittest
        pytest_plugins = "pytest_unittest"
        class MyTestCase(unittest.TestCase):
            def testpassing(self):
                self.assertEquals('foo', 'foo')
            def test_failing(self):
                self.assertEquals('foo', 'bar')
    """)
    sorter = testdir.inline_run(testpath)
    assert sorter.matchreport("testpassing").passed
    assert sorter.matchreport("test_failing").failed 

def test_setup(testdir):
    testpath = testdir.makepyfile(test_two="""
        import unittest
        pytest_plugins = "pytest_unittest" # XXX 
        class MyTestCase(unittest.TestCase):
            def setUp(self):
                self.foo = 1
            def test_setUp(self):
                self.assertEquals(1, self.foo)
    """)
    sorter = testdir.inline_run(testpath)
    rep = sorter.matchreport("test_setUp")
    assert rep.passed

def test_teardown(testdir):
    testpath = testdir.makepyfile(test_three="""
        import unittest
        pytest_plugins = "pytest_unittest" # XXX 
        class MyTestCase(unittest.TestCase):
            l = []
            def test_one(self):
                pass
            def tearDown(self):
                self.l.append(None)
        class Second(unittest.TestCase):
            def test_check(self):
                self.assertEquals(MyTestCase.l, [None])
    """)
    sorter = testdir.inline_run(testpath)
    passed, skipped, failed = sorter.countoutcomes()
    print "COUNTS", passed, skipped, failed
    assert failed == 0, failed
    assert passed == 2
    assert passed + skipped + failed == 2

