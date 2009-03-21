""" basic test session implementation. 

* drives collection of tests 
* triggers executions of tests   
* produces events used by reporting 
"""

import py
from py.__.test import event, outcome

# imports used for genitems()
Item = py.test.collect.Item
Collector = py.test.collect.Collector
from runner import basic_collect_report

class Session(object): 
    """ 
        Session drives the collection and running of tests
        and generates test events for reporters. 
    """ 
    def __init__(self, config):
        self.config = config
        self.bus = config.bus # shortcut 
        self.bus.register(self)
        self._testsfailed = False
        self._nomatch = False
        self.shouldstop = False

    def fixoptions(self):
        """ check, fix and determine conflicting options. """
        option = self.config.option 
        #if option.runbrowser and not option.startserver:
        #    #print "--runbrowser implies --startserver"
        #    option.startserver = True
        # conflicting options
        if option.looponfailing and option.usepdb:
            raise ValueError, "--looponfailing together with --pdb not supported."
        if option.executable and option.usepdb:
            raise ValueError, "--exec together with --pdb not supported."

    def genitems(self, colitems, keywordexpr=None):
        """ yield Items from iterating over the given colitems. """
        while colitems: 
            next = colitems.pop(0)
            if isinstance(next, (tuple, list)):
                colitems[:] = list(next) + colitems 
                continue
            assert self.bus is next.config.bus
            notify = self.bus.notify 
            if isinstance(next, Item):
                remaining = self.filteritems([next])
                if remaining:
                    notify("itemstart", next)
                    yield next 
            else:
                assert isinstance(next, Collector)
                notify("collectionstart", event.CollectionStart(next))
                ev = basic_collect_report(next)
                if ev.passed:
                    for x in self.genitems(ev.result, keywordexpr):
                        yield x 
                notify("collectionreport", ev)
            if self.shouldstop:
                break

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
            self.bus.notify("deselected", event.Deselected(deselected, ))
            if self.config.option.keyword.endswith(":"):
                self._nomatch = True
        return remaining 

    def collect(self, colitems): 
        keyword = self.config.option.keyword
        for x in self.genitems(colitems, keyword):
            yield x

    def sessionstarts(self):
        """ setup any neccessary resources ahead of the test run. """
        self.bus.notify("testrunstart", event.TestrunStart())
        
    def pyevent_itemtestreport(self, rep):
        if rep.failed:
            self._testsfailed = True
            if self.config.option.exitfirst:
                self.shouldstop = True
    pyevent_collectionreport = pyevent_itemtestreport

    def sessionfinishes(self, exitstatus=0, excinfo=None):
        """ teardown any resources after a test run. """ 
        self.bus.notify("testrunfinish", 
                        event.TestrunFinish(exitstatus=exitstatus, excinfo=excinfo))

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
        #self.bus.notify("testnodeready", maketestnodeready())
        exitstatus = outcome.EXIT_OK
        captured_excinfo = None
        try:
            for item in self.collect(colitems): 
                if self.shouldstop: 
                    break 
                if not self.config.option.collectonly: 
                    self.runtest(item)

            self.config._setupstate.teardown_all()
        except KeyboardInterrupt:
            captured_excinfo = py.code.ExceptionInfo()
            exitstatus = outcome.EXIT_INTERRUPTED
        except:
            captured_excinfo = py.code.ExceptionInfo()
            self.bus.notify("internalerror", event.InternalException(captured_excinfo))
            exitstatus = outcome.EXIT_INTERNALERROR
        if exitstatus == 0 and self._testsfailed:
            exitstatus = outcome.EXIT_TESTSFAILED
        self.sessionfinishes(exitstatus=exitstatus, excinfo=captured_excinfo)
        return exitstatus

    def runpdb(self, excinfo):
        from py.__.test.custompdb import post_mortem
        post_mortem(excinfo._excinfo[2])

    def runtest(self, item):
        runner = item._getrunner()
        pdb = self.config.option.usepdb and self.runpdb or None
        testrep = runner(item, pdb=pdb) 
        self.bus.notify("itemtestreport", testrep)
