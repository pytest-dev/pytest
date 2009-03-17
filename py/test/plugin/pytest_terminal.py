import py
import sys

class TerminalPlugin(object):
    """ Report a test run to a terminal. """
    def pytest_configure(self, config):
        if config.option.collectonly:
            self.reporter = CollectonlyReporter(config)
        else:
            self.reporter = TerminalReporter(config)
        # XXX see remote.py's XXX 
        for attr in 'pytest_terminal_hasmarkup', 'pytest_terminal_fullwidth':
            if hasattr(config, attr):
                #print "SETTING TERMINAL OPTIONS", attr, getattr(config, attr)
                name = attr.split("_")[-1]
                assert hasattr(self.reporter._tw, name), name
                setattr(self.reporter._tw, name, getattr(config, attr))
        config.bus.register(self.reporter)

class TerminalReporter:
    def __init__(self, config, file=None):
        self.config = config 
        self.stats = {}       
        self.curdir = py.path.local()
        if file is None:
            file = py.std.sys.stdout
        self._tw = py.io.TerminalWriter(file)
        self.currentfspath = None 

    def write_fspath_result(self, fspath, res):
        if fspath != self.currentfspath:
            self._tw.line()
            relpath = self.curdir.bestrelpath(fspath)
            self._tw.write(relpath + " ")
            self.currentfspath = fspath
        self._tw.write(res)

    def write_ensure_prefix(self, prefix, extra="", **kwargs):
        if self.currentfspath != prefix:
            self._tw.line()
            self.currentfspath = prefix 
            self._tw.write(prefix)
        if extra:
            self._tw.write(extra, **kwargs)
            self.currentfspath = -2

    def ensure_newline(self):
        if self.currentfspath: 
            self._tw.line()
            self.currentfspath = None

    def write_line(self, line, **markup):
        line = str(line)
        self.ensure_newline()
        self._tw.line(line, **markup)

    def write_sep(self, sep, title=None, **markup):
        self.ensure_newline()
        self._tw.sep(sep, title, **markup)

    def getcategoryletterword(self, event):
        res = self.config.pytestplugins.call_firstresult("pytest_report_teststatus", event=event)
        if res:
            return res
        for cat in 'skipped failed passed ???'.split():
            if getattr(event, cat, None):
                break 
        return cat, self.getoutcomeletter(event), self.getoutcomeword(event)

    def getoutcomeletter(self, event):
        return event.shortrepr 

    def getoutcomeword(self, event):
        if event.passed: 
            return "PASS", dict(green=True)
        elif event.failed: 
            return "FAIL", dict(red=True)
        elif event.skipped: 
            return "SKIP"
        else: 
            return "???", dict(red=True)

    def pyevent_internalerror(self, event):
        for line in str(event.repr).split("\n"):
            self.write_line("InternalException: " + line)

    def pyevent_hostgatewayready(self, event):
        if self.config.option.verbose:
            self.write_line("HostGatewayReady: %s" %(event.host,))

    def pyevent_plugin_registered(self, plugin):
        if self.config.option.traceconfig: 
            msg = "PLUGIN registered: %s" %(plugin,)
            # XXX this event may happen during setup/teardown time 
            #     which unfortunately captures our output here 
            #     which garbles our output if we use self.write_line 
            self.write_line(msg)

    def pyevent_hostup(self, event):
        d = event.platinfo.copy()
        d['host'] = event.host.address
        d['version'] = repr_pythonversion(d['sys.version_info'])
        self.write_line("HOSTUP: %(host)s %(sys.platform)s "
                      "%(sys.executable)s - Python %(version)s" %
                      d)

    def pyevent_hostdown(self, event):
        host = event.host
        error = event.error
        if error:
            self.write_line("HostDown %s: %s" %(host, error))

    def pyevent_trace(self, category, msg):
        if self.config.option.debug or \
           self.config.option.traceconfig and category.find("config") != -1:
            self.write_line("[%s] %s" %(category, msg))

    def pyevent_itemstart(self, event):
        if self.config.option.verbose:
            info = event.item.repr_metainfo()
            line = info.verboseline(basedir=self.curdir) + " "
            extra = ""
            if event.host:
                extra = "-> " + str(event.host)
            self.write_ensure_prefix(line, extra)
        else:
            # ensure that the path is printed before the 1st test of
            # a module starts running
            fspath = event.item.fspath 
            self.write_fspath_result(fspath, "")

    def pyevent_rescheduleitems(self, event):
        if self.config.option.debug:
            self.write_sep("!", "RESCHEDULING %s " %(event.items,))

    def pyevent_deselected(self, event):
        self.stats.setdefault('deselected', []).append(event)
    
    def pyevent_itemtestreport(self, event):
        fspath = event.colitem.fspath 
        cat, letter, word = self.getcategoryletterword(event)
        if isinstance(word, tuple):
            word, markup = word
        else:
            markup = {}
        self.stats.setdefault(cat, []).append(event)
        if not self.config.option.verbose:
            self.write_fspath_result(fspath, letter)
        else:
            info = event.colitem.repr_metainfo()
            line = info.verboseline(basedir=self.curdir) + " "
            self.write_ensure_prefix(line, word, **markup)

    def pyevent_collectionreport(self, event):
        if not event.passed:
            if event.failed:
                self.stats.setdefault("failed", []).append(event)
                msg = event.longrepr.reprcrash.message 
                self.write_fspath_result(event.colitem.fspath, "F")
            elif event.skipped:
                self.stats.setdefault("skipped", []).append(event)
                self.write_fspath_result(event.colitem.fspath, "S")

    def pyevent_testrunstart(self, event):
        self.write_sep("=", "test session starts", bold=True)
        self._sessionstarttime = py.std.time.time()
        rev = py.__pkg__.getrev()
        self.write_line("using py lib: %s <rev %s>" % (
                       py.path.local(py.__file__).dirpath(), rev))
        if self.config.option.traceconfig:
            plugins = []
            for x in self.config.pytestplugins._plugins:
                if isinstance(x, str) and x.startswith("pytest_"):
                    plugins.append(x[7:])
                else:
                    plugins.append(str(x)) # XXX display conftest plugins more nicely 
            plugins = ", ".join(plugins) 
            self.write_line("active plugins: %s" %(plugins,))
        for i, testarg in py.builtin.enumerate(self.config.args):
            self.write_line("test object %d: %s" %(i+1, testarg))

    def pyevent_testrunfinish(self, event):
        self._tw.line("")
        if event.exitstatus in (0, 1, 2):
            self.summary_failures()
            self.summary_skips()
            self.config.pytestplugins.call_each("pytest_terminal_summary", terminalreporter=self)
        if event.excrepr is not None:
            self.summary_final_exc(event.excrepr)
        if event.exitstatus == 2:
            self.write_sep("!", "KEYBOARD INTERRUPT")
        self.summary_deselected()
        self.summary_stats()

    def pyevent_looponfailinginfo(self, event):
        if event.failreports:
            self.write_sep("#", "LOOPONFAILING", red=True)
            for report in event.failreports:
                try:
                    loc = report.longrepr.reprcrash
                except AttributeError:
                    loc = str(report.longrepr)[:50]
                self.write_line(loc, red=True)
        self.write_sep("#", "waiting for changes")
        for rootdir in event.rootdirs:
            self.write_line("### Watching:   %s" %(rootdir,), bold=True)

    #
    # summaries for TestrunFinish 
    #

    def summary_failures(self):
        if 'failed' in self.stats and self.config.option.tbstyle != "no":
            self.write_sep("=", "FAILURES")
            for ev in self.stats['failed']:
                self.write_sep("_")
                ev.toterminal(self._tw)

    def summary_stats(self):
        session_duration = py.std.time.time() - self._sessionstarttime

        keys = "failed passed skipped deselected".split()
        parts = []
        for key in keys:
            val = self.stats.get(key, None)
            if val:
                parts.append("%d %s" %(len(val), key))
        line = ", ".join(parts)
        # XXX coloring
        self.write_sep("=", "%s in %.2f seconds" %(line, session_duration))

    def summary_deselected(self):
        if 'deselected' in self.stats:
            self.write_sep("=", "%d tests deselected by %r" %(
                len(self.stats['deselected']), self.config.option.keyword), bold=True)

    def summary_skips(self):
        if 'skipped' in self.stats:
            if 'failed' not in self.stats or self.config.option.showskipsummary:
                fskips = folded_skips(self.stats['skipped'])
                if fskips:
                    self.write_sep("_", "skipped test summary")
                    for num, fspath, lineno, reason in fskips:
                        self._tw.line("%s:%d: [%d] %s" %(fspath, lineno, num, reason))

    def summary_final_exc(self, excrepr):
        self.write_sep("!")
        if self.config.option.verbose:
            excrepr.toterminal(self._tw)
        else:
            excrepr.reprcrash.toterminal(self._tw)

    def out_hostinfo(self):
        self._tw.line("host 0: %s %s - Python %s" %
                       (py.std.sys.platform, 
                        py.std.sys.executable, 
                        repr_pythonversion()))

