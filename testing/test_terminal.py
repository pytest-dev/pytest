"""
terminal reporting of the full testing process.
"""
import pytest,py
import sys

from _pytest.terminal import TerminalReporter, repr_pythonversion, getreportopt
from _pytest import runner

def basic_run_report(item):
    runner.call_and_report(item, "setup", log=False)
    return runner.call_and_report(item, "call", log=False)

class Option:
    def __init__(self, verbose=False, fulltrace=False):
        self.verbose = verbose
        self.fulltrace = fulltrace

    @property
    def args(self):
        l = []
        if self.verbose:
            l.append('-v')
        if self.fulltrace:
            l.append('--fulltrace')
        return l

def pytest_generate_tests(metafunc):
    if "option" in metafunc.funcargnames:
        metafunc.addcall(id="default",
                         funcargs={'option': Option(verbose=False)})
        metafunc.addcall(id="verbose",
                         funcargs={'option': Option(verbose=True)})
        metafunc.addcall(id="quiet",
                         funcargs={'option': Option(verbose=-1)})
        metafunc.addcall(id="fulltrace",
                         funcargs={'option': Option(fulltrace=True)})


class TestTerminal:
    def test_pass_skip_fail(self, testdir, option):
        p = testdir.makepyfile("""
            import pytest
            def test_ok():
                pass
            def test_skip():
                pytest.skip("xx")
            def test_func():
                assert 0
        """)
        result = testdir.runpytest(*option.args)
        if option.verbose:
            result.stdout.fnmatch_lines([
                "*test_pass_skip_fail.py:2: *test_ok*PASS*",
                "*test_pass_skip_fail.py:4: *test_skip*SKIP*",
                "*test_pass_skip_fail.py:6: *test_func*FAIL*",
            ])
        else:
            result.stdout.fnmatch_lines([
            "*test_pass_skip_fail.py .sF"
        ])
        result.stdout.fnmatch_lines([
            "    def test_func():",
            ">       assert 0",
            "E       assert 0",
        ])

    def test_internalerror(self, testdir, linecomp):
        modcol = testdir.getmodulecol("def test_one(): pass")
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        excinfo = pytest.raises(ValueError, "raise ValueError('hello')")
        rep.pytest_internalerror(excinfo.getrepr())
        linecomp.assert_contains_lines([
            "INTERNALERROR> *ValueError*hello*"
        ])

    def test_writeline(self, testdir, linecomp):
        modcol = testdir.getmodulecol("def test_one(): pass")
        stringio = py.io.TextIO()
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        rep.write_fspath_result(py.path.local("xy.py"), '.')
        rep.write_line("hello world")
        lines = linecomp.stringio.getvalue().split('\n')
        assert not lines[0]
        assert lines[1].endswith("xy.py .")
        assert lines[2] == "hello world"

    def test_show_runtest_logstart(self, testdir, linecomp):
        item = testdir.getitem("def test_func(): pass")
        tr = TerminalReporter(item.config, file=linecomp.stringio)
        item.config.pluginmanager.register(tr)
        location = item.reportinfo()
        tr.config.hook.pytest_runtest_logstart(nodeid=item.nodeid,
            location=location, fspath=str(item.fspath))
        linecomp.assert_contains_lines([
            "*test_show_runtest_logstart.py*"
        ])

    def test_runtest_location_shown_before_test_starts(self, testdir):
        p1 = testdir.makepyfile("""
            def test_1():
                import time
                time.sleep(20)
        """)
        child = testdir.spawn_pytest("")
        child.expect(".*test_runtest_location.*py")
        child.sendeof()
        child.kill(15)

    def test_itemreport_subclasses_show_subclassed_file(self, testdir):
        p1 = testdir.makepyfile(test_p1="""
            class BaseTests:
                def test_p1(self):
                    pass
            class TestClass(BaseTests):
                pass
        """)
        p2 = testdir.makepyfile(test_p2="""
            from test_p1 import BaseTests
            class TestMore(BaseTests):
                pass
        """)
        result = testdir.runpytest(p2)
        result.stdout.fnmatch_lines([
            "*test_p2.py .",
            "*1 passed*",
        ])
        result = testdir.runpytest("-v", p2)
        result.stdout.fnmatch_lines([
            "*test_p2.py <- *test_p1.py:2: TestMore.test_p1*",
        ])

    def test_itemreport_directclasses_not_shown_as_subclasses(self, testdir):
        a = testdir.mkpydir("a")
        a.join("test_hello.py").write(py.code.Source("""
            class TestClass:
                def test_method(self):
                    pass
        """))
        result = testdir.runpytest("-v")
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            "*a/test_hello.py*PASS*",
        ])
        assert " <- " not in result.stdout.str()

    def test_keyboard_interrupt(self, testdir, option):
        p = testdir.makepyfile("""
            def test_foobar():
                assert 0
            def test_spamegg():
                import py; pytest.skip('skip me please!')
            def test_interrupt_me():
                raise KeyboardInterrupt   # simulating the user
        """)

        result = testdir.runpytest(*option.args)
        result.stdout.fnmatch_lines([
            "    def test_foobar():",
            ">       assert 0",
            "E       assert 0",
            "*_keyboard_interrupt.py:6: KeyboardInterrupt*",
        ])
        if option.fulltrace:
            result.stdout.fnmatch_lines([
                "*raise KeyboardInterrupt   # simulating the user*",
            ])
        result.stdout.fnmatch_lines(['*KeyboardInterrupt*'])

    def test_keyboard_in_sessionstart(self, testdir):
        testdir.makeconftest("""
            def pytest_sessionstart():
                raise KeyboardInterrupt
        """)
        p = testdir.makepyfile("""
            def test_foobar():
                pass
        """)

        result = testdir.runpytest()
        assert result.ret == 2
        result.stdout.fnmatch_lines(['*KeyboardInterrupt*'])


