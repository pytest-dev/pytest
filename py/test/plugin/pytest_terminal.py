"""
Implements terminal reporting of the full testing process.

This is a good source for looking at the various reporting hooks. 
"""
import py
import sys

def pytest_addoption(parser):
    group = parser.getgroup("debugconfig")
    group.addoption('--collectonly',
        action="store_true", dest="collectonly",
        help="only collect tests, don't execute them."),
    group.addoption('--traceconfig',
               action="store_true", dest="traceconfig", default=False,
               help="trace considerations of conftest.py files."),
    group._addoption('--nomagic',
               action="store_true", dest="nomagic", default=False,
               help="don't reinterpret asserts, no traceback cutting. ")
    group._addoption('--fulltrace',
               action="store_true", dest="fulltrace", default=False,
               help="don't cut any tracebacks (default is to cut).")
    group.addoption('--debug',
               action="store_true", dest="debug", default=False,
               help="generate and show debugging information.")

def pytest_configure(config):
    if config.option.collectonly:
        reporter = CollectonlyReporter(config)
    else:
        reporter = TerminalReporter(config)
    # XXX see remote.py's XXX 
    for attr in 'pytest_terminal_hasmarkup', 'pytest_terminal_fullwidth':
        if hasattr(config, attr):
            #print "SETTING TERMINAL OPTIONS", attr, getattr(config, attr)
            name = attr.split("_")[-1]
            assert hasattr(self.reporter._tw, name), name
            setattr(reporter._tw, name, getattr(config, attr))
    config.pluginmanager.register(reporter, 'terminalreporter')

