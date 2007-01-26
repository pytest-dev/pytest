""" master code and test dispatching for 
    making 1-n master -> slave connection
    and test it locally. 
"""

import time, threading
import py, sys

if sys.platform == 'win32':
    py.test.skip("rsession is unsupported on Windows.")

from py.__.test.rsession.master import dispatch_loop, setup_slave, MasterNode, randomgen
from py.__.test.rsession.outcome import ReprOutcome, Outcome 
from py.__.test.rsession.testing.test_slave import funcpass_spec, funcfail_spec, funchang_spec
from py.__.test.rsession import report
from py.__.test.rsession.hostmanage import HostInfo

def setup_module(mod):
    # bind an empty config
    config = py.test.config._reparse([])
    config._overwrite('dist_taskspernode', 10)
    mod.pkgdir = py.path.local(py.__file__).dirpath().dirpath()
    mod.rootcol = py.test.collect.Directory(mod.pkgdir)

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

class Item(py.test.Item):
    def get_collector_trail(self):
        return (self.name,)

def test_masternode():
    try:
        raise ValueError()
    except ValueError:
        excinfo = py.code.ExceptionInfo()
    
    ch = DummyChannel()
    reportlist = []
    mnode = MasterNode(ch, reportlist.append, {})
    mnode.send(Item("ok"))
    mnode.send(Item("notok"))
    ch.callback(Outcome().make_repr())
    ch.callback(Outcome(excinfo=excinfo).make_repr())
    assert len(reportlist) == 4
    received = [i for i in reportlist 
        if isinstance(i, report.ReceivedItemOutcome)]
    assert received[0].outcome.passed 
    assert not received[1].outcome.passed 

def test_unique_nodes():
    ch = DummyChannel()
    reportlist = []
    mnode = MasterNode(ch, reportlist.append, {})
    mnode.send(Item("ok"))
    mnode.send(Item("ok"))
    ch.callback(Outcome().make_repr())
    ch.callback(Outcome().make_repr())
    assert len(reportlist) == 3

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

def test_slave_setup():
    gw = py.execnet.PopenGateway()
    config = py.test.config._reparse([])
    channel = setup_slave(gw, pkgdir, config)
    spec = rootcol.getitembynames(funcpass_spec).get_collector_trail()
    channel.send(spec)
    output = ReprOutcome(channel.receive())
    assert output.passed
    channel.send(42)
    channel.waitclose(10)
    gw.exit()

def test_slave_running():
    def simple_report(event):
        if not isinstance(event, report.ReceivedItemOutcome):
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
        config = py.test.config._reparse([])
        channel = setup_slave(gw, pkgdir, config)
        mn = MasterNode(channel, simple_report, {})
        return mn
    
    master_nodes = [open_gw(), open_gw(), open_gw()]
    funcpass_item = rootcol.getitembynames(funcpass_spec)
    funcfail_item = rootcol.getitembynames(funcfail_spec)
    itemgenerator = iter([funcfail_item] + 
                         [funcpass_item] * 5 + [funcfail_item] * 5)
    shouldstop = lambda : False
    dispatch_loop(master_nodes, itemgenerator, shouldstop)

def test_slave_running_interrupted():
    #def simple_report(event):
    #    if not isinstance(event, report.ReceivedItemOutcome):
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
        config = py.test.config._reparse([])
        channel = setup_slave(gw, pkgdir, config)
        mn = MasterNode(channel, reports.append, {})
        return mn, gw, channel

    mn, gw, channel = open_gw()
    rootcol = py.test.collect.Directory(pkgdir)
    funchang_item = rootcol.getitembynames(funchang_spec)
    mn.send(funchang_item)
    mn.send(StopIteration)
    # XXX: We have to wait here a bit to make sure that it really did happen
    channel.waitclose(2)

def test_randomgen():
    d = {}
    gen = randomgen({1:True, 2:True, 3:True}, d)
    for i in range(100):
        assert gen.next() in [1,2,3]
    d[3] = True
    for i in range(100):
        assert gen.next() in [1,2]
    d[2] = True
    d[1] = True
    py.test.raises(StopIteration, "gen.next()")

