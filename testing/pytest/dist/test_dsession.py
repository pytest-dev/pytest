from py.impl.test.dist.dsession import DSession
from py.impl.test import outcome
import py
import execnet

XSpec = execnet.XSpec

def run(item, node, excinfo=None):
    runner = item.config.pluginmanager.getplugin("runner")
    rep = runner.ItemTestReport(item=item, 
        excinfo=excinfo, when="call")
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
        print(queue.get())

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
        assert name == 'pytest_collectreport'
        report = kwargs['report']  
        assert len(report.result) == 1

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
        assert name == "pytest_rescheduleitems"
        assert kwargs['items'] == [item]

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
        session.queueevent("pytest_rescheduleitems", items=[item])
        session.loop_once(loopstate)
        # check that RescheduleEvents are not immediately
        # rescheduled if there are no nodes
        assert loopstate.dowork == False 
        session.queueevent(None)
        session.loop_once(loopstate)
        session.queueevent(None)
        session.loop_once(loopstate)
        assert node.sent == [[item]]
        session.queueevent("pytest_runtest_logreport", report=run(item, node))
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
        session.queueevent("pytest_testnodedown", node=node, error=None)

        loopstate = session._initloopstate([item])
        loopstate.dowork = False
        session.loop_once(loopstate)
        dumpqueue(session.queue)
        assert loopstate.exitstatus == outcome.EXIT_NOHOSTS

    def test_removeitem_from_failing_teardown(self, testdir):
        # teardown reports only come in when they signal a failure
        # internal session-management should basically ignore them 
        # XXX probably it'S best to invent a new error hook for 
        # teardown/setup related failures
        modcol = testdir.getmodulecol("""
            def test_one(): 
                pass 
            def teardown_function(function):
                assert 0
        """)
        item1, = modcol.collect()

        # setup a session with two nodes
        session = DSession(item1.config)
        node1, node2 = MockNode(), MockNode()
        session.addnode(node1)
        session.addnode(node2)
      
        # have one test pending for a node that goes down 
        session.senditems_each([item1])
        nodes = session.item2nodes[item1]
        class rep:
            failed = True
            item = item1
            node = nodes[0]
            when = "call"
        session.queueevent("pytest_runtest_logreport", report=rep)
        reprec = testdir.getreportrecorder(session)
        print(session.item2nodes)
        loopstate = session._initloopstate([])
        assert len(session.item2nodes[item1]) == 2
        session.loop_once(loopstate)
        assert len(session.item2nodes[item1]) == 1
        rep.when = "teardown"
        session.queueevent("pytest_runtest_logreport", report=rep)
        session.loop_once(loopstate)
        assert len(session.item2nodes[item1]) == 1

    def test_testnodedown_causes_reschedule_pending(self, testdir):
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
        item1.config.option.dist = "load"
        session.queueevent("pytest_testnodedown", node=node, error="xyz")
        reprec = testdir.getreportrecorder(session)
        print(session.item2nodes)
        loopstate = session._initloopstate([])
        session.loop_once(loopstate)

        assert loopstate.colitems == [item2] # do not reschedule crash item
        rep = reprec.matchreport(names="pytest_runtest_logreport")
        assert rep.failed
        assert rep.item == item1
        assert str(rep.longrepr).find("crashed") != -1
        #assert str(testrep.longrepr).find(node.gateway.spec) != -1

    def test_testnodeready_adds_to_available(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        # setup a session with two nodes
        session = DSession(item.config)
        node1 = MockNode()
        session.queueevent("pytest_testnodeready", node=node1)
        loopstate = session._initloopstate([item])
        loopstate.dowork = False
        assert len(session.node2pending) == 0
        session.loop_once(loopstate)
        assert len(session.node2pending) == 1

    def runthrough(self, item, excinfo=None):
        session = DSession(item.config)
        node = MockNode()
        session.addnode(node)
        loopstate = session._initloopstate([item])

        session.queueevent(None)
        session.loop_once(loopstate)

        assert node.sent == [[item]]
        ev = run(item, node, excinfo=excinfo) 
        session.queueevent("pytest_runtest_logreport", report=ev)
        session.loop_once(loopstate)
        assert loopstate.shuttingdown  
        session.queueevent("pytest_testnodedown", node=node, error=None)
        session.loop_once(loopstate)
        dumpqueue(session.queue)
        return session, loopstate.exitstatus 

    def test_exit_completed_tests_ok(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session, exitstatus = self.runthrough(item)
        assert exitstatus == outcome.EXIT_OK

    def test_exit_completed_tests_fail(self, testdir):
        item = testdir.getitem("def test_func(): 0/0")
        session, exitstatus = self.runthrough(item, excinfo="fail")
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
        items = modcol.config.hook.pytest_make_collect_report(collector=modcol).result

        # trigger testing  - this sends tests to the node
        session.triggertesting(items)

        # run tests ourselves and produce reports 
        ev1 = run(items[0], node, "fail")
        ev2 = run(items[1], node, None)
        session.queueevent("pytest_runtest_logreport", report=ev1) # a failing one
        session.queueevent("pytest_runtest_logreport", report=ev2)
        # now call the loop
        loopstate = session._initloopstate(items)
        session.loop_once(loopstate)
        assert loopstate.testsfailed
        assert loopstate.shuttingdown

    def test_shuttingdown_filters(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)
        node = MockNode()
        session.addnode(node)
        loopstate = session._initloopstate([])
        loopstate.shuttingdown = True
        reprec = testdir.getreportrecorder(session)
        session.queueevent("pytest_runtest_logreport", report=run(item, node))
        session.loop_once(loopstate)
        assert not reprec.getcalls("pytest_testnodedown")
        session.queueevent("pytest_testnodedown", node=node, error=None)
        session.loop_once(loopstate)
        assert reprec.getcall('pytest_testnodedown').node == node

    def test_filteritems(self, testdir):
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
        hookrecorder = testdir.getreportrecorder(session).hookrecorder
        remaining = session.filteritems(items)
        assert remaining == []
        
        event = hookrecorder.getcalls("pytest_deselected")[-1]
        assert event.items == items 

        modcol.config.option.keyword = "test_fail"
        remaining = session.filteritems(items)
        assert remaining == [items[0]]

        event = hookrecorder.getcalls("pytest_deselected")[-1]
        assert event.items == [items[1]]

    def test_testnodedown_shutdown_after_completion(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        session = DSession(item.config)

        node = MockNode()
        session.addnode(node)
        session.senditems_load([item])
        session.queueevent("pytest_runtest_logreport", report=run(item, node))
        loopstate = session._initloopstate([])
        session.loop_once(loopstate)
        assert node._shutdown is True
        assert loopstate.exitstatus is None, "loop did not wait for testnodedown"
        assert loopstate.shuttingdown 
        session.queueevent("pytest_testnodedown", node=node, error=None)
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

        colreport = modcol.config.hook.pytest_make_collect_report(collector=modcol)
        item1, item2 = colreport.result
        session.senditems_load([item1])
        # node2pending will become empty when the loop sees the report 
        rep = run(item1, node)
        session.queueevent("pytest_runtest_logreport", report=run(item1, node)) 

        # but we have a collection pending
        session.queueevent("pytest_collectreport", report=colreport) 

        loopstate = session._initloopstate([])
        session.loop_once(loopstate)
        assert loopstate.exitstatus is None, "loop did not care for collection report"
        assert not loopstate.colitems 
        session.loop_once(loopstate)
        assert loopstate.colitems == colreport.result
        assert loopstate.exitstatus is None, "loop did not care for colitems"

    def test_dist_some_tests(self, testdir):
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
        hookrecorder = testdir.getreportrecorder(config).hookrecorder
        dsession.main([config.getfsnode(p1)])
        rep = hookrecorder.popcall("pytest_runtest_logreport").report
        assert rep.passed
        rep = hookrecorder.popcall("pytest_runtest_logreport").report
        assert rep.skipped
        rep = hookrecorder.popcall("pytest_runtest_logreport").report
        assert rep.failed
        # see that the node is really down 
        node = hookrecorder.popcall("pytest_testnodedown").node
        assert node.gateway.spec.popen
        #XXX eq.geteventargs("pytest_sessionfinish")

def test_collected_function_causes_remote_skip(testdir):
    sub = testdir.mkpydir("testing")
    sub.join("test_module.py").write(py.code.Source("""
        import py
        path = py.path.local(%r)
        if path.check():
            path.remove()
        else:
            py.test.skip("remote skip")
        def test_func(): 
            pass
        def test_func2(): 
            pass
    """ % str(sub.ensure("somefile"))))
    result = testdir.runpytest('-v', '--dist=each', '--tx=popen')
    result.stdout.fnmatch_lines([
        "*2 skipped*"
    ])

def test_teardownfails_one_function(testdir):
    p = testdir.makepyfile("""
        def test_func(): 
            pass
        def teardown_function(function):
            assert 0
    """)
    result = testdir.runpytest(p, '--dist=each', '--tx=popen')
    result.stdout.fnmatch_lines([
        "*def teardown_function(function):*", 
        "*1 passed*1 error*"
    ])

@py.test.mark.xfail 
def test_terminate_on_hangingnode(testdir):
    p = testdir.makeconftest("""
        def pytest__teardown_final(session):
            if session.nodeid: # running on slave
                import time
                time.sleep(2)
    """)
    result = testdir.runpytest(p, '--dist=each', '--tx=popen')
    assert result.duration < 2.0 
    result.stdout.fnmatch_lines([
        "*0 passed*",
    ])



