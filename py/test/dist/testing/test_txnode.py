
import py
from py.__.test.dist.txnode import TXNode

class EventQueue:
    def __init__(self, registry, queue=None):
        if queue is None:
            queue = py.std.Queue.Queue()
        self.queue = queue
        registry.register(self)

    def geteventargs(self, eventname, timeout=2.0):
        events = []
        while 1:
            try:
                eventcall = self.queue.get(timeout=timeout)
            except py.std.Queue.Empty:
                #print "node channel", self.node.channel
                #print "remoteerror", self.node.channel._getremoteerror()
                py.builtin.print_("seen events", events)
                raise IOError("did not see %r events" % (eventname))
            else:
                name, args, kwargs = eventcall 
                assert isinstance(name, str)
                if name == eventname:
                    if args:
                        return args
                    return kwargs
                events.append(name)
                if name == "pytest_internalerror":
                    py.builtin.print_(str(kwargs["excrepr"]))

class MySetup:
    def __init__(self, request):
        self.id = 0
        self.request = request

    def geteventargs(self, eventname, timeout=2.0):
        eq = EventQueue(self.config.pluginmanager, self.queue)
        return eq.geteventargs(eventname, timeout=timeout)

    def makenode(self, config=None):
        if config is None:
            config = py.test.config._reparse([])
        self.config = config
        self.queue = py.std.Queue.Queue()
        self.xspec = py.execnet.XSpec("popen")
        self.gateway = py.execnet.makegateway(self.xspec)
        self.id += 1
        self.gateway.id = str(self.id)
        self.node = TXNode(self.gateway, self.config, putevent=self.queue.put)
        assert not self.node.channel.isclosed()
        return self.node 

    def xfinalize(self):
        if hasattr(self, 'node'):
            gw = self.node.gateway
            py.builtin.print_("exiting:", gw)
            gw.exit()

def pytest_funcarg__mysetup(request):
    mysetup = MySetup(request)
    #pyfuncitem.addfinalizer(mysetup.finalize)
    return mysetup

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
        kwargs = mysetup.geteventargs("pytest_testnodedown")
        assert kwargs['node'] is node 
        assert str(kwargs['error']).find("AttributeError") != -1

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
        kwargs = mysetup.geteventargs("pytest_testnodedown")
        assert kwargs['node'] is node 
        assert str(kwargs['error']).find("Not properly terminated") != -1

    def test_node_down(self, mysetup):
        node = mysetup.makenode()
        node.shutdown()
        kwargs = mysetup.geteventargs("pytest_testnodedown")
        assert kwargs['node'] is node 
        assert not kwargs['error']
        node.callback(node.ENDMARK)
        excinfo = py.test.raises(IOError, 
            "mysetup.geteventargs('testnodedown', timeout=0.01)")

    def test_send_on_closed_channel(self, testdir, mysetup):
        item = testdir.getitem("def test_func(): pass")
        node = mysetup.makenode(item.config)
        node.channel.close()
        py.test.raises(IOError, "node.send(item)")
        #ev = self.getcalls(pytest_internalerror)
        #assert ev.excinfo.errisinstance(IOError)

    def test_send_one(self, testdir, mysetup):
        item = testdir.getitem("def test_func(): pass")
        node = mysetup.makenode(item.config)
        node.send(item)
        kwargs = mysetup.geteventargs("pytest_runtest_logreport")
        rep = kwargs['report'] 
        assert rep.passed 
        py.builtin.print_(rep)
        assert rep.item == item

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
            kwargs = mysetup.geteventargs("pytest_runtest_logreport")
            report = kwargs['report']
            assert getattr(report, outcome) 

        node.sendlist(items)
        for outcome in "passed failed skipped".split():
            rep = mysetup.geteventargs("pytest_runtest_logreport")['report']
            assert getattr(rep, outcome) 
