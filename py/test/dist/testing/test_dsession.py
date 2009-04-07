from py.__.test.dist.dsession import DSession
from py.__.test.runner import basic_collect_report 
from py.__.test import outcome
import py

XSpec = py.execnet.XSpec

def run(item, node):
    from py.__.test.runner import basic_run_report
    rep = basic_run_report(item)
    rep.node = node
    return rep 

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
    def test_add_remove_node(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        node = MockNode()
        rep = run(item, node)
        session = DSession(item.config)
        assert not session.node2pending
        session.addnode(node)
        assert len(session.node2pending) == 1
        session.senditems_load([item])
        pending = session.removenode(node)
        assert pending == [item]
        assert item not in session.item2nodes
        l = session.removenode(node)
        assert not l 

    def test_senditems_each_and_receive_with_two_nodes(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        node1 = MockNode()
        node2 = MockNode()
        session = DSession(item.config)
        session.addnode(node1)
        session.addnode(node2)
        session.senditems_each([item])
        assert session.node2pending[node1] == [item]
        assert session.node2pending[node2] == [item]
        assert node1 in session.item2nodes[item]
        assert node2 in session.item2nodes[item]
        session.removeitem(item, node1)
        assert session.item2nodes[item] == [node2]
        session.removeitem(item, node2)
        assert not session.node2pending[node1] 
        assert not session.item2nodes

    def test_senditems_load_and_receive_one_node(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        node = MockNode()
        rep = run(item, node)
        session = DSession(item.config)
        session.addnode(node)
        session.senditems_load([item])  
        assert session.node2pending[node] == [item]
        assert session.item2nodes[item] == [node]
        session.removeitem(item, node)
        assert not session.node2pending[node] 
        assert not session.item2nodes

    def test_triggertesting_collect(self, testdir):
        modcol = testdir.getmodulecol("""
            def test_func():
                pass
        """)
        session = DSession(modcol.config)
        session.triggertesting([modcol])
        name, args, kwargs = session.queue.get(block=False)
        assert name == 'collectreport'
        rep, = args 
        assert len(rep.result) == 1

    def test_triggertesting_item(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)
        node1 = MockNode()
        node2 = MockNode()
        session.addnode(node1)
        session.addnode(node2)
        session.triggertesting([item] * (session.MAXITEMSPERHOST*2 + 1))
        sent1 = node1.sent[0]
        sent2 = node2.sent[0]
        assert sent1 == [item] * session.MAXITEMSPERHOST
        assert sent2 == [item] * session.MAXITEMSPERHOST
        assert session.node2pending[node1] == sent1
        assert session.node2pending[node2] == sent2
        name, args, kwargs = session.queue.get(block=False)
        assert name == "rescheduleitems"
        items, = args 
        assert items == [item]

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
        node = MockNode()
        session.addnode(node)
        loopstate = session._initloopstate([])
        session.queueevent("rescheduleitems", [item])
        session.loop_once(loopstate)
        # check that RescheduleEvents are not immediately
        # rescheduled if there are no nodes
        assert loopstate.dowork == False 
        session.queueevent("anonymous")
        session.loop_once(loopstate)
        session.queueevent("anonymous")
        session.loop_once(loopstate)
        assert node.sent == [[item]]
        session.queueevent("itemtestreport", run(item, node))
        session.loop_once(loopstate)
        assert loopstate.shuttingdown 
        assert not loopstate.testsfailed 

    def test_no_node_remaining_for_tests(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        # setup a session with one node
        session = DSession(item.config)
        node = MockNode()
        session.addnode(node)
       
        # setup a HostDown event
        session.queueevent("testnodedown", node, None)

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

        # setup a session with two nodes
        session = DSession(item1.config)
        node1, node2 = MockNode(), MockNode()
        session.addnode(node1)
        session.addnode(node2)
      
        # have one test pending for a node that goes down 
        session.senditems_load([item1, item2])
        node = session.item2nodes[item1] [0]
        session.queueevent("testnodedown", node, None)
        evrec = EventRecorder(session.bus)
        print session.item2nodes
        loopstate = session._initloopstate([])
        session.loop_once(loopstate)

        assert loopstate.colitems == [item2] # do not reschedule crash item
        testrep = evrec.matchreport(names="itemtestreport")
        assert testrep.failed
        assert testrep.colitem == item1
        assert str(testrep.longrepr).find("crashed") != -1
        #assert str(testrep.longrepr).find(node.gateway.spec) != -1

    def test_testnodeready_adds_to_available(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        # setup a session with two nodes
        session = DSession(item.config)
        node1 = MockNode()
        session.queueevent("testnodeready", node1)
        loopstate = session._initloopstate([item])
        loopstate.dowork = False
        assert len(session.node2pending) == 0
        session.loop_once(loopstate)
        assert len(session.node2pending) == 1

    def test_event_propagation(self, testdir, EventRecorder):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)
      
        evrec = EventRecorder(session.bus)
        session.queueevent("NOP", 42)
        session.loop_once(session._initloopstate([]))
        assert evrec.getcall('NOP')

    def runthrough(self, item):
        session = DSession(item.config)
        node = MockNode()
        session.addnode(node)
        loopstate = session._initloopstate([item])

        session.queueevent("NOP")
        session.loop_once(loopstate)

        assert node.sent == [[item]]
        ev = run(item, node) 
        session.queueevent("itemtestreport", ev)
        session.loop_once(loopstate)
        assert loopstate.shuttingdown  
        session.queueevent("testnodedown", node, None)
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
        node = MockNode()
        session.addnode(node)
        items = basic_collect_report(modcol).result

        # trigger testing  - this sends tests to the node
        session.triggertesting(items)

        # run tests ourselves and produce reports 
        ev1 = run(items[0], node)
        ev2 = run(items[1], node)
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
        node = MockNode()
        session.addnode(node)
        loopstate = session._initloopstate([])
        loopstate.shuttingdown = True
        evrec = EventRecorder(session.bus)
        session.queueevent("itemtestreport", run(item, node))
        session.loop_once(loopstate)
        assert not evrec.getcalls("testnodedown")
        session.queueevent("testnodedown", node, None)
        session.loop_once(loopstate)
        assert evrec.getcall('testnodedown').node == node

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
        
        event = evrec.getcalls("deselected")[-1]
        assert event.items == items 

        modcol.config.option.keyword = "test_fail"
        remaining = session.filteritems(items)
        assert remaining == [items[0]]

        event = evrec.getcalls("deselected")[-1]
        assert event.items == [items[1]]

    def test_testnodedown_shutdown_after_completion(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)

        node = MockNode()
        session.addnode(node)
        session.senditems_load([item])
        session.queueevent("itemtestreport", run(item, node))
        loopstate = session._initloopstate([])
        session.loop_once(loopstate)
        assert node._shutdown is True
        assert loopstate.exitstatus is None, "loop did not wait for testnodedown"
        assert loopstate.shuttingdown 
        session.queueevent("testnodedown", node, None)
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
        node = MockNode()
        session.addnode(node)

        colreport = basic_collect_report(modcol)
        item1, item2 = colreport.result
        session.senditems_load([item1])
        # node2pending will become empty when the loop sees the report 
        rep = run(item1, node)

        session.queueevent("itemtestreport", run(item1, node)) 

        # but we have a collection pending
        session.queueevent("collectreport", colreport) 

        loopstate = session._initloopstate([])
        session.loop_once(loopstate)
        assert loopstate.exitstatus is None, "loop did not care for collection report"
        assert not loopstate.colitems 
        session.loop_once(loopstate)
        assert loopstate.colitems == colreport.result
        assert loopstate.exitstatus is None, "loop did not care for colitems"

    def test_dist_some_tests(self, testdir):
        from py.__.test.dist.testing.test_txnode import EventQueue
        p1 = testdir.makepyfile(test_one="""
            def test_1(): 
                pass
            def test_x():
                import py
                py.test.skip("aaa")
            def test_fail():
                assert 0
        """)
        config = testdir.parseconfig('-d', p1, '--tx=popen')
        dsession = DSession(config)
        eq = EventQueue(config.bus)
        dsession.main([config.getfsnode(p1)])
        ev, = eq.geteventargs("itemtestreport")
        assert ev.passed
        ev, = eq.geteventargs("itemtestreport")
        assert ev.skipped
        ev, = eq.geteventargs("itemtestreport")
        assert ev.failed
        # see that the node is really down 
        node, error = eq.geteventargs("testnodedown")
        assert node.gateway.spec.popen
        eq.geteventargs("testrunfinish")

