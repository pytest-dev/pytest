"""
Implements terminal reporting of the full testing process.

This is a good source for looking at the various reporting hooks.
"""
import py
import sys
import os

def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption('-v', '--verbose', action="count",
               dest="verbose", default=0, help="increase verbosity."),
    group._addoption('-r',
         action="store", dest="reportchars", default=None, metavar="chars",
         help="show extra test summary info as specified by chars (f)ailed, "
              "(s)skipped, (x)failed, (X)passed.")
    group._addoption('-l', '--showlocals',
         action="store_true", dest="showlocals", default=False,
         help="show locals in tracebacks (disabled by default).")
    group._addoption('--report',
         action="store", dest="report", default=None, metavar="opts",
         help="(deprecated, use -r)")
    group._addoption('--tb', metavar="style",
               action="store", dest="tbstyle", default='long',
               type="choice", choices=['long', 'short', 'no', 'line', 'native'],
               help="traceback print mode (long/short/line/no).")
    group._addoption('--fulltrace',
               action="store_true", dest="fulltrace", default=False,
               help="don't cut any tracebacks (default is to cut).")

def pytest_configure(config):
    if config.option.collectonly:
        reporter = CollectonlyReporter(config)
    else:
        reporter = TerminalReporter(config)
    config.pluginmanager.register(reporter, 'terminalreporter')

def getreportopt(config):
    reportopts = ""
    optvalue = config.getvalue("report")
    if optvalue:
        py.builtin.print_("DEPRECATED: use -r instead of --report option.",
            file=py.std.sys.stderr)
        if optvalue:
            for setting in optvalue.split(","):
                setting = setting.strip()
                if setting == "skipped":
                    reportopts += "s"
                elif setting == "xfailed":
                    reportopts += "x"
    reportchars = config.getvalue("reportchars")
    if reportchars:
        for char in reportchars:
            if char not in reportopts:
                reportopts += char
    return reportopts

def pytest_report_teststatus(report):
    if report.passed:
        letter = "."
    elif report.skipped:
        letter = "s"
    elif report.failed:
        letter = "F"
        if report.when != "call":
            letter = "f"
    return report.outcome, letter, report.outcome.upper()

