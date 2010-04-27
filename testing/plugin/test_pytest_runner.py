import py
from py._plugin import pytest_runner as runner
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
        ss.teardown_exact(item)
        ss.teardown_exact(item)
        ss.teardown_exact(item)

    def test_setup_fails_and_failure_is_cached(self, testdir):
        item = testdir.getitem("""
            def setup_module(mod):
                raise ValueError(42)
            def test_func(): pass
        """)
        ss = runner.SetupState()
        py.test.raises(ValueError, "ss.prepare(item)")
        py.test.raises(ValueError, "ss.prepare(item)")

class BaseFunctionalTests:
    def test_passfunction(self, testdir):
        reports = testdir.runitem("""
            def test_func():
                pass
        """)
        rep = reports[1]
        assert rep.passed 
        assert not rep.failed
        assert rep.shortrepr == "."
        assert not hasattr(rep, 'longrepr')
                
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
        assert isinstance(rep.longrepr, ReprExceptionInfo)
        assert str(rep.shortrepr) == "F"

    def test_skipfunction(self, testdir):
        reports = testdir.runitem("""
            import py
            def test_func():
                py.test.skip("hello")
        """)
        rep = reports[1]
        assert not rep.failed 
        assert not rep.passed 
        assert rep.skipped 
        #assert rep.skipped.when == "call"
        #assert rep.skipped.when == "call"
        #assert rep.skipped == "%sreason == "hello"
        #assert rep.skipped.location.lineno == 3
        #assert rep.skipped.location.path
        #assert not rep.skipped.failurerepr 

    def test_skip_in_setup_function(self, testdir):
        reports = testdir.runitem("""
            import py
            def setup_function(func):
                py.test.skip("hello")
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
            import py
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
            import py
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
        assert rep.longrepr.reprcrash.lineno == 3
        assert rep.longrepr.reprtraceback.reprentries 

    def test_custom_failure_repr(self, testdir):
        testdir.makepyfile(conftest="""
            import py
            class Function(py.test.collect.Function):
                def repr_failure(self, excinfo):
                    return "hello" 
        """)
        reports = testdir.runitem("""
            import py
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

    def test_failure_in_setup_function_ignores_custom_repr(self, testdir):
        testdir.makepyfile(conftest="""
            import py
            class Function(py.test.collect.Function):
                def repr_failure(self, excinfo):
                    assert 0
        """)
        reports = testdir.runitem("""
            import py
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
                import py
                def test_func():
                    raise py.test.exc.Exit()
            """)
        except py.test.exc.Exit:
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
    pytestmark = py.test.mark.skipif("not hasattr(os, 'fork')")

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

class TestCollectionReports:
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
        res = rep.result 
        assert len(res) == 2
        assert res[0].name == "test_func1" 
        assert res[1].name == "TestClass" 

    def test_skip_at_module_scope(self, testdir):
        col = testdir.getmodulecol("""
            import py
            py.test.skip("hello")
            def test_func():
                pass
        """)
        rep = runner.pytest_make_collect_report(col)
        assert not rep.failed 
        assert not rep.passed 
        assert rep.skipped 

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
# following passes if withpy defaults to True in pycoll.PyObjMix._getplugins()
@py.test.mark.xfail
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
    assert result.stdout.fnmatch_lines([
        "*2 passed*"
    ])
