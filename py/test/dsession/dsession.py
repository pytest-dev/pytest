""" 

    EXPERIMENTAL dsession session  (for dist/non-dist unification)

"""

import py
from py.__.test import event
from py.__.test.runner import basic_run_report, basic_collect_report
from py.__.test.session import Session
from py.__.test import outcome 

import Queue 

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

    def pyevent_itemtestreport(self, event):
        if event.colitem in self.dsession.item2host:
            self.dsession.removeitem(event.colitem)
        if event.failed:
            self.testsfailed = True

    def pyevent_collectionreport(self, event):
        if event.passed:
            self.colitems.extend(event.result)

    def pyevent_testnodeready(self, event):
        self.dsession.addhost(event.host)

    def pyevent_testnodedown(self, event):
        pending = self.dsession.removehost(event.host)
        if pending:
            crashitem = pending[0]
            self.dsession.handle_crashitem(crashitem, event.host)
            self.colitems.extend(pending[1:])

    def pyevent_rescheduleitems(self, event):
        self.colitems.extend(event.items)
        self.dowork = False # avoid busywait

class DSession(Session):
    """ 
        Session drives the collection and running of tests
        and generates test events for reporters. 
    """ 
    MAXITEMSPERHOST = 15
    
    def __init__(self, config):
        super(DSession, self).__init__(config=config)
        
        self.queue = Queue.Queue()
        self.host2pending = {}
        self.item2host = {}
        if self.config.getvalue("executable") and \
           not self.config.getvalue("numprocesses"):
            self.config.option.numprocesses = 1

    def fixoptions(self):
        """ check, fix and determine conflicting options. """
        option = self.config.option 
        #if option.runbrowser and not option.startserver:
        #    #print "--runbrowser implies --startserver"
        #    option.startserver = True
        if self.config.getvalue("dist_boxed") and option.dist:
            option.boxed = True
        # conflicting options
        if option.looponfailing and option.usepdb:
            raise ValueError, "--looponfailing together with --pdb not supported."
        if option.executable and option.usepdb:
            raise ValueError, "--exec together with --pdb not supported."
        if option.executable and not option.dist and not option.numprocesses:
            option.numprocesses = 1
        config = self.config
        if config.option.numprocesses:
            return
        try:
            config.getvalue('hosts')
        except KeyError:
            print "Please specify hosts for distribution of tests:"
            print "cmdline: --gateways=host1,host2,..."
            print "conftest.py: pytest_option_hosts=['host1','host2',]"
            print "environment: PYTEST_OPTION_HOSTS=host1,host2,host3"
            print 
            print "see also: http://codespeak.net/py/current/doc/test.html#automated-distributed-testing"
            raise SystemExit

    def main(self, colitems=None):
        colitems = self.getinitialitems(colitems)
        self.sessionstarts()
        self.setup_hosts()
        exitstatus = self.loop(colitems)
        self.teardown_hosts()
        self.sessionfinishes() 
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
            except Queue.Empty:
                continue
        loopstate.dowork = True 
          
        eventname, args, kwargs = eventcall
        self.bus.notify(eventname, *args, **kwargs)

        # termination conditions
        if ((loopstate.testsfailed and self.config.option.exitfirst) or 
            (not self.item2host and not colitems and not self.queue.qsize())):
            self.triggershutdown()
            loopstate.shuttingdown = True
        elif not self.host2pending:
            loopstate.exitstatus = outcome.EXIT_NOHOSTS
           
    def loop_once_shutdown(self, loopstate):
        # once we are in shutdown mode we dont send 
        # events other than HostDown upstream 
        eventname, args, kwargs = self.queue.get()
        if eventname == "testnodedown":
            ev, = args
            self.bus.notify("testnodedown", ev)
            self.removehost(ev.host)
        if not self.host2pending:
            # finished
            if loopstate.testsfailed:
                loopstate.exitstatus = outcome.EXIT_TESTSFAILED
            else:
                loopstate.exitstatus = outcome.EXIT_OK

    def _initloopstate(self, colitems):
        loopstate = LoopState(self, colitems)
        self.config.bus.register(loopstate)
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
            exitstatus = outcome.EXIT_INTERRUPTED
        except:
            self.bus.notify("internalerror", event.InternalException())
            exitstatus = outcome.EXIT_INTERNALERROR
        self.config.bus.unregister(loopstate)
        if exitstatus == 0 and self._testsfailed:
            exitstatus = outcome.EXIT_TESTSFAILED
        return exitstatus

    def triggershutdown(self):
        for host in self.host2pending:
            host.node.shutdown()

    def addhost(self, host):
        assert host not in self.host2pending
        self.host2pending[host] = []

    def removehost(self, host):
        try:
            pending = self.host2pending.pop(host)
        except KeyError:
            # this happens if we didn't receive a testnodeready event yet
            return []
        for item in pending:
            del self.item2host[item]
        return pending

    def triggertesting(self, colitems):
        colitems = self.filteritems(colitems)
        senditems = []
        for next in colitems:
            if isinstance(next, py.test.collect.Item):
                senditems.append(next)
            else:
                self.bus.notify("collectionstart", event.CollectionStart(next))
                self.queueevent("collectionreport", basic_collect_report(next))
        self.senditems(senditems)

    def queueevent(self, eventname, *args, **kwargs):
        self.queue.put((eventname, args, kwargs)) 

    def senditems(self, tosend):
        if not tosend:
            return 
        for host, pending in self.host2pending.items():
            room = self.MAXITEMSPERHOST - len(pending)
            if room > 0:
                sending = tosend[:room]
                host.node.sendlist(sending)
                for item in sending:
                    #assert item not in self.item2host, (
                    #    "sending same item %r to multiple hosts "
                    #    "not implemented" %(item,))
                    self.item2host[item] = host
                    self.bus.notify("itemstart", event.ItemStart(item, host))
                pending.extend(sending)
                tosend[:] = tosend[room:]  # update inplace
                if not tosend:
                    break
        if tosend:
            # we have some left, give it to the main loop
            self.queueevent("rescheduleitems", event.RescheduleItems(tosend))

    def removeitem(self, item):
        if item not in self.item2host:
            raise AssertionError(item, self.item2host)
        host = self.item2host.pop(item)
        self.host2pending[host].remove(item)
        #self.config.bus.notify("removeitem", item, host.hostid)

    def handle_crashitem(self, item, host):
        longrepr = "!!! Host %r crashed during running of test %r" %(host, item)
        rep = event.ItemTestReport(item, when="???", excinfo=longrepr)
        self.bus.notify("itemtestreport", rep)

    def setup_hosts(self):
        """ setup any neccessary resources ahead of the test run. """
        from py.__.test.dsession.hostmanage import HostManager
        self.hm = HostManager(self.config)
        self.hm.setup_hosts(putevent=self.queue.put)

    def teardown_hosts(self):
        """ teardown any resources after a test run. """ 
        self.hm.teardown_hosts()

# debugging function
def dump_picklestate(item):
    l = []
    while 1:
        state = item.__getstate__()
        l.append(state)
        item = state[-1]
        if len(state) != 2:
            break
    return l