class CollectonlyReporter:
    INDENT = "  "

    def __init__(self, config, out=None):
        self.config = config 
        if out is None:
            out = py.std.sys.stdout
        self.out = py.io.TerminalWriter(out)
        self.indent = ""
        self._failed = []

    def outindent(self, line):
        self.out.line(self.indent + str(line))

    def pyevent_collectionstart(self, event):
        self.outindent(event.collector)
        self.indent += self.INDENT 
    
    def pyevent_itemstart(self, event):
        self.outindent(event.item)

    def pyevent_collectionreport(self, event):
        if not event.passed:
            self.outindent("!!! %s !!!" % event.longrepr.reprcrash.message)
            self._failed.append(event)
        self.indent = self.indent[:-len(self.INDENT)]

    def pyevent_testrunfinish(self, event):
        if self._failed:
            self.out.sep("!", "collection failures")
        for event in self._failed:
            event.toterminal(self.out)
                
def folded_skips(skipped):
    d = {}
    for event in skipped:
        entry = event.longrepr.reprcrash 
        key = entry.path, entry.lineno, entry.message
        d.setdefault(key, []).append(event)
    l = []
    for key, events in d.iteritems(): 
        l.append((len(events),) + key)
    return l 

def repr_pythonversion(v=None):
    if v is None:
        v = sys.version_info
    try:
        return "%s.%s.%s-%s-%s" % v
    except (TypeError, ValueError):
        return str(v)

