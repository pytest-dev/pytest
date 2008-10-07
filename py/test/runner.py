""" 
    internal classes for

    * executing test items 
    * running collectors 
    * and generating report events about it 
"""

import py, os, sys

from py.__.test import event
from py.__.test.outcome import Skipped, Exit
from py.__.test.dsession.mypickle import ImmutablePickler
import py.__.test.custompdb

class RobustRun(object):
    """ a robust setup/execute/teardown protocol. """
    def __init__(self, colitem, pdb=None):
        self.colitem = colitem 
        self.getcapture = colitem._config._getcapture 
        self.pdb = pdb 

    def __repr__(self):
        return "<%s colitem=%s>" %(self.__class__.__name__, self.colitem)

    def run(self):
        """ return result of running setup, execution, teardown procedures. """ 
        excinfo = None
        res = NORESULT
        capture = self.getcapture()
        try:
            try:
                when = "setup"
                self.setup()
                try:
                    res = self.execute()
                finally:
                    when = "teardown"
                    self.teardown()
                    when = "execute"
            finally:
                outerr = capture.reset()
        except (Exit, KeyboardInterrupt):
            raise
        except: 
            excinfo = py.code.ExceptionInfo()
        return self.makereport(res, when, excinfo, outerr)

    def getkw(self, when, excinfo, outerr):
        if excinfo.errisinstance(Skipped):
            outcome = "skipped"
            shortrepr = "s"
            longrepr = excinfo._getreprcrash()
        else:
            outcome = "failed"
            if when == "execute":
                longrepr = self.colitem.repr_failure(excinfo, outerr)
                shortrepr = self.colitem.shortfailurerepr
            else:
                longrepr = self.colitem._repr_failure_py(excinfo, outerr)
                shortrepr = self.colitem.shortfailurerepr.lower()
        kw = { outcome: OutcomeRepr(when, shortrepr, longrepr)}
        return kw

class ItemRunner(RobustRun):
    def setup(self):
        self.colitem._setupstate.prepare(self.colitem)
    def teardown(self):
        self.colitem._setupstate.teardown_exact(self.colitem)
    def execute(self):
        self.colitem.runtest()
    def makereport(self, res, when, excinfo, outerr):
        if excinfo: 
            kw = self.getkw(when, excinfo, outerr)
        else:
            kw = {'passed': OutcomeRepr(when, '.', "")}
        testrep = event.ItemTestReport(self.colitem, **kw)
        if self.pdb and testrep.failed:
            tw = py.io.TerminalWriter()
            testrep.toterminal(tw)
            self.pdb(excinfo)
        return testrep

class CollectorRunner(RobustRun):
    def setup(self):
        pass
    def teardown(self):
        pass
    def execute(self):
        return self.colitem._memocollect()
    def makereport(self, res, when, excinfo, outerr):
        if excinfo: 
            kw = self.getkw(when, excinfo, outerr)
        else:
            kw = {'passed': OutcomeRepr(when, '', "")}
        return event.CollectionReport(self.colitem, res, **kw)

NORESULT = object()
# 
# public entrypoints / objects 
#

class OutcomeRepr(object):
    def __init__(self, when, shortrepr, longrepr):
        self.when = when
        self.shortrepr = shortrepr 
        self.longrepr = longrepr 
    def __str__(self):
        return "<OutcomeRepr when=%r, shortrepr=%r, len-longrepr=%s" %(
            self.when, self.shortrepr, len(str(self.longrepr)))

def basic_collect_report(item):
    return CollectorRunner(item).run()
    
def basic_run_report(item, pdb=None):
    return ItemRunner(item, pdb=pdb).run()

from cPickle import Pickler, Unpickler
from cStringIO import StringIO

def forked_run_report(item, pdb=None):
    EXITSTATUS_TESTEXIT = 4

    ipickle = ImmutablePickler(uneven=0)
    ipickle.selfmemoize(item._config)
    def runforked():
        try:
            testrep = basic_run_report(item)
        except (KeyboardInterrupt, Exit): 
            os._exit(EXITSTATUS_TESTEXIT)
        return ipickle.dumps(testrep)

    ff = py.process.ForkedFunc(runforked)
    result = ff.waitfinish()
    if result.retval is not None:
        return ipickle.loads(result.retval)
    else:
        if result.exitstatus == EXITSTATUS_TESTEXIT:
            raise Exit("forked test item %s raised Exit" %(item,))
        return report_crash(item, result)

def report_crash(item, result):
    path, lineno = item.getfslineno()
    longrepr = [
        ("X", "CRASHED"), 
        ("%s:%s: CRASHED with signal %d" %(path, lineno, result.signal)),
    ]
    outcomerepr = OutcomeRepr(when="???", shortrepr="X", longrepr=longrepr)
    return event.ItemTestReport(item, failed=outcomerepr)
