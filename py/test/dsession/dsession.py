""" 

    EXPERIMENTAL dsession session  (for dist/non-dist unification)

"""

import py
from py.__.test import event
import py.__.test.custompdb
from py.__.test.dsession.hostmanage import HostManager
Item = (py.test.collect.Item, py.test.collect.Item)
Collector = (py.test.collect.Collector, py.test.collect.Collector)
from py.__.test.runner import basic_run_report, basic_collect_report
from py.__.test.session import Session
from py.__.test.runner import OutcomeRepr
from py.__.test import outcome 

import Queue 

class LoopState(object):
    def __init__(self, colitems):
        self.colitems = colitems
        self.exitstatus = None 
        # loopstate.dowork is False after reschedule events 
        # because otherwise we might very busily loop 
        # waiting for a host to become ready.  
        self.dowork = True
        self.shuttingdown = False
        self.testsfailed = False

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
        self._testsfailed = False
        self.trace = config.maketrace("dsession.log")

    def fixoptions(self):
        """ check, fix and determine conflicting options. """
        option = self.config.option 
        if option.runbrowser and not option.startserver:
            #print "--runbrowser implies --startserver"
            option.startserver = True
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
            config.getvalue('dist_hosts')
        except KeyError:
            print "Don't know where to distribute tests to.  You may want"
            print "to specify either a number of local processes to start"
            print "with '--numprocesses=NUM' or specify 'dist_hosts' in a local"
            print "conftest.py file, for example:"
            print
            print "  dist_hosts = ['localhost'] * 4 # for 3 processors"
            print "  dist_hosts = ['you@remote.com', '...'] # for testing on ssh accounts"
            print "   # with your remote ssh accounts"
            print 
            print "see also: http://codespeak.net/py/current/doc/test.html#automated-distributed-testing"
            raise SystemExit

    def main(self, colitems=None):
        colitems = self.getinitialitems(colitems)
        self.bus.notify(event.TestrunStart())
        self.setup_hosts()
        exitstatus = self.loop(colitems)
        self.bus.notify(event.TestrunFinish(exitstatus=exitstatus))
        self.teardown_hosts()
        return exitstatus

    def loop_once(self, loopstate):
        if loopstate.shuttingdown:
            return self.loop_once_shutdown(loopstate)
        colitems = loopstate.colitems 
        if loopstate.dowork and loopstate.colitems:
            self.triggertesting(colitems) 
            colitems[:] = []
        # we use a timeout here so that control-C gets through 
        while 1:
            try:
                ev = self.queue.get(timeout=2.0)
                break
            except Queue.Empty:
                continue
        loopstate.dowork = True 
        self.bus.notify(ev)
        if isinstance(ev, event.ItemTestReport):
            self.removeitem(ev.colitem)
            if ev.failed:
                loopstate.testsfailed = True
        elif isinstance(ev, event.CollectionReport):
            if ev.passed:
                colitems.extend(ev.result)
        elif isinstance(ev, event.HostUp):
            self.addhost(ev.host)
        elif isinstance(ev, event.HostDown):
            pending = self.removehost(ev.host)
            if pending:
                crashitem = pending.pop(0)
                self.handle_crashitem(crashitem, ev.host)
                colitems.extend(pending)
        elif isinstance(ev, event.RescheduleItems):
            colitems.extend(ev.items)
            loopstate.dowork = False # avoid busywait

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
        ev = self.queue.get()
        if isinstance(ev, event.HostDown):
            self.bus.notify(ev)
            self.removehost(ev.host)
        if not self.host2pending:
            # finished
            if loopstate.testsfailed:
                loopstate.exitstatus = outcome.EXIT_TESTSFAILED
            else:
                loopstate.exitstatus = outcome.EXIT_OK

    def loop(self, colitems):
        try:
            loopstate = LoopState(colitems)
            loopstate.dowork = False # first receive at least one HostUp events
            while 1:
                self.loop_once(loopstate)
                if loopstate.exitstatus is not None:
                    exitstatus = loopstate.exitstatus
                    break 
        except KeyboardInterrupt:
            exitstatus = outcome.EXIT_INTERRUPTED
        except:
            self.bus.notify(event.InternalException())
            exitstatus = outcome.EXIT_INTERNALERROR
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
        pending = self.host2pending.pop(host)
        for item in pending:
            del self.item2host[item]
        self.trace("removehost %s, pending=%r" %(host.hostid, pending))
        return pending

    def triggertesting(self, colitems):
        colitems = self.filteritems(colitems)
        senditems = []
        for next in colitems:
            if isinstance(next, Item):
                senditems.append(next)
            else:
                ev = basic_collect_report(next)
                self.bus.notify(event.CollectionStart(next))
                self.queue.put(ev)
        self.senditems(senditems)

    def senditems(self, tosend):
        if not tosend:
            return 
        for host, pending in self.host2pending.items():
            room = self.MAXITEMSPERHOST - len(pending)
            if room > 0:
                sending = tosend[:room]
                host.node.sendlist(sending)
                self.trace("sent to host %s: %r" %(host.hostid, sending))
                for item in sending:
                    #assert item not in self.item2host, (
                    #    "sending same item %r to multiple hosts "
                    #    "not implemented" %(item,))
                    self.item2host[item] = host
                    self.bus.notify(event.ItemStart(item, host))
                pending.extend(sending)
                tosend[:] = tosend[room:]  # update inplace
                if not tosend:
                    break
        if tosend:
            # we have some left, give it to the main loop
            self.queue.put(event.RescheduleItems(tosend))

    def removeitem(self, item):
        if item not in self.item2host:
            raise AssertionError(item, self.item2host)
        host = self.item2host.pop(item)
        self.host2pending[host].remove(item)
        self.trace("removed %r, host=%r" %(item,host.hostid))

    def handle_crashitem(self, item, host):
        longrepr = "%r CRASHED THE HOST %r" %(item, host)
        outcome = OutcomeRepr(when="execute", shortrepr="c", longrepr=longrepr)
        rep = event.ItemTestReport(item, failed=outcome)
        self.bus.notify(rep)

    def setup_hosts(self):
        """ setup any neccessary resources ahead of the test run. """
        self.hm = HostManager(self)
        self.hm.setup_hosts(notify=self.queue.put)

    def teardown_hosts(self):
        """ teardown any resources after a test run. """ 
        for host in self.host2pending:
            host.gw.exit()


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
