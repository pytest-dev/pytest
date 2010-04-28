""" 
collect and run test items and create reports. 
"""

import py, sys

def pytest_namespace():
    return {
        'raises'       : raises, 
        'skip'         : skip,
        'importorskip' : importorskip,
        'fail'         : fail, 
        'exit'         : exit, 
    }

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
            elif excinfo.errisinstance(py.test.skip.Exception):
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
            if excinfo.errisinstance(py.test.skip.Exception):
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
        # check if the last collection node has raised an error 
        for col in self.stack:
            if hasattr(col, '_prepare_exc'):
                py.builtin._reraise(*col._prepare_exc) 
        for col in needed_collectors[len(self.stack):]: 
            self.stack.append(col) 
            try:
                col.setup() 
            except Exception:
                col._prepare_exc = sys.exc_info()
                raise

# =============================================================
# Test OutcomeExceptions and helpers for creating them. 


class OutcomeException(Exception): 
    """ OutcomeException and its subclass instances indicate and 
        contain info about test and collection outcomes. 
    """ 
    def __init__(self, msg=None, excinfo=None): 
        self.msg = msg 
        self.excinfo = excinfo

    def __repr__(self):
        if self.msg: 
            return repr(self.msg) 
        return "<%s instance>" %(self.__class__.__name__,)
    __str__ = __repr__

class Skipped(OutcomeException): 
    # XXX hackish: on 3k we fake to live in the builtins 
    # in order to have Skipped exception printing shorter/nicer
    __module__ = 'builtins'

class Failed(OutcomeException): 
    """ raised from an explicit call to py.test.fail() """
    __module__ = 'builtins'

class ExceptionFailure(Failed): 
    """ raised by py.test.raises on an exception-assertion mismatch. """
    def __init__(self, expr, expected, msg=None, excinfo=None): 
        Failed.__init__(self, msg=msg, excinfo=excinfo) 
        self.expr = expr 
        self.expected = expected

class Exit(KeyboardInterrupt):
    """ raised by py.test.exit for immediate program exits without tracebacks and reporter/summary. """
    def __init__(self, msg="unknown reason"):
        self.msg = msg 
        KeyboardInterrupt.__init__(self, msg)

# exposed helper methods 

def exit(msg): 
    """ exit testing process as if KeyboardInterrupt was triggered. """ 
    __tracebackhide__ = True
    raise Exit(msg)

exit.Exception = Exit

def skip(msg=""):
    """ skip an executing test with the given message.  Note: it's usually
    better use the py.test.mark.skipif marker to declare a test to be
    skipped under certain conditions like mismatching platforms or 
    dependencies.  See the pytest_skipping plugin for details. 
    """
    __tracebackhide__ = True
    raise Skipped(msg=msg) 

skip.Exception = Skipped

def fail(msg=""):
    """ explicitely fail an currently-executing test with the given Message. """
    __tracebackhide__ = True
    raise Failed(msg=msg) 

fail.Exception = Failed

def raises(ExpectedException, *args, **kwargs):
    """ if args[0] is callable: raise AssertionError if calling it with 
        the remaining arguments does not raise the expected exception.  
        if args[0] is a string: raise AssertionError if executing the
        the string in the calling scope does not raise expected exception. 
        for examples:
        x = 5
        raises(TypeError, lambda x: x + 'hello', x=x)
        raises(TypeError, "x + 'hello'")
    """
    __tracebackhide__ = True 
    assert args
    if isinstance(args[0], str):
        code, = args
        assert isinstance(code, str)
        frame = sys._getframe(1)
        loc = frame.f_locals.copy()
        loc.update(kwargs)
        #print "raises frame scope: %r" % frame.f_locals
        try:
            code = py.code.Source(code).compile()
            py.builtin.exec_(code, frame.f_globals, loc)
            # XXX didn'T mean f_globals == f_locals something special?
            #     this is destroyed here ...
        except ExpectedException:
            return py.code.ExceptionInfo()
    else:
        func = args[0]
        try:
            func(*args[1:], **kwargs)
        except ExpectedException:
            return py.code.ExceptionInfo()
        k = ", ".join(["%s=%r" % x for x in kwargs.items()])
        if k:
            k = ', ' + k
        expr = '%s(%r%s)' %(getattr(func, '__name__', func), args, k)
    raise ExceptionFailure(msg="DID NOT RAISE", 
                           expr=args, expected=ExpectedException) 

raises.Exception = ExceptionFailure

def importorskip(modname, minversion=None):
    """ return imported module if it has a higher __version__ than the 
    optionally specified 'minversion' - otherwise call py.test.skip() 
    with a message detailing the mismatch. 
    """
    compile(modname, '', 'eval') # to catch syntaxerrors
    try:
        mod = __import__(modname, None, None, ['__doc__'])
    except ImportError:
        py.test.skip("could not import %r" %(modname,))
    if minversion is None:
        return mod
    verattr = getattr(mod, '__version__', None)
    if isinstance(minversion, str):
        minver = minversion.split(".")
    else:
        minver = list(minversion)
    if verattr is None or verattr.split(".") < minver:
        py.test.skip("module %r has __version__ %r, required is: %r" %(
                     modname, verattr, minversion))
    return mod

