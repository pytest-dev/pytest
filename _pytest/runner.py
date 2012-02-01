""" basic collect and runtest protocol implementations """

import py, sys, time
from py._code.code import TerminalRepr

def pytest_namespace():
    return {
        'fail'         : fail,
        'skip'         : skip,
        'importorskip' : importorskip,
        'exit'         : exit,
    }

#
# pytest plugin hooks

def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group.addoption('--durations',
         action="store", type="int", default=None, metavar="N",
         help="show N slowest setup/test durations (N=0 for all)."),

def pytest_terminal_summary(terminalreporter):
    durations = terminalreporter.config.option.durations
    if durations is None:
        return
    tr = terminalreporter
    dlist = []
    for replist in tr.stats.values():
        for rep in replist:
            if hasattr(rep, 'duration'):
                dlist.append(rep)
    if not dlist:
        return
    dlist.sort(key=lambda x: x.duration)
    dlist.reverse()
    if not durations:
        tr.write_sep("=", "slowest test durations")
    else:
        tr.write_sep("=", "slowest %s test durations" % durations)
        dlist = dlist[:durations]

    for rep in dlist:
        nodeid = rep.nodeid.replace("::()::", "::")
        tr.write_line("%02.2fs %-8s %s" %
            (rep.duration, rep.when, nodeid))

def pytest_sessionstart(session):
    session._setupstate = SetupState()
def pytest_sessionfinish(session):
    session._setupstate.teardown_all()

class NodeInfo:
    def __init__(self, location):
        self.location = location

def pytest_runtest_protocol(item, nextitem):
    item.ihook.pytest_runtest_logstart(
        nodeid=item.nodeid, location=item.location,
    )
    runtestprotocol(item, nextitem=nextitem)
    return True

def runtestprotocol(item, log=True, nextitem=None):
    rep = call_and_report(item, "setup", log)
    reports = [rep]
    if rep.passed:
        reports.append(call_and_report(item, "call", log))
    reports.append(call_and_report(item, "teardown", log,
        nextitem=nextitem))
    return reports

def pytest_runtest_setup(item):
    item.session._setupstate.prepare(item)

def pytest_runtest_call(item):
    item.runtest()

def pytest_runtest_teardown(item, nextitem):
    item.session._setupstate.teardown_exact(item, nextitem)

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

def call_and_report(item, when, log=True, **kwds):
    call = call_runtest_hook(item, when, **kwds)
    hook = item.ihook
    report = hook.pytest_runtest_makereport(item=item, call=call)
    if log:
        hook.pytest_runtest_logreport(report=report)
    return report

def call_runtest_hook(item, when, **kwds):
    hookname = "pytest_runtest_" + when
    ihook = getattr(item.ihook, hookname)
    return CallInfo(lambda: ihook(item=item, **kwds), when=when)

class CallInfo:
    """ Result/Exception info a function invocation. """
    #: None or ExceptionInfo object.
    excinfo = None
    def __init__(self, func, when):
        #: context of invocation: one of "setup", "call",
        #: "teardown", "memocollect"
        self.when = when
        self.start = time.time()
        try:
            try:
                self.result = func()
            except KeyboardInterrupt:
                raise
            except:
                self.excinfo = py.code.ExceptionInfo()
        finally:
            self.stop = time.time()

    def __repr__(self):
        if self.excinfo:
            status = "exception: %s" % str(self.excinfo.value)
        else:
            status = "result: %r" % (self.result,)
        return "<CallInfo when=%r %s>" % (self.when, status)

def getslaveinfoline(node):
    try:
        return node._slaveinfocache
    except AttributeError:
        d = node.slaveinfo
        ver = "%s.%s.%s" % d['version_info'][:3]
        node._slaveinfocache = s = "[%s] %s -- Python %s %s" % (
            d['id'], d['sysplatform'], ver, d['executable'])
        return s

