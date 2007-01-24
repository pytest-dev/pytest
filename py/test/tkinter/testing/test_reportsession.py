
import py
from py.__.test.tkinter import reportsession 
from py.__.test.tkinter.util import Status, TestReport, Null
ReportSession = reportsession.ReportSession

class TestReportSession:

    class ChannelMock:

        def __init__(self, receinvelist = []):
            self.reset(receinvelist)

        def reset(self, receivelist = []):
            self.receivelist = receivelist
            self.sendlist = []

        def send(self, obj):
            self.sendlist.append(obj)

        def receive(self):
            return self.receivelist.pop(0)
        
    def setup_method(self, method):
        self.channel = self.ChannelMock()
        self.session = ReportSession(Null(), self.channel)
        self.collitems = [Null(), Null()]
    
    def test_header_sends_report_with_id_root(self):
        self.session.header(self.collitems)
        
        assert self.channel.sendlist != []
        report = TestReport.fromChannel(self.channel.sendlist[0])
        assert report.status == Status.NotExecuted()
        assert report.id == TestReport.root_id
        assert report.label == 'Root'

    def test_footer_sends_report_and_None(self):
        self.session.header(self.collitems)
        self.session.footer(self.collitems)

        assert self.channel.sendlist != []
        assert self.channel.sendlist[-1] is None
        report = TestReport.fromChannel(self.channel.sendlist[-2])
        assert report.status == Status.NotExecuted()
        assert report.id == TestReport.root_id

##     def test_status_is_passed_to_root(self):
##         self.session.header(self.collitems)
##         self.session.start(self.collitems[0])
##         self.session.finish(self.collitems[0], py.test.collect.Collector.Failed())
##         self.session.footer(self.collitems)

##         assert self.channel.sendlist[-1] is None
##         assert self.channel.sendlist.pop() is None

##         report = TestReport.fromChannel(self.channel.sendlist[-1])
##         assert report.name == 'Root'
##         assert report.status == Status.Failed()

 

