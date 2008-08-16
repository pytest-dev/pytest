
""" --collectonly session, not to spread logic all over the place
"""
import py
from py.__.test.report.base import BaseReporter 
from py.__.test.outcome import Skipped as Skipped2
from py.__.test.outcome import Skipped

class CollectonlyReporter(BaseReporter):
    INDENT = "  "

    def __init__(self, config, out=None, bus=None):
        super(CollectonlyReporter, self).__init__(bus=bus)
        self.config = config
        if out is None:
            out = py.std.sys.stdout
        self.out = py.io.TerminalWriter(out)
        self.indent = ""
        self._failed = []

    def outindent(self, line):
        self.out.line(self.indent + str(line))

    def rep_CollectionStart(self, ev):
        self.outindent(ev.collector)
        self.indent += self.INDENT 
    
    def rep_ItemStart(self, event):
        self.outindent(event.item)

    def rep_CollectionReport(self, ev):
        super(CollectonlyReporter, self).rep_CollectionReport(ev)
        if ev.failed:
            self.outindent("!!! %s !!!" % ev.outcome.longrepr.reprcrash.message)
        elif ev.skipped:
            self.outindent("!!! %s !!!" % ev.outcome.longrepr.message)
        self.indent = self.indent[:-len(self.INDENT)]

    def rep_TestrunFinish(self, session):
        for ev in self._failed:
            ev.toterminal(self.out)
                
Reporter = CollectonlyReporter
