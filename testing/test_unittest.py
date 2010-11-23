import pytest

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
    reprec = testdir.inline_run(testpath)
    assert reprec.matchreport("testpassing").passed
    assert reprec.matchreport("test_failing").failed

def test_isclasscheck_issue53(testdir):
    testpath = testdir.makepyfile("""
        import unittest
        class _E(object):
            def __getattr__(self, tag):
                pass
        E = _E()
    """)
    result = testdir.runpytest(testpath)
    assert result.ret == 0

def test_setup(testdir):
    testpath = testdir.makepyfile(test_two="""
        import unittest
        class MyTestCase(unittest.TestCase):
            def setUp(self):
                self.foo = 1
            def test_setUp(self):
                self.assertEquals(1, self.foo)
    """)
    reprec = testdir.inline_run(testpath)
    rep = reprec.matchreport("test_setUp")
    assert rep.passed

def test_new_instances(testdir):
    testpath = testdir.makepyfile("""
        import unittest
        class MyTestCase(unittest.TestCase):
            def test_func1(self):
                self.x = 2
            def test_func2(self):
                assert not hasattr(self, 'x')
    """)
    reprec = testdir.inline_run(testpath)
    reprec.assertoutcome(passed=2)

def test_teardown(testdir):
    testpath = testdir.makepyfile("""
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
    reprec = testdir.inline_run(testpath)
    passed, skipped, failed = reprec.countoutcomes()
    assert failed == 0, failed
    assert passed == 2
    assert passed + skipped + failed == 2

def test_module_level_pytestmark(testdir):
    testpath = testdir.makepyfile("""
        import unittest
        import pytest
        pytestmark = pytest.mark.xfail
        class MyTestCase(unittest.TestCase):
            def test_func1(self):
                assert 0
    """)
    reprec = testdir.inline_run(testpath, "-s")
    reprec.assertoutcome(skipped=1)

def test_class_setup(testdir):
    testpath = testdir.makepyfile("""
        import unittest
        import pytest
        class MyTestCase(unittest.TestCase):
            x = 0
            @classmethod
            def setUpClass(cls):
                cls.x += 1
            def test_func1(self):
                assert self.x == 1
            def test_func2(self):
                assert self.x == 1
            @classmethod
            def tearDownClass(cls):
                cls.x -= 1
        def test_teareddown():
            assert MyTestCase.x == 0
    """)
    reprec = testdir.inline_run(testpath)
    reprec.assertoutcome(passed=3)


@pytest.mark.multi(type=['Error', 'Failure'])
def test_testcase_adderrorandfailure_defers(testdir, type):
    testdir.makepyfile("""
        from unittest import TestCase
        import pytest
        class MyTestCase(TestCase):
            def run(self, result):
                excinfo = pytest.raises(ZeroDivisionError, lambda: 0/0)
                try:
                    result.add%s(self, excinfo._excinfo)
                except KeyboardInterrupt:
                    raise
                except:
                    pytest.fail("add%s should not raise")
            def test_hello(self):
                pass
    """ % (type, type))
    result = testdir.runpytest()
    assert 'should not raise' not in result.stdout.str()

@pytest.mark.multi(type=['Error', 'Failure'])
def test_testcase_custom_exception_info(testdir, type):
    testdir.makepyfile("""
        from unittest import TestCase
        import py, pytest
        class MyTestCase(TestCase):
            def run(self, result):
                excinfo = pytest.raises(ZeroDivisionError, lambda: 0/0)
                # we fake an incompatible exception info
                from _pytest.monkeypatch import monkeypatch
                mp = monkeypatch()
                def t(*args):
                    mp.undo()
                    raise TypeError()
                mp.setattr(py.code, 'ExceptionInfo', t)
                try:
                    excinfo = excinfo._excinfo
                    result.add%(type)s(self, excinfo)
                finally:
                    mp.undo()
            def test_hello(self):
                pass
    """ % locals())
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
        "NOTE: Incompatible Exception Representation*",
        "*ZeroDivisionError*",
        "*1 failed*",
    ])

def test_testcase_totally_incompatible_exception_info(testdir):
    item, = testdir.getitems("""
        from unittest import TestCase
        class MyTestCase(TestCase):
            def test_hello(self):
                pass
    """)
    item.addError(None, 42)
    excinfo = item._excinfo
    assert 'ERROR: Unknown Incompatible' in str(excinfo.getrepr())
