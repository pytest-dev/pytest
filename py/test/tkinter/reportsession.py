'''GuiSession builds TestReport instances and sends them to tkgui.Manager'''
import py
from util import TestReport
from py.__.test.session import Session

class TkinterSession(Session):

    def __init__(self, config = None, channel = None):
        super(ReportSession, self).__init__(config)
        self.channel = channel
        self.reportlist = []
        
    def header(self, colitems):
        super(ReportSession, self).header(colitems)
        report = TestReport()
        report.settime()
        self.reportlist = [report]
        self.sendreport(report)
        
    def footer(self, colitems):
        super(ReportSession, self).footer(colitems)
        report = self.reportlist.pop()
        report.settime()
        self.sendreport(report)
        self.channel.send(None)

    def start(self, colitem):
        super(ReportSession, self).start(colitem)
        report = TestReport()
        report.start(colitem)
        self.reportlist.append(report)
        self.sendreport(report)

    def finish(self, colitem, outcome):
        super(ReportSession, self).finish(colitem, outcome)
        colitem.finishcapture()
        colitem.finishcapture()
        report = self.reportlist.pop()
        report.finish(colitem, outcome, self.config)
        self.reportlist[-1].status.update(report.status)
        self.sendreport(report)
        #py.std.time.sleep(0.5)
        
    def sendreport(self, report):
        self.channel.send(report.to_channel())

ReportSession = TkinterSession