# ===============================================================================
#
# plugin tests 
#
# ===============================================================================

from py.__.test import event
from py.__.test.runner import basic_run_report
from py.__.test.dsession.masterslave import makehostup

class TestTerminal:
    def test_hostup(self, testdir, linecomp):
        from py.__.execnet.gwmanage import GatewaySpec
        item = testdir.getitem("def test_func(): pass")
        rep = TerminalReporter(item.config, linecomp.stringio)
        rep.pyevent_hostup(makehostup())
        linecomp.assert_contains_lines([
            "*localhost %s %s - Python %s" %(sys.platform, 
            sys.executable, repr_pythonversion(sys.version_info))
        ])

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
        rep.config.bus.register(rep)
        rep.config.bus.notify("testrunstart", event.TestrunStart())
        
        for item in testdir.genitems([modcol]):
            ev = basic_run_report(item) 
            rep.config.bus.notify("itemtestreport", ev)
        linecomp.assert_contains_lines([
                "*test_pass_skip_fail.py .sF"
        ])
        rep.config.bus.notify("testrunfinish", event.TestrunFinish())
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
        rep.config.bus.register(rep)
        rep.config.bus.notify("testrunstart", event.TestrunStart())
        items = modcol.collect()
        for item in items:
            rep.config.bus.notify("itemstart", event.ItemStart(item))
            s = linecomp.stringio.getvalue().strip()
            assert s.endswith(item.name)
            rep.config.bus.notify("itemtestreport", basic_run_report(item))

        linecomp.assert_contains_lines([
            "*test_pass_skip_fail_verbose.py:2: *test_ok*PASS",
            "*test_pass_skip_fail_verbose.py:4: *test_skip*SKIP",
            "*test_pass_skip_fail_verbose.py:6: *test_func*FAIL",
        ])
        rep.config.bus.notify("testrunfinish", event.TestrunFinish())
        linecomp.assert_contains_lines([
            "    def test_func():",
            ">       assert 0",
            "E       assert 0",
        ])

    def test_collect_fail(self, testdir, linecomp):
        modcol = testdir.getmodulecol("import xyz")
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        rep.config.bus.register(rep)
        rep.config.bus.notify("testrunstart", event.TestrunStart())
        l = list(testdir.genitems([modcol]))
        assert len(l) == 0
        linecomp.assert_contains_lines([
            "*test_collect_fail.py F*"
        ])
        rep.config.bus.notify("testrunfinish", event.TestrunFinish())
        linecomp.assert_contains_lines([
            ">   import xyz",
            "E   ImportError: No module named xyz"
        ])

    def test_internalerror(self, testdir, linecomp):
        modcol = testdir.getmodulecol("def test_one(): pass")
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        excinfo = py.test.raises(ValueError, "raise ValueError('hello')")
        rep.pyevent_internalerror(event.InternalException(excinfo))
        linecomp.assert_contains_lines([
            "InternalException: >*raise ValueError*"
        ])

    def test_hostready_crash(self, testdir, linecomp):
        from py.__.execnet.gwmanage import GatewaySpec
        modcol = testdir.getmodulecol("""
            def test_one():
                pass
        """, configargs=("-v",))
        host1 = GatewaySpec("localhost")
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        rep.pyevent_hostgatewayready(event.HostGatewayReady(host1, None))
        linecomp.assert_contains_lines([
            "*HostGatewayReady*"
        ])
        rep.pyevent_hostdown(event.HostDown(host1, "myerror"))
        linecomp.assert_contains_lines([
            "*HostDown*myerror*", 
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

    def test_looponfailingreport(self, testdir, linecomp):
        modcol = testdir.getmodulecol("""
            def test_fail():
                assert 0
            def test_fail2():
                raise ValueError()
        """)
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        reports = [basic_run_report(x) for x in modcol.collect()]
        rep.pyevent_looponfailinginfo(event.LooponfailingInfo(reports, [modcol.config.topdir]))
        linecomp.assert_contains_lines([
            "*test_looponfailingreport.py:2: assert 0",
            "*test_looponfailingreport.py:4: ValueError*",
            "*waiting*", 
            "*%s*" % (modcol.config.topdir),
        ])

    def test_tb_option(self, testdir, linecomp):
        # XXX usage of testdir and event bus
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
            rep.config.bus.register(rep)
            rep.config.bus.notify("testrunstart", event.TestrunStart())
            rep.config.bus.notify("testrunstart", event.TestrunStart())
            for item in testdir.genitems([modcol]):
                rep.config.bus.notify("itemtestreport", basic_run_report(item))
            rep.config.bus.notify("testrunfinish", event.TestrunFinish())
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
        modcol = testdir.getmodulecol("""
            def test_foobar():
                pass
        """)
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        modcol.config.bus.register(rep)
        l = list(testdir.genitems([modcol]))
        assert len(l) == 1
        rep.config.bus.notify("itemstart", event.ItemStart(l[0]))
        linecomp.assert_contains_lines([
            "*test_show_path_before_running_test.py*"
        ])

    def pseudo_keyboard_interrupt(self, testdir, linecomp, verbose=False):
        modcol = testdir.getmodulecol("""
            def test_foobar():
                assert 0
            def test_spamegg():
                import py; py.test.skip('skip me please!')
            def test_interrupt_me():
                raise KeyboardInterrupt   # simulating the user
        """, configargs=("--showskipsummary",) + ("-v",)*verbose)
        rep = TerminalReporter(modcol.config, file=linecomp.stringio)
        modcol.config.bus.register(rep)
        bus = modcol.config.bus
        bus.notify("testrunstart", event.TestrunStart())
        try:
            for item in testdir.genitems([modcol]):
                bus.notify("itemtestreport", basic_run_report(item))
        except KeyboardInterrupt:
            excinfo = py.code.ExceptionInfo()
        else:
            py.test.fail("no KeyboardInterrupt??")
        s = linecomp.stringio.getvalue()
        if not verbose:
            assert s.find("_keyboard_interrupt.py Fs") != -1
        bus.notify("testrunfinish", event.TestrunFinish(exitstatus=2, excinfo=excinfo))
        text = linecomp.stringio.getvalue()
        linecomp.assert_contains_lines([
            "    def test_foobar():",
            ">       assert 0",
            "E       assert 0",
        ])
        assert "Skipped: 'skip me please!'" in text
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

        ev1 = event.CollectionReport(None, None)
        ev1.when = "execute"
        ev1.skipped = True
        ev1.longrepr = longrepr 
        
        ev2 = event.ItemTestReport(None, excinfo=longrepr)
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
        modcol.config.bus.register(rep)
        indent = rep.indent
        rep.config.bus.notify("collectionstart", event.CollectionStart(modcol))
        linecomp.assert_contains_lines([
           "<Module 'test_collectonly_basic.py'>"
        ])
        item = modcol.join("test_func")
        rep.config.bus.notify("itemstart", event.ItemStart(item))
        linecomp.assert_contains_lines([
           "  <Function 'test_func'>", 
        ])
        rep.config.bus.notify( "collectionreport", 
            event.CollectionReport(modcol, [], excinfo=None))
        assert rep.indent == indent 

    def test_collectonly_skipped_module(self, testdir, linecomp):
        modcol = testdir.getmodulecol(configargs=['--collectonly'], source="""
            import py
            py.test.skip("nomod")
        """)
        rep = CollectonlyReporter(modcol.config, out=linecomp.stringio)
        modcol.config.bus.register(rep)
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
        modcol.config.bus.register(rep)
        cols = list(testdir.genitems([modcol]))
        assert len(cols) == 0
        linecomp.assert_contains_lines("""
            <Module 'test_collectonly_failed_module.py'>
              !!! ValueError: 0 !!!
        """)

def test_repr_python_version():
    py.magic.patch(sys, 'version_info', (2, 5, 1, 'final', 0))
    try:
        assert repr_pythonversion() == "2.5.1-final-0"
        py.std.sys.version_info = x = (2,3)
        assert repr_pythonversion() == str(x) 
    finally: 
        py.magic.revert(sys, 'version_info') 

def test_generic(plugintester):
    plugintester.apicheck(TerminalPlugin)
    plugintester.apicheck(TerminalReporter)
    plugintester.apicheck(CollectonlyReporter)