class TerminalReporter:
    def __init__(self, config, file=None):
        self.config = config 
        self.stats = {}       
        self.curdir = py.path.local()
        if file is None:
            file = py.std.sys.stdout
        self._tw = py.io.TerminalWriter(file)
        self.currentfspath = None 
        self.gateway2info = {}

    def write_fspath_result(self, fspath, res):
        fspath = self.curdir.bestrelpath(fspath)
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

    def getcategoryletterword(self, rep):
        res = self.config.hook.pytest_report_teststatus(report=rep)
        if res:
            return res
        for cat in 'skipped failed passed ???'.split():
            if getattr(rep, cat, None):
                break 
        return cat, self.getoutcomeletter(rep), self.getoutcomeword(rep)

    def getoutcomeletter(self, rep):
        return rep.shortrepr 

    def getoutcomeword(self, rep):
        if rep.passed: 
            return "PASS", dict(green=True)
        elif rep.failed: 
            return "FAIL", dict(red=True)
        elif rep.skipped: 
            return "SKIP"
        else: 
            return "???", dict(red=True)

    def pytest_internalerror(self, excrepr):
        for line in str(excrepr).split("\n"):
            self.write_line("INTERNALERROR> " + line)

    def pyexecnet_gwmanage_newgateway(self, gateway, platinfo):
        #self.write_line("%s instantiated gateway from spec %r" %(gateway.id, gateway.spec._spec))
        d = {}
        d['version'] = repr_pythonversion(platinfo.version_info)
        d['id'] = gateway.id
        d['spec'] = gateway.spec._spec 
        d['platform'] = platinfo.platform 
        if self.config.option.verbose:
            d['extra'] = "- " + platinfo.executable
        else:
            d['extra'] = ""
        d['cwd'] = platinfo.cwd
        infoline = ("%(id)s %(spec)s -- platform %(platform)s, "
                        "Python %(version)s "
                        "cwd: %(cwd)s"
                        "%(extra)s" % d)
        self.write_line(infoline)
        self.gateway2info[gateway] = infoline

    def pyexecnet_gwmanage_rsyncstart(self, source, gateways):
        targets = ", ".join([gw.id for gw in gateways])
        msg = "rsyncstart: %s -> %s" %(source, targets)
        if not self.config.option.verbose:
            msg += " # use --verbose to see rsync progress"
        self.write_line(msg)

    def pyexecnet_gwmanage_rsyncfinish(self, source, gateways):
        targets = ", ".join([gw.id for gw in gateways])
        self.write_line("rsyncfinish: %s -> %s" %(source, targets))

    def pytest_plugin_registered(self, plugin):
        if self.config.option.traceconfig: 
            msg = "PLUGIN registered: %s" %(plugin,)
            # XXX this event may happen during setup/teardown time 
            #     which unfortunately captures our output here 
            #     which garbles our output if we use self.write_line 
            self.write_line(msg)

    def pytest_testnodeready(self, node):
        self.write_line("%s txnode ready to receive tests" %(node.gateway.id,))

    def pytest_testnodedown(self, node, error):
        if error:
            self.write_line("%s node down, error: %s" %(node.gateway.id, error))

    def pytest_trace(self, category, msg):
        if self.config.option.debug or \
           self.config.option.traceconfig and category.find("config") != -1:
            self.write_line("[%s] %s" %(category, msg))

    def pytest_rescheduleitems(self, items):
        if self.config.option.debug:
            self.write_sep("!", "RESCHEDULING %s " %(items,))

    def pytest_deselected(self, items):
        self.stats.setdefault('deselected', []).append(items)

    def pytest_itemstart(self, item, node=None):
        if self.config.option.dist != "no":
            # for dist-testing situations itemstart means we 
            # queued the item for sending, not interesting (unless debugging) 
            if self.config.option.debug:
                line = self._reportinfoline(item)
                extra = ""
                if node:
                    extra = "-> " + str(node.gateway.id)
                self.write_ensure_prefix(line, extra)
        else:
            if self.config.option.verbose:
                line = self._reportinfoline(item)
                self.write_ensure_prefix(line, "") 
            else:
                # ensure that the path is printed before the 
                # 1st test of a module starts running

                self.write_fspath_result(self._getfspath(item), "")

    def pytest__teardown_final_logerror(self, report):
        self.stats.setdefault("error", []).append(report)
 
    def pytest_runtest_logreport(self, report):
        rep = report
        cat, letter, word = self.getcategoryletterword(rep)
        if not letter and not word:
            # probably passed setup/teardown
            return
        if isinstance(word, tuple):
            word, markup = word
        else:
            markup = {}
        self.stats.setdefault(cat, []).append(rep)
        if not self.config.option.verbose:
            self.write_fspath_result(self._getfspath(rep.item), letter)
        else:
            line = self._reportinfoline(rep.item)
            if not hasattr(rep, 'node'):
                self.write_ensure_prefix(line, word, **markup)
            else:
                self.ensure_newline()
                if hasattr(rep, 'node'):
                    self._tw.write("%s " % rep.node.gateway.id)
                self._tw.write(word, **markup)
                self._tw.write(" " + line)
                self.currentfspath = -2

    def pytest_collectreport(self, report):
        if not report.passed:
            if report.failed:
                self.stats.setdefault("error", []).append(report)
                msg = report.longrepr.reprcrash.message 
                self.write_fspath_result(report.collector.fspath, "E")
            elif report.skipped:
                self.stats.setdefault("skipped", []).append(report)
                self.write_fspath_result(report.collector.fspath, "S")

    def pytest_sessionstart(self, session):
        self.write_sep("=", "test session starts", bold=True)
        self._sessionstarttime = py.std.time.time()

        verinfo = ".".join(map(str, sys.version_info[:3]))
        msg = "python: platform %s -- Python %s" % (sys.platform, verinfo)
        if self.config.option.verbose or self.config.option.debug or getattr(self.config.option, 'pastebin', None):
            msg += " -- pytest-%s" % (py.__version__)
            msg += " -- " + str(sys.executable)
        self.write_line(msg)

        if self.config.option.debug or self.config.option.traceconfig:
            self.write_line("using py lib: %s" % (py.path.local(py.__file__).dirpath()))
        if self.config.option.traceconfig:
            plugins = []
            for plugin in self.config.pluginmanager.comregistry:
                name = getattr(plugin, '__name__', None)
                if name is None:
                    name = plugin.__class__.__name__
                plugins.append(name)
            plugins = ", ".join(plugins) 
            self.write_line("active plugins: %s" %(plugins,))
        for i, testarg in enumerate(self.config.args):
            self.write_line("test object %d: %s" %(i+1, testarg))

    def pytest_sessionfinish(self, exitstatus, __multicall__):
        __multicall__.execute() 
        self._tw.line("")
        if exitstatus in (0, 1, 2):
            self.summary_errors()
            self.summary_failures()
            self.summary_skips()
            self.config.hook.pytest_terminal_summary(terminalreporter=self)
        if exitstatus == 2:
            self._report_keyboardinterrupt()
        self.summary_deselected()
        self.summary_stats()

    def pytest_keyboard_interrupt(self, excinfo):
        self._keyboardinterrupt_memo = excinfo.getrepr()

    def _report_keyboardinterrupt(self):
        self.write_sep("!", "KEYBOARD INTERRUPT")
        excrepr = self._keyboardinterrupt_memo
        if self.config.option.verbose:
            excrepr.toterminal(self._tw)
        else:
            excrepr.reprcrash.toterminal(self._tw)

    def pytest_looponfailinfo(self, failreports, rootdirs):
        if failreports:
            self.write_sep("#", "LOOPONFAILING", red=True)
            for report in failreports:
                try:
                    loc = report.longrepr.reprcrash
                except AttributeError:
                    loc = str(report.longrepr)[:50]
                self.write_line(loc, red=True)
        self.write_sep("#", "waiting for changes")
        for rootdir in rootdirs:
            self.write_line("### Watching:   %s" %(rootdir,), bold=True)

    def _reportinfoline(self, item):
        collect_fspath = self._getfspath(item)
        fspath, lineno, msg = self._getreportinfo(item)
        if fspath and fspath != collect_fspath:
            fspath = "%s <- %s" % (
                self.curdir.bestrelpath(collect_fspath),
                self.curdir.bestrelpath(fspath))
        elif fspath:
            fspath = self.curdir.bestrelpath(fspath)
        if lineno is not None:
            lineno += 1
        if fspath and lineno and msg:
            line = "%(fspath)s:%(lineno)s: %(msg)s"
        elif fspath and msg:
            line = "%(fspath)s: %(msg)s"
        elif fspath and lineno:
            line = "%(fspath)s:%(lineno)s %(extrapath)s"
        else:
            line = "[noreportinfo]"
        return line % locals() + " "
        
    def _getfailureheadline(self, rep):
        if hasattr(rep, "collector"):
            return str(rep.collector.fspath)
        elif hasattr(rep, 'item'):
            fspath, lineno, msg = self._getreportinfo(rep.item)
            return msg
        else:
            return "test session" 

    def _getreportinfo(self, item):
        try:
            return item.__reportinfo
        except AttributeError:
            pass
        reportinfo = item.config.hook.pytest_report_iteminfo(item=item)
        # cache on item
        item.__reportinfo = reportinfo
        return reportinfo

    def _getfspath(self, item):
        try:
            return item.fspath
        except AttributeError:
            fspath, lineno, msg = self._getreportinfo(item)
            return fspath

    #
    # summaries for sessionfinish 
    #

    def summary_failures(self):
        if 'failed' in self.stats and self.config.option.tbstyle != "no":
            self.write_sep("=", "FAILURES")
            for rep in self.stats['failed']:
                msg = self._getfailureheadline(rep)
                self.write_sep("_", msg)
                self.write_platinfo(rep)
                rep.toterminal(self._tw)

    def summary_errors(self):
        if 'error' in self.stats and self.config.option.tbstyle != "no":
            self.write_sep("=", "ERRORS")
            for rep in self.stats['error']:
                msg = self._getfailureheadline(rep)
                if not hasattr(rep, 'when'):
                    # collect
                    msg = "ERROR during collection " + msg
                elif rep.when == "setup":
                    msg = "ERROR at setup of " + msg 
                elif rep.when == "teardown":
                    msg = "ERROR at teardown of " + msg 
                self.write_sep("_", msg)
                self.write_platinfo(rep)
                rep.toterminal(self._tw)

    def write_platinfo(self, rep):
        if hasattr(rep, 'node'):
            self.write_line(self.gateway2info.get(
                rep.node.gateway, 
                "node %r (platinfo not found? strange)")
                    [:self._tw.fullwidth-1])

    def summary_stats(self):
        session_duration = py.std.time.time() - self._sessionstarttime

        keys = "failed passed skipped deselected".split()
        for key in self.stats.keys():
            if key not in keys:
                keys.append(key)
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
            if 'failed' not in self.stats: #  or self.config.option.showskipsummary:
                fskips = folded_skips(self.stats['skipped'])
                if fskips:
                    self.write_sep("_", "skipped test summary")
                    for num, fspath, lineno, reason in fskips:
                        self._tw.line("%s:%d: [%d] %s" %(fspath, lineno, num, reason))

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

    def pytest_internalerror(self, excrepr):
        for line in str(excrepr).split("\n"):
            self.out.line("INTERNALERROR> " + line)

    def pytest_collectstart(self, collector):
        self.outindent(collector)
        self.indent += self.INDENT 
    
    def pytest_itemstart(self, item, node=None):
        self.outindent(item)

    def pytest_collectreport(self, report):
        if not report.passed:
            self.outindent("!!! %s !!!" % report.longrepr.reprcrash.message)
            self._failed.append(report)
        self.indent = self.indent[:-len(self.INDENT)]

    def pytest_sessionfinish(self, session, exitstatus):
        if self._failed:
            self.out.sep("!", "collection failures")
        for rep in self._failed:
            rep.toterminal(self.out)
                
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

