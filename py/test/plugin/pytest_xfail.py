"""
mark tests as expected-to-fail and report them separately. 

example::

    @py.test.mark.xfail
    def test_hello():
        ...
        assert 0
"""
import py

pytest_plugins = ['keyword']

def pytest_runtest_makereport(__call__, item, call):
    if call.when != "call":
        return
    if hasattr(item, 'obj') and hasattr(item.obj, 'func_dict'):
        if 'xfail' in item.obj.func_dict:
            res = __call__.execute(firstresult=True)
            if call.excinfo:
                res.skipped = True
                res.failed = res.passed = False
            else:
                res.skipped = res.passed = False
                res.failed = True
            return res 

def pytest_report_teststatus(rep):
    """ return shortletter and verbose word. """
    if 'xfail' in rep.keywords: 
        if rep.skipped:
            return "xfailed", "x", "xfail"
        elif rep.failed:
            return "xpassed", "P", "xpass" 

# called by the terminalreporter instance/plugin
def pytest_terminal_summary(terminalreporter):
    tr = terminalreporter
    xfailed = tr.stats.get("xfailed")
    if xfailed:
        tr.write_sep("_", "expected failures")
        for event in xfailed:
            entry = event.longrepr.reprcrash 
            key = entry.path, entry.lineno, entry.message
            reason = event.longrepr.reprcrash.message
            modpath = event.item.getmodpath(includemodule=True)
            #tr._tw.line("%s %s:%d: %s" %(modpath, entry.path, entry.lineno, entry.message))
            tr._tw.line("%s %s:%d: " %(modpath, entry.path, entry.lineno))

    xpassed = terminalreporter.stats.get("xpassed")
    if xpassed:
        tr.write_sep("_", "UNEXPECTEDLY PASSING TESTS")
        for event in xpassed:
            tr._tw.line("%s: xpassed" %(event.item,))


# ===============================================================================
#
# plugin tests 
#
# ===============================================================================

def test_xfail(testdir, linecomp):
    p = testdir.makepyfile(test_one="""
        import py
        @py.test.mark.xfail
        def test_this():
            assert 0

        @py.test.mark.xfail
        def test_that():
            assert 1
    """)
    result = testdir.runpytest(p)
    extra = result.stdout.fnmatch_lines([
        "*expected failures*",
        "*test_one.test_this*test_one.py:4*",
        "*UNEXPECTEDLY PASSING*",
        "*test_that*",
    ])
    assert result.ret == 1
