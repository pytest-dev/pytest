"""
advanced skipping for python test functions, classes or modules.

With this plugin you can mark test functions for conditional skipping 
or as "xfail", expected-to-fail.  Skipping a test will avoid running it
while xfail-marked tests will run and result in an inverted outcome:
a pass becomes a failure and a fail becomes a semi-passing one. 

The need for skipping a test is usually connected to a condition.  
If a test fails under all conditions then it's probably better
to mark your test as 'xfail'. 

By passing ``--report=xfailed,skipped`` to the terminal reporter 
you will see summary information on skips and xfail-run tests
at the end of a test run. 

.. _skipif:

mark a test function to be skipped
-------------------------------------------

Here is an example for skipping a test function when
running on Python3::

    @py.test.mark.skipif("sys.version_info >= (3,0)")
    def test_function():
        ...


During test function setup the skipif condition is 
evaluated by calling ``eval(expr, namespace)``.  The namespace
contains the  ``sys`` and ``os`` modules as well as the 
test ``config`` object.  The latter allows you to skip based 
on a test configuration value e.g. like this::

    @py.test.mark.skipif("not config.getvalue('db')")
    def test_function(...):
        ...


mark many test functions at once 
--------------------------------------

As with all metadata function marking you can do it at
`whole class- or module level`_.  Here is an example 
for skipping all methods of a test class based on platform::

    class TestPosixCalls:
        pytestmark = py.test.mark.skipif("sys.platform == 'win32'")
    
        def test_function(self):
            # will not be setup or run under 'win32' platform
            #


.. _`whole class- or module level`: mark.html#scoped-marking


mark a test function as expected to fail 
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

    @py.test.mark.xfail(if"sys.version_info >= (3,0)")

    def test_function():
        ...


skipping on a missing import dependency
--------------------------------------------------

You can use the following import helper at module level 
or within a test or setup function.

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
# XXX py.test.skip, .importorskip and the Skipped class 
# should also be defined in this plugin, requires thought/changes

import py

def pytest_runtest_setup(item):
    expr, result = evalexpression(item, 'skipif')
    if result:
        py.test.skip(expr)

def pytest_runtest_makereport(__multicall__, item, call):
    if call.when != "call":
        return
    expr, result = evalexpression(item, 'xfail')
    rep = __multicall__.execute()
    if result:
        if call.excinfo:
            rep.skipped = True
            rep.failed = rep.passed = False
        else:
            rep.skipped = rep.passed = False
            rep.failed = True
        rep.keywords['xfail'] = expr 
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
            return "xpassed", "P", "xpass"

# called by the terminalreporter instance/plugin
def pytest_terminal_summary(terminalreporter):
    show_xfailed(terminalreporter)
    show_skipped(terminalreporter)

def show_xfailed(terminalreporter):
    tr = terminalreporter
    xfailed = tr.stats.get("xfailed")
    if xfailed:
        if not tr.hasopt('xfailed'):
            if tr.config.getvalue("verbose"):
                tr.write_line(
                  "%d expected failures, use --report=xfailed for more info" %
                  len(xfailed))
            return
        tr.write_sep("_", "expected failures")
        for rep in xfailed:
            entry = rep.longrepr.reprcrash
            modpath = rep.item.getmodpath(includemodule=True)
            pos = "%s %s:%d: " %(modpath, entry.path, entry.lineno)
            reason = rep.longrepr.reprcrash.message
            i = reason.find("\n")
            if i != -1:
                reason = reason[:i]
            tr._tw.line("%s %s" %(pos, reason))

    xpassed = terminalreporter.stats.get("xpassed")
    if xpassed:
        tr.write_sep("_", "UNEXPECTEDLY PASSING TESTS")
        for rep in xpassed:
            fspath, lineno, modpath = rep.item.reportinfo()
            pos = "%s %s:%d: unexpectedly passing" %(modpath, fspath, lineno)
            tr._tw.line(pos)


def evalexpression(item, keyword):
    if isinstance(item, py.test.collect.Function):
        markholder = getattr(item.obj, keyword, None)
        result = False
        if markholder:
            d = {'os': py.std.os, 'sys': py.std.sys, 'config': item.config}
            expr, result = None, True
            for expr in markholder.args:
                if isinstance(expr, str):
                    result = eval(expr, d)
                else:
                    result = expr
                if not result:
                    break
            return expr, result
    return None, False

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

def show_skipped(terminalreporter):
    tr = terminalreporter
    skipped = tr.stats.get('skipped', [])
    if skipped:
        if not tr.hasopt('skipped'):
            if tr.config.getvalue("verbose"):
                tr.write_line(
                    "%d skipped tests, use --report=skipped for more info" %
                    len(skipped))
            return
        fskips = folded_skips(skipped)
        if fskips:
            tr.write_sep("_", "skipped test summary")
            for num, fspath, lineno, reason in fskips:
                tr._tw.line("%s:%d: [%d] %s" %(fspath, lineno, num, reason))
