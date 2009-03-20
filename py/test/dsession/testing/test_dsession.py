from py.__.test.dsession.dsession import DSession
from py.__.test.dsession.masterslave import maketestnodeready
from py.__.test.runner import basic_collect_report 
from py.__.test import event
from py.__.test import outcome
import py

def run(item):
    runner = item._getrunner()
    return runner(item)

class MockNode:
    def __init__(self):
        self.sent = []

    def sendlist(self, items):
        self.sent.append(items)

    def shutdown(self):
        self._shutdown=True

def dumpqueue(queue):
    while queue.qsize():
        print queue.get()

class TestDSession:
    def test_fixoptions(self, testdir):
        config = testdir.parseconfig("--exec=xxx")
        config.pytestplugins.do_configure(config)
        config.initsession().fixoptions()
        assert config.option.numprocesses == 1
        config = testdir.parseconfig("--exec=xxx", '-n3')
        config.initsession().fixoptions()
        assert config.option.numprocesses == 3

    def test_add_remove_host(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        rep = run(item)
        session = DSession(item.config)
        host = py.execnet.XSpec("popen")
        host.node = MockNode()
        assert not session.host2pending
        session.addhost(host)
        assert len(session.host2pending) == 1
        session.senditems([item])
        pending = session.removehost(host)
        assert pending == [item]
        assert item not in session.item2host
        l = session.removehost(host)
        assert not l 

    def test_senditems_removeitems(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        rep = run(item)
        session = DSession(item.config)
        host = py.execnet.XSpec("popen")
        host.node = MockNode()
        session.addhost(host)
        session.senditems([item])  
        assert session.host2pending[host] == [item]
        assert session.item2host[item] == host
        session.removeitem(item)
        assert not session.host2pending[host] 
        assert not session.item2host

    def test_triggertesting_collect(self, testdir):
        modcol = testdir.getmodulecol("""
            def test_func():
                pass
        """)
        session = DSession(modcol.config)
        session.triggertesting([modcol])
        name, args, kwargs = session.queue.get(block=False)
        assert name == 'collectionreport'
        rep, = args 
        assert len(rep.result) == 1

    def test_triggertesting_item(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)
        host1 = py.execnet.XSpec("popen")
        host1.node = MockNode()
        host2 = py.execnet.XSpec("popen")
        host2.node = MockNode()
        session.addhost(host1)
        session.addhost(host2)
        session.triggertesting([item] * (session.MAXITEMSPERHOST*2 + 1))
        host1_sent = host1.node.sent[0]
        host2_sent = host2.node.sent[0]
        assert host1_sent == [item] * session.MAXITEMSPERHOST
        assert host2_sent == [item] * session.MAXITEMSPERHOST
        assert session.host2pending[host1] == host1_sent
        assert session.host2pending[host2] == host2_sent
        name, args, kwargs = session.queue.get(block=False)
        assert name == "rescheduleitems"
        ev, = args 
        assert ev.items == [item]

    def test_keyboardinterrupt(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)
        def raise_(timeout=None): raise KeyboardInterrupt()
        session.queue.get = raise_
        exitstatus = session.loop([])
        assert exitstatus == outcome.EXIT_INTERRUPTED

    def test_internalerror(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)
        def raise_(): raise ValueError()
        session.queue.get = raise_
        exitstatus = session.loop([])
        assert exitstatus == outcome.EXIT_INTERNALERROR

    def test_rescheduleevent(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)
        host1 = GatewaySpec("localhost")
        host1.node = MockNode()
        session.addhost(host1)
        ev = event.RescheduleItems([item])
        loopstate = session._initloopstate([])
        session.queueevent("rescheduleitems", ev)
        session.loop_once(loopstate)
        # check that RescheduleEvents are not immediately
        # rescheduled if there are no hosts 
        assert loopstate.dowork == False 
        session.queueevent("anonymous", event.NOP())
        session.loop_once(loopstate)
        session.queueevent("anonymous", event.NOP())
        session.loop_once(loopstate)
        assert host1.node.sent == [[item]]
        session.queueevent("itemtestreport", run(item))
        session.loop_once(loopstate)
        assert loopstate.shuttingdown 
        assert not loopstate.testsfailed 

    def test_no_hosts_remaining_for_tests(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        # setup a session with one host
        session = DSession(item.config)
        host1 = GatewaySpec("localhost")
        host1.node = MockNode()
        session.addhost(host1)
       
        # setup a HostDown event
        ev = event.HostDown(host1, None)
        session.queueevent("testnodedown", ev)

        loopstate = session._initloopstate([item])
        loopstate.dowork = False
        session.loop_once(loopstate)
        dumpqueue(session.queue)
        assert loopstate.exitstatus == outcome.EXIT_NOHOSTS

    def test_testnodedown_causes_reschedule_pending(self, testdir, EventRecorder):
        modcol = testdir.getmodulecol("""
            def test_crash(): 
                assert 0
            def test_fail(): 
                x
        """)
        item1, item2 = modcol.collect()

        # setup a session with two hosts 
        session = DSession(item1.config)
        host1 = GatewaySpec("localhost")
        host1.node = MockNode()
        session.addhost(host1)
        host2 = GatewaySpec("localhost")
        host2.node = MockNode()
        session.addhost(host2)
      
        # have one test pending for a host that goes down 
        session.senditems([item1, item2])
        host = session.item2host[item1]
        ev = event.HostDown(host, None)
        session.queueevent("testnodedown", ev)
        evrec = EventRecorder(session.bus)
        print session.item2host
        loopstate = session._initloopstate([])
        session.loop_once(loopstate)

        assert loopstate.colitems == [item2] # do not reschedule crash item
        testrep = evrec.getfirstnamed("itemtestreport")
        assert testrep.failed
        assert testrep.colitem == item1
        assert str(testrep.longrepr).find("crashed") != -1
        assert str(testrep.longrepr).find(host.address) != -1

    def test_testnodeready_adds_to_available(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        # setup a session with two hosts 
        session = DSession(item.config)
        host1 = GatewaySpec("localhost")
        testnodeready = maketestnodeready(host1)
        session.queueevent("testnodeready", testnodeready)
        loopstate = session._initloopstate([item])
        loopstate.dowork = False
        assert len(session.host2pending) == 0
        session.loop_once(loopstate)
        assert len(session.host2pending) == 1

    def test_event_propagation(self, testdir, EventRecorder):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)
      
        evrec = EventRecorder(session.bus)
        session.queueevent("NOPevent", 42)
        session.loop_once(session._initloopstate([]))
        assert evrec.getfirstnamed('NOPevent')

    def runthrough(self, item):
        session = DSession(item.config)
        host1 = GatewaySpec("localhost")
        host1.node = MockNode()
        session.addhost(host1)
        loopstate = session._initloopstate([item])

        session.queueevent("NOP")
        session.loop_once(loopstate)

        assert host1.node.sent == [[item]]
        ev = run(item)
        session.queueevent("itemtestreport", ev)
        session.loop_once(loopstate)
        assert loopstate.shuttingdown  
        session.queueevent("testnodedown", event.HostDown(host1, None))
        session.loop_once(loopstate)
        dumpqueue(session.queue)
        return session, loopstate.exitstatus 

    def test_exit_completed_tests_ok(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session, exitstatus = self.runthrough(item)
        assert exitstatus == outcome.EXIT_OK

    def test_exit_completed_tests_fail(self, testdir):
        item = testdir.getitem("def test_func(): 0/0")
        session, exitstatus = self.runthrough(item)
        assert exitstatus == outcome.EXIT_TESTSFAILED

    def test_exit_on_first_failing(self, testdir):
        modcol = testdir.getmodulecol("""
            def test_fail(): 
                assert 0
            def test_pass(): 
                pass
        """)
        modcol.config.option.exitfirst = True
        session = DSession(modcol.config)
        host1 = GatewaySpec("localhost")
        host1.node = MockNode()
        session.addhost(host1)
        items = basic_collect_report(modcol).result

        # trigger testing  - this sends tests to host1
        session.triggertesting(items)

        # run tests ourselves and produce reports 
        ev1 = run(items[0])
        ev2 = run(items[1])
        session.queueevent("itemtestreport", ev1) # a failing one
        session.queueevent("itemtestreport", ev2)
        # now call the loop
        loopstate = session._initloopstate(items)
        session.loop_once(loopstate)
        assert loopstate.testsfailed
        assert loopstate.shuttingdown

    def test_shuttingdown_filters_events(self, testdir, EventRecorder):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)
        host = GatewaySpec("localhost")
        session.addhost(host)
        loopstate = session._initloopstate([])
        loopstate.shuttingdown = True
        evrec = EventRecorder(session.bus)
        session.queueevent("itemtestreport", run(item))
        session.loop_once(loopstate)
        assert not evrec.getfirstnamed("testnodedown")
        ev = event.HostDown(host)
        session.queueevent("testnodedown", ev)
        session.loop_once(loopstate)
        assert evrec.getfirstnamed('testnodedown') == ev

    def test_filteritems(self, testdir, EventRecorder):
        modcol = testdir.getmodulecol("""
            def test_fail(): 
                assert 0
            def test_pass(): 
                pass
        """)
        session = DSession(modcol.config)

        modcol.config.option.keyword = "nothing"
        dsel = session.filteritems([modcol])
        assert dsel == [modcol] 
        items = modcol.collect()
        evrec = EventRecorder(session.bus)
        remaining = session.filteritems(items)
        assert remaining == []
        
        event = evrec.events[-1]
        assert event.name == "deselected"
        assert event.args[0].items == items 

        modcol.config.option.keyword = "test_fail"
        remaining = session.filteritems(items)
        assert remaining == [items[0]]

        event = evrec.events[-1]
        assert event.name == "deselected"
        assert event.args[0].items == [items[1]]

    def test_testnodedown_shutdown_after_completion(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)

        host = GatewaySpec("localhost")
        host.node = MockNode()
        session.addhost(host)
        session.senditems([item])
        session.queueevent("itemtestreport", run(item))
        loopstate = session._initloopstate([])
        session.loop_once(loopstate)
        assert host.node._shutdown is True
        assert loopstate.exitstatus is None, "loop did not wait for testnodedown"
        assert loopstate.shuttingdown 
        session.queueevent("testnodedown", event.HostDown(host, None))
        session.loop_once(loopstate)
        assert loopstate.exitstatus == 0

    def test_nopending_but_collection_remains(self, testdir):
        modcol = testdir.getmodulecol("""
            def test_fail(): 
                assert 0
            def test_pass(): 
                pass
        """)
        session = DSession(modcol.config)
        host = GatewaySpec("localhost")
        host.node = MockNode()
        session.addhost(host)

        colreport = basic_collect_report(modcol)
        item1, item2 = colreport.result
        session.senditems([item1])
        # host2pending will become empty when the loop sees
        # the report 
        session.queueevent("itemtestreport", run(item1)) 

        # but we have a collection pending
        session.queueevent("collectionreport", colreport) 

        loopstate = session._initloopstate([])
        session.loop_once(loopstate)
        assert loopstate.exitstatus is None, "loop did not care for collection report"
        assert not loopstate.colitems 
        session.loop_once(loopstate)
        assert loopstate.colitems == colreport.result
        assert loopstate.exitstatus is None, "loop did not care for colitems"
