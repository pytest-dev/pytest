import py
from suptest import assert_lines_contain_lines, FileCreation

pydir = py.path.local(py.__file__).dirpath()
pytestpath = pydir.join("bin", "py.test")
EXPECTTIMEOUT=10.0

def setup_module(mod):
    mod.modtmpdir = py.test.ensuretemp(mod.__name__)

class Result:
    def __init__(self, ret, outlines, errlines):
        self.ret = ret
        self.outlines = outlines
        self.errlines = errlines

class AcceptBase(FileCreation):
    def popen(self, cmdargs, stdout, stderr, **kw):
        if not hasattr(py.std, 'subprocess'):
            py.test.skip("no subprocess module")
        return py.std.subprocess.Popen(cmdargs, stdout=stdout, stderr=stderr, **kw)

    def run(self, *cmdargs):
        cmdargs = map(str, cmdargs)
        p1 = py.path.local("stdout")
        p2 = py.path.local("stderr")
        print "running", cmdargs, "curdir=", py.path.local()
        popen = self.popen(cmdargs, stdout=p1.open("w"), stderr=p2.open("w"))
        ret = popen.wait()
        out, err = p1.readlines(cr=0), p2.readlines(cr=0)
        if err:
            for line in err: 
                print >>py.std.sys.stderr, line
        return Result(ret, out, err)

    def runpybin(self, scriptname, *args):
        bindir = py.path.local(py.__file__).dirpath("bin")
        if py.std.sys.platform == "win32":
            script = bindir.join("win32", scriptname + ".cmd")
        else:
            script = bindir.join(scriptname)
        assert script.check()
        return self.run(script, *args)

    def runpytest(self, *args):
        return self.runpybin("py.test", *args)

    def setup_method(self, method):
        super(AcceptBase, self).setup_method(method)
        self.old = self.tmpdir.chdir()

    def teardown_method(self, method):
        self.old.chdir()

