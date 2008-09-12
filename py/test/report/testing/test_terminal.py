import py
import sys
from py.__.test.report.terminal import TerminalReporter
from py.__.test import event
#from py.__.test.testing import suptest
from py.__.test.runner import basic_run_report
from py.__.test.testing.suptest import InlineCollection, popvalue 
from py.__.test.testing.suptest import assert_stringio_contains_lines
from py.__.test.dsession.hostmanage import Host, makehostup
from py.__.test.report.base import repr_pythonversion

class TestTerminal(InlineCollection):
    def test_session_reporter_subscription(self):
        config = py.test.config._reparse(['xxx'])
        session = config.initsession()
        session.sessionstarts()
        rep = session.reporter
        assert isinstance(rep, TerminalReporter)
        assert rep.processevent in session.bus._subscribers
        session.sessionfinishes()
        #assert rep.processevent not in session.bus._subscribers

    def test_hostup(self):
        item = self.getitem("def test_func(): pass")
        stringio = py.std.cStringIO.StringIO()
        rep = TerminalReporter(item._config, file=stringio)
        rep.processevent(event.TestrunStart())
        host = Host("localhost")
        rep.processevent(makehostup(host))
        s = popvalue(stringio)
        expect = "%s %s %s - Python %s" %(host.hostid, sys.platform, 
            sys.executable, repr_pythonversion(sys.version_info))
        assert s.find(expect) != -1

    def test_pass_skip_fail(self):
        modcol = self.getmodulecol("""
            import py
            def test_ok():
                pass
            def test_skip():
                py.test.skip("xx")
            def test_func():
                assert 0
        """, withsession=True)
        stringio = py.std.cStringIO.StringIO()
        rep = TerminalReporter(modcol._config, file=stringio)
        rep.processevent(event.TestrunStart())
        for item in self.session.genitems([modcol]):
            ev = basic_run_report(item) 
            rep.processevent(ev)
        s = popvalue(stringio)
        assert s.find("test_pass_skip_fail.py .sF") != -1
        rep.processevent(event.TestrunFinish())
        assert_stringio_contains_lines(stringio, [
            "    def test_func():",
            ">       assert 0",
            "E       assert 0",
        ])

    def test_pass_skip_fail_verbose(self):
        modcol = self.getmodulecol("""
            import py
            def test_ok():
                pass
            def test_skip():
                py.test.skip("xx")
            def test_func():
                assert 0
        """, configargs=("-v",), withsession=True)
        stringio = py.std.cStringIO.StringIO()
        rep = TerminalReporter(modcol._config, file=stringio)
        rep.processevent(event.TestrunStart())
        items = modcol.collect()
        for item in items:
            rep.processevent(event.ItemStart(item))
            s = stringio.getvalue().strip()
            assert s.endswith(item.name)
            ev = basic_run_report(item) 
            rep.processevent(ev)

        assert_stringio_contains_lines(stringio, [
            "*test_pass_skip_fail_verbose.py:2: *test_ok*PASS",
            "*test_pass_skip_fail_verbose.py:4: *test_skip*SKIP",
            "*test_pass_skip_fail_verbose.py:6: *test_func*FAIL",
        ])
        rep.processevent(event.TestrunFinish())
        assert_stringio_contains_lines(stringio, [
            "    def test_func():",
            ">       assert 0",
            "E       assert 0",
        ])

    def test_collect_fail(self):
        modcol = self.getmodulecol("""
            import xyz
        """, withsession=True)
        stringio = py.std.cStringIO.StringIO()
        rep = TerminalReporter(modcol._config, bus=self.session.bus, file=stringio)
        rep.processevent(event.TestrunStart())
        l = list(self.session.genitems([modcol]))
        assert len(l) == 0
        s = popvalue(stringio) 
        print s
        assert s.find("test_collect_fail.py - ImportError: No module named") != -1
        rep.processevent(event.TestrunFinish())
        assert_stringio_contains_lines(stringio, [
            ">   import xyz",
            "E   ImportError: No module named xyz"
        ])

    def test_internal_exception(self):
        modcol = self.getmodulecol("def test_one(): pass")
        stringio = py.std.cStringIO.StringIO()
        rep = TerminalReporter(modcol._config, file=stringio)
        excinfo = py.test.raises(ValueError, "raise ValueError('hello')")
        rep.processevent(event.InternalException(excinfo))
        s = popvalue(stringio)
        assert s.find("InternalException:") != -1 

    def test_hostready_crash(self):
        modcol = self.getmodulecol("""
            def test_one():
                pass
        """, configargs=("-v",))
        stringio = py.std.cStringIO.StringIO()
        host1 = Host("localhost")
        rep = TerminalReporter(modcol._config, file=stringio)
        rep.processevent(event.HostGatewayReady(host1, None))
        s = popvalue(stringio)
        assert s.find("HostGatewayReady") != -1
        rep.processevent(event.HostDown(host1, "myerror"))
        s = popvalue(stringio)
        assert s.find("HostDown") != -1
        assert s.find("myerror") != -1

    def test_writeline(self):
        modcol = self.getmodulecol("def test_one(): pass")
        stringio = py.std.cStringIO.StringIO()
        rep = TerminalReporter(modcol._config, file=stringio)
        rep.write_fspath_result(py.path.local("xy.py"), '.')
        rep.write_line("hello world")
        lines = popvalue(stringio).split('\n')
        assert not lines[0]
        assert lines[1].endswith("xy.py .")
        assert lines[2] == "hello world"

    def test_looponfailingreport(self):
        modcol = self.getmodulecol("""
            def test_fail():
                assert 0
            def test_fail2():
                raise ValueError()
        """)
        stringio = py.std.cStringIO.StringIO()
        rep = TerminalReporter(modcol._config, file=stringio)
        reports = [basic_run_report(x) for x in modcol.collect()]
        rep.processevent(event.LooponfailingInfo(reports, [modcol._config.topdir]))
        assert_stringio_contains_lines(stringio, [
            "*test_looponfailingreport.py:2: assert 0",
            "*test_looponfailingreport.py:4: ValueError*",
            "*waiting*", 
            "*%s*" % (modcol._config.topdir),
        ])

    def test_tb_option(self):
        for tbopt in ["no", "short", "long"]:
            print 'testing --tb=%s...' % tbopt
            modcol = self.getmodulecol("""
                import py
                def g():
                    raise IndexError
                def test_func():
                    print 6*7
                    g()  # --calling--
            """, configargs=("--tb=%s" % tbopt,), withsession=True)
            stringio = py.std.cStringIO.StringIO()
            rep = TerminalReporter(modcol._config, file=stringio)
            rep.processevent(event.TestrunStart())
            for item in self.session.genitems([modcol]):
                ev = basic_run_report(item) 
                rep.processevent(ev)
            rep.processevent(event.TestrunFinish())
            s = popvalue(stringio)
            if tbopt == "long":
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

    def test_show_path_before_running_test(self):
        modcol = self.getmodulecol("""
            def test_foobar():
                pass
        """, withsession=True)
        stringio = py.std.cStringIO.StringIO()
        rep = TerminalReporter(modcol._config, bus=self.session.bus, file=stringio)
        l = list(self.session.genitems([modcol]))
        assert len(l) == 1
        rep.processevent(event.ItemStart(l[0]))
        s = popvalue(stringio) 
        print s
        assert s.find("test_show_path_before_running_test.py") != -1

    def test_keyboard_interrupt(self, verbose=False):
        modcol = self.getmodulecol("""
            def test_foobar():
                assert 0
            def test_spamegg():
                import py; py.test.skip('skip me please!')
            def test_interrupt_me():
                raise KeyboardInterrupt   # simulating the user
        """, configargs=("--showskipsummary",) + ("-v",)*verbose,
             withsession=True)
        stringio = py.std.cStringIO.StringIO()
        rep = TerminalReporter(modcol._config, bus=self.session.bus, file=stringio)
        rep.processevent(event.TestrunStart())
        try:
            for item in self.session.genitems([modcol]):
                ev = basic_run_report(item) 
                rep.processevent(ev)
        except KeyboardInterrupt:
            excinfo = py.code.ExceptionInfo()
        else:
            py.test.fail("no KeyboardInterrupt??")
        s = popvalue(stringio)
        if not verbose:
            assert s.find("_keyboard_interrupt.py Fs") != -1
        rep.processevent(event.TestrunFinish(exitstatus=2, excinfo=excinfo))
        assert_stringio_contains_lines(stringio, [
            "    def test_foobar():",
            ">       assert 0",
            "E       assert 0",
        ])
        text = stringio.getvalue()
        assert "Skipped: 'skip me please!'" in text
        assert "_keyboard_interrupt.py:6: KeyboardInterrupt" in text
        see_details = "raise KeyboardInterrupt   # simulating the user" in text
        assert see_details == verbose

    def test_verbose_keyboard_interrupt(self):
        self.test_keyboard_interrupt(verbose=True)