class TerminalReporter:
    def __init__(self, config, file=None):
        self.config = config
        self.stats = {}
        self.curdir = py.path.local()
        if file is None:
            file = py.std.sys.stdout
            # we try hard to make printing resilient against 
            # later changes on FD level.
            if hasattr(os, 'dup') and hasattr(file, 'fileno'):
                try:
                    newfd = os.dup(file.fileno())
                except ValueError:
                    pass
                else:
                    file = os.fdopen(newfd, file.mode, 1)
        self._tw = py.io.TerminalWriter(file)
        self.currentfspath = None
        self.reportchars = getreportopt(config)

    def hasopt(self, char):
        char = {'xfailed': 'x', 'skipped': 's'}.get(char,char)
        return char in self.reportchars

    def write_fspath_result(self, fspath, res):
        if fspath != self.currentfspath:
            self.currentfspath = fspath
            fspath = self.curdir.bestrelpath(fspath)
            self._tw.line()
            relpath = self.curdir.bestrelpath(fspath)
            self._tw.write(relpath + " ")
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

    def pytest_internalerror(self, excrepr):
        for line in str(excrepr).split("\n"):
            self.write_line("INTERNALERROR> " + line)
        return 1

    def pytest_plugin_registered(self, plugin):
        if self.config.option.traceconfig:
            msg = "PLUGIN registered: %s" %(plugin,)
            # XXX this event may happen during setup/teardown time
            #     which unfortunately captures our output here
            #     which garbles our output if we use self.write_line
            self.write_line(msg)

    def pytest_trace(self, category, msg):
        if self.config.option.debug or \
           self.config.option.traceconfig and category.find("config") != -1:
            self.write_line("[%s] %s" %(category, msg))

    def pytest_deselected(self, items):
        self.stats.setdefault('deselected', []).extend(items)

    def pytest__teardown_final_logerror(self, report):
        self.stats.setdefault("error", []).append(report)

    def pytest_runtest_logstart(self, nodeid, location, fspath):
        # ensure that the path is printed before the
        # 1st test of a module starts running
        if self.config.option.verbose:
            line = self._locationline(fspath, *location)
            self.write_ensure_prefix(line, "")
        else:
            self.write_fspath_result(py.path.local(fspath), "")

    def pytest_runtest_logreport(self, report):
        rep = report
        res = self.config.hook.pytest_report_teststatus(report=rep)
        cat, letter, word = res
        self.stats.setdefault(cat, []).append(rep)
        if not letter and not word:
            # probably passed setup/teardown
            return
        if not self.config.option.verbose:
            if not hasattr(rep, 'node'):
                self.write_fspath_result(rep.fspath, letter)
            else:
                self._tw.write(letter)
        else:
            if isinstance(word, tuple):
                word, markup = word
            else:
                if rep.passed:
                    markup = {'green':True}
                elif rep.failed:
                    markup = {'red':True}
                elif rep.skipped:
                    markup = {'yellow':True}
            line = self._locationline(str(rep.fspath), *rep.location)
            if not hasattr(rep, 'node'):
                self.write_ensure_prefix(line, word, **markup)
                #self._tw.write(word, **markup)
            else:
                self.ensure_newline()
                if hasattr(rep, 'node'):
                    self._tw.write("[%s] " % rep.node.gateway.id)
                self._tw.write(word, **markup)
                self._tw.write(" " + line)
                self.currentfspath = -2

    def pytest_collectreport(self, report):
        if not report.passed:
            if report.failed:
                self.stats.setdefault("error", []).append(report)
                self.write_fspath_result(report.fspath, "E")
            elif report.skipped:
                self.stats.setdefault("skipped", []).append(report)
                self.write_fspath_result(report.fspath, "S")

    def pytest_sessionstart(self, session):
        self.write_sep("=", "test session starts", bold=True)
        self._sessionstarttime = py.std.time.time()
        verinfo = ".".join(map(str, sys.version_info[:3]))
        msg = "platform %s -- Python %s" % (sys.platform, verinfo)
        msg += " -- pytest-%s" % (py.__version__)
        if self.config.option.verbose or self.config.option.debug or \
           getattr(self.config.option, 'pastebin', None):
            msg += " -- " + str(sys.executable)
        self.write_line(msg)
        lines = self.config.hook.pytest_report_header(config=self.config)
        lines.reverse()
        for line in flatten(lines):
            self.write_line(line)

    def pytest_log_finishcollection(self):
        for i, testarg in enumerate(self.config.args):
            self.write_line("test path %d: %s" %(i+1, testarg))

    def pytest_sessionfinish(self, exitstatus, __multicall__):
        __multicall__.execute()
        self._tw.line("")
        if exitstatus in (0, 1, 2):
            self.summary_errors()
            self.summary_failures()
            self.config.hook.pytest_terminal_summary(terminalreporter=self)
        if exitstatus == 2:
            self._report_keyboardinterrupt()
        self.summary_deselected()
        self.summary_stats()

    def pytest_keyboard_interrupt(self, excinfo):
        self._keyboardinterrupt_memo = excinfo.getrepr(funcargs=True)

    def _report_keyboardinterrupt(self):
        excrepr = self._keyboardinterrupt_memo
        msg = excrepr.reprcrash.message
        self.write_sep("!", msg)
        if "KeyboardInterrupt" in msg:
            if self.config.getvalue("fulltrace"):
                excrepr.toterminal(self._tw)
            else:
                excrepr.reprcrash.toterminal(self._tw)

    def _locationline(self, collect_fspath, fspath, lineno, domain):
        if fspath and fspath != collect_fspath:
            fspath = "%s <- %s" % (
                self.curdir.bestrelpath(py.path.local(collect_fspath)),
                self.curdir.bestrelpath(py.path.local(fspath)))
        elif fspath:
            fspath = self.curdir.bestrelpath(py.path.local(fspath))
        if lineno is not None:
            lineno += 1
        if fspath and lineno and domain:
            line = "%(fspath)s:%(lineno)s: %(domain)s"
        elif fspath and domain:
            line = "%(fspath)s: %(domain)s"
        elif fspath and lineno:
            line = "%(fspath)s:%(lineno)s %(extrapath)s"
        else:
            line = "[nolocation]"
        return line % locals() + " "

    def _getfailureheadline(self, rep):
        if hasattr(rep, 'location'):
            fspath, lineno, domain = rep.location
            return domain
        else:
            return "test session" # XXX?

    def _getcrashline(self, rep):
        try:
            return str(rep.longrepr.reprcrash)
        except AttributeError:
            try:
                return str(rep.longrepr)[:50]
            except AttributeError:
                return ""

    #
    # summaries for sessionfinish
    #

    def summary_failures(self):
        tbstyle = self.config.getvalue("tbstyle")
        if 'failed' in self.stats and tbstyle != "no":
            self.write_sep("=", "FAILURES")
            for rep in self.stats['failed']:
                if tbstyle == "line":
                    line = self._getcrashline(rep)
                    self.write_line(line)
                else:
                    msg = self._getfailureheadline(rep)
                    self.write_sep("_", msg)
                    rep.toterminal(self._tw)

    def summary_errors(self):
        if 'error' in self.stats and self.config.option.tbstyle != "no":
            self.write_sep("=", "ERRORS")
            for rep in self.stats['error']:
                msg = self._getfailureheadline(rep)
                if not hasattr(rep, 'when'):
                    # collect
                    msg = "ERROR collecting " + msg
                elif rep.when == "setup":
                    msg = "ERROR at setup of " + msg
                elif rep.when == "teardown":
                    msg = "ERROR at teardown of " + msg
                self.write_sep("_", msg)
                rep.toterminal(self._tw)

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
        self.write_sep("=", "%s in %.2f seconds" %(line, session_duration), bold=True)

    def summary_deselected(self):
        if 'deselected' in self.stats:
            self.write_sep("=", "%d tests deselected by %r" %(
                len(self.stats['deselected']), self.config.option.keyword), bold=True)


