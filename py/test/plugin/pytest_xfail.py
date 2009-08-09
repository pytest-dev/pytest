"""
mark python test functions as expected-to-fail and report them separately. 

usage
------------

Use the generic mark decorator to mark your test functions as 
'expected to fail':: 

    @py.test.mark.xfail
    def test_hello():
        ...

This test will be executed but no traceback will be reported 
when it fails. Instead terminal reporting will list it in the 
"expected to fail" section or "unexpectedly passing" section.  

"""

import py

def pytest_runtest_makereport(__call__, item, call):
    if call.when != "call":
        return
    if hasattr(item, 'obj') and hasattr(item.obj, 'func_dict'):
        if 'xfail' in item.obj.func_dict:
            res = __call__.execute()
            if call.excinfo:
                res.skipped = True
                res.failed = res.passed = False
            else:
                res.skipped = res.passed = False
                res.failed = True
            return res 

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


# =============================================================================
#
# plugin tests 
#
# =============================================================================

def test_xfail(testdir):
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

