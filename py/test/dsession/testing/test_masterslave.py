
import py
from py.__.test.dsession.masterslave import MasterNode
from py.__.test.dsession.hostmanage import Host
from py.__.test import event 
from py.__.test.testing import suptest

class TestMasterSlaveConnection(suptest.InlineCollection):
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
        self.makepyfile(__init__="")
        self.config = self.parseconfig(self.tmpdir)
        self.queue = py.std.Queue.Queue()
        self.host = Host("localhost") 
        self.host.initgateway()
        self.node = MasterNode(self.host, self.config, self.queue.put)
        assert not self.node.channel.isclosed()

    def getitem(self, source):
        kw = {"test_" + self.tmpdir.basename: py.code.Source(source).strip()}
        path = self.makepyfile(**kw)
        fscol = self.config.getfsnode(path)
        return fscol.collect_by_name("test_func")

    def getitems(self, source):
        kw = {"test_" + self.tmpdir.basename: py.code.Source(source).strip()}
        path = self.makepyfile(**kw)
        fscol = self.config.getfsnode(path)
        return fscol.collect()
       
    def teardown_method(self, method):
        print "at teardown:", self.node.channel
        #if not self.node.channel.isclosed():
        #    self.node.shutdown()
        self.host.gw.exit()

    def test_crash_invalid_item(self):
        self.node.send(123) # invalid item 
        ev = self.getevent(event.HostDown)
        assert ev.host == self.host
        assert str(ev.error).find("AttributeError") != -1

    def test_crash_killed(self):
        if not hasattr(py.std.os, 'kill'):
            py.test.skip("no os.kill")
        item = self.getitem("""
            def test_func():
                import os
                os.kill(os.getpid(), 15)
        """)
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
        item = self.getitem("def test_func(): pass")
        self.node.channel.close()
        py.test.raises(IOError, "self.node.send(item)")
        #ev = self.getevent(event.InternalException)
        #assert ev.excinfo.errisinstance(IOError)

    def test_send_one(self):
        item = self.getitem("def test_func(): pass")
        self.node.send(item)
        ev = self.getevent()
        assert ev.passed 
        assert ev.colitem == item
        #assert event.item == item 
        #assert event.item is not item 

    def test_send_some(self):
        items = self.getitems("""
            def test_pass(): 
                pass
            def test_fail():
                assert 0
            def test_skip():
                import py
                py.test.skip("x")
        """)
        for item in items:
            self.node.send(item)
        for outcome in "passed failed skipped".split():
            ev = self.getevent()
            assert getattr(ev, outcome) 

        self.node.sendlist(items)
        for outcome in "passed failed skipped".split():
            ev = self.getevent()
            assert getattr(ev, outcome) 
