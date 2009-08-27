"""
collect and execute doctests from modules and test files. 

Usage
-------------

By default all files matching the ``test_*.txt`` pattern will 
be run with the ``doctest`` module.  If you issue::

    py.test --doctest-modules

all python files in your projects will be doctest-run 
as well. 
"""

import py
from py.__.code.code import TerminalRepr, ReprFileLocation
import doctest

def pytest_addoption(parser):
    group = parser.addgroup("doctest options")
    group.addoption("--doctest-modules", 
        action="store_true", default=False,
        help="search all python files for doctests", 
        dest="doctestmodules")
    
def pytest_collect_file(path, parent):
    if path.ext == ".py":
        if parent.config.getvalue("doctestmodules"):
            return DoctestModule(path, parent)
    if path.check(fnmatch="test_*.txt"):
        return DoctestTextfile(path, parent)

class ReprFailDoctest(TerminalRepr):
    def __init__(self, reprlocation, lines):
        self.reprlocation = reprlocation
        self.lines = lines
    def toterminal(self, tw):
        for line in self.lines:
            tw.line(line)
        self.reprlocation.toterminal(tw)
             
class DoctestItem(py.test.collect.Item):
    def __init__(self, path, parent):
        name = self.__class__.__name__ + ":" + path.basename
        super(DoctestItem, self).__init__(name=name, parent=parent)
        self.fspath = path 

    def repr_failure(self, excinfo):
        if excinfo.errisinstance(doctest.DocTestFailure):
            doctestfailure = excinfo.value
            example = doctestfailure.example
            test = doctestfailure.test
            filename = test.filename 
            lineno = test.lineno + example.lineno + 1
            message = excinfo.type.__name__
            reprlocation = ReprFileLocation(filename, lineno, message)
            checker = doctest.OutputChecker() 
            REPORT_UDIFF = doctest.REPORT_UDIFF
            filelines = py.path.local(filename).readlines(cr=0)
            i = max(test.lineno, max(0, lineno - 10)) # XXX? 
            lines = []
            for line in filelines[i:lineno]:
                lines.append("%03d %s" % (i+1, line))
                i += 1
            lines += checker.output_difference(example, 
                    doctestfailure.got, REPORT_UDIFF).split("\n")
            return ReprFailDoctest(reprlocation, lines)
        elif excinfo.errisinstance(doctest.UnexpectedException):
            excinfo = py.code.ExceptionInfo(excinfo.value.exc_info)
            return super(DoctestItem, self).repr_failure(excinfo)
        else: 
            return super(DoctestItem, self).repr_failure(excinfo)

class DoctestTextfile(DoctestItem):
    def runtest(self):
        if not self._deprecated_testexecution():
            failed, tot = doctest.testfile(
                str(self.fspath), module_relative=False, 
                raise_on_error=True, verbose=0)

class DoctestModule(DoctestItem):
    def runtest(self):
        module = self.fspath.pyimport()
        failed, tot = doctest.testmod(
            module, raise_on_error=True, verbose=0)


#
# Plugin tests
#

class TestDoctests:

    def test_collect_testtextfile(self, testdir):
        testdir.maketxtfile(whatever="")
        checkfile = testdir.maketxtfile(test_something="""
            alskdjalsdk
            >>> i = 5
            >>> i-1
            4
        """)
        for x in (testdir.tmpdir, checkfile): 
            #print "checking that %s returns custom items" % (x,) 
            items, reprec = testdir.inline_genitems(x)
            assert len(items) == 1
            assert isinstance(items[0], DoctestTextfile)

    def test_collect_module(self, testdir):
        path = testdir.makepyfile(whatever="#")
        for p in (path, testdir.tmpdir): 
            items, reprec = testdir.inline_genitems(p, '--doctest-modules')
            assert len(items) == 1
            assert isinstance(items[0], DoctestModule)

    def test_simple_doctestfile(self, testdir):
        p = testdir.maketxtfile(test_doc="""
            >>> x = 1
            >>> x == 1
            False
        """)
        reprec = testdir.inline_run(p)
        reprec.assertoutcome(failed=1)

    def test_doctest_unexpected_exception(self, testdir):
        from py.__.test.outcome import Failed 

        p = testdir.maketxtfile("""
            >>> i = 0
            >>> i = 1 
            >>> x
            2
        """)
        reprec = testdir.inline_run(p)
        call = reprec.getcall("pytest_runtest_logreport")
        assert call.report.failed
        assert call.report.longrepr 
        # XXX 
        #testitem, = items
        #excinfo = py.test.raises(Failed, "testitem.runtest()")
        #repr = testitem.repr_failure(excinfo, ("", ""))
        #assert repr.reprlocation 

    def test_doctestmodule(self, testdir):
        p = testdir.makepyfile("""
            '''
                >>> x = 1
                >>> x == 1
                False

            '''
        """)
        reprec = testdir.inline_run(p, "--doctest-modules")
        reprec.assertoutcome(failed=1) 

    def test_doctestmodule_external(self, testdir):
        p = testdir.makepyfile("""
            #
            def somefunc():
                '''
                    >>> i = 0
                    >>> i + 1
                    2
                '''
        """)
        result = testdir.runpytest(p, "--doctest-modules")
        result.stdout.fnmatch_lines([
            '004 *>>> i = 0',
            '005 *>>> i + 1',
            '*Expected:',
            "*    2",
            "*Got:",
            "*    1",
            "*:5: DocTestFailure"
        ])
        

    def test_txtfile_failing(self, testdir):
        p = testdir.maketxtfile("""
            >>> i = 0
            >>> i + 1
            2
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            '001 >>> i = 0',
            '002 >>> i + 1',
            'Expected:',
            "    2",
            "Got:",
            "    1",
            "*test_txtfile_failing.txt:2: DocTestFailure"
        ])
