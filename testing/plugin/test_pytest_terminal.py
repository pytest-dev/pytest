"""
terminal reporting of the full testing process.
"""
import py
import sys

# ===============================================================================
# plugin tests 
#
# ===============================================================================

from py._plugin.pytest_terminal import TerminalReporter, \
    CollectonlyReporter,  repr_pythonversion, getreportopt
from py._plugin import pytest_runner as runner 

def basic_run_report(item):
    return runner.call_and_report(item, "call", log=False)

class Option:
    def __init__(self, verbose=False, dist=None):
        self.verbose = verbose
        self.dist = dist
    def _getcmdargs(self):
        l = []
        if self.verbose:
            l.append('-v')
        if self.dist:
            l.append('--dist=%s' % self.dist)
            l.append('--tx=popen')
        return l
    def _getcmdstring(self):
        return " ".join(self._getcmdargs())

def pytest_generate_tests(metafunc):
    if "option" in metafunc.funcargnames:
        metafunc.addcall(id="default", param=Option(verbose=False))
        metafunc.addcall(id="verbose", param=Option(verbose=True))
        if not getattr(metafunc.function, 'nodist', False):
            metafunc.addcall(id="verbose-dist", 
                             param=Option(dist='each', verbose=True))

def pytest_funcarg__option(request):
    if request.param.dist:
        request.config.pluginmanager.skipifmissing("xdist")
    return request.param