class TestPyTest(AcceptBase):
    def test_assertion_magic(self):
        p = self.makepyfile(test_one="""
            def test_this():
                x = 0
                assert x
        """)
        result = self.runpytest(p)
        extra = assert_lines_contain_lines(result.outlines, [
            ">       assert x", 
            "E       assert 0",
        ])
        assert result.ret == 1
        
   
    def test_collectonly_simple(self):
        p = self.makepyfile(test_one="""
            def test_func1():
                pass
            class TestClass:
                def test_method(self):
                    pass
        """)
        result = self.runpytest("--collectonly", p)
        err = "".join(result.errlines)
        assert err.strip().startswith("inserting into sys.path")
        assert result.ret == 0
        extra = assert_lines_contain_lines(result.outlines, py.code.Source("""
            <Module 'test_one.py'>
              <Function 'test_func1'*>
              <Class 'TestClass'>
                <Instance '()'>
                  <Function 'test_method'*>
        """).strip())

    def test_nested_import_error(self):
        p = self.makepyfile(
            test_one="""
                import import_fails
                def test_this():
                    assert import_fails.a == 1
            """, 
            import_fails="import does_not_work"
        )
        result = self.runpytest(p)
        extra = assert_lines_contain_lines(result.outlines, [
            ">   import import_fails",
            "E   ImportError: No module named does_not_work",
        ])
        assert result.ret == 1

    def test_skipped_reasons(self):
        p1 = self.makepyfile(
            test_one="""
                from conftest import doskip
                def setup_function(func):
                    doskip()
                def test_func():
                    pass
                class TestClass:
                    def test_method(self):
                        doskip()
           """,
           test_two = """
                from conftest import doskip
                doskip()
           """,
           conftest = """
                import py
                def doskip():
                    py.test.skip('test')
            """
        )
        result = self.runpytest() 
        extra = assert_lines_contain_lines(result.outlines, [
            "*test_one.py ss",
            "*test_two.py - Skipped*", 
            "___* skipped test summary *_", 
            "*conftest.py:3: *3* Skipped: 'test'", 
        ])
        assert result.ret == 0

    def test_deselected(self):
        p1 = self.makepyfile(test_one="""
                def test_one():
                    pass
                def test_two():
                    pass
                def test_three():
                    pass
           """,
        )
        result = self.runpytest("-k", "test_two:")
        extra = assert_lines_contain_lines(result.outlines, [
            "*test_one.py ..", 
            "=* 1 test*deselected by 'test_two:'*=", 
        ])
        assert result.ret == 0

    def test_no_skip_summary_if_failure(self):
        p1 = self.makepyfile(test_one="""
            import py
            def test_ok():
                pass
            def test_fail():
                assert 0
            def test_skip():
                py.test.skip("dontshow")
        """)
        result = self.runpytest() 
        assert str(result.outlines).find("skip test summary") == -1
        assert result.ret == 1

    def test_passes(self):
        p1 = self.makepyfile(test_one="""
            def test_passes():
                pass
            class TestClass:
                def test_method(self):
                    pass
        """)
        old = p1.dirpath().chdir()
        try:
            result = self.runpytest()
        finally:
            old.chdir()
        extra = assert_lines_contain_lines(result.outlines, [
            "test_one.py ..", 
            "* failures: no failures*", 
        ])
        assert result.ret == 0

    def test_header_trailer_info(self):
        p1 = self.makepyfile(test_one="""
            def test_passes():
                pass
        """)
        result = self.runpytest()
        verinfo = ".".join(map(str, py.std.sys.version_info[:3]))
        extra = assert_lines_contain_lines(result.outlines, [
            "*===== test session starts ====*",
            "*localhost* %s %s - Python %s*" %(
                    py.std.sys.platform, py.std.sys.executable, verinfo),
            "*test_one.py .",
            "=* 1/1 passed + 0 skips in *.[0-9][0-9] seconds *=", 
            "=* no failures :)*=",
        ])

    def test_traceback_failure(self):
        p1 = self.makepyfile(test_fail="""
            def g():
                return 2
            def f(x):
                assert x == g()
            def test_onefails():
                f(3)
        """)
        result = self.runpytest(p1)
        assert_lines_contain_lines(result.outlines, [
            "*test_fail.py F", 
            "====* FAILURES *====",
            "____*____", 
            "",
            "    def test_onefails():",
            ">       f(3)",
            "",
            "*test_fail.py:6: ",
            "_ _ _ *",
            #"",
            "    def f(x):",
            ">       assert x == g()",
            "E       assert 3 == 2",
            "E        +  where 2 = g()",
            "",
            "*test_fail.py:4: AssertionError"
        ])

    def test_capturing_outerr(self): 
        p1 = self.makepyfile(test_one="""
            import sys 
            def test_capturing():
                print 42
                print >>sys.stderr, 23 
            def test_capturing_error():
                print 1
                print >>sys.stderr, 2
                raise ValueError
        """)
        result = self.runpytest(p1)
        assert_lines_contain_lines(result.outlines, [
            "*test_one.py .F", 
            "====* FAILURES *====",
            "____*____", 
            "*test_one.py:8: ValueError",
            "*--- Captured stdout ---*",
            "1",
            "*--- Captured stderr ---*",
            "2",
        ])

    def test_showlocals(self): 
        p1 = self.makepyfile(test_one="""
            def test_showlocals():
                x = 3
                y = "x" * 5000 
                assert 0
        """)
        result = self.runpytest(p1, '-l')
        assert_lines_contain_lines(result.outlines, [
            #"_ _ * Locals *", 
            "x* = 3",
            "y* = 'xxxxxx*"
        ])

    def test_doctest_simple_failing(self):
        p = self.maketxtfile(doc="""
            >>> i = 0
            >>> i + 1
            2
        """)
        result = self.runpytest(p)
        assert_lines_contain_lines(result.outlines, [
            '001 >>> i = 0',
            '002 >>> i + 1',
            'Expected:',
            "    2",
            "Got:",
            "    1",
            "*doc.txt:2: DocTestFailure"
        ])

    def test_dist_testing(self):
        p1 = self.makepyfile(
            test_one="""
                import py
                def test_fail0():
                    assert 0
                def test_fail1():
                    raise ValueError()
                def test_ok():
                    pass
                def test_skip():
                    py.test.skip("hello")
            """, 
            conftest="""
                dist_hosts = ['localhost'] * 3
            """
        )
        result = self.runpytest(p1, '-d')
        assert_lines_contain_lines(result.outlines, [
            "HOSTUP: localhost*Python*",
            #"HOSTUP: localhost*Python*",
            #"HOSTUP: localhost*Python*",
            "*1/3 passed + 1 skip*",
            "*failures: 2*",
        ])
        assert result.ret == 1

    def test_dist_tests_with_crash(self):
        if not hasattr(py.std.os, 'kill'):
            py.test.skip("no os.kill")
        
        p1 = self.makepyfile(
            test_one="""
                import py
                def test_fail0():
                    assert 0
                def test_fail1():
                    raise ValueError()
                def test_ok():
                    pass
                def test_skip():
                    py.test.skip("hello")
                def test_crash():
                    import time
                    import os
                    time.sleep(0.5)
                    os.kill(os.getpid(), 15)
            """, 
            conftest="""
                dist_hosts = ['localhost'] * 3
            """
        )
        result = self.runpytest(p1, '-d')
        assert_lines_contain_lines(result.outlines, [
            "*localhost*Python*",
            "*localhost*Python*",
            "*localhost*Python*",
            "HostDown*localhost*TERMINATED*",
            "*1/4 passed + 1 skip*",
            "*failures: 3*",
        ])
        assert result.ret == 1

    def test_keyboard_interrupt(self):
        p1 = self.makepyfile(test_one="""
            import py
            def test_fail():
                raise ValueError()
            def test_inter():
                raise KeyboardInterrupt()
        """)
        result = self.runpytest(p1)
        assert_lines_contain_lines(result.outlines, [
            #"*test_inter() INTERRUPTED",
            "*KEYBOARD INTERRUPT*",
            "*0/1 passed*",
        ])

    def test_verbose_reporting(self):
        p1 = self.makepyfile(test_one="""
            import py
            def test_fail():
                raise ValueError()
            def test_pass():
                pass
            class TestClass:
                def test_skip(self):
                    py.test.skip("hello")
            def test_gen():
                def check(x):
                    assert x == 1
                yield check, 0
        """)
        result = self.runpytest(p1, '-v')
        assert_lines_contain_lines(result.outlines, [
            "*test_one.py:2: test_fail*FAIL", 
            "*test_one.py:4: test_pass*PASS",
            "*test_one.py:7: TestClass.test_skip*SKIP",
            "*test_one.py:10: test_gen*FAIL",
        ])
        assert result.ret == 1

