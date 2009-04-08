""" 
    internal classes for

    * executing test items 
    * running collectors 
    * and generating report events about it 
"""

import py

from py.__.test.outcome import Exit, Skipped

def basic_run_report(item, pdb=None):
    """ return report about setting up and running a test item. """ 
    excinfo = None
    capture = item.config._getcapture()
    try:
        try:
            when = "setup"
            item.config._setupstate.prepare(item)
            try:
                when = "execute"
                res = item.runtest()
            finally:
                when = "teardown"
                item.config._setupstate.teardown_exact(item)
                when = "execute"
        finally:
            outerr = capture.reset()
    except (Exit, KeyboardInterrupt):
        raise
    except: 
        excinfo = py.code.ExceptionInfo()
    testrep = item.config.api.pytest_item_makereport(
        item=item, excinfo=excinfo, when=when, outerr=outerr)
    if pdb and testrep.failed:
        tw = py.io.TerminalWriter()
        testrep.toterminal(tw)
        pdb(excinfo)
    return testrep

def basic_collect_report(collector):
    excinfo = res = None
    try:
        capture = collector.config._getcapture()
        try:
            res = collector._memocollect()
        finally:
            outerr = capture.reset()
    except (Exit, KeyboardInterrupt):
        raise
    except: 
        excinfo = py.code.ExceptionInfo()
    return CollectReport(collector, res, excinfo, outerr)

from cPickle import Pickler, Unpickler

def forked_run_report(item, pdb=None):
    EXITSTATUS_TESTEXIT = 4
    from py.__.test.dist.mypickle import ImmutablePickler
    ipickle = ImmutablePickler(uneven=0)
    ipickle.selfmemoize(item.config)
    def runforked():
        try:
            testrep = basic_run_report(item)
        except (KeyboardInterrupt, Exit): 
            py.std.os._exit(EXITSTATUS_TESTEXIT)
        return ipickle.dumps(testrep)

    ff = py.process.ForkedFunc(runforked)
    result = ff.waitfinish()
    if result.retval is not None:
        return ipickle.loads(result.retval)
    else:
        if result.exitstatus == EXITSTATUS_TESTEXIT:
            raise Exit("forked test item %s raised Exit" %(item,))
        return report_process_crash(item, result)

def report_process_crash(item, result):
    path, lineno = item.getfslineno()
    longrepr = [
        ("X", "CRASHED"), 
        ("%s:%s: CRASHED with signal %d" %(path, lineno, result.signal)),
    ]
    return ItemTestReport(item, excinfo=longrepr, when="???")

class BaseReport(object):
    def __repr__(self):
        l = ["%s=%s" %(key, value)
           for key, value in self.__dict__.items()]
        return "<%s %s>" %(self.__class__.__name__, " ".join(l),)

    def toterminal(self, out):
        longrepr = self.longrepr 
        if hasattr(longrepr, 'toterminal'):
            longrepr.toterminal(out)
        else:
            out.line(str(longrepr))
   
class ItemTestReport(BaseReport):
    failed = passed = skipped = False

    def __init__(self, colitem, excinfo=None, when=None, outerr=None):
        self.colitem = colitem 
        if colitem and when != "setup":
            self.keywords = colitem.readkeywords() 
        else:
            # if we fail during setup it might mean 
            # we are not able to access the underlying object
            # this might e.g. happen if we are unpickled 
            # and our parent collector did not collect us 
            # (because it e.g. skipped for platform reasons)
            self.keywords = {}  
        if not excinfo:
            self.passed = True
            self.shortrepr = "." 
        else:
            self.when = when 
            if not isinstance(excinfo, py.code.ExceptionInfo):
                self.failed = True
                shortrepr = "?"
                longrepr = excinfo 
            elif excinfo.errisinstance(Skipped):
                self.skipped = True 
                shortrepr = "s"
                longrepr = self.colitem._repr_failure_py(excinfo, outerr)
            else:
                self.failed = True
                shortrepr = self.colitem.shortfailurerepr
                if self.when == "execute":
                    longrepr = self.colitem.repr_failure(excinfo, outerr)
                else: # exception in setup or teardown 
                    longrepr = self.colitem._repr_failure_py(excinfo, outerr)
                    shortrepr = shortrepr.lower()
            self.shortrepr = shortrepr 
            self.longrepr = longrepr 
            

class CollectReport(BaseReport):
    skipped = failed = passed = False 

    def __init__(self, colitem, result, excinfo=None, outerr=None):
        # XXX rename to collector 
        self.colitem = colitem 
        if not excinfo:
            self.passed = True
            self.result = result 
        else:
            self.outerr = outerr
            self.longrepr = self.colitem._repr_failure_py(excinfo, outerr)
            if excinfo.errisinstance(Skipped):
                self.skipped = True
                self.reason = str(excinfo.value)
            else:
                self.failed = True

class ItemSetupReport(BaseReport):
    failed = passed = skipped = False
    def __init__(self, item, excinfo=None, outerr=None):
        self.item = item 
        self.outerr = outerr 
        if not excinfo:
            self.passed = True
        else:
            if excinfo.errisinstance(Skipped):
                self.skipped = True 
            else:
                self.failed = True
            self.excrepr = item._repr_failure_py(excinfo, [])

class SetupState(object):
    """ shared state for setting up/tearing down test items or collectors. """
    def __init__(self):
        self.stack = []

    def teardown_all(self): 
        while self.stack: 
            col = self.stack.pop() 
            col.teardown() 

    def teardown_exact(self, item):
        if self.stack and self.stack[-1] == item:
            col = self.stack.pop()
            col.teardown()
     
    def prepare(self, colitem): 
        """ setup objects along the collector chain to the test-method
            Teardown any unneccessary previously setup objects."""
        needed_collectors = colitem.listchain() 
        while self.stack: 
            if self.stack == needed_collectors[:len(self.stack)]: 
                break 
            col = self.stack.pop() 
            col.teardown()
        for col in needed_collectors[len(self.stack):]: 
            col.setup() 
            self.stack.append(col) 
