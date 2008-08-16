
import py
from py.__.test.dsession.masterslave import MasterNode
from py.__.test.dsession.hostmanage import Host 
from basetest import BasicRsessionTest
from py.__.test import event 

class TestMasterSlaveConnection(BasicRsessionTest): 
    def getevent(self, eventtype=event.ItemTestReport, timeout=2.0):
        events = []
        while 1:
            try:
                ev = self.queue.get(timeout=timeout)
            except py.std.Queue.Empty:
                print "node channel", self.node.channel
                print "remoteerror", self.node.channel._getremoteerror()
                print "seen events", events
                raise IOError("did not see %r events" % (eventtype))
            else:
                if isinstance(ev, eventtype):
                    return ev
                events.append(ev)

    def setup_method(self, method):
        super(TestMasterSlaveConnection, self).setup_method(method)
        self.queue = py.std.Queue.Queue()
        self.host = Host("localhost") 
        self.host.initgateway()
        self.node = MasterNode(self.host, self.session.config, 
                               self.queue.put)
        assert not self.node.channel.isclosed()
       
    def teardown_method(self, method):
        print "at teardown:", self.node.channel
        self.host.gw.exit()

    def test_crash_invalid_item(self):
        self.node.send(123) # invalid item 
        ev = self.getevent(event.HostDown)
        assert ev.host == self.host
        assert str(ev.error).find("AttributeError") != -1

    def test_crash_killed(self):
        if not hasattr(py.std.os, 'kill'):
            py.test.skip("no os.kill")
        item = self.getfunc("kill15")
        self.node.send(item) 
        ev = self.getevent(event.HostDown)
        assert ev.host == self.host
        assert str(ev.error).find("TERMINATED") != -1

    def test_node_down(self):
        self.node.shutdown()
        ev = self.getevent(event.HostDown)
        assert ev.host == self.host 
        assert not ev.error
        self.node.callback(self.node.ENDMARK)
        excinfo = py.test.raises(IOError, 
            "self.getevent(event.HostDown, timeout=0.01)")

    def test_send_on_closed_channel(self):
        item = self.getfunc("passed")
        self.node.channel.close()
        py.test.raises(IOError, "self.node.send(item)")
        #ev = self.getevent(event.InternalException)
        #assert ev.excinfo.errisinstance(IOError)

    def test_send_one(self):
        item = self.getfunc("passed")
        self.node.send(self.getfunc("passed"))
        ev = self.getevent()
        assert ev.passed 
        assert ev.colitem == item
        #assert event.item == item 
        #assert event.item is not item 

    def test_send_some(self):
        for outcome in "passed failed skipped".split():
            self.node.send(self.getfunc(outcome))
            ev = self.getevent()
            assert getattr(ev, outcome) 

    def test_send_list(self):
        l = []
        for outcome in "passed failed skipped".split():
            l.append(self.getfunc(outcome))
        self.node.sendlist(l)
        for outcome in "passed failed skipped".split():
            ev = self.getevent()
            assert getattr(ev, outcome) 