class TestTerminal:
    def test_pass_skip_fail(self, testdir, option):
        p = testdir.makepyfile("""
            import py
            def test_ok():
                pass
            def test_skip():
                py.test.skip("xx")
            def test_func():
                assert 0
        """)
        result = testdir.runpytest(*option._getcmdargs())
        if option.verbose:
            if not option.dist:
                result.stdout.fnmatch_lines([
                    "*test_pass_skip_fail.py:2: *test_ok*PASS*",
                    "*test_pass_skip_fail.py:4: *test_skip*SKIP*",
                    "*test_pass_skip_fail.py:6: *test_func*FAIL*",
                ])
            else:
                expected = [
                    "*PASS*test_pass_skip_fail.py:2: *test_ok*", 
                    "*SKIP*test_pass_skip_fail.py:4: *test_skip*", 
                    "*FAIL*test_pass_skip_fail.py:6: *test_func*", 
                ]
                for line in expected:
                    result.stdout.fnmatch_lines([line])
        else:
            result.stdout.fnmatch_lines([
            "*test_pass_skip_fail.py .sF"
        ])
        result.stdout.fnmatch_lines([
            "    def test_func():",
            ">       assert 0",
            "E       assert 0",
        ])

    def test_collect_fail(self, testdir, option):
        p = testdir.makepyfile("import xyz\n")
        result = testdir.runpytest(*option._getcmdargs())
        result.stdout.fnmatch_lines([
            "*test_collect_fail.py E*",
            ">   import xyz",
            "E   ImportError: No module named xyz",
            "*1 error*",
        ])

    def test_internalerror(self, testdir, linecomp):
        modcol = testdir.getmodulecol("def test_one(): pass")
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        excinfo = py.test.raises(ValueError, "raise ValueError('hello')")
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

    def test_testid(self, testdir, linecomp):
        func,method = testdir.getitems("""
            def test_func():
                pass
            class TestClass:
                def test_method(self):
                    pass
        """)
        tr = TerminalReporter(func.config, file=linecomp.stringio)
        id = tr.gettestid(func)
        assert id.endswith("test_testid.py::test_func")
        fspath = py.path.local(id.split("::")[0])
        assert fspath.check()
        id = tr.gettestid(method)
        assert id.endswith("test_testid.py::TestClass::test_method")

    def test_looponfailreport(self, testdir, linecomp):
        modcol = testdir.getmodulecol("""
            def test_fail():
                assert 0
            def test_fail2():
                raise ValueError()
        """)
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        reports = [basic_run_report(x) for x in modcol.collect()]
        rep.pytest_looponfailinfo(reports, [modcol.config.topdir])
        linecomp.assert_contains_lines([
            "*test_looponfailreport.py:2: assert 0",
            "*test_looponfailreport.py:4: ValueError*",
            "*waiting*", 
            "*%s*" % (modcol.config.topdir),
        ])

    def test_tb_option(self, testdir, option):
        p = testdir.makepyfile("""
            import py
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
            import py
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

    def test_show_path_before_running_test(self, testdir, linecomp):
        item = testdir.getitem("def test_func(): pass")
        tr = TerminalReporter(item.config, file=linecomp.stringio)
        item.config.pluginmanager.register(tr)
        tr.config.hook.pytest_itemstart(item=item)
        linecomp.assert_contains_lines([
            "*test_show_path_before_running_test.py*"
        ])

    def test_itemreport_reportinfo(self, testdir, linecomp):
        testdir.makeconftest("""
            import py
            class Function(py.test.collect.Function):
                def reportinfo(self):
                    return "ABCDE", 42, "custom"    
        """)
        item = testdir.getitem("def test_func(): pass")
        tr = TerminalReporter(item.config, file=linecomp.stringio)
        item.config.pluginmanager.register(tr)
        tr.config.option.verbose = True
        tr.config.hook.pytest_itemstart(item=item)
        linecomp.assert_contains_lines([
            "*ABCDE:43: custom*"
        ])

    def test_itemreport_pytest_report_iteminfo(self, testdir, linecomp):
        item = testdir.getitem("def test_func(): pass")
        class Plugin:
            def pytest_report_iteminfo(self, item):
                return "FGHJ", 42, "custom"
        item.config.pluginmanager.register(Plugin())             
        tr = TerminalReporter(item.config, file=linecomp.stringio)
        item.config.pluginmanager.register(tr)
        tr.config.option.verbose = True
        tr.config.hook.pytest_itemstart(item=item)
        linecomp.assert_contains_lines([
            "*FGHJ:43: custom*"
        ])

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

    def test_keyboard_interrupt_dist(self, testdir, option):
        # xxx could be refined to check for return code 
        p = testdir.makepyfile("""
            def test_sleep():
                import time
                time.sleep(10)
        """)
        child = testdir.spawn_pytest(" ".join(option._getcmdargs()))
        child.expect(".*test session starts.*")
        child.kill(2) # keyboard interrupt
        child.expect(".*KeyboardInterrupt.*")
        #child.expect(".*seconds.*")
        child.close()
        #assert ret == 2 

    @py.test.mark.nodist
    def test_keyboard_interrupt(self, testdir, option):
        p = testdir.makepyfile("""
            def test_foobar():
                assert 0
            def test_spamegg():
                import py; py.test.skip('skip me please!')
            def test_interrupt_me():
                raise KeyboardInterrupt   # simulating the user
        """)

        result = testdir.runpytest(*option._getcmdargs())
        result.stdout.fnmatch_lines([
            "    def test_foobar():",
            ">       assert 0",
            "E       assert 0",
            "*_keyboard_interrupt.py:6: KeyboardInterrupt*", 
        ])
        if option.verbose:
            result.stdout.fnmatch_lines([
                "*raise KeyboardInterrupt   # simulating the user*",
            ])
        result.stdout.fnmatch_lines(['*KEYBOARD INTERRUPT*'])

    def test_pytest_report_header(self, testdir):
        testdir.makeconftest("""
            def pytest_report_header(config):
                return "hello: info" 
        """)
        testdir.mkdir("a").join("conftest.py").write("""
def pytest_report_header(config):
    return ["line1", "line2"]""")
        result = testdir.runpytest("a")
        result.stdout.fnmatch_lines([
            "*hello: info*",
            "line1",
            "line2",
        ])


class TestCollectonly:
    def test_collectonly_basic(self, testdir, linecomp):
        modcol = testdir.getmodulecol(configargs=['--collectonly'], source="""
            def test_func():
                pass
        """)
        rep = CollectonlyReporter(modcol.config, out=linecomp.stringio)
        modcol.config.pluginmanager.register(rep)
        indent = rep.indent
        rep.config.hook.pytest_collectstart(collector=modcol)
        linecomp.assert_contains_lines([
           "<Module 'test_collectonly_basic.py'>"
        ])
        item = modcol.join("test_func")
        rep.config.hook.pytest_itemstart(item=item)
        linecomp.assert_contains_lines([
           "  <Function 'test_func'>", 
        ])
        rep.config.hook.pytest_collectreport(
            report=runner.CollectReport(modcol, [], excinfo=None))
        assert rep.indent == indent 

    def test_collectonly_skipped_module(self, testdir, linecomp):
        modcol = testdir.getmodulecol(configargs=['--collectonly'], source="""
            import py
            py.test.skip("nomod")
        """)
        rep = CollectonlyReporter(modcol.config, out=linecomp.stringio)
        modcol.config.pluginmanager.register(rep)
        cols = list(testdir.genitems([modcol]))
        assert len(cols) == 0
        linecomp.assert_contains_lines("""
            <Module 'test_collectonly_skipped_module.py'>
              !!! Skipped: 'nomod' !!!
        """)

    def test_collectonly_failed_module(self, testdir, linecomp):
        modcol = testdir.getmodulecol(configargs=['--collectonly'], source="""
            raise ValueError(0)
        """)
        rep = CollectonlyReporter(modcol.config, out=linecomp.stringio)
        modcol.config.pluginmanager.register(rep)
        cols = list(testdir.genitems([modcol]))
        assert len(cols) == 0
        linecomp.assert_contains_lines("""
            <Module 'test_collectonly_failed_module.py'>
              !!! ValueError: 0 !!!
        """)

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
        assert result.ret == 1
        extra = result.stdout.fnmatch_lines(py.code.Source("""
            <Module '*.py'>
              *ImportError*
            !!!*failures*!!!
            *test_collectonly_error.py:1*
        """).strip())


def test_repr_python_version(monkeypatch):
    monkeypatch.setattr(sys, 'version_info', (2, 5, 1, 'final', 0))
    assert repr_pythonversion() == "2.5.1-final-0"
    py.std.sys.version_info = x = (2,3)
    assert repr_pythonversion() == str(x) 

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
            "python: platform %s -- Python %s*" %(
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
        pytestconfig.pluginmanager.skipifmissing("xdist")
        result = testdir.runpytest(p1, '-v', '-n 1')
        result.stdout.fnmatch_lines([
            "*FAIL*test_verbose_reporting.py:2: test_fail*", 
        ])
        assert result.ret == 1

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
    testdict = {}
    class Config:
        def getvalue(self, name):
            return testdict.get(name, None)
    config = Config()
    testdict.update(dict(report="xfailed"))
    assert getreportopt(config) == "x"

    testdict.update(dict(report="xfailed,skipped"))
    assert getreportopt(config) == "xs"

    testdict.update(dict(report="skipped,xfailed"))
    assert getreportopt(config) == "sx"

    testdict.update(dict(report="skipped", reportchars="sf"))
    assert getreportopt(config) == "sf"

    testdict.update(dict(reportchars="sfx"))
    assert getreportopt(config) == "sfx"

def test_terminalreporter_reportopt_conftestsetting(testdir):
    testdir.makeconftest("option_report = 'skipped'")
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

def test_trace_reporting(testdir):
    result = testdir.runpytest("--traceconfig")
    result.stdout.fnmatch_lines([
        "*active plugins*"
    ])
    assert result.ret == 0

@py.test.mark.nodist
def test_show_funcarg(testdir, option):
    args = option._getcmdargs() + ["--funcargs"]
    result = testdir.runpytest(*args)
    result.stdout.fnmatch_lines([
            "*tmpdir*",
            "*temporary directory*",
        ]
    )
