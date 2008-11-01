""" basic test session implementation. 

* drives collection of tests 
* triggers executions of tests   
* produces events used by reporting 
"""

import py
from py.__.test import event, outcome
from py.__.test.event import EventBus
import py.__.test.custompdb
from py.__.test.resultlog import ResultLog

# used for genitems()
from py.__.test.outcome import Exit
Item = (py.test.collect.Item, py.test.collect.Item)
Collector = (py.test.collect.Collector, py.test.collect.Collector)
from runner import basic_collect_report
from py.__.test.dsession.hostmanage import makehostup

class Session(object): 
    """ 
        Session drives the collection and running of tests
        and generates test events for reporters. 
    """ 
    def __init__(self, config):
        self.config = config
        self.bus = EventBus()
        self._nomatch = False
        eventlog = self.config.option.eventlog
        if eventlog:
            self.eventlog = py.path.local(eventlog)
            f = self.eventlog.open("w")
            def eventwrite(ev):
                print >>f, ev
                f.flush()
            self.bus.subscribe(eventwrite)
        resultlog = self.config.option.resultlog
        if resultlog:
            f = open(resultlog, 'w', 1) # line buffered
            self.resultlog = ResultLog(self.bus, f)

    def fixoptions(self):
        """ check, fix and determine conflicting options. """
        option = self.config.option 
        if option.runbrowser and not option.startserver:
            #print "--runbrowser implies --startserver"
            option.startserver = True
        # conflicting options
        if option.looponfailing and option.usepdb:
            raise ValueError, "--looponfailing together with --pdb not supported."
        if option.executable and option.usepdb:
            raise ValueError, "--exec together with --pdb not supported."

    def genitems(self, colitems, keywordexpr=None):
        """ yield Items from iterating over the given colitems. """
        while colitems: 
            next = colitems.pop(0)
            if isinstance(next, Item):
                remaining = self.filteritems([next])
                if remaining:
                    self.bus.notify(event.ItemStart(next))
                    yield next 
            else:
                assert isinstance(next, Collector)
                self.bus.notify(event.CollectionStart(next))
                ev = basic_collect_report(next)
                if ev.passed:
                    for x in self.genitems(ev.result, keywordexpr):
                        yield x 
                self.bus.notify(ev)

    def filteritems(self, colitems):
        """ return items to process (some may be deselected)"""
        keywordexpr = self.config.option.keyword 
        if not keywordexpr or self._nomatch:
            return colitems
        if keywordexpr[-1] == ":": 
            keywordexpr = keywordexpr[:-1]
        remaining = []
        deselected = []
        for colitem in colitems:
            if isinstance(colitem, Item):
                if colitem._skipbykeyword(keywordexpr):
                    deselected.append(colitem)
                    continue
            remaining.append(colitem)
        if deselected: 
            self.bus.notify(event.Deselected(deselected, ))
            if self.config.option.keyword.endswith(":"):
                self._nomatch = True
        return remaining 

    def collect(self, colitems): 
        keyword = self.config.option.keyword
        for x in self.genitems(colitems, keyword):
            yield x

    def sessionstarts(self):
        """ setup any neccessary resources ahead of the test run. """
        self.bus.notify(event.TestrunStart())
        self._failurelist = []
        self.bus.subscribe(self._processfailures)

    def _processfailures(self, ev):
        if isinstance(ev, event.BaseReport) and ev.failed:
            self._failurelist.append(ev) 
            if self.config.option.exitfirst: 
                self.shouldstop = True 

    def sessionfinishes(self, exitstatus=0, excinfo=None):
        """ teardown any resources after a test run. """ 
        self.bus.notify(event.TestrunFinish(exitstatus=exitstatus,
                                            excinfo=excinfo))
        self.bus.unsubscribe(self._processfailures)
        #self.reporter.deactivate()
        return self._failurelist 

    def getinitialitems(self, colitems):
        if colitems is None:
            colitems = [self.config.getfsnode(arg) 
                            for arg in self.config.args]
        return colitems

    def main(self, colitems=None):
        """ main loop for running tests. """
        colitems = self.getinitialitems(colitems)
        self.shouldstop = False 
        self.sessionstarts()
        self.bus.notify(makehostup())
        exitstatus = outcome.EXIT_OK
        captured_excinfo = None
        try:
            for item in self.collect(colitems): 
                if self.shouldstop: 
                    break 
                if not self.config.option.collectonly: 
                    self.runtest(item)
            py.test.collect.Item._setupstate.teardown_all()
        except KeyboardInterrupt:
            captured_excinfo = py.code.ExceptionInfo()
            exitstatus = outcome.EXIT_INTERRUPTED
        except:
            self.bus.notify(event.InternalException())
            exitstatus = outcome.EXIT_INTERNALERROR
        if self._failurelist and exitstatus == 0:
            exitstatus = outcome.EXIT_TESTSFAILED
        self.sessionfinishes(exitstatus=exitstatus, excinfo=captured_excinfo)
        return exitstatus

    def runpdb(self, excinfo):
        py.__.test.custompdb.post_mortem(excinfo._excinfo[2])

    def runtest(self, item):
        runner = item._getrunner()
        pdb = self.config.option.usepdb and self.runpdb or None
        testrep = runner(item, pdb=pdb) 
        self.bus.notify(testrep)

