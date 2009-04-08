"""
for marking and reporting "expected to fail" tests. 
    @py.test.mark.xfail("needs refactoring")
    def test_hello():
        ...
        assert 0
"""
import py

class XfailPlugin(object):
    """ mark and report specially about "expected to fail" tests. """

    def pytest_item_makereport(self, __call__, item, excinfo, when, outerr):
        if hasattr(item, 'obj') and hasattr(item.obj, 'func_dict'):
            if 'xfail' in item.obj.func_dict:
                res = __call__.execute(firstresult=True)
                if excinfo:
                    res.skipped = True
                    res.failed = res.passed = False
                else:
                    res.skipped = res.passed = False
                    res.failed = True
                return res 

    def pytest_report_teststatus(self, rep):
        """ return shortletter and verbose word. """
        if 'xfail' in rep.keywords: 
            if rep.skipped:
                return "xfailed", "x", "xfail"
            elif rep.failed:
                return "xpassed", "P", "xpass" 

    # a hook implemented called by the terminalreporter instance/plugin
    def pytest_terminal_summary(self, terminalreporter):
        tr = terminalreporter
        xfailed = tr.stats.get("xfailed")
        if xfailed:
            tr.write_sep("_", "expected failures")
            for event in xfailed:
                entry = event.longrepr.reprcrash 
                key = entry.path, entry.lineno, entry.message
                reason = event.longrepr.reprcrash.message
                modpath = event.colitem.getmodpath(includemodule=True)
                #tr._tw.line("%s %s:%d: %s" %(modpath, entry.path, entry.lineno, entry.message))
                tr._tw.line("%s %s:%d: " %(modpath, entry.path, entry.lineno))

        xpassed = terminalreporter.stats.get("xpassed")
        if xpassed:
            tr.write_sep("_", "UNEXPECTEDLY PASSING TESTS")
            for event in xpassed:
                tr._tw.line("%s: xpassed" %(event.colitem,))

# ===============================================================================
#
# plugin tests 
#
# ===============================================================================

def test_generic(plugintester):
    plugintester.apicheck(XfailPlugin) 
               
def test_xfail(plugintester, linecomp):
    testdir = plugintester.testdir()
    p = testdir.makepyfile(test_one="""
        import py
        pytest_plugins="pytest_xfail",
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
        "*test_one.test_this*test_one.py:5*",
        "*UNEXPECTEDLY PASSING*",
        "*test_that*",
    ])
    assert result.ret == 1