class BaseReport(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def toterminal(self, out):
        longrepr = self.longrepr
        if hasattr(self, 'node'):
            out.line(getslaveinfoline(self.node))
        if hasattr(longrepr, 'toterminal'):
            longrepr.toterminal(out)
        else:
            out.line(str(longrepr))

    passed = property(lambda x: x.outcome == "passed")
    failed = property(lambda x: x.outcome == "failed")
    skipped = property(lambda x: x.outcome == "skipped")

    @property
    def fspath(self):
        return self.nodeid.split("::")[0]

def pytest_runtest_makereport(item, call):
    when = call.when
    duration = call.stop-call.start
    keywords = dict([(x,1) for x in item.keywords])
    excinfo = call.excinfo
    if not call.excinfo:
        outcome = "passed"
        longrepr = None
    else:
        excinfo = call.excinfo
        if not isinstance(excinfo, py.code.ExceptionInfo):
            outcome = "failed"
            longrepr = excinfo
        elif excinfo.errisinstance(py.test.skip.Exception):
            outcome = "skipped"
            r = excinfo._getreprcrash()
            longrepr = (str(r.path), r.lineno, r.message)
        else:
            outcome = "failed"
            if call.when == "call":
                longrepr = item.repr_failure(excinfo)
            else: # exception in setup or teardown
                longrepr = item._repr_failure_py(excinfo)
    return TestReport(item.nodeid, item.location,
                      keywords, outcome, longrepr, when,
                      duration=duration)

class TestReport(BaseReport):
    """ Basic test report object (also used for setup and teardown calls if
    they fail).
    """
    def __init__(self, nodeid, location,
            keywords, outcome, longrepr, when, sections=(), duration=0, **extra):
        #: normalized collection node id
        self.nodeid = nodeid

        #: a (filesystempath, lineno, domaininfo) tuple indicating the
        #: actual location of a test item - it might be different from the
        #: collected one e.g. if a method is inherited from a different module.
        self.location = location

        #: a name -> value dictionary containing all keywords and
        #: markers associated with a test invocation.
        self.keywords = keywords

        #: test outcome, always one of "passed", "failed", "skipped".
        self.outcome = outcome

        #: None or a failure representation.
        self.longrepr = longrepr

        #: one of 'setup', 'call', 'teardown' to indicate runtest phase.
        self.when = when

        #: list of (secname, data) extra information which needs to
        #: marshallable
        self.sections = list(sections)

        #: time it took to run just the test
        self.duration = duration

        self.__dict__.update(extra)

    def __repr__(self):
        return "<TestReport %r when=%r outcome=%r>" % (
            self.nodeid, self.when, self.outcome)

class TeardownErrorReport(BaseReport):
    outcome = "failed"
    when = "teardown"
    def __init__(self, longrepr, **extra):
        self.longrepr = longrepr
        self.sections = []
        self.__dict__.update(extra)

def pytest_make_collect_report(collector):
    call = CallInfo(collector._memocollect, "memocollect")
    longrepr = None
    if not call.excinfo:
        outcome = "passed"
    else:
        if call.excinfo.errisinstance(py.test.skip.Exception):
            outcome = "skipped"
            r = collector._repr_failure_py(call.excinfo, "line").reprcrash
            longrepr = (str(r.path), r.lineno, r.message)
        else:
            outcome = "failed"
            errorinfo = collector.repr_failure(call.excinfo)
            if not hasattr(errorinfo, "toterminal"):
                errorinfo = CollectErrorRepr(errorinfo)
            longrepr = errorinfo
    return CollectReport(collector.nodeid, outcome, longrepr,
        getattr(call, 'result', None))

class CollectReport(BaseReport):
    def __init__(self, nodeid, outcome, longrepr, result, sections=(), **extra):
        self.nodeid = nodeid
        self.outcome = outcome
        self.longrepr = longrepr
        self.result = result or []
        self.sections = list(sections)
        self.__dict__.update(extra)

    @property
    def location(self):
        return (self.fspath, None, self.fspath)

    def __repr__(self):
        return "<CollectReport %r lenresult=%s outcome=%r>" % (
                self.nodeid, len(self.result), self.outcome)

class CollectErrorRepr(TerminalRepr):
    def __init__(self, msg):
        self.longrepr = msg
    def toterminal(self, out):
        out.line(str(self.longrepr), red=True)

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

    def teardown_exact(self, item, nextitem):
        needed_collectors = nextitem and nextitem.listchain() or []
        self._teardown_towards(needed_collectors)

    def _teardown_towards(self, needed_collectors):
        while self.stack:
            if self.stack == needed_collectors[:len(self.stack)]:
                break
            self._pop_and_teardown()

    def prepare(self, colitem):
        """ setup objects along the collector chain to the test-method
            and teardown previously setup objects."""
        needed_collectors = colitem.listchain()
        self._teardown_towards(needed_collectors)

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
    def __init__(self, msg=None, pytrace=True):
        self.msg = msg
        self.pytrace = pytrace

    def __repr__(self):
        if self.msg:
            return str(self.msg)
        return "<%s instance>" %(self.__class__.__name__,)
    __str__ = __repr__

class Skipped(OutcomeException):
    # XXX hackish: on 3k we fake to live in the builtins
    # in order to have Skipped exception printing shorter/nicer
    __module__ = 'builtins'

class Failed(OutcomeException):
    """ raised from an explicit call to py.test.fail() """
    __module__ = 'builtins'

class Exit(KeyboardInterrupt):
    """ raised for immediate program exits (no tracebacks/summaries)"""
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
    better to use the py.test.mark.skipif marker to declare a test to be
    skipped under certain conditions like mismatching platforms or
    dependencies.  See the pytest_skipping plugin for details.
    """
    __tracebackhide__ = True
    raise Skipped(msg=msg)
skip.Exception = Skipped

def fail(msg="", pytrace=True):
    """ explicitely fail an currently-executing test with the given Message.
    if @pytrace is not True the msg represents the full failure information.
    """
    __tracebackhide__ = True
    raise Failed(msg=msg, pytrace=pytrace)
fail.Exception = Failed


def importorskip(modname, minversion=None):
    """ return imported module if it has a higher __version__ than the
    optionally specified 'minversion' - otherwise call py.test.skip()
    with a message detailing the mismatch.
    """
    __tracebackhide__ = True
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
