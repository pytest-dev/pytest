""" 

    EXPERIMENTAL dsession session  (for dist/non-dist unification)

"""

import py
from _py.test.session import Session
from _py.test import outcome 
from _py.test.dist.nodemanage import NodeManager
queue = py.builtin._tryimport('queue', 'Queue')

debug_file = None # open('/tmp/loop.log', 'w')
def debug(*args):
    if debug_file is not None:
        s = " ".join(map(str, args))
        debug_file.write(s+"\n")
        debug_file.flush()

class LoopState(object):
    def __init__(self, dsession, colitems):
        self.dsession = dsession
        self.colitems = colitems
        self.exitstatus = None 
        # loopstate.dowork is False after reschedule events 
        # because otherwise we might very busily loop 
        # waiting for a host to become ready.  
        self.dowork = True
        self.shuttingdown = False
        self.testsfailed = False

    def __repr__(self):
        return "<LoopState exitstatus=%r shuttingdown=%r len(colitems)=%d>" % (
            self.exitstatus, self.shuttingdown, len(self.colitems))

    def pytest_runtest_logreport(self, report):
        if report.item in self.dsession.item2nodes:
            if report.when != "teardown": # otherwise we already managed it
                self.dsession.removeitem(report.item, report.node)
        if report.failed:
            self.testsfailed = True

    def pytest_collectreport(self, report):
        if report.passed:
            self.colitems.extend(report.result)

    def pytest_testnodeready(self, node):
        self.dsession.addnode(node)

    def pytest_testnodedown(self, node, error=None):
        pending = self.dsession.removenode(node)
        if pending:
            if error:
                crashitem = pending[0]
                debug("determined crashitem", crashitem)
                self.dsession.handle_crashitem(crashitem, node)
                # XXX recovery handling for "each"? 
                # currently pending items are not retried 
                if self.dsession.config.option.dist == "load":
                    self.colitems.extend(pending[1:])

    def pytest_rescheduleitems(self, items):
        self.colitems.extend(items)
        self.dowork = False # avoid busywait

