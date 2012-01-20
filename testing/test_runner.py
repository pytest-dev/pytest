import pytest, py, sys, os
from _pytest import runner
from py._code.code import ReprExceptionInfo

class TestSetupState:
    def test_setup(self, testdir):
        ss = runner.SetupState()
        item = testdir.getitem("def test_func(): pass")
        l = [1]
        ss.prepare(item)
        ss.addfinalizer(l.pop, colitem=item)
        assert l
        ss._pop_and_teardown()
        assert not l

    def test_setup_scope_None(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        ss = runner.SetupState()
        l = [1]
        ss.prepare(item)
        ss.addfinalizer(l.pop, colitem=None)
        assert l
        ss._pop_and_teardown()
        assert l
        ss._pop_and_teardown()
        assert l
        ss.teardown_all()
        assert not l

    def test_teardown_exact_stack_empty(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        ss = runner.SetupState()
        ss.teardown_exact(item, None)
        ss.teardown_exact(item, None)
        ss.teardown_exact(item, None)

    def test_setup_fails_and_failure_is_cached(self, testdir):
        item = testdir.getitem("""
            def setup_module(mod):
                raise ValueError(42)
            def test_func(): pass
        """)
        ss = runner.SetupState()
        pytest.raises(ValueError, "ss.prepare(item)")
        pytest.raises(ValueError, "ss.prepare(item)")

class BaseFunctionalTests:
    def test_passfunction(self, testdir):
        reports = testdir.runitem("""
            def test_func():
                pass
        """)
        rep = reports[1]
        assert rep.passed
        assert not rep.failed
        assert rep.outcome == "passed"
        assert not rep.longrepr

    def test_failfunction(self, testdir):
        reports = testdir.runitem("""
            def test_func():
                assert 0
        """)
        rep = reports[1]
        assert not rep.passed
        assert not rep.skipped
        assert rep.failed
        assert rep.when == "call"
        assert rep.outcome == "failed"
        #assert isinstance(rep.longrepr, ReprExceptionInfo)

    def test_skipfunction(self, testdir):
        reports = testdir.runitem("""
            import pytest
            def test_func():
                pytest.skip("hello")
        """)
        rep = reports[1]
        assert not rep.failed
        assert not rep.passed
        assert rep.skipped
        assert rep.outcome == "skipped"
        #assert rep.skipped.when == "call"
        #assert rep.skipped.when == "call"
        #assert rep.skipped == "%sreason == "hello"
        #assert rep.skipped.location.lineno == 3
        #assert rep.skipped.location.path
        #assert not rep.skipped.failurerepr

    def test_skip_in_setup_function(self, testdir):
        reports = testdir.runitem("""
            import pytest
            def setup_function(func):
                pytest.skip("hello")
            def test_func():
                pass
        """)
        print(reports)
        rep = reports[0]
        assert not rep.failed
        assert not rep.passed
        assert rep.skipped
        #assert rep.skipped.reason == "hello"
        #assert rep.skipped.location.lineno == 3
        #assert rep.skipped.location.lineno == 3
        assert len(reports) == 2
        assert reports[1].passed # teardown

    def test_failure_in_setup_function(self, testdir):
        reports = testdir.runitem("""
            import pytest
            def setup_function(func):
                raise ValueError(42)
            def test_func():
                pass
        """)
        rep = reports[0]
        assert not rep.skipped
        assert not rep.passed
        assert rep.failed
        assert rep.when == "setup"
        assert len(reports) == 2

    def test_failure_in_teardown_function(self, testdir):
        reports = testdir.runitem("""
            import pytest
            def teardown_function(func):
                raise ValueError(42)
            def test_func():
                pass
        """)
        print(reports)
        assert len(reports) == 3
        rep = reports[2]
        assert not rep.skipped
        assert not rep.passed
        assert rep.failed
        assert rep.when == "teardown"
        #assert rep.longrepr.reprcrash.lineno == 3
        #assert rep.longrepr.reprtraceback.reprentries

    def test_custom_failure_repr(self, testdir):
        testdir.makepyfile(conftest="""
            import pytest
            class Function(pytest.Function):
                def repr_failure(self, excinfo):
                    return "hello"
        """)
        reports = testdir.runitem("""
            import pytest
            def test_func():
                assert 0
        """)
        rep = reports[1]
        assert not rep.skipped
        assert not rep.passed
        assert rep.failed
        #assert rep.outcome.when == "call"
        #assert rep.failed.where.lineno == 3
        #assert rep.failed.where.path.basename == "test_func.py"
        #assert rep.failed.failurerepr == "hello"

    def test_teardown_final_returncode(self, testdir):
        rec = testdir.inline_runsource("""
            def test_func():
                pass
            def teardown_function(func):
                raise ValueError(42)
        """)
        assert rec.ret == 1

    def test_exact_teardown_issue90(self, testdir):
        rec = testdir.inline_runsource("""
            import pytest

            class TestClass:
                def test_method(self):
                    pass
                def teardown_class(cls):
                    raise Exception()

            def test_func():
                pass
            def teardown_function(func):
                raise ValueError(42)
        """)
        reps = rec.getreports("pytest_runtest_logreport")
        print (reps)
        for i in range(2):
            assert reps[i].nodeid.endswith("test_method")
            assert reps[i].passed
        assert reps[2].when == "teardown"
        assert reps[2].failed
        assert len(reps) == 6
        for i in range(3,5):
            assert reps[i].nodeid.endswith("test_func")
            assert reps[i].passed
        assert reps[5].when == "teardown"
        assert reps[5].nodeid.endswith("test_func")
        assert reps[5].failed

    def test_failure_in_setup_function_ignores_custom_repr(self, testdir):
        testdir.makepyfile(conftest="""
            import pytest
            class Function(pytest.Function):
                def repr_failure(self, excinfo):
                    assert 0
        """)
        reports = testdir.runitem("""
            def setup_function(func):
                raise ValueError(42)
            def test_func():
                pass
        """)
        assert len(reports) == 2
        rep = reports[0]
        print(rep)
        assert not rep.skipped
        assert not rep.passed
        assert rep.failed
        #assert rep.outcome.when == "setup"
        #assert rep.outcome.where.lineno == 3
        #assert rep.outcome.where.path.basename == "test_func.py"
        #assert instanace(rep.failed.failurerepr, PythonFailureRepr)

    def test_systemexit_does_not_bail_out(self, testdir):
        try:
            reports = testdir.runitem("""
                def test_func():
                    raise SystemExit(42)
            """)
        except SystemExit:
            py.test.fail("runner did not catch SystemExit")
        rep = reports[1]
        assert rep.failed
        assert rep.when == "call"

    def test_exit_propagates(self, testdir):
        try:
            testdir.runitem("""
                import pytest
                def test_func():
                    raise pytest.exit.Exception()
            """)
        except py.test.exit.Exception:
            pass
        else:
            py.test.fail("did not raise")

class TestExecutionNonForked(BaseFunctionalTests):
    def getrunner(self):
        def f(item):
            return runner.runtestprotocol(item, log=False)
        return f

    def test_keyboardinterrupt_propagates(self, testdir):
        try:
            testdir.runitem("""
                def test_func():
                    raise KeyboardInterrupt("fake")
            """)
        except KeyboardInterrupt:
            pass
        else:
            py.test.fail("did not raise")

class TestExecutionForked(BaseFunctionalTests):
    pytestmark = pytest.mark.skipif("not hasattr(os, 'fork')")

    def getrunner(self):
        # XXX re-arrange this test to live in pytest-xdist
        xplugin = py.test.importorskip("xdist.plugin")
        return xplugin.forked_run_report

    def test_suicide(self, testdir):
        reports = testdir.runitem("""
            def test_func():
                import os
                os.kill(os.getpid(), 15)
        """)
        rep = reports[0]
        assert rep.failed
        assert rep.when == "???"

class TestSessionReports:
    def test_collect_result(self, testdir):
        col = testdir.getmodulecol("""
            def test_func1():
                pass
            class TestClass:
                pass
        """)
        rep = runner.pytest_make_collect_report(col)
        assert not rep.failed
        assert not rep.skipped
        assert rep.passed
        locinfo = rep.location
        assert locinfo[0] == col.fspath.basename
        assert not locinfo[1]
        assert locinfo[2] == col.fspath.basename
        res = rep.result
        assert len(res) == 2
        assert res[0].name == "test_func1"
        assert res[1].name == "TestClass"

    def test_skip_at_module_scope(self, testdir):
        col = testdir.getmodulecol("""
            import pytest
            pytest.skip("hello")
            def test_func():
                pass
        """)
        rep = runner.pytest_make_collect_report(col)
        assert not rep.failed
        assert not rep.passed
        assert rep.skipped


reporttypes = [
    runner.BaseReport,
    runner.TestReport,
    runner.TeardownErrorReport,
    runner.CollectReport,
]

@pytest.mark.parametrize('reporttype', reporttypes, ids=[x.__name__ for x in reporttypes])
def test_report_extra_parameters(reporttype):
    args = py.std.inspect.getargspec(reporttype.__init__)[0][1:]
    basekw = dict.fromkeys(args, [])
    report = reporttype(newthing=1, **basekw)
    assert report.newthing == 1

def test_callinfo():
    ci = runner.CallInfo(lambda: 0, '123')
    assert ci.when == "123"
    assert ci.result == 0
    assert "result" in repr(ci)
    ci = runner.CallInfo(lambda: 0/0, '123')
    assert ci.when == "123"
    assert not hasattr(ci, 'result')
    assert ci.excinfo
    assert "exc" in repr(ci)

# design question: do we want general hooks in python files?
# then something like the following functional tests makes sense
@pytest.mark.xfail
def test_runtest_in_module_ordering(testdir):
    p1 = testdir.makepyfile("""
        def pytest_runtest_setup(item): # runs after class-level!
            item.function.mylist.append("module")
        class TestClass:
            def pytest_runtest_setup(self, item):
                assert not hasattr(item.function, 'mylist')
                item.function.mylist = ['class']
            def pytest_funcarg__mylist(self, request):
                return request.function.mylist
            def pytest_runtest_call(self, item, __multicall__):
                try:
                    __multicall__.execute()
                except ValueError:
                    pass
            def test_hello1(self, mylist):
                assert mylist == ['class', 'module'], mylist
                raise ValueError()
            def test_hello2(self, mylist):
                assert mylist == ['class', 'module'], mylist
        def pytest_runtest_teardown(item):
            del item.function.mylist
    """)
    result = testdir.runpytest(p1)
    result.stdout.fnmatch_lines([
        "*2 passed*"
    ])


def test_pytest_exit():
    try:
        py.test.exit("hello")
    except py.test.exit.Exception:
        excinfo = py.code.ExceptionInfo()
        assert excinfo.errisinstance(KeyboardInterrupt)

def test_pytest_fail():
    try:
        py.test.fail("hello")
    except py.test.fail.Exception:
        excinfo = py.code.ExceptionInfo()
        s = excinfo.exconly(tryshort=True)
        assert s.startswith("Failed")

def test_pytest_fail_notrace(testdir):
    testdir.makepyfile("""
        import pytest
        def test_hello():
            pytest.fail("hello", pytrace=False)
        def teardown_function(function):
            pytest.fail("world", pytrace=False)
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
        "world",
        "hello",
    ])
    assert 'def teardown_function' not in result.stdout.str()

def test_exception_printing_skip():
    try:
        pytest.skip("hello")
    except pytest.skip.Exception:
        excinfo = py.code.ExceptionInfo()
        s = excinfo.exconly(tryshort=True)
        assert s.startswith("Skipped")

def test_importorskip():
    importorskip = py.test.importorskip
    def f():
        importorskip("asdlkj")
    try:
        sys = importorskip("sys")
        assert sys == py.std.sys
        #path = py.test.importorskip("os.path")
        #assert path == py.std.os.path
        excinfo = pytest.raises(pytest.skip.Exception, f)
        path = py.path.local(excinfo.getrepr().reprcrash.path)
        # check that importorskip reports the actual call
        # in this test the test_runner.py file
        assert path.purebasename == "test_runner"
        pytest.raises(SyntaxError, "py.test.importorskip('x y z')")
        pytest.raises(SyntaxError, "py.test.importorskip('x=y')")
        path = importorskip("py", minversion=".".join(py.__version__))
        mod = py.std.types.ModuleType("hello123")
        mod.__version__ = "1.3"
        pytest.raises(pytest.skip.Exception, """
            py.test.importorskip("hello123", minversion="5.0")
        """)
    except pytest.skip.Exception:
        print(py.code.ExceptionInfo())
        py.test.fail("spurious skip")

def test_importorskip_imports_last_module_part():
    ospath = py.test.importorskip("os.path")
    assert os.path == ospath


def test_pytest_cmdline_main(testdir):
    p = testdir.makepyfile("""
        import py
        def test_hello():
            assert 1
        if __name__ == '__main__':
           py.test.cmdline.main([__file__])
    """)
    import subprocess
    popen = subprocess.Popen([sys.executable, str(p)], stdout=subprocess.PIPE)
    s = popen.stdout.read()
    ret = popen.wait()
    assert ret == 0

