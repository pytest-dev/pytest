""" 
collect and run test items and create reports. 
"""

import py
from py.impl.test.outcome import Skipped

#
# pytest plugin hooks 

# XXX move to pytest_sessionstart and fix py.test owns tests 
def pytest_configure(config):
    config._setupstate = SetupState()

def pytest_sessionfinish(session, exitstatus):
    if hasattr(session.config, '_setupstate'):
        hook = session.config.hook
        rep = hook.pytest__teardown_final(session=session)
        if rep:
            hook.pytest__teardown_final_logerror(report=rep)

def pytest_make_collect_report(collector):
    result = excinfo = None
    try:
        result = collector._memocollect()
    except KeyboardInterrupt:
        raise
    except:
        excinfo = py.code.ExceptionInfo()
    return CollectReport(collector, result, excinfo)

def pytest_runtest_protocol(item):
    runtestprotocol(item)
    return True

def runtestprotocol(item, log=True):
    rep = call_and_report(item, "setup", log)
    reports = [rep]
    if rep.passed:
        reports.append(call_and_report(item, "call", log))
    reports.append(call_and_report(item, "teardown", log))
    return reports

def pytest_runtest_setup(item):
    item.config._setupstate.prepare(item)

def pytest_runtest_call(item):
    if not item._deprecated_testexecution():
        item.runtest()

def pytest_runtest_makereport(item, call):
    return ItemTestReport(item, call.excinfo, call.when)

def pytest_runtest_teardown(item):
    item.config._setupstate.teardown_exact(item)

def pytest__teardown_final(session):
    call = CallInfo(session.config._setupstate.teardown_all, when="teardown")
    if call.excinfo:
        ntraceback = call.excinfo.traceback .cut(excludepath=py._pydir)
        call.excinfo.traceback = ntraceback.filter()
        rep = TeardownErrorReport(call.excinfo)
        return rep 

def pytest_report_teststatus(report):
    if report.when in ("setup", "teardown"):
        if report.failed:
            #      category, shortletter, verbose-word 
            return "error", "E", "ERROR"
        elif report.skipped:
            return "skipped", "s", "SKIPPED"
        else:
            return "", "", ""
#
# Implementation

def call_and_report(item, when, log=True):
    call = call_runtest_hook(item, when)
    hook = item.ihook
    report = hook.pytest_runtest_makereport(item=item, call=call)
    if log and (when == "call" or not report.passed):
        hook.pytest_runtest_logreport(report=report) 
    return report

def call_runtest_hook(item, when):
    hookname = "pytest_runtest_" + when 
    ihook = getattr(item.ihook, hookname)
    return CallInfo(lambda: ihook(item=item), when=when)

class CallInfo:
    excinfo = None 
    def __init__(self, func, when):
        self.when = when 
        try:
            self.result = func()
        except KeyboardInterrupt:
            raise
        except:
            self.excinfo = py.code.ExceptionInfo()

    def __repr__(self):
        if self.excinfo:
            status = "exception: %s" % str(self.excinfo.value)
        else:
            status = "result: %r" % (self.result,)
        return "<CallInfo when=%r %s>" % (self.when, status)

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

    def __init__(self, item, excinfo=None, when=None):
        self.item = item 
        self.when = when
        if item and when != "setup":
            self.keywords = item.readkeywords() 
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
            if not isinstance(excinfo, py.code.ExceptionInfo):
                self.failed = True
                shortrepr = "?"
                longrepr = excinfo 
            elif excinfo.errisinstance(Skipped):
                self.skipped = True 
                shortrepr = "s"
                longrepr = self.item._repr_failure_py(excinfo)
            else:
                self.failed = True
                shortrepr = self.item.shortfailurerepr
                if self.when == "call":
                    longrepr = self.item.repr_failure(excinfo)
                else: # exception in setup or teardown 
                    longrepr = self.item._repr_failure_py(excinfo)
                    shortrepr = shortrepr.lower()
            self.shortrepr = shortrepr 
            self.longrepr = longrepr 

    def __repr__(self):
        status = (self.passed and "passed" or 
                  self.skipped and "skipped" or 
                  self.failed and "failed" or 
                  "CORRUPT")
        l = [repr(self.item.name), "when=%r" % self.when, "outcome %r" % status,]
        if hasattr(self, 'node'):
            l.append("txnode=%s" % self.node.gateway.id)
        info = " " .join(map(str, l))
        return "<ItemTestReport %s>" % info 

    def getnode(self):
        return self.item 

class CollectReport(BaseReport):
    skipped = failed = passed = False 

    def __init__(self, collector, result, excinfo=None):
        self.collector = collector 
        if not excinfo:
            self.passed = True
            self.result = result 
        else:
            self.longrepr = self.collector._repr_failure_py(excinfo)
            if excinfo.errisinstance(Skipped):
                self.skipped = True
                self.reason = str(excinfo.value)
            else:
                self.failed = True

    def getnode(self):
        return self.collector 

class TeardownErrorReport(BaseReport):
    skipped = passed = False 
    failed = True
    when = "teardown"
    def __init__(self, excinfo):
        self.longrepr = excinfo.getrepr(funcargs=True)

class SetupState(object):
    """ shared state for setting up/tearing down test items or collectors. """
    def __init__(self):
        self.stack = []
        self._finalizers = {}

    def addfinalizer(self, finalizer, colitem):
        """ attach a finalizer to the given colitem. 
        if colitem is None, this will add a finalizer that 
        is called at the end of teardown_all(). 
        """
        assert hasattr(finalizer, '__call__')
        #assert colitem in self.stack
        self._finalizers.setdefault(colitem, []).append(finalizer)

    def _pop_and_teardown(self):
        colitem = self.stack.pop()
        self._teardown_with_finalization(colitem)

    def _callfinalizers(self, colitem):
        finalizers = self._finalizers.pop(colitem, None)
        while finalizers:
            fin = finalizers.pop()
            fin()

    def _teardown_with_finalization(self, colitem): 
        self._callfinalizers(colitem) 
        if colitem: 
            colitem.teardown()
        for colitem in self._finalizers:
            assert colitem is None or colitem in self.stack

    def teardown_all(self): 
        while self.stack: 
            self._pop_and_teardown()
        self._teardown_with_finalization(None)
        assert not self._finalizers

    def teardown_exact(self, item):
        if self.stack and item == self.stack[-1]:
            self._pop_and_teardown()
        else:
            self._callfinalizers(item)
     
    def prepare(self, colitem): 
        """ setup objects along the collector chain to the test-method
            and teardown previously setup objects."""
        needed_collectors = colitem.listchain() 
        while self.stack: 
            if self.stack == needed_collectors[:len(self.stack)]: 
                break 
            self._pop_and_teardown()
        for col in needed_collectors[len(self.stack):]: 
            col.setup() 
            self.stack.append(col) 
