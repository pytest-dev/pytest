""" master code and test dispatching for 
    making 1-n master -> slave connection
    and test it locally. 
"""

import time, threading
import py, sys

if sys.platform == 'win32':
    py.test.skip("rsession is unsupported on Windows.")

from py.__.test.rsession.master import dispatch_loop, MasterNode
from py.__.test.rsession.slave import setup_slave 
from py.__.test.rsession.outcome import ReprOutcome, Outcome 
from py.__.test.rsession import repevent
from py.__.test.rsession.hostmanage import HostInfo

def setup_module(mod):
    # bind an empty config
    mod.tmpdir = tmpdir = py.test.ensuretemp(mod.__name__)
    # to avoid rsyncing
    config = py.test.config._reparse([tmpdir])
    config.option.dist_taskspernode = 10 
    mod.rootcol = config._getcollector(tmpdir)

class DummyGateway(object):
    def __init__(self):
        self.host = HostInfo("localhost")

class DummyChannel(object):
    def __init__(self):
        self.sent = []
        self.gateway = DummyGateway()

    def setcallback(self, func):
        self.callback = func 

    def send(self, item):
        assert py.std.marshal.dumps(item)
        self.sent.append(item)

class NonWorkingChannel(object):
    def setcallback(self, func):
        pass

    def send(self, item):
        raise IOError

    def _getremoteerror(self):
        return "blah"

class Item(py.test.collect.Item):
    def _get_collector_trail(self):
        return (self.name,)

def test_masternode():
    try:
        raise ValueError()
    except ValueError:
        excinfo = py.code.ExceptionInfo()
    
    ch = DummyChannel()
    reportlist = []
    mnode = MasterNode(ch, reportlist.append)
    mnode.send(Item("ok"))
    mnode.send(Item("notok"))
    ch.callback(Outcome().make_repr())
    ch.callback(Outcome(excinfo=excinfo).make_repr())
    assert len(reportlist) == 4
    received = [i for i in reportlist 
        if isinstance(i, repevent.ReceivedItemOutcome)]
    assert received[0].outcome.passed 
    assert not received[1].outcome.passed 

def test_masternode_nonworking_channel():
    ch = NonWorkingChannel()
    reportlist = []
    mnode = MasterNode(ch, reportlist.append)
    cap = py.io.StdCaptureFD()
    py.test.raises(IOError, 'mnode.send(Item("ok"))')
    out, err = cap.reset()
    assert out.find("blah") != -1

def test_sending_two_noes():
    # XXX fijal: this test previously tested that the second
    #     item result would not get send. why? did i miss
    #     something? 
    #     
    ch = DummyChannel()
    reportlist = []
    mnode = MasterNode(ch, reportlist.append)
    mnode.send(Item("ok"))
    mnode.send(Item("ok"))
    ch.callback(Outcome().make_repr())
    ch.callback(Outcome().make_repr())
    assert len(reportlist) == 4

def test_outcome_repr():
    out = ReprOutcome(Outcome(skipped=True).make_repr())
    s = repr(out)
    assert s.lower().find("skip") != -1

class DummyMasterNode(object):
    def __init__(self):
        self.pending = []
    
    def send(self, data):
        self.pending.append(data)

def test_dispatch_loop():
    masternodes = [DummyMasterNode(), DummyMasterNode()]
    itemgenerator = iter(range(100))
    shouldstop = lambda : False
    def waiter():
        for node in masternodes:
            node.pending.pop()
    dispatch_loop(masternodes, itemgenerator, shouldstop, waiter=waiter)

class TestSlave:
    def setup_class(cls):
        cls.tmpdir = tmpdir = py.test.ensuretemp(cls.__name__)
        cls.pkgpath = pkgpath = tmpdir.join("slavetestpkg")
        pkgpath.ensure("__init__.py")
        pkgpath.join("test_something.py").write(py.code.Source("""
            def funcpass(): 
                pass

            def funcfail():
                raise AssertionError("hello world")
        """))
        cls.config = py.test.config._reparse([tmpdir])
        assert cls.config.topdir == tmpdir
        cls.rootcol = cls.config._getcollector(tmpdir)

    def _gettrail(self, *names):
        item = self.rootcol._getitembynames(names)
        return self.config.get_collector_trail(item) 
        
    def test_slave_setup(self):
        py.test.skip("Doesn't work anymore")
        pkgname = self.pkgpath.basename
        host = HostInfo("localhost:%s" %(self.tmpdir,))
        host.initgateway()
        channel = setup_slave(host, self.config)
        spec = self._gettrail(pkgname, "test_something.py", "funcpass")
        print "sending", spec
        channel.send(spec)
        output = ReprOutcome(channel.receive())
        assert output.passed
        channel.send(42)
        channel.waitclose(10)
        host.gw.exit()

    def test_slave_running(self):
        py.test.skip("XXX test broken, needs refactoring")
        def simple_report(event):
            if not isinstance(event, repevent.ReceivedItemOutcome):
                return
            item = event.item
            if item.code.name == 'funcpass':
                assert event.outcome.passed
            else:
                assert not event.outcome.passed
        
        def open_gw():
            gw = py.execnet.PopenGateway()
            gw.host = HostInfo("localhost")
            gw.host.gw = gw
            config = py.test.config._reparse([tmpdir])
            channel = setup_slave(gw.host, config)
            mn = MasterNode(channel, simple_report, {})
            return mn
        
        master_nodes = [open_gw(), open_gw(), open_gw()]
        funcpass_item = rootcol._getitembynames(funcpass_spec)
        funcfail_item = rootcol._getitembynames(funcfail_spec)
        itemgenerator = iter([funcfail_item] + 
                             [funcpass_item] * 5 + [funcfail_item] * 5)
        shouldstop = lambda : False
        dispatch_loop(master_nodes, itemgenerator, shouldstop)

def test_slave_running_interrupted():
    py.test.skip("XXX test broken, needs refactoring")
    #def simple_report(event):
    #    if not isinstance(event, repevent.ReceivedItemOutcome):
    #        return
    #    item = event.item
    #    if item.code.name == 'funcpass':
    #        assert event.outcome.passed
    #    else:
    #        assert not event.outcome.passed
    reports = []
    
    def open_gw():
        gw = py.execnet.PopenGateway()
        gw.host = HostInfo("localhost")
        gw.host.gw = gw
        config = py.test.config._reparse([tmpdir])
        channel = setup_slave(gw.host, config)
        mn = MasterNode(channel, reports.append, {})
        return mn, gw, channel

    mn, gw, channel = open_gw()
    rootcol = py.test.collect.Directory(pkgdir)
    funchang_item = rootcol._getitembynames(funchang_spec)
    mn.send(funchang_item)
    mn.send(StopIteration)
    # XXX: We have to wait here a bit to make sure that it really did happen
    channel.waitclose(2)

