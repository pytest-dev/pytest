import py

pydir = py.path.local(py.__file__).dirpath()
pytestpath = pydir.join("bin", "py.test")
EXPECTTIMEOUT=10.0

class TestGeneralUsage:
    def test_config_error(self, testdir):
        testdir.makeconftest("""
            class ConftestPlugin:
                def pytest_configure(self, config):
                    raise config.Error("hello")
        """)
        result = testdir.runpytest(testdir.tmpdir)
        assert result.ret != 0
        assert result.stderr.fnmatch_lines([
            '*ERROR: hello'
        ])

    def test_basetemp(self, testdir):
        mytemp = testdir.tmpdir.mkdir("mytemp")
        p = testdir.makepyfile("""
            import py
            def test_1(): 
                py.test.ensuretemp('xyz')
        """)
        result = testdir.runpytest(p, '--basetemp=%s' %mytemp)
        assert result.ret == 0
        assert mytemp.join('xyz').check(dir=1)
                
    def test_assertion_magic(self, testdir):
        p = testdir.makepyfile("""
            def test_this():
                x = 0
                assert x
        """)
        result = testdir.runpytest(p)
        extra = result.stdout.fnmatch_lines([
            ">       assert x", 
            "E       assert 0",
        ])
        assert result.ret == 1

    def test_collectonly_simple(self, testdir):
        p = testdir.makepyfile("""
            def test_func1():
                pass
            class TestClass:
                def test_method(self):
                    pass
        """)
        result = testdir.runpytest("--collectonly", p)
        stderr = result.stderr.str().strip()
        assert stderr.startswith("inserting into sys.path")
        assert result.ret == 0
        extra = result.stdout.fnmatch_lines(py.code.Source("""
            <Module '*.py'>
              <Function 'test_func1'*>
              <Class 'TestClass'>
                <Instance '()'>
                  <Function 'test_method'*>
        """).strip())

    def test_collectonly_error(self, testdir):
        p = testdir.makepyfile("import Errlkjqweqwe")
        result = testdir.runpytest("--collectonly", p)
        stderr = result.stderr.str().strip()
        assert stderr.startswith("inserting into sys.path")
        assert result.ret == 1
        extra = result.stdout.fnmatch_lines(py.code.Source("""
            <Module '*.py'>
              *ImportError*
            !!!*failures*!!!
            *test_collectonly_error.py:1*
        """).strip())


    def test_nested_import_error(self, testdir):
        p = testdir.makepyfile("""
                import import_fails
                def test_this():
                    assert import_fails.a == 1
        """)
        testdir.makepyfile(import_fails="import does_not_work")
        result = testdir.runpytest(p)
        extra = result.stdout.fnmatch_lines([
            ">   import import_fails",
            "E   ImportError: No module named does_not_work",
        ])
        assert result.ret == 1

    def test_skipped_reasons(self, testdir):
        testdir.makepyfile(
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
        result = testdir.runpytest() 
        extra = result.stdout.fnmatch_lines([
            "*test_one.py ss",
            "*test_two.py S",
            "___* skipped test summary *_", 
            "*conftest.py:3: *3* Skipped: 'test'", 
        ])
        assert result.ret == 0

    def test_deselected(self, testdir):
        testpath = testdir.makepyfile("""
                def test_one():
                    pass
                def test_two():
                    pass
                def test_three():
                    pass
           """
        )
        result = testdir.runpytest("-k", "test_two:", testpath)
        extra = result.stdout.fnmatch_lines([
            "*test_deselected.py ..", 
            "=* 1 test*deselected by 'test_two:'*=", 
        ])
        assert result.ret == 0

    def test_no_skip_summary_if_failure(self, testdir):
        testdir.makepyfile("""
            import py
            def test_ok():
                pass
            def test_fail():
                assert 0
            def test_skip():
                py.test.skip("dontshow")
        """)
        result = testdir.runpytest() 
        assert result.stdout.str().find("skip test summary") == -1
        assert result.ret == 1

    def test_passes(self, testdir):
        p1 = testdir.makepyfile("""
            def test_passes():
                pass
            class TestClass:
                def test_method(self):
                    pass
        """)
        old = p1.dirpath().chdir()
        try:
            result = testdir.runpytest()
        finally:
            old.chdir()
        extra = result.stdout.fnmatch_lines([
            "test_passes.py ..", 
            "* 2 pass*",
        ])
        assert result.ret == 0

    def test_header_trailer_info(self, testdir):
        p1 = testdir.makepyfile("""
            def test_passes():
                pass
        """)
        result = testdir.runpytest()
        verinfo = ".".join(map(str, py.std.sys.version_info[:3]))
        extra = result.stdout.fnmatch_lines([
            "*===== test session starts ====*",
            "python: platform %s -- Python %s*" %(
                    py.std.sys.platform, verinfo), # , py.std.sys.executable),
            "*test_header_trailer_info.py .",
            "=* 1 passed in *.[0-9][0-9] seconds *=", 
        ])

    def test_traceback_failure(self, testdir):
        p1 = testdir.makepyfile("""
            def g():
                return 2
            def f(x):
                assert x == g()
            def test_onefails():
                f(3)
        """)
        result = testdir.runpytest(p1)
        result.stdout.fnmatch_lines([
            "*test_traceback_failure.py F", 
            "====* FAILURES *====",
            "____*____", 
            "",
            "    def test_onefails():",
            ">       f(3)",
            "",
            "*test_*.py:6: ",
            "_ _ _ *",
            #"",
            "    def f(x):",
            ">       assert x == g()",
            "E       assert 3 == 2",
            "E        +  where 2 = g()",
            "",
            "*test_traceback_failure.py:4: AssertionError"
        ])

    def test_capturing_outerr(self, testdir): 
        p1 = testdir.makepyfile("""
            import sys 
            def test_capturing():
                print 42
                print >>sys.stderr, 23 
            def test_capturing_error():
                print 1
                print >>sys.stderr, 2
                raise ValueError
        """)
        result = testdir.runpytest(p1)
        result.stdout.fnmatch_lines([
            "*test_capturing_outerr.py .F", 
            "====* FAILURES *====",
            "____*____", 
            "*test_capturing_outerr.py:8: ValueError",
            "*--- Captured stdout ---*",
            "1",
            "*--- Captured stderr ---*",
            "2",
        ])

    def test_showlocals(self, testdir): 
        p1 = testdir.makepyfile("""
            def test_showlocals():
                x = 3
                y = "x" * 5000 
                assert 0
        """)
        result = testdir.runpytest(p1, '-l')
        result.stdout.fnmatch_lines([
            #"_ _ * Locals *", 
            "x* = 3",
            "y* = 'xxxxxx*"
        ])

    def test_verbose_reporting(self, testdir):
        p1 = testdir.makepyfile("""
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
        result = testdir.runpytest(p1, '-v')
        result.stdout.fnmatch_lines([
            "*test_verbose_reporting.py:2: test_fail*FAIL*", 
            "*test_verbose_reporting.py:4: test_pass*PASS*",
            "*test_verbose_reporting.py:7: TestClass.test_skip*SKIP*",
            "*test_verbose_reporting.py:10: test_gen*FAIL*",
        ])
        assert result.ret == 1
        result = testdir.runpytest(p1, '-v', '-n 1')
        result.stdout.fnmatch_lines([
            "*FAIL*test_verbose_reporting.py:2: test_fail*", 
        ])
        assert result.ret == 1

class TestDistribution:
    def test_dist_conftest_options(self, testdir):
        p1 = testdir.tmpdir.ensure("dir", 'p1.py')
        p1.dirpath("__init__.py").write("")
        p1.dirpath("conftest.py").write(py.code.Source("""
            print "importing conftest", __file__
            import py
            Option = py.test.config.Option 
            option = py.test.config.addoptions("someopt", 
                Option('--someopt', action="store_true", dest="someopt", default=False))
            dist_rsync_roots = ['../dir']
            print "added options", option
            print "config file seen from conftest", py.test.config
        """))
        p1.write(py.code.Source("""
            import py, conftest
            def test_1(): 
                print "config from test_1", py.test.config
                print "conftest from test_1", conftest.__file__
                print "test_1: py.test.config.option.someopt", py.test.config.option.someopt
                print "test_1: conftest", conftest
                print "test_1: conftest.option.someopt", conftest.option.someopt
                assert conftest.option.someopt 
        """))
        result = testdir.runpytest('-d', '--tx=popen', p1, '--someopt')
        assert result.ret == 0
        extra = result.stdout.fnmatch_lines([
            "*1 passed*", 
        ])

    def test_manytests_to_one_popen(self, testdir):
        p1 = testdir.makepyfile("""
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
        )
        result = testdir.runpytest(p1, '-d', '--tx=popen', '--tx=popen')
        result.stdout.fnmatch_lines([
            "*1*popen*Python*",
            "*2*popen*Python*",
            "*2 failed, 1 passed, 1 skipped*",
        ])
        assert result.ret == 1

    def test_dist_conftest_specified(self, testdir):
        p1 = testdir.makepyfile("""
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
        )
        testdir.makeconftest("""
            pytest_option_tx = 'popen popen popen'.split()
        """)
        result = testdir.runpytest(p1, '-d')
        result.stdout.fnmatch_lines([
            "*1*popen*Python*",
            "*2*popen*Python*",
            "*3*popen*Python*",
            "*2 failed, 1 passed, 1 skipped*",
        ])
        assert result.ret == 1

    def test_dist_tests_with_crash(self, testdir):
        if not hasattr(py.std.os, 'kill'):
            py.test.skip("no os.kill")
        
        p1 = testdir.makepyfile("""
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
            """
        )
        result = testdir.runpytest(p1, '-d', '--tx=3*popen')
        result.stdout.fnmatch_lines([
            "*popen*Python*",
            "*popen*Python*",
            "*popen*Python*",
            "*node down*",
            "*3 failed, 1 passed, 1 skipped*"
        ])
        assert result.ret == 1

    def test_distribution_rsyncdirs_example(self, testdir):
        source = testdir.mkdir("source")
        dest = testdir.mkdir("dest")
        subdir = source.mkdir("example_pkg")
        subdir.ensure("__init__.py")
        p = subdir.join("test_one.py")
        p.write("def test_5(): assert not __file__.startswith(%r)" % str(p))
        result = testdir.runpytest("-d", "--rsyncdir=%(subdir)s" % locals(), 
            "--tx=popen//chdir=%(dest)s" % locals(), p)
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            "*1* *popen*platform*",
            #"RSyncStart: [G1]",
            #"RSyncFinished: [G1]",
            "*1 passed*"
        ])
        assert dest.join(subdir.basename).check(dir=1)

    def test_dist_each(self, testdir):
        interpreters = []
        for name in ("python2.4", "python2.5"):
            interp = py.path.local.sysfind(name)
            if interp is None:
                py.test.skip("%s not found" % name)
            interpreters.append(interp)

        testdir.makepyfile(__init__="", test_one="""
            import sys
            def test_hello():
                print "%s...%s" % sys.version_info[:2]
                assert 0
        """)
        args = ["--dist=each"]
        args += ["--tx", "popen//python=%s" % interpreters[0]]
        args += ["--tx", "popen//python=%s" % interpreters[1]]
        result = testdir.runpytest(*args)
        result.stdout.fnmatch_lines(["2...4"])
        result.stdout.fnmatch_lines(["2...5"])


class TestInteractive:
    def getspawn(self, tmpdir):
        pexpect = py.test.importorskip("pexpect")
        basetemp = tmpdir.mkdir("basetemp")
        def spawn(cmd):
            cmd = cmd + " --basetemp=" + str(basetemp)
            return pexpect.spawn(cmd, logfile=tmpdir.join("spawn.out").open("w"))
        return spawn

    def requirespexpect(self, version_needed):
        pexpect = py.test.importorskip("pexpect")
        ver = tuple(map(int, pexpect.__version__.split(".")))
        if ver < version_needed:
            py.test.skip("pexpect version %s needed" %(".".join(map(str, version_needed))))
       
    def test_pdb_interaction(self, testdir):
        self.requirespexpect((2,3))
        spawn = self.getspawn(testdir.tmpdir)
        p1 = testdir.makepyfile("""
            def test_1():
                i = 0
                assert i == 1
        """)
        child = spawn("%s %s --pdb %s" % (py.std.sys.executable, pytestpath, p1))
        child.timeout = EXPECTTIMEOUT
        #child.expect(".*def test_1.*")
        child.expect(".*i = 0.*")
        child.expect("(Pdb)")
        child.sendeof()
        child.expect("1 failed")
        if child.isalive(): 
            child.wait()

    def test_simple_looponfail_interaction(self, testdir):
        spawn = self.getspawn(testdir.tmpdir)
        p1 = testdir.makepyfile("""
            def test_1():
                assert 1 == 0 
        """)
        p1.setmtime(p1.mtime() - 50.0)  
        child = spawn("%s %s --looponfail %s" % (py.std.sys.executable, pytestpath, p1))
        child.timeout = EXPECTTIMEOUT
        child.expect("assert 1 == 0")
        child.expect("test_simple_looponfail_interaction.py:")
        child.expect("1 failed")
        child.expect("waiting for changes")
        p1.write(py.code.Source("""
            def test_1():
                assert 1 == 1
        """))
        child.expect("MODIFIED.*test_simple_looponfail_interaction.py", timeout=4.0)
        child.expect("1 passed", timeout=5.0)
        child.kill(15)
       
class TestKeyboardInterrupt: 
    def test_raised_in_testfunction(self, testdir):
        p1 = testdir.makepyfile("""
            import py
            def test_fail():
                raise ValueError()
            def test_inter():
                raise KeyboardInterrupt()
        """)
        result = testdir.runpytest(p1)
        result.stdout.fnmatch_lines([
            #"*test_inter() INTERRUPTED",
            "*KEYBOARD INTERRUPT*",
            "*1 failed*", 
        ])

