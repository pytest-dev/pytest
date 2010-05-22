"""
advanced skipping for python test functions, classes or modules.

With this plugin you can mark test functions for conditional skipping 
or as "xfail", expected-to-fail.  Skipping a test will avoid running it
while xfail-marked tests will run and result in an inverted outcome:
a pass becomes a failure and a fail becomes a semi-passing one. 

The need for skipping a test is usually connected to a condition.  
If a test fails under all conditions then it's probably better
to mark your test as 'xfail'. 

By passing ``-rxs`` to the terminal reporter you will see extra
summary information on skips and xfail-run tests at the end of a test run. 

.. _skipif:

Skipping a single function 
-------------------------------------------

Here is an example for marking a test function to be skipped
when run on a Python3 interpreter::

    @py.test.mark.skipif("sys.version_info >= (3,0)")
    def test_function():
        ...

During test function setup the skipif condition is 
evaluated by calling ``eval(expr, namespace)``.  The namespace
contains the  ``sys`` and ``os`` modules and the test 
``config`` object.  The latter allows you to skip based 
on a test configuration value e.g. like this::

    @py.test.mark.skipif("not config.getvalue('db')")
    def test_function(...):
        ...

Create a shortcut for your conditional skip decorator 
at module level like this::

    win32only = py.test.mark.skipif("sys.platform != 'win32'")

    @win32only
    def test_function():
        ...


skip groups of test functions 
--------------------------------------

As with all metadata function marking you can do it at
`whole class- or module level`_.  Here is an example 
for skipping all methods of a test class based on platform::

    class TestPosixCalls:
        pytestmark = py.test.mark.skipif("sys.platform == 'win32'")
    
        def test_function(self):
            # will not be setup or run under 'win32' platform
            #

The ``pytestmark`` decorator will be applied to each test function.
If your code targets python2.6 or above you can equivalently use 
the skipif decorator on classes::

    @py.test.mark.skipif("sys.platform == 'win32'")
    class TestPosixCalls:
    
        def test_function(self):
            # will not be setup or run under 'win32' platform
            #

It is fine in general to apply multiple "skipif" decorators
on a single function - this means that if any of the conditions
apply the function will be skipped. 

.. _`whole class- or module level`: mark.html#scoped-marking


mark a test function as **expected to fail**
-------------------------------------------------------

You can use the ``xfail`` marker to indicate that you
expect the test to fail:: 

    @py.test.mark.xfail
    def test_function():
        ...

This test will be run but no traceback will be reported
when it fails. Instead terminal reporting will list it in the
"expected to fail" or "unexpectedly passing" sections.

Same as with skipif_ you can also selectively expect a failure
depending on platform::

    @py.test.mark.xfail("sys.version_info >= (3,0)")
    def test_function():
        ...

To not run a test and still regard it as "xfailed"::

    @py.test.mark.xfail(..., run=False)

To specify an explicit reason to be shown with xfailure detail::

    @py.test.mark.xfail(..., reason="my reason")

imperative xfail from within a test or setup function
------------------------------------------------------

If you cannot declare xfail-conditions at import time
you can also imperatively produce an XFail-outcome from 
within test or setup code.  Example::

    def test_function():
        if not valid_config():
            py.test.xfail("unsuppored configuration")


skipping on a missing import dependency
--------------------------------------------------

You can use the following import helper at module level 
or within a test or test setup function::

    docutils = py.test.importorskip("docutils")

If ``docutils`` cannot be imported here, this will lead to a
skip outcome of the test.  You can also skip dependeing if
if a library does not come with a high enough version::

    docutils = py.test.importorskip("docutils", minversion="0.3")

The version will be read from the specified module's ``__version__`` attribute.

imperative skip from within a test or setup function
------------------------------------------------------

If for some reason you cannot declare skip-conditions
you can also imperatively produce a Skip-outcome from 
within test or setup code.  Example::

    def test_function():
        if not valid_config():
            py.test.skip("unsuppored configuration")

"""

import py

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption('--runxfail', 
           action="store_true", dest="runxfail", default=False,
           help="run tests even if they are marked xfail")

class MarkEvaluator:
    def __init__(self, item, name):
        self.item = item
        self.name = name
        self.holder = getattr(item.obj, name, None)

    def __bool__(self):
        return bool(self.holder)
    __nonzero__ = __bool__

    def istrue(self):
        if self.holder:
            d = {'os': py.std.os, 'sys': py.std.sys, 'config': self.item.config}
            if self.holder.args:
                self.result = False
                for expr in self.holder.args:
                    self.expr = expr
                    if isinstance(expr, str):
                        result = cached_eval(self.item.config, expr, d)
                    else:
                        result = expr
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
                return "condition: " + self.expr
        return expl
        

def pytest_runtest_setup(item):
    if not isinstance(item, py.test.collect.Function):
        return
    evalskip = MarkEvaluator(item, 'skipif')
    if evalskip.istrue():
        py.test.skip(evalskip.getexplanation())
    item._evalxfail = MarkEvaluator(item, 'xfail')
    if not item.config.getvalue("runxfail"):
        if item._evalxfail.istrue():
            if not item._evalxfail.get('run', True):
                py.test.skip("xfail")

def pytest_runtest_makereport(__multicall__, item, call):
    if not isinstance(item, py.test.collect.Function):
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
            rep.skipped = True
            rep.failed = False
            return rep
    if call.when == "setup":
        rep = __multicall__.execute()
        if rep.skipped and evalxfail.istrue():
            expl = evalxfail.getexplanation()
            if not evalxfail.get("run", True):
                expl = "[NOTRUN] " + expl
            rep.keywords['xfail'] = expl
        return rep
    elif call.when == "call":
        rep = __multicall__.execute()
        if not item.config.getvalue("runxfail") and evalxfail.istrue():
            if call.excinfo:
                rep.skipped = True
                rep.failed = rep.passed = False
            else:
                rep.skipped = rep.passed = False
                rep.failed = True
            rep.keywords['xfail'] = evalxfail.getexplanation()
        else:
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
        elif char == "f":
            show_failed(terminalreporter, lines)
        elif char == "s":
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
            pos = terminalreporter.gettestid(rep.item)
            lines.append("FAIL %s" %(pos, ))

def show_xfailed(terminalreporter, lines):
    xfailed = terminalreporter.stats.get("xfailed")
    if xfailed:
        for rep in xfailed:
            pos = terminalreporter.gettestid(rep.item)
            reason = rep.keywords['xfail']
            lines.append("XFAIL %s %s" %(pos, reason))

def show_xpassed(terminalreporter, lines):
    xpassed = terminalreporter.stats.get("xpassed")
    if xpassed:
        for rep in xpassed:
            pos = terminalreporter.gettestid(rep.item)
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
        config._evalcache[expr] = x = eval(expr, d)
        return x


def folded_skips(skipped):
    d = {}
    for event in skipped:
        entry = event.longrepr.reprcrash 
        key = entry.path, entry.lineno, entry.message
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
