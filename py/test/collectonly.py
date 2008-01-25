
""" --collectonly session, not to spread logic all over the place
"""

import py
from py.__.test.session import Session
from py.__.test.reporter import LocalReporter

class CollectReporter(LocalReporter):
    def __init__(self, *args, **kwds):
        super(LocalReporter, self).__init__(*args, **kwds)
        self.indent = 0
    
    def report_ReceivedItemOutcome(self, event):
        pass

    def report_ItemStart(self, event):
        self.out.line(" " * self.indent + str(event.item))
        self.indent += 2

    def report_ItemFinish(self, event):
        self.indent -= 2

    def report_FailedTryiter(self, event):
        self.out.line(" " * self.indent + "- FAILED TO LOAD MODULE -")

    def report_SkippedTryiter(self, event):
        self.out.line(" " * self.indent + "- skipped -")

    def summary(self):
        self.out.sep("=", "Total time: %.1f" % (self.timeend - self.timestart))

class CollectSession(Session):
    reporterclass = CollectReporter
    
    def run(self, item):
        pass
