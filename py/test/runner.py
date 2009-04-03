""" 
    internal classes for

    * executing test items 
    * running collectors 
    * and generating report events about it 
"""

import py, os, sys

from py.__.test import event
from py.__.test.outcome import Exit
from py.__.test.dist.mypickle import ImmutablePickler

class RobustRun(object):
    """ a robust setup/execute/teardown protocol used both for test collectors 
        and test items. 
    """
    def __init__(self, colitem, pdb=None):
        self.colitem = colitem 
        self.getcapture = colitem.config._getcapture 
        self.pdb = pdb 

    def __repr__(self):
        return "<%s colitem=%s>" %(self.__class__.__name__, self.colitem)


class ItemRunner(RobustRun):
    def run(self):
        """ return result of running setup, execution, teardown procedures. """ 
        excinfo = None
        capture = self.getcapture()
        try:
            try:
                when = "setup"
                self.colitem.config._setupstate.prepare(self.colitem)
                try:
                    when = "execute"
                    res = self.colitem.runtest()
                finally:
                    when = "teardown"
                    self.colitem.config._setupstate.teardown_exact(self.colitem)
                    when = "execute"
            finally:
                outerr = capture.reset()
        except (Exit, KeyboardInterrupt):
            raise
        except: 
            excinfo = py.code.ExceptionInfo()
        return self.makereport(when, excinfo, outerr)

    def makereport(self, when, excinfo, outerr):
        testrep = self.colitem.config.pytestplugins.call_firstresult(
            "pytest_item_makereport", item=self.colitem, 
            excinfo=excinfo, when=when, outerr=outerr)
        if self.pdb and testrep.failed:
            tw = py.io.TerminalWriter()
            testrep.toterminal(tw)
            self.pdb(excinfo)
        return testrep

class CollectorRunner(RobustRun):
    def run(self):
        """ return result of running setup, execution, teardown procedures. """ 
        excinfo = None
        res = NORESULT
        capture = self.getcapture()
        try:
            try:
                res = self.colitem._memocollect()
            finally:
                outerr = capture.reset()
        except (Exit, KeyboardInterrupt):
            raise
        except: 
            excinfo = py.code.ExceptionInfo()
        return self.makereport(res, "execute", excinfo, outerr)

    def makereport(self, res, when, excinfo, outerr):
        return event.CollectionReport(self.colitem, res, excinfo, when, outerr)
   
NORESULT = object()
# 
# public entrypoints / objects 
#

def basic_collect_report(item):
    return CollectorRunner(item).run()
    
def basic_run_report(item, pdb=None):
    return ItemRunner(item, pdb=pdb).run()

from cPickle import Pickler, Unpickler
from cStringIO import StringIO

def forked_run_report(item, pdb=None):
    EXITSTATUS_TESTEXIT = 4

    ipickle = ImmutablePickler(uneven=0)
    ipickle.selfmemoize(item.config)
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
        return report_process_crash(item, result)

def report_process_crash(item, result):
    path, lineno = item.getfslineno()
    longrepr = [
        ("X", "CRASHED"), 
        ("%s:%s: CRASHED with signal %d" %(path, lineno, result.signal)),
    ]
    return event.ItemTestReport(item, excinfo=longrepr, when="???")
