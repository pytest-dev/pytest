"""
advanced conditional skipping for python test functions, classes or modules.

You can mark functions, classes or modules for for conditional
skipping (skipif) or as expected-to-fail (xfail).  The difference
between the two is that 'xfail' will still execute test functions
but it will invert the outcome: a passing test becomes a failure and
a failing test is a semi-passing one.  All skip conditions are 
reported at the end of test run through the terminal reporter.

.. _skipif:

skip a test function conditionally
-------------------------------------------

Here is an example for skipping a test function on Python3::

    @py.test.mark.skipif("sys.version_info >= (3,0)")
    def test_function():
        ...

The 'skipif' marker accepts an **arbitrary python expression** 
as a condition.  When setting up the test function the condition
is evaluated by calling ``eval(expr, namespace)``.  The namespace
contains the  ``sys`` and ``os`` modules as well as the 
test ``config`` object.  The latter allows you to skip based 
on a test configuration value e.g. like this::

    @py.test.mark.skipif("not config.getvalue('db')")
    def test_function(...):
        ...


conditionally mark a function as "expected to fail"
-------------------------------------------------------

You can use the ``xfail`` keyword to mark your test functions as
'expected to fail'::

    @py.test.mark.xfail
    def test_hello():
        ...

This test will be executed but no traceback will be reported
when it fails. Instead terminal reporting will list it in the
"expected to fail" or "unexpectedly passing" sections.
As with skipif_ you may selectively expect a failure
depending on platform::

    @py.test.mark.xfail("sys.version_info >= (3,0)")
    def test_function():
        ...

skip/xfail a whole test class or module
-------------------------------------------

Instead of marking single functions you can skip
a whole class of tests when running on a specific
platform::

    class TestSomething:
        skipif = "sys.platform == 'win32'"

Or you can mark all test functions as expected
to fail for a specific test configuration::

    xfail = "config.getvalue('db') == 'mysql'"


skip if a dependency cannot be imported
---------------------------------------------

You can use a helper to skip on a failing import::

    docutils = py.test.importorskip("docutils")

You can use this helper at module level or within
a test or setup function.

You can also skip if a library does not come with a high enough version::

    docutils = py.test.importorskip("docutils", minversion="0.3")

The version will be read from the specified module's ``__version__`` attribute.

dynamically skip from within a test or setup
-------------------------------------------------

If you want to skip the execution of a test you can call
``py.test.skip()`` within a test, a setup or from a
`funcarg factory`_ function.  Example::

    def test_function():
        if not valid_config():
            py.test.skip("unsuppored configuration")

.. _`funcarg factory`: ../funcargs.html#factory

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
    if hasattr(item, 'obj'):
        expr, result = evalexpression(item, 'xfail')
        if result:
            rep = __multicall__.execute()
            if call.excinfo:
                rep.skipped = True
                rep.failed = rep.passed = False
            else:
                rep.skipped = rep.passed = False
                rep.failed = True
            rep.keywords['xfail'] = True # expr
            return rep

def pytest_report_teststatus(report):
    if 'xfail' in report.keywords:
        if report.skipped:
            return "xfailed", "x", "xfail"
        elif report.failed:
            return "xpassed", "P", "xpass"

# called by the terminalreporter instance/plugin
def pytest_terminal_summary(terminalreporter):
    tr = terminalreporter
    xfailed = tr.stats.get("xfailed")
    if xfailed:
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


def getexpression(item, keyword):
    if isinstance(item, py.test.collect.Function):
        val = getattr(item.obj, keyword, None)
        val = getattr(val, '_0', val)
        if val is not None:
            return val
        cls = item.getparent(py.test.collect.Class)
        if cls and hasattr(cls.obj, keyword):
            return getattr(cls.obj, keyword)
        mod = item.getparent(py.test.collect.Module)
        return getattr(mod.obj, keyword, None)

def evalexpression(item, keyword):
    expr = getexpression(item, keyword)
    result = None
    if expr:
        if isinstance(expr, str):
            d = {'os': py.std.os, 'sys': py.std.sys, 'config': item.config}
            result = eval(expr, d)
        else:
            result = expr
    return expr, result

