"""
terminal reporting of the full testing process.
"""
import py
import sys

# ===============================================================================
# plugin tests 
#
# ===============================================================================

import pytest_runner as runner # XXX 
from pytest_terminal import TerminalReporter, CollectonlyReporter
from pytest_terminal import repr_pythonversion, folded_skips

def basic_run_report(item):
    return runner.call_and_report(item, "call", log=False)

class TestTerminal:
    def test_pass_skip_fail(self, testdir, linecomp):
        modcol = testdir.getmodulecol("""
            import py
            def test_ok():
                pass
            def test_skip():
                py.test.skip("xx")
            def test_func():
                assert 0
        """)
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        rep.config.pluginmanager.register(rep)
        rep.config.hook.pytest_sessionstart(session=testdir.session)

        for item in testdir.genitems([modcol]):
            ev = basic_run_report(item) 
            rep.config.hook.pytest_runtest_logreport(rep=ev)
        linecomp.assert_contains_lines([
                "*test_pass_skip_fail.py .sF"
        ])
        rep.config.hook.pytest_sessionfinish(session=testdir.session, exitstatus=1)
        linecomp.assert_contains_lines([
            "    def test_func():",
            ">       assert 0",
            "E       assert 0",
        ])

    def test_pass_skip_fail_verbose(self, testdir, linecomp):
        modcol = testdir.getmodulecol("""
            import py
            def test_ok():
                pass
            def test_skip():
                py.test.skip("xx")
            def test_func():
                assert 0
        """, configargs=("-v",))
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        rep.config.pluginmanager.register(rep)
        rep.config.hook.pytest_sessionstart(session=testdir.session)
        items = modcol.collect()
        rep.config.option.debug = True # 
        for item in items:
            rep.config.hook.pytest_itemstart(item=item, node=None)
            s = linecomp.stringio.getvalue().strip()
            assert s.endswith(item.name)
            rep.config.hook.pytest_runtest_logreport(rep=basic_run_report(item))

        linecomp.assert_contains_lines([
            "*test_pass_skip_fail_verbose.py:2: *test_ok*PASS*",
            "*test_pass_skip_fail_verbose.py:4: *test_skip*SKIP*",
            "*test_pass_skip_fail_verbose.py:6: *test_func*FAIL*",
        ])
        rep.config.hook.pytest_sessionfinish(session=testdir.session, exitstatus=1)
        linecomp.assert_contains_lines([
            "    def test_func():",
            ">       assert 0",
            "E       assert 0",
        ])

    def test_collect_fail(self, testdir, linecomp):
        modcol = testdir.getmodulecol("import xyz")
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        rep.config.pluginmanager.register(rep)
        rep.config.hook.pytest_sessionstart(session=testdir.session)
        l = list(testdir.genitems([modcol]))
        assert len(l) == 0
        linecomp.assert_contains_lines([
            "*test_collect_fail.py F*"
        ])
        rep.config.hook.pytest_sessionfinish(session=testdir.session, exitstatus=1)
        linecomp.assert_contains_lines([
            ">   import xyz",
            "E   ImportError: No module named xyz"
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
        modcol = testdir.getmodulecol("""
            def test_one():
                pass
        """, configargs=("-v",))

        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        class gw1:
            id = "X1"
            spec = py.execnet.XSpec("popen")
        class gw2:
            id = "X2"
            spec = py.execnet.XSpec("popen")
        class rinfo:
            version_info = (2, 5, 1, 'final', 0)
            executable = "hello"
            platform = "xyz"
            cwd = "qwe"
        
        rep.pyexecnet_gwmanage_newgateway(gw1, rinfo)
        linecomp.assert_contains_lines([
            "X1*popen*xyz*2.5*"
        ])

        rep.pyexecnet_gwmanage_rsyncstart(source="hello", gateways=[gw1, gw2])
        linecomp.assert_contains_lines([
            "rsyncstart: hello -> X1, X2"
        ])
        rep.pyexecnet_gwmanage_rsyncfinish(source="hello", gateways=[gw1, gw2])
        linecomp.assert_contains_lines([
            "rsyncfinish: hello -> X1, X2"
        ])

    def test_writeline(self, testdir, linecomp):
        modcol = testdir.getmodulecol("def test_one(): pass")
        stringio = py.std.cStringIO.StringIO()
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

    def test_tb_option(self, testdir, linecomp):
        # XXX usage of testdir 
        for tbopt in ["long", "short", "no"]:
            print 'testing --tb=%s...' % tbopt
            modcol = testdir.getmodulecol("""
                import py
                def g():
                    raise IndexError
                def test_func():
                    print 6*7
                    g()  # --calling--
            """, configargs=("--tb=%s" % tbopt,))
            rep = TerminalReporter(modcol.config, file=linecomp.stringio)
            rep.config.pluginmanager.register(rep)
            rep.config.hook.pytest_sessionstart(session=testdir.session)
            for item in testdir.genitems([modcol]):
                rep.config.hook.pytest_runtest_logreport(
                    rep=basic_run_report(item))
            rep.config.hook.pytest_sessionfinish(session=testdir.session, exitstatus=1)
            s = linecomp.stringio.getvalue()
            if tbopt == "long":
                print s
                assert 'print 6*7' in s
            else:
                assert 'print 6*7' not in s
            if tbopt != "no":
                assert '--calling--' in s
                assert 'IndexError' in s
            else:
                assert 'FAILURES' not in s
                assert '--calling--' not in s
                assert 'IndexError' not in s
            linecomp.stringio.truncate(0)

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
        tr.config.hook.pytest_itemstart(item=item)
        linecomp.assert_contains_lines([
            "*ABCDE "
        ])
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
        tr.config.hook.pytest_itemstart(item=item)
        linecomp.assert_contains_lines([
            "*FGHJ "
        ])
        tr.config.option.verbose = True
        tr.config.hook.pytest_itemstart(item=item)
        linecomp.assert_contains_lines([
            "*FGHJ:43: custom*"
        ])


    def pseudo_keyboard_interrupt(self, testdir, linecomp, verbose=False):
        modcol = testdir.getmodulecol("""
            def test_foobar():
                assert 0
            def test_spamegg():
                import py; py.test.skip('skip me please!')
            def test_interrupt_me():
                raise KeyboardInterrupt   # simulating the user
        """, configargs=("-v",)*verbose)
        #""", configargs=("--showskipsummary",) + ("-v",)*verbose)
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        modcol.config.pluginmanager.register(rep)
        modcol.config.hook.pytest_sessionstart(session=testdir.session)
        try:
            for item in testdir.genitems([modcol]):
                modcol.config.hook.pytest_runtest_logreport(
                    rep=basic_run_report(item))
        except KeyboardInterrupt:
            excinfo = py.code.ExceptionInfo()
        else:
            py.test.fail("no KeyboardInterrupt??")
        s = linecomp.stringio.getvalue()
        if not verbose:
            assert s.find("_keyboard_interrupt.py Fs") != -1
        modcol.config.hook.pytest_sessionfinish(
            session=testdir.session, exitstatus=2, excrepr=excinfo.getrepr())
        text = linecomp.stringio.getvalue()
        linecomp.assert_contains_lines([
            "    def test_foobar():",
            ">       assert 0",
            "E       assert 0",
        ])
        #assert "Skipped: 'skip me please!'" in text
        assert "_keyboard_interrupt.py:6: KeyboardInterrupt" in text
        see_details = "raise KeyboardInterrupt   # simulating the user" in text
        assert see_details == verbose

    def test_keyboard_interrupt(self, testdir, linecomp):
        self.pseudo_keyboard_interrupt(testdir, linecomp)
        
    def test_verbose_keyboard_interrupt(self, testdir, linecomp):
        self.pseudo_keyboard_interrupt(testdir, linecomp, verbose=True)

    def test_skip_reasons_folding(self):
        class longrepr:
            class reprcrash:
                path = 'xyz'
                lineno = 3
                message = "justso"

        ev1 = runner.CollectReport(None, None)
        ev1.when = "execute"
        ev1.skipped = True
        ev1.longrepr = longrepr 
        
        ev2 = runner.ItemTestReport(None, excinfo=longrepr)
        ev2.skipped = True

        l = folded_skips([ev1, ev2])
        assert len(l) == 1
        num, fspath, lineno, reason = l[0]
        assert num == 2
        assert fspath == longrepr.reprcrash.path
        assert lineno == longrepr.reprcrash.lineno
        assert reason == longrepr.reprcrash.message

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
            rep=runner.CollectReport(modcol, [], excinfo=None))
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

def test_repr_python_version(monkeypatch):
    monkeypatch.setattr(sys, 'version_info', (2, 5, 1, 'final', 0))
    assert repr_pythonversion() == "2.5.1-final-0"
    py.std.sys.version_info = x = (2,3)
    assert repr_pythonversion() == str(x) 