class DSession(Session):
    """ 
        Session drives the collection and running of tests
        and generates test events for reporters. 
    """ 
    MAXITEMSPERHOST = 15
    
    def __init__(self, config):
        self.queue = queue.Queue()
        self.node2pending = {}
        self.item2nodes = {}
        super(DSession, self).__init__(config=config)

    #def pytest_configure(self, __multicall__, config):
    #    __multicall__.execute()
    #    try:
    #        config.getxspecs()
    #    except config.Error:
    #        print
    #        raise config.Error("dist mode %r needs test execution environments, "
    #                           "none found." %(config.option.dist))

    def main(self, colitems=None):
        colitems = self.getinitialitems(colitems)
        self.sessionstarts()
        self.setup()
        exitstatus = self.loop(colitems)
        self.teardown()
        self.sessionfinishes(exitstatus=exitstatus) 
        return exitstatus

    def loop_once(self, loopstate):
        if loopstate.shuttingdown:
            return self.loop_once_shutdown(loopstate)
        colitems = loopstate.colitems 
        if loopstate.dowork and colitems:
            self.triggertesting(loopstate.colitems) 
            colitems[:] = []
        # we use a timeout here so that control-C gets through 
        while 1:
            try:
                eventcall = self.queue.get(timeout=2.0)
                break
            except queue.Empty:
                continue
        loopstate.dowork = True 
          
        callname, args, kwargs = eventcall
        if callname is not None:
            call = getattr(self.config.hook, callname)
            assert not args
            call(**kwargs)

        # termination conditions
        if ((loopstate.testsfailed and self.config.option.exitfirst) or 
            (not self.item2nodes and not colitems and not self.queue.qsize())):
            self.triggershutdown()
            loopstate.shuttingdown = True
        elif not self.node2pending:
            loopstate.exitstatus = outcome.EXIT_NOHOSTS
           
    def loop_once_shutdown(self, loopstate):
        # once we are in shutdown mode we dont send 
        # events other than HostDown upstream 
        eventname, args, kwargs = self.queue.get()
        if eventname == "pytest_testnodedown":
            self.config.hook.pytest_testnodedown(**kwargs)
            self.removenode(kwargs['node'])
        elif eventname == "pytest_runtest_logreport":
            # might be some teardown report
            self.config.hook.pytest_runtest_logreport(**kwargs)
        if not self.node2pending:
            # finished
            if loopstate.testsfailed:
                loopstate.exitstatus = outcome.EXIT_TESTSFAILED
            else:
                loopstate.exitstatus = outcome.EXIT_OK
        #self.config.pluginmanager.unregister(loopstate)

    def _initloopstate(self, colitems):
        loopstate = LoopState(self, colitems)
        self.config.pluginmanager.register(loopstate)
        return loopstate

    def loop(self, colitems):
        try:
            loopstate = self._initloopstate(colitems)
            loopstate.dowork = False # first receive at least one HostUp events
            while 1:
                self.loop_once(loopstate)
                if loopstate.exitstatus is not None:
                    exitstatus = loopstate.exitstatus
                    break 
        except KeyboardInterrupt:
            excinfo = py.code.ExceptionInfo()
            self.config.hook.pytest_keyboard_interrupt(excinfo=excinfo)
            exitstatus = outcome.EXIT_INTERRUPTED
        except:
            self.config.pluginmanager.notify_exception()
            exitstatus = outcome.EXIT_INTERNALERROR
        self.config.pluginmanager.unregister(loopstate)
        if exitstatus == 0 and self._testsfailed:
            exitstatus = outcome.EXIT_TESTSFAILED
        return exitstatus

    def triggershutdown(self):
        for node in self.node2pending:
            node.shutdown()

    def addnode(self, node):
        assert node not in self.node2pending
        self.node2pending[node] = []

    def removenode(self, node):
        try:
            pending = self.node2pending.pop(node)
        except KeyError:
            # this happens if we didn't receive a testnodeready event yet
            return []
        for item in pending:
            l = self.item2nodes[item]
            l.remove(node)
            if not l:
                del self.item2nodes[item]
        return pending

    def triggertesting(self, colitems):
        colitems = self.filteritems(colitems)
        senditems = []
        for next in colitems:
            if isinstance(next, py.test.collect.Item):
                senditems.append(next)
            else:
                self.config.hook.pytest_collectstart(collector=next)
                colrep = self.config.hook.pytest_make_collect_report(collector=next)
                self.queueevent("pytest_collectreport", report=colrep)
        if self.config.option.dist == "each":
            self.senditems_each(senditems)
        else:
            # XXX assert self.config.option.dist == "load"
            self.senditems_load(senditems)

    def queueevent(self, eventname, **kwargs):
        self.queue.put((eventname, (), kwargs)) 

    def senditems_each(self, tosend):
        if not tosend:
            return 
        room = self.MAXITEMSPERHOST
        for node, pending in self.node2pending.items():
            room = min(self.MAXITEMSPERHOST - len(pending), room)
        sending = tosend[:room]
        for node, pending in self.node2pending.items():
            node.sendlist(sending)
            pending.extend(sending)
            for item in sending:
                nodes = self.item2nodes.setdefault(item, [])
                assert node not in nodes
                nodes.append(node)
                self.config.hook.pytest_itemstart(item=item, node=node)
        tosend[:] = tosend[room:]  # update inplace
        if tosend:
            # we have some left, give it to the main loop
            self.queueevent("pytest_rescheduleitems", items=tosend)

    def senditems_load(self, tosend):
        if not tosend:
            return 
        for node, pending in self.node2pending.items():
            room = self.MAXITEMSPERHOST - len(pending)
            if room > 0:
                sending = tosend[:room]
                node.sendlist(sending)
                for item in sending:
                    #assert item not in self.item2node, (
                    #    "sending same item %r to multiple "
                    #    "not implemented" %(item,))
                    self.item2nodes.setdefault(item, []).append(node)
                    self.config.hook.pytest_itemstart(item=item, node=node)
                pending.extend(sending)
                tosend[:] = tosend[room:]  # update inplace
                if not tosend:
                    break
        if tosend:
            # we have some left, give it to the main loop
            self.queueevent("pytest_rescheduleitems", items=tosend)

    def removeitem(self, item, node):
        if item not in self.item2nodes:
            raise AssertionError(item, self.item2nodes)
        nodes = self.item2nodes[item]
        if node in nodes: # the node might have gone down already
            nodes.remove(node)
        if not nodes:
            del self.item2nodes[item]
        pending = self.node2pending[node]
        pending.remove(item)

    def handle_crashitem(self, item, node):
        runner = item.config.pluginmanager.getplugin("runner") 
        info = "!!! Node %r crashed during running of test %r" %(node, item)
        rep = runner.ItemTestReport(item=item, excinfo=info, when="???")
        rep.node = node
        self.config.hook.pytest_runtest_logreport(report=rep)

    def setup(self):
        """ setup any neccessary resources ahead of the test run. """
        self.nodemanager = NodeManager(self.config)
        self.nodemanager.setup_nodes(putevent=self.queue.put)
        if self.config.option.dist == "each":
            self.nodemanager.wait_nodesready(5.0)

    def teardown(self):
        """ teardown any resources after a test run. """ 
        self.nodemanager.teardown_nodes()