class TestCollectonly:
    def test_collectonly_basic(self, testdir):
        testdir.makepyfile("""
            def test_func():
                pass
        """)
        result = testdir.runpytest("--collectonly",)
        result.stdout.fnmatch_lines([
           "<Module 'test_collectonly_basic.py'>",
           "  <Function 'test_func'>",
        ])

    def test_collectonly_skipped_module(self, testdir):
        testdir.makepyfile("""
            import pytest
            pytest.skip("hello")
        """)
        result = testdir.runpytest("--collectonly", "-rs")
        result.stdout.fnmatch_lines([
            "SKIP*hello*",
            "*1 skip*",
        ])

    def test_collectonly_failed_module(self, testdir):
        testdir.makepyfile("""raise ValueError(0)""")
        result = testdir.runpytest("--collectonly")
        result.stdout.fnmatch_lines([
            "*raise ValueError*",
            "*1 error*",
        ])

    def test_collectonly_fatal(self, testdir):
        p1 = testdir.makeconftest("""
            def pytest_collectstart(collector):
                assert 0, "urgs"
        """)
        result = testdir.runpytest("--collectonly")
        result.stdout.fnmatch_lines([
            "*INTERNAL*args*"
        ])
        assert result.ret == 3

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
        #assert stderr.startswith("inserting into sys.path")
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            "*<Module '*.py'>",
            "* <Function 'test_func1'*>",
            "* <Class 'TestClass'>",
            #"*  <Instance '()'>",
            "*   <Function 'test_method'*>",
        ])

    def test_collectonly_error(self, testdir):
        p = testdir.makepyfile("import Errlkjqweqwe")
        result = testdir.runpytest("--collectonly", p)
        stderr = result.stderr.str().strip()
        assert result.ret == 1
        result.stdout.fnmatch_lines(py.code.Source("""
            *ERROR*
            *import Errlk*
            *ImportError*
            *1 error*
        """).strip())

    def test_collectonly_missing_path(self, testdir):
        """this checks issue 115,
            failure in parseargs will cause session
            not to have the items attribute
        """
        result = testdir.runpytest("--collectonly", "uhm_missing_path")
        assert result.ret == 3
        result.stderr.fnmatch_lines([
            '*ERROR: file not found*',
        ])

    def test_collectonly_quiet(self, testdir):
        testdir.makepyfile("def test_foo(): pass")
        result = testdir.runpytest("--collectonly", "-q")
        result.stdout.fnmatch_lines([
            '*test_foo*',
        ])

    def test_collectonly_more_quiet(self, testdir):
        testdir.makepyfile(test_fun="def test_foo(): pass")
        result = testdir.runpytest("--collectonly", "-qq")
        result.stdout.fnmatch_lines([
            '*test_fun.py: 1*',
        ])


