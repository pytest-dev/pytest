import pytest, py, sys

class TestOEJSKITSpecials:
    def test_funcarg_non_pycollectobj(self, testdir): # rough jstests usage
        testdir.makeconftest("""
            import pytest
            def pytest_pycollect_makeitem(collector, name, obj):
                if name == "MyClass":
                    return MyCollector(name, parent=collector)
            class MyCollector(pytest.Collector):
                def reportinfo(self):
                    return self.fspath, 3, "xyz"
        """)
        modcol = testdir.getmodulecol("""
            def pytest_funcarg__arg1(request):
                return 42
            class MyClass:
                pass
        """)
        # this hook finds funcarg factories
        rep = modcol.ihook.pytest_make_collect_report(collector=modcol)
        clscol = rep.result[0]
        clscol.obj = lambda arg1: None
        clscol.funcargs = {}
        pytest._fillfuncargs(clscol)
        assert clscol.funcargs['arg1'] == 42

    def test_autouse_fixture(self, testdir): # rough jstests usage
        testdir.makeconftest("""
            import pytest
            def pytest_pycollect_makeitem(collector, name, obj):
                if name == "MyClass":
                    return MyCollector(name, parent=collector)
            class MyCollector(pytest.Collector):
                def reportinfo(self):
                    return self.fspath, 3, "xyz"
        """)
        modcol = testdir.getmodulecol("""
            import pytest
            @pytest.fixture(autouse=True)
            def hello():
                pass
            def pytest_funcarg__arg1(request):
                return 42
            class MyClass:
                pass
        """)
        # this hook finds funcarg factories
        rep = modcol.ihook.pytest_make_collect_report(collector=modcol)
        clscol = rep.result[0]
        clscol.obj = lambda: None
        clscol.funcargs = {}
        pytest._fillfuncargs(clscol)
        assert not clscol.funcargs


class TestMockDecoration:
    def test_wrapped_getfuncargnames(self):
        from _pytest.python import getfuncargnames
        def wrap(f):
            def func():
                pass
            func.__wrapped__ = f
            return func
        @wrap
        def f(x):
            pass
        l = getfuncargnames(f)
        assert l == ("x",)

    def test_wrapped_getfuncargnames_patching(self):
        from _pytest.python import getfuncargnames
        def wrap(f):
            def func():
                pass
            func.__wrapped__ = f
            func.patchings = ["qwe"]
            return func
        @wrap
        def f(x, y, z):
            pass
        l = getfuncargnames(f)
        assert l == ("y", "z")

    def test_unittest_mock(self, testdir):
        pytest.importorskip("unittest.mock")
        testdir.makepyfile("""
            import unittest.mock
            class T(unittest.TestCase):
                @unittest.mock.patch("os.path.abspath")
                def test_hello(self, abspath):
                    import os
                    os.path.abspath("hello")
                    abspath.assert_any_call("hello")
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_mock(self, testdir):
        pytest.importorskip("mock", "1.0.1")
        testdir.makepyfile("""
            import os
            import unittest
            import mock

            class T(unittest.TestCase):
                @mock.patch("os.path.abspath")
                def test_hello(self, abspath):
                    os.path.abspath("hello")
                    abspath.assert_any_call("hello")
            @mock.patch("os.path.abspath")
            @mock.patch("os.path.normpath")
            def test_someting(normpath, abspath, tmpdir):
                abspath.return_value = "this"
                os.path.normpath(os.path.abspath("hello"))
                normpath.assert_any_call("this")
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=2)
