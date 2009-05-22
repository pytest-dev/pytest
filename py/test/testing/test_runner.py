import py
from py.__.test import runner 
from py.__.code.excinfo import ReprExceptionInfo

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


class BaseFunctionalTests:
    def test_funcattr(self, testdir):
        rep = testdir.runitem("""
            import py
            @py.test.mark(xfail="needs refactoring")
            def test_func():
                raise Exit()
        """)
        assert rep.keywords['xfail'] == "needs refactoring" 

    def test_passfunction(self, testdir):
        rep = testdir.runitem("""
            def test_func():
                pass
        """)
        assert rep.passed 
        assert not rep.failed
        assert rep.shortrepr == "."
        assert not hasattr(rep, 'longrepr')
                
    def test_failfunction(self, testdir):
        rep = testdir.runitem("""
            def test_func():
                assert 0
        """)
        assert not rep.passed 
        assert not rep.skipped 
        assert rep.failed 
        assert rep.when == "runtest"
        assert isinstance(rep.longrepr, ReprExceptionInfo)
        assert str(rep.shortrepr) == "F"

    def test_skipfunction(self, testdir):
        rep = testdir.runitem("""
            import py
            def test_func():
                py.test.skip("hello")
        """)
        assert not rep.failed 
        assert not rep.passed 
        assert rep.skipped 
        #assert rep.skipped.when == "runtest"
        #assert rep.skipped.when == "runtest"
        #assert rep.skipped == "%sreason == "hello"
        #assert rep.skipped.location.lineno == 3
        #assert rep.skipped.location.path
        #assert not rep.skipped.failurerepr 

    def test_skip_in_setup_function(self, testdir):
        rep = testdir.runitem("""
            import py
            def setup_function(func):
                py.test.skip("hello")
            def test_func():
                pass
        """)
        print rep
        assert not rep.failed 
        assert not rep.passed 
        assert rep.skipped 
        #assert rep.skipped.reason == "hello"
        #assert rep.skipped.location.lineno == 3
        #assert rep.skipped.location.lineno == 3

    def test_failure_in_setup_function(self, testdir):
        rep = testdir.runitem("""
            import py
            def setup_function(func):
                raise ValueError(42)
            def test_func():
                pass
        """)
        print rep
        assert not rep.skipped 
        assert not rep.passed 
        assert rep.failed 
        assert rep.when == "setup"

    def test_failure_in_teardown_function(self, testdir):
        rep = testdir.runitem("""
            import py
            def teardown_function(func):
                raise ValueError(42)
            def test_func():
                pass
        """)
        print rep
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
                def repr_failure(self, excinfo, outerr):
                    return "hello" 
        """)
        rep = testdir.runitem("""
            import py
            def test_func():
                assert 0
        """)
        assert not rep.skipped 
        assert not rep.passed 
        assert rep.failed 
        #assert rep.outcome.when == "runtest"
        #assert rep.failed.where.lineno == 3
        #assert rep.failed.where.path.basename == "test_func.py" 
        #assert rep.failed.failurerepr == "hello"

    def test_failure_in_setup_function_ignores_custom_failure_repr(self, testdir):
        testdir.makepyfile(conftest="""
            import py
            class Function(py.test.collect.Function):
                def repr_failure(self, excinfo):
                    assert 0
        """)
        rep = testdir.runitem("""
            import py
            def setup_function(func):
                raise ValueError(42)
            def test_func():
                pass
        """)
        print rep
        assert not rep.skipped 
        assert not rep.passed 
        assert rep.failed 
        #assert rep.outcome.when == "setup"
        #assert rep.outcome.where.lineno == 3
        #assert rep.outcome.where.path.basename == "test_func.py" 
        #assert instanace(rep.failed.failurerepr, PythonFailureRepr)

    def test_capture_in_func(self, testdir):
        rep = testdir.runitem("""
            import py
            def setup_function(func):
                print >>py.std.sys.stderr, "in setup"
            def test_func():
                print "in function"
                assert 0
            def teardown_func(func):
                print "in teardown"
        """)
        assert rep.failed 
        # out, err = rep.failed.outerr
        # assert out == ['in function\nin teardown\n']
        # assert err == ['in setup\n']
        
    def test_systemexit_does_not_bail_out(self, testdir):
        try:
            rep = testdir.runitem("""
                def test_func():
                    raise SystemExit(42)
            """)
        except SystemExit:
            py.test.fail("runner did not catch SystemExit")
        assert rep.failed
        assert rep.when == "runtest"

    def test_exit_propagates(self, testdir):
        from py.__.test.outcome import Exit
        try:
            testdir.runitem("""
                from py.__.test.outcome import Exit
                def test_func():
                    raise Exit()
            """)
        except Exit:
            pass
        else: 
            py.test.fail("did not raise")


class TestExecutionNonForked(BaseFunctionalTests):
    def getrunner(self):
        return runner.basic_run_report 

    def test_keyboardinterrupt_propagates(self, testdir):
        from py.__.test.outcome import Exit
        try:
            testdir.runitem("""
                def test_func():
                    raise KeyboardInterrupt("fake")
            """)
        except KeyboardInterrupt, e:
            pass
        else: 
            py.test.fail("did not raise")

class TestExecutionForked(BaseFunctionalTests): 
    def getrunner(self):
        if not hasattr(py.std.os, 'fork'):
            py.test.skip("no os.fork available")
        return runner.forked_run_report

    def test_suicide(self, testdir):
        rep = testdir.runitem("""
            def test_func():
                import os
                os.kill(os.getpid(), 15)
        """)
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
        rep = runner.basic_collect_report(col)
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
        rep = runner.basic_collect_report(col)
        assert not rep.failed 
        assert not rep.passed 
        assert rep.skipped 