def test_repr_python_version(monkeypatch):
    try:
        monkeypatch.setattr(sys, 'version_info', (2, 5, 1, 'final', 0))
        assert repr_pythonversion() == "2.5.1-final-0"
        py.std.sys.version_info = x = (2,3)
        assert repr_pythonversion() == str(x)
    finally:
        monkeypatch.undo() # do this early as pytest can get confused

class TestFixtureReporting:
    def test_setup_fixture_error(self, testdir):
        p = testdir.makepyfile("""
            def setup_function(function):
                print ("setup func")
                assert 0
            def test_nada():
                pass
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*ERROR at setup of test_nada*",
            "*setup_function(function):*",
            "*setup func*",
            "*assert 0*",
            "*1 error*",
        ])
        assert result.ret != 0

    def test_teardown_fixture_error(self, testdir):
        p = testdir.makepyfile("""
            def test_nada():
                pass
            def teardown_function(function):
                print ("teardown func")
                assert 0
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*ERROR at teardown*",
            "*teardown_function(function):*",
            "*assert 0*",
            "*Captured stdout*",
            "*teardown func*",
            "*1 passed*1 error*",
        ])

    def test_teardown_fixture_error_and_test_failure(self, testdir):
        p = testdir.makepyfile("""
            def test_fail():
                assert 0, "failingfunc"

            def teardown_function(function):
                print ("teardown func")
                assert False
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*ERROR at teardown of test_fail*",
            "*teardown_function(function):*",
            "*assert False*",
            "*Captured stdout*",
            "*teardown func*",

            "*test_fail*",
            "*def test_fail():",
            "*failingfunc*",
            "*1 failed*1 error*",
         ])

class TestTerminalFunctional:
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
        result.stdout.fnmatch_lines([
            "*test_deselected.py ..",
            "=* 1 test*deselected by*test_two:*=",
        ])
        assert result.ret == 0

    def test_no_skip_summary_if_failure(self, testdir):
        testdir.makepyfile("""
            import pytest
            def test_ok():
                pass
            def test_fail():
                assert 0
            def test_skip():
                pytest.skip("dontshow")
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
        result.stdout.fnmatch_lines([
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
        result.stdout.fnmatch_lines([
            "*===== test session starts ====*",
            "platform %s -- Python %s*" %(
                    py.std.sys.platform, verinfo), # , py.std.sys.executable),
            "*test_header_trailer_info.py .",
            "=* 1 passed in *.[0-9][0-9] seconds *=",
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

    def test_verbose_reporting(self, testdir, pytestconfig):
        p1 = testdir.makepyfile("""
            import pytest
            def test_fail():
                raise ValueError()
            def test_pass():
                pass
            class TestClass:
                def test_skip(self):
                    pytest.skip("hello")
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

        pytestconfig.pluginmanager.skipifmissing("xdist")
        result = testdir.runpytest(p1, '-v', '-n 1')
        result.stdout.fnmatch_lines([
            "*FAIL*test_verbose_reporting.py:2: test_fail*",
        ])
        assert result.ret == 1

    def test_quiet_reporting(self, testdir):
        p1 = testdir.makepyfile("def test_pass(): pass")
        result = testdir.runpytest(p1, '-q')
        s = result.stdout.str()
        assert 'test session starts' not in s
        assert p1.basename not in s
        assert "===" not in s

def test_fail_extra_reporting(testdir):
    p = testdir.makepyfile("def test_this(): assert 0")
    result = testdir.runpytest(p)
    assert 'short test summary' not in result.stdout.str()
    result = testdir.runpytest(p, '-rf')
    result.stdout.fnmatch_lines([
        "*test summary*",
        "FAIL*test_fail_extra_reporting*",
    ])

def test_fail_reporting_on_pass(testdir):
    p = testdir.makepyfile("def test_this(): assert 1")
    result = testdir.runpytest(p, '-rf')
    assert 'short test summary' not in result.stdout.str()

def test_getreportopt():
    class config:
        class option:
            reportchars = ""
    config.option.report = "xfailed"
    assert getreportopt(config) == "x"

    config.option.report = "xfailed,skipped"
    assert getreportopt(config) == "xs"

    config.option.report = "skipped,xfailed"
    assert getreportopt(config) == "sx"

    config.option.report = "skipped"
    config.option.reportchars = "sf"
    assert getreportopt(config) == "sf"

    config.option.reportchars = "sfx"
    assert getreportopt(config) == "sfx"

def test_terminalreporter_reportopt_addopts(testdir):
    testdir.makeini("[pytest]\naddopts=-rs")
    p = testdir.makepyfile("""
        def pytest_funcarg__tr(request):
            tr = request.config.pluginmanager.getplugin("terminalreporter")
            return tr
        def test_opt(tr):
            assert tr.hasopt('skipped')
            assert not tr.hasopt('qwe')
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
        "*1 passed*"
    ])

def test_tbstyle_short(testdir):
    p = testdir.makepyfile("""
        def pytest_funcarg__arg(request):
            return 42
        def test_opt(arg):
            x = 0
            assert x
    """)
    result = testdir.runpytest("--tb=short")
    s = result.stdout.str()
    assert 'arg = 42' not in s
    assert 'x = 0' not in s
    result.stdout.fnmatch_lines([
        "*%s:5*" % p.basename,
        ">*assert x",
        "E*assert*",
    ])
    result = testdir.runpytest()
    s = result.stdout.str()
    assert 'x = 0' in s
    assert 'assert x' in s

def test_traceconfig(testdir, monkeypatch):
    result = testdir.runpytest("--traceconfig")
    result.stdout.fnmatch_lines([
        "*active plugins*"
    ])
    assert result.ret == 0


class TestGenericReporting:
    """ this test class can be subclassed with a different option
        provider to run e.g. distributed tests.
    """
    def test_collect_fail(self, testdir, option):
        p = testdir.makepyfile("import xyz\n")
        result = testdir.runpytest(*option.args)
        result.stdout.fnmatch_lines([
            ">   import xyz",
            "E   ImportError: No module named *xyz*",
            "*1 error*",
        ])

    def test_maxfailures(self, testdir, option):
        p = testdir.makepyfile("""
            def test_1():
                assert 0
            def test_2():
                assert 0
            def test_3():
                assert 0
        """)
        result = testdir.runpytest("--maxfail=2", *option.args)
        result.stdout.fnmatch_lines([
            "*def test_1():*",
            "*def test_2():*",
            "*!! Interrupted: stopping after 2 failures*!!*",
            "*2 failed*",
        ])


    def test_tb_option(self, testdir, option):
        p = testdir.makepyfile("""
            import pytest
            def g():
                raise IndexError
            def test_func():
                print (6*7)
                g()  # --calling--
        """)
        for tbopt in ["long", "short", "no"]:
            print('testing --tb=%s...' % tbopt)
            result = testdir.runpytest('--tb=%s' % tbopt)
            s = result.stdout.str()
            if tbopt == "long":
                assert 'print (6*7)' in s
            else:
                assert 'print (6*7)' not in s
            if tbopt != "no":
                assert '--calling--' in s
                assert 'IndexError' in s
            else:
                assert 'FAILURES' not in s
                assert '--calling--' not in s
                assert 'IndexError' not in s

    def test_tb_crashline(self, testdir, option):
        p = testdir.makepyfile("""
            import pytest
            def g():
                raise IndexError
            def test_func1():
                print (6*7)
                g()  # --calling--
            def test_func2():
                assert 0, "hello"
        """)
        result = testdir.runpytest("--tb=line")
        bn = p.basename
        result.stdout.fnmatch_lines([
            "*%s:3: IndexError*" % bn,
            "*%s:8: AssertionError: hello*" % bn,
        ])
        s = result.stdout.str()
        assert "def test_func2" not in s

    def test_pytest_report_header(self, testdir, option):
        testdir.makeconftest("""
            def pytest_report_header(config):
                return "hello: info"
        """)
        testdir.mkdir("a").join("conftest.py").write("""
def pytest_report_header(config):
    return ["line1", "line2"]""")
        result = testdir.runpytest("a")
        result.stdout.fnmatch_lines([
            "line1",
            "line2",
            "*hello: info*",
        ])

@pytest.mark.xfail("not hasattr(os, 'dup')")
def test_fdopen_kept_alive_issue124(testdir):
    testdir.makepyfile("""
        import os, sys
        k = []
        def test_open_file_and_keep_alive(capfd):
            stdout = os.fdopen(1, 'w', 1)
            k.append(stdout)

        def test_close_kept_alive_file():
            stdout = k.pop()
            stdout.close()
    """)
    result = testdir.runpytest("-s")
    result.stdout.fnmatch_lines([
        "*2 passed*"
    ])
