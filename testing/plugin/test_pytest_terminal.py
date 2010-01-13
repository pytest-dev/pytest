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
        metafunc.addcall(
            id="default", 
            funcargs={'option': Option(verbose=False)}
        )
        metafunc.addcall(
            id="verbose", 
            funcargs={'option': Option(verbose=True)}
        )
        if metafunc.config.pluginmanager.hasplugin("xdist"):
            nodist = getattr(metafunc.function, 'nodist', False)
            if not nodist:
                metafunc.addcall(
                    id="verbose-dist", 
                    funcargs={'option': Option(dist='each', verbose=True)}
                )

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
        p = testdir.makepyfile("import xyz")
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
            "INTERNALERROR> *raise ValueError*"
        ])

    def test_gwmanage_events(self, testdir, linecomp):
        execnet = py.test.importorskip("execnet")
        modcol = testdir.getmodulecol("""
            def test_one():
                pass
        """, configargs=("-v",))

        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        class gw1:
            id = "X1"
            spec = execnet.XSpec("popen")
        class gw2:
            id = "X2"
            spec = execnet.XSpec("popen")
        class rinfo:
            version_info = (2, 5, 1, 'final', 0)
            executable = "hello"
            platform = "xyz"
            cwd = "qwe"
        
        rep.pytest_gwmanage_newgateway(gw1, rinfo)
        linecomp.assert_contains_lines([
            "*X1*popen*xyz*2.5*"
        ])

        rep.pytest_gwmanage_rsyncstart(source="hello", gateways=[gw1, gw2])
        linecomp.assert_contains_lines([
            "rsyncstart: hello -> [X1], [X2]"
        ])
        rep.pytest_gwmanage_rsyncfinish(source="hello", gateways=[gw1, gw2])
        linecomp.assert_contains_lines([
            "rsyncfinish: hello -> [X1], [X2]"
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
        assert result.stdout.fnmatch_lines([
            "*test_p2.py .",
            "*1 passed*",
        ])
        result = testdir.runpytest("-v", p2)
        result.stdout.fnmatch_lines([
            "*test_p2.py <- *test_p1.py:2: TestMore.test_p1*",
        ])

    def test_keyboard_interrupt_dist(self, testdir, option):
        p = testdir.makepyfile("""
            raise KeyboardInterrupt
        """)
        result = testdir.runpytest(*option._getcmdargs())
        assert result.ret == 2
        result.stdout.fnmatch_lines(['*KEYBOARD INTERRUPT*'])

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
        testdir.mkdir("a").join("conftest.py").write("""if 1:
            def pytest_report_header(config):
                return ["line1", "line2"]
        """)
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


def test_getreportopt():
    assert getreportopt(None) == {}
    assert getreportopt("hello") == {'hello': True}
    assert getreportopt("hello, world") == dict(hello=True, world=True)
    assert getreportopt("nohello") == dict(hello=False)

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
    assert result.stdout.fnmatch_lines([
        "*1 passed*"
    ])
    def test_trace_reporting(self, testdir):
        result = testdir.runpytest("--trace")
        assert result.stdout.fnmatch_lines([
            "*active plugins*"
        ])
        assert result.ret == 0