class CollectonlyReporter:
    INDENT = "  "

    def __init__(self, config, out=None):
        self.config = config
        if out is None:
            out = py.std.sys.stdout
        self._tw = py.io.TerminalWriter(out)
        self.indent = ""
        self._failed = []

    def outindent(self, line):
        self._tw.line(self.indent + str(line))

    def pytest_internalerror(self, excrepr):
        for line in str(excrepr).split("\n"):
            self._tw.line("INTERNALERROR> " + line)

    def pytest_collectstart(self, collector):
        self.outindent(collector)
        self.indent += self.INDENT

    def pytest_log_itemcollect(self, item):
        self.outindent(item)

    def pytest_collectreport(self, report):
        if not report.passed:
            if hasattr(report.longrepr, 'reprcrash'):
                msg = report.longrepr.reprcrash.message
            else:
                # XXX unify (we have CollectErrorRepr here)
                msg = str(report.longrepr.longrepr)
            self.outindent("!!! %s !!!" % msg)
            #self.outindent("!!! error !!!")
            self._failed.append(report)
        self.indent = self.indent[:-len(self.INDENT)]

    def pytest_log_finishcollection(self):
        if self._failed:
            self._tw.sep("!", "collection failures")
        for rep in self._failed:
            rep.toterminal(self._tw)
        return self._failed and 1 or 0

def repr_pythonversion(v=None):
    if v is None:
        v = sys.version_info
    try:
        return "%s.%s.%s-%s-%s" % v
    except (TypeError, ValueError):
        return str(v)

def flatten(l):
    for x in l:
        if isinstance(x, (list, tuple)):
            for y in flatten(x):
                yield y
        else:
            yield x

