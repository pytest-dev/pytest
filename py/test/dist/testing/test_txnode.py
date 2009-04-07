
import py
from py.__.test.dist.txnode import TXNode

class EventQueue:
    def __init__(self, bus, queue=None):
        if queue is None:
            queue = py.std.Queue.Queue()
        self.queue = queue
        bus.register(self)

    def pyevent(self, eventname, args, kwargs):
        self.queue.put((eventname, args, kwargs))

    def geteventargs(self, eventname, timeout=2.0):
        events = []
        while 1:
            try:
                eventcall = self.queue.get(timeout=timeout)
            except py.std.Queue.Empty:
                #print "node channel", self.node.channel
                #print "remoteerror", self.node.channel._getremoteerror()
                print "seen events", events
                raise IOError("did not see %r events" % (eventname))
            else:
                name, args, kwargs = eventcall 
                assert isinstance(name, str)
                if name == eventname:
                    return args
                events.append(name)
                if name == "internalerror":
                    print str(kwargs["excrepr"])

class MySetup:
    def __init__(self, pyfuncitem):
        self.pyfuncitem = pyfuncitem

    def geteventargs(self, eventname, timeout=2.0):
        eq = EventQueue(self.config.bus, self.queue)
        return eq.geteventargs(eventname, timeout=timeout)

    def makenode(self, config=None):
        if config is None:
            config = py.test.config._reparse([])
        self.config = config
        self.queue = py.std.Queue.Queue()
        self.xspec = py.execnet.XSpec("popen")
        self.gateway = py.execnet.makegateway(self.xspec)
        self.node = TXNode(self.gateway, self.config, putevent=self.queue.put)
        assert not self.node.channel.isclosed()
        return self.node 

    def xfinalize(self):
        if hasattr(self, 'node'):
            gw = self.node.gateway
            print "exiting:", gw
            gw.exit()

def pytest_funcarg__mysetup(pyfuncitem):
    mysetup = MySetup(pyfuncitem)
    #pyfuncitem.addfinalizer(mysetup.finalize)
    return mysetup

def pytest_funcarg__testdir(__call__, pyfuncitem):
    # decorate to make us always change to testdir
    testdir = __call__.execute(firstresult=True)
    testdir.chdir()
    return testdir 

def test_node_hash_equality(mysetup):
    node = mysetup.makenode()
    node2 = mysetup.makenode()
    assert node != node2
    assert node == node
    assert not (node != node)

class TestMasterSlaveConnection:
    def test_crash_invalid_item(self, mysetup):
        node = mysetup.makenode()
        node.send(123) # invalid item 
        n, error = mysetup.geteventargs("testnodedown")
        assert n is node 
        assert str(error).find("AttributeError") != -1

    def test_crash_killed(self, testdir, mysetup):
        if not hasattr(py.std.os, 'kill'):
            py.test.skip("no os.kill")
        item = testdir.getitem("""
            def test_func():
                import os
                os.kill(os.getpid(), 15)
        """)
        node = mysetup.makenode(item.config)
        node.send(item) 
        n, error = mysetup.geteventargs("testnodedown")
        assert n is node 
        assert str(error).find("Not properly terminated") != -1

    def test_node_down(self, mysetup):
        node = mysetup.makenode()
        node.shutdown()
        n, error = mysetup.geteventargs("testnodedown")
        assert n is node 
        assert not error
        node.callback(node.ENDMARK)
        excinfo = py.test.raises(IOError, 
            "mysetup.geteventargs('testnodedown', timeout=0.01)")

    def test_send_on_closed_channel(self, testdir, mysetup):
        item = testdir.getitem("def test_func(): pass")
        node = mysetup.makenode(item.config)
        node.channel.close()
        py.test.raises(IOError, "node.send(item)")
        #ev = self.getcalls("internalerror")
        #assert ev.excinfo.errisinstance(IOError)

    def test_send_one(self, testdir, mysetup):
        item = testdir.getitem("def test_func(): pass")
        node = mysetup.makenode(item.config)
        node.send(item)
        ev, = mysetup.geteventargs("itemtestreport")
        assert ev.passed 
        assert ev.colitem == item
        #assert event.item == item 
        #assert event.item is not item 

    def test_send_some(self, testdir, mysetup):
        items = testdir.getitems("""
            def test_pass(): 
                pass
            def test_fail():
                assert 0
            def test_skip():
                import py
                py.test.skip("x")
        """)
        node = mysetup.makenode(items[0].config)
        for item in items:
            node.send(item)
        for outcome in "passed failed skipped".split():
            ev, = mysetup.geteventargs("itemtestreport")
            assert getattr(ev, outcome) 

        node.sendlist(items)
        for outcome in "passed failed skipped".split():
            ev, = mysetup.geteventargs("itemtestreport")
            assert getattr(ev, outcome) 