class TestInteractive(AcceptBase):
    def getspawn(self):
        pexpect = py.test.importorskip("pexpect")
        def spawn(cmd):
            return pexpect.spawn(cmd, logfile=self.tmpdir.join("spawn.out").open("w"))
        return spawn

    def requirespexpect(self, version_needed):
        import pexpect
        ver = tuple(map(int, pexpect.__version__.split(".")))
        if ver < version_needed:
            py.test.skip("pexpect version %s needed" %(".".join(map(str, version_needed))))
       
    def test_pdb_interaction(self):
        self.requirespexpect((2,3))
        spawn = self.getspawn()
        self.makepyfile(test_one="""
            def test_1():
                #hello
                assert 1 == 0 
        """)
       
        child = spawn("%s %s --pdb test_one.py" % (py.std.sys.executable, 
                      pytestpath))
        child.timeout = EXPECTTIMEOUT
        child.expect(".*def test_1.*")
        child.expect(".*hello.*")
        child.expect("(Pdb)")
        child.sendeof()
        child.expect("failures: 1")
        if child.isalive(): 
            child.wait()

    def test_simple_looponfailing_interaction(self):
        spawn = self.getspawn()
        test_one = self.makepyfile(test_one="""
            def test_1():
                assert 1 == 0 
        """)
        test_one.setmtime(test_one.mtime() - 5.0)  
        child = spawn("%s %s --looponfailing test_one.py" % (py.std.sys.executable, 
                      str(pytestpath)))
        child.timeout = EXPECTTIMEOUT
        child.expect("assert 1 == 0")
        child.expect("test_one.py:")
        child.expect("failures: 1")
        child.expect("waiting for changes")
        test_one.write(py.code.Source("""
            def test_1():
                assert 1 == 1
        """))
        child.expect("MODIFIED.*test_one.py", timeout=4.0)
        child.expect("failures: no failures", timeout=5.0)
        child.kill(15)
 
