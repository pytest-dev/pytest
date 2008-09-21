import py
from py.__.test.outcome import Failed
from py.__.test.testing import suptest
conftestpath = py.magic.autopath().dirpath("conftest.py")

def test_version():
    mod = conftestpath.pyimport()
    assert hasattr(mod, "__version__")

class TestTestCaseInstance(suptest.InlineSession):
    def setup_method(self, method):
        super(TestTestCaseInstance, self).setup_method(method)
        self.tmpdir.ensure("__init__.py")
        conftestpath.copy(self.tmpdir.join(conftestpath.basename))
         
    def test_simple_unittest(self):
        test_one = self.makepyfile(test_one="""
            import unittest
            class MyTestCase(unittest.TestCase):
                def testpassing(self):
                    self.assertEquals('foo', 'foo')
        """)
        sorter = self.parse_and_run(test_one)
        rep = sorter.getreport("testpassing")
        assert rep.passed

    def test_simple_failing(self):
        test_one = self.makepyfile(test_one="""
            import unittest
            class MyTestCase(unittest.TestCase):
                def test_failing(self):
                    self.assertEquals('foo', 'bar')
        """)
        sorter = self.parse_and_run(test_one)
        rep = sorter.getreport("test_failing")
        assert rep.failed

    def test_setup(self):
        test_one = self.makepyfile(test_one="""
            import unittest
            class MyTestCase(unittest.TestCase):
                def setUp(self):
                    self.foo = 1
                def test_setUp(self):
                    self.assertEquals(1, self.foo)
        """)
        sorter = self.parse_and_run(test_one)
        rep = sorter.getreport("test_setUp")
        assert rep.passed

    def test_teardown(self):
        test_one = self.makepyfile(test_one="""
            import unittest
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
        sorter = self.parse_and_run(test_one)
        passed, skipped, failed = sorter.countoutcomes()
        assert passed + skipped + failed == 2
        assert failed == 0, failed
        assert passed == 2
