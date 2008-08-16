import py
from py.__.test.testing.suptest import InlineCollection
from py.__.test.runner import basic_run_report, forked_run_report, basic_collect_report
from py.__.test.runner import RobustRun
from py.__.code.excinfo import ReprExceptionInfo

class BaseTests(InlineCollection):
    def test_passfunction(self):
        ev = self.runitem("""
            def test_func():
                pass
        """)
        assert ev.passed 
        assert not ev.failed
        assert ev.outcome.shortrepr == "."
        assert not ev.outcome.longrepr
                
    def test_failfunction(self):
        ev = self.runitem("""
            def test_func():
                assert 0
        """)
        assert not ev.passed 
        assert not ev.skipped 
        assert ev.failed 
        assert ev.outcome.when == "execute"
        assert isinstance(ev.outcome.longrepr, ReprExceptionInfo)
        assert str(ev.outcome.shortrepr) == "F"

    def test_skipfunction(self):
        ev = self.runitem("""
            import py
            def test_func():
                py.test.skip("hello")
        """)
        assert not ev.failed 
        assert not ev.passed 
        assert ev.skipped 
        #assert ev.skipped.when == "execute"
        #assert ev.skipped.when == "execute"
        #assert ev.skipped == "%sreason == "hello"
        #assert ev.skipped.location.lineno == 3
        #assert ev.skipped.location.path
        #assert not ev.skipped.failurerepr 

    def test_skip_in_setup_function(self):
        ev = self.runitem("""
            import py
            def setup_function(func):
                py.test.skip("hello")
            def test_func():
                pass
        """)
        print ev
        assert not ev.failed 
        assert not ev.passed 
        assert ev.skipped 
        #assert ev.skipped.reason == "hello"
        #assert ev.skipped.location.lineno == 3
        #assert ev.skipped.location.lineno == 3

    def test_failure_in_setup_function(self):
        ev = self.runitem("""
            import py
            def setup_function(func):
                raise ValueError(42)
            def test_func():
                pass
        """)
        print ev
        assert not ev.skipped 
        assert not ev.passed 
        assert ev.failed 
        assert ev.outcome.when == "setup"

    def test_failure_in_teardown_function(self):
        ev = self.runitem("""
            import py
            def teardown_function(func):
                raise ValueError(42)
            def test_func():
                pass
        """)
        print ev
        assert not ev.skipped 
        assert not ev.passed 
        assert ev.failed 
        #assert ev.outcome.when == "teardown" 
        #assert ev.outcome.where.lineno == 3
        #assert ev.outcome.entries 

    def test_custom_failure_repr(self):
        self.makepyfile(conftest="""
            import py
            class Function(py.test.collect.Function):
                def repr_failure(self, excinfo, outerr):
                    return "hello" 
        """)
        ev = self.runitem("""
            import py
            def test_func():
                assert 0
        """)
        assert not ev.skipped 
        assert not ev.passed 
        assert ev.failed 
        #assert ev.outcome.when == "execute"
        #assert ev.failed.where.lineno == 3
        #assert ev.failed.where.path.basename == "test_func.py" 
        #assert ev.failed.failurerepr == "hello"

    def test_failure_in_setup_function_ignores_custom_failure_repr(self):
        self.makepyfile(conftest="""
            import py
            class Function(py.test.collect.Function):
                def repr_failure(self, excinfo):
                    assert 0
        """)
        ev = self.runitem("""
            import py
            def setup_function(func):
                raise ValueError(42)
            def test_func():
                pass
        """)
        print ev
        assert not ev.skipped 
        assert not ev.passed 
        assert ev.failed 
        #assert ev.outcome.when == "setup"
        #assert ev.outcome.where.lineno == 3
        #assert ev.outcome.where.path.basename == "test_func.py" 
        #assert instanace(ev.failed.failurerepr, PythonFailureRepr)

    def test_capture_in_func(self):
        ev = self.runitem("""
            import py
            def setup_function(func):
                print >>py.std.sys.stderr, "in setup"
            def test_func():
                print "in function"
                assert 0
            def teardown_func(func):
                print "in teardown"
        """)
        assert ev.failed 
        # out, err = ev.failed.outerr
        # assert out == ['in function\nin teardown\n']
        # assert err == ['in setup\n']
        
    def test_systemexit_does_not_bail_out(self):
        try:
            ev = self.runitem("""
                def test_func():
                    raise SystemExit(42)
            """)
        except SystemExit:
            py.test.fail("runner did not catch SystemExit")
        assert ev.failed
        assert ev.outcome.when == "execute"

    def test_exit_propagates(self):
        from py.__.test.outcome import Exit
        try:
            self.runitem("""
                from py.__.test.outcome import Exit
                def test_func():
                    raise Exit()
            """)
        except Exit:
            pass
        else: 
            py.test.fail("did not raise")

class TestExecutionNonForked(BaseTests):
    def getrunner(self):
        return basic_run_report 

    def test_keyboardinterrupt_propagates(self):
        from py.__.test.outcome import Exit
        try:
            self.runitem("""
                def test_func():
                    raise KeyboardInterrupt("fake")
            """)
        except KeyboardInterrupt, e:
            pass
        else: 
            py.test.fail("did not raise")

    def test_pdb_on_fail(self):
        l = []
        ev = self.runitem("""
            def test_func():
                assert 0
        """, pdb=l.append)
        assert ev.failed
        assert ev.outcome.when == "execute"
        assert len(l) == 1

    def test_pdb_on_skip(self):
        l = []
        ev = self.runitem("""
            import py
            def test_func():
                py.test.skip("hello")
        """, pdb=l.append)
        assert len(l) == 0
        assert ev.skipped 

class TestExecutionForked(BaseTests): 
    def getrunner(self):
        if not hasattr(py.std.os, 'fork'):
            py.test.skip("no os.fork available")
        return forked_run_report

    def test_suicide(self):
        ev = self.runitem("""
            def test_func():
                import os
                os.kill(os.getpid(), 15)
        """)
        assert ev.failed
        assert ev.outcome.when == "???"

class TestCollectionEvent(InlineCollection):
    def test_collect_result(self):
        col = self.getmodulecol("""
            def test_func1():
                pass
            class TestClass:
                pass
        """)
        ev = basic_collect_report(col)
        assert not ev.failed
        assert not ev.skipped
        assert ev.passed 
        res = ev.result 
        assert len(res) == 2
        assert res[0].name == "test_func1" 
        assert res[1].name == "TestClass" 

    def test_skip_at_module_scope(self):
        col = self.getmodulecol("""
            import py
            py.test.skip("hello")
            def test_func():
                pass
        """)
        ev = basic_collect_report(col)
        assert not ev.failed 
        assert not ev.passed 
        assert ev.skipped 


class TestRunnerRepr(InlineCollection):
    def test_runner_repr(self):
        item = self.getitem("def test_func(): pass")
        robustrun = RobustRun(item)
        r = repr(robustrun)
        assert r
        assert r.find(item.name) != -1
