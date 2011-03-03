""" support for skip/xfail functions and markers. """

import py, pytest
import sys

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption('--runxfail',
           action="store_true", dest="runxfail", default=False,
           help="run tests even if they are marked xfail")

def pytest_namespace():
    return dict(xfail=xfail)

class XFailed(pytest.fail.Exception):
    """ raised from an explicit call to py.test.xfail() """

def xfail(reason=""):
    """ xfail an executing test or setup functions with the given reason."""
    __tracebackhide__ = True
    raise XFailed(reason)
xfail.Exception = XFailed

class MarkEvaluator:
    def __init__(self, item, name):
        self.item = item
        self.name = name

    @property
    def holder(self):
        return self.item.keywords.get(self.name, None)
    def __bool__(self):
        return bool(self.holder)
    __nonzero__ = __bool__

    def wasvalid(self):
        return not hasattr(self, 'exc')

    def istrue(self):
        try:
            return self._istrue()
        except KeyboardInterrupt:
            raise
        except:
            self.exc = sys.exc_info()
            if isinstance(self.exc[1], SyntaxError):
                msg = [" " * (self.exc[1].offset + 4) + "^",]
                msg.append("SyntaxError: invalid syntax")
            else:
                msg = py.std.traceback.format_exception_only(*self.exc[:2])
            pytest.fail("Error evaluating %r expression\n"
                        "    %s\n"
                        "%s"
                        %(self.name, self.expr, "\n".join(msg)),
                        pytrace=False)

    def _getglobals(self):
        d = {'os': py.std.os, 'sys': py.std.sys, 'config': self.item.config}
        func = self.item.obj
        try:
            d.update(func.__globals__)
        except AttributeError:
            d.update(func.func_globals)
        return d

    def _istrue(self):
        if self.holder:
            d = self._getglobals()
            if self.holder.args:
                self.result = False
                for expr in self.holder.args:
                    self.expr = expr
                    if isinstance(expr, str):
                        result = cached_eval(self.item.config, expr, d)
                    else:
                        pytest.fail("expression is not a string")
                    if result:
                        self.result = True
                        self.expr = expr
                        break
            else:
                self.result = True
        return getattr(self, 'result', False)

    def get(self, attr, default=None):
        return self.holder.kwargs.get(attr, default)

    def getexplanation(self):
        expl = self.get('reason', None)
        if not expl:
            if not hasattr(self, 'expr'):
                return ""
            else:
                return "condition: " + str(self.expr)
        return expl


def pytest_runtest_setup(item):
    if not isinstance(item, pytest.Function):
        return
    evalskip = MarkEvaluator(item, 'skipif')
    if evalskip.istrue():
        py.test.skip(evalskip.getexplanation())
    item._evalxfail = MarkEvaluator(item, 'xfail')
    check_xfail_no_run(item)

def pytest_pyfunc_call(pyfuncitem):
    check_xfail_no_run(pyfuncitem)

def check_xfail_no_run(item):
    if not item.config.option.runxfail:
        evalxfail = item._evalxfail
        if evalxfail.istrue():
            if not evalxfail.get('run', True):
                py.test.xfail("[NOTRUN] " + evalxfail.getexplanation())

def pytest_runtest_makereport(__multicall__, item, call):
    if not isinstance(item, pytest.Function):
        return
    if not (call.excinfo and
        call.excinfo.errisinstance(py.test.xfail.Exception)):
        evalxfail = getattr(item, '_evalxfail', None)
        if not evalxfail:
            return
    if call.excinfo and call.excinfo.errisinstance(py.test.xfail.Exception):
        if not item.config.getvalue("runxfail"):
            rep = __multicall__.execute()
            rep.keywords['xfail'] = "reason: " + call.excinfo.value.msg
            rep.outcome = "skipped"
            return rep
    rep = __multicall__.execute()
    evalxfail = item._evalxfail
    if not item.config.option.runxfail:
        if evalxfail.wasvalid() and evalxfail.istrue():
            if call.excinfo:
                rep.outcome = "skipped"
                rep.keywords['xfail'] = evalxfail.getexplanation()
            elif call.when == "call":
                rep.outcome = "failed"
                rep.keywords['xfail'] = evalxfail.getexplanation()
            return rep
    if 'xfail' in rep.keywords:
        del rep.keywords['xfail']
    return rep

# called by terminalreporter progress reporting
def pytest_report_teststatus(report):
    if 'xfail' in report.keywords:
        if report.skipped:
            return "xfailed", "x", "xfail"
        elif report.failed:
            return "xpassed", "X", "XPASS"

# called by the terminalreporter instance/plugin
def pytest_terminal_summary(terminalreporter):
    tr = terminalreporter
    if not tr.reportchars:
        #for name in "xfailed skipped failed xpassed":
        #    if not tr.stats.get(name, 0):
        #        tr.write_line("HINT: use '-r' option to see extra "
        #              "summary info about tests")
        #        break
        return

    lines = []
    for char in tr.reportchars:
        if char == "x":
            show_xfailed(terminalreporter, lines)
        elif char == "X":
            show_xpassed(terminalreporter, lines)
        elif char in "fF":
            show_failed(terminalreporter, lines)
        elif char in "sS":
            show_skipped(terminalreporter, lines)
    if lines:
        tr._tw.sep("=", "short test summary info")
        for line in lines:
            tr._tw.line(line)

def show_failed(terminalreporter, lines):
    tw = terminalreporter._tw
    failed = terminalreporter.stats.get("failed")
    if failed:
        for rep in failed:
            pos = rep.nodeid
            lines.append("FAIL %s" %(pos, ))

def show_xfailed(terminalreporter, lines):
    xfailed = terminalreporter.stats.get("xfailed")
    if xfailed:
        for rep in xfailed:
            pos = rep.nodeid
            reason = rep.keywords['xfail']
            lines.append("XFAIL %s" % (pos,))
            if reason:
                lines.append("  " + str(reason))

def show_xpassed(terminalreporter, lines):
    xpassed = terminalreporter.stats.get("xpassed")
    if xpassed:
        for rep in xpassed:
            pos = rep.nodeid
            reason = rep.keywords['xfail']
            lines.append("XPASS %s %s" %(pos, reason))

def cached_eval(config, expr, d):
    if not hasattr(config, '_evalcache'):
        config._evalcache = {}
    try:
        return config._evalcache[expr]
    except KeyError:
        #import sys
        #print >>sys.stderr, ("cache-miss: %r" % expr)
        exprcode = py.code.compile(expr, mode="eval")
        config._evalcache[expr] = x = eval(exprcode, d)
        return x


def folded_skips(skipped):
    d = {}
    for event in skipped:
        key = event.longrepr
        assert len(key) == 3, (event, key)
        d.setdefault(key, []).append(event)
    l = []
    for key, events in d.items():
        l.append((len(events),) + key)
    return l

def show_skipped(terminalreporter, lines):
    tr = terminalreporter
    skipped = tr.stats.get('skipped', [])
    if skipped:
        #if not tr.hasopt('skipped'):
        #    tr.write_line(
        #        "%d skipped tests, specify -rs for more info" %
        #        len(skipped))
        #    return
        fskips = folded_skips(skipped)
        if fskips:
            #tr.write_sep("_", "skipped test summary")
            for num, fspath, lineno, reason in fskips:
                if reason.startswith("Skipped: "):
                    reason = reason[9:]
                lines.append("SKIP [%d] %s:%d: %s" %
                    (num, fspath, lineno, reason))
