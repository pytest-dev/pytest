import py

class DoctestPlugin:
    def pytest_addoption(self, parser):
        group = parser.addgroup("doctest options")
        group.addoption("--doctest-modules", 
            action="store_true", default=False,
            dest="doctestmodules")
    
    def pytest_collect_file(self, path, parent):
        if path.ext == ".py":
            if parent.config.getvalue("doctestmodules"):
                return DoctestModule(path, parent)
        if path.check(fnmatch="test_*.txt"):
            return DoctestTextfile(path, parent)

from py.__.code.excinfo import Repr, ReprFileLocation

class ReprFailDoctest(Repr):
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

    def repr_failure(self, excinfo, outerr):
        if excinfo.errisinstance(py.compat.doctest.DocTestFailure):
            doctestfailure = excinfo.value
            example = doctestfailure.example
            test = doctestfailure.test
            filename = test.filename 
            lineno = example.lineno + 1
            message = excinfo.type.__name__
            reprlocation = ReprFileLocation(filename, lineno, message)
            checker = py.compat.doctest.OutputChecker() 
            REPORT_UDIFF = py.compat.doctest.REPORT_UDIFF
            filelines = py.path.local(filename).readlines(cr=0)
            i = max(0, lineno - 10)
            lines = []
            for line in filelines[i:lineno]:
                lines.append("%03d %s" % (i+1, line))
                i += 1
            lines += checker.output_difference(example, 
                    doctestfailure.got, REPORT_UDIFF).split("\n")
            return ReprFailDoctest(reprlocation, lines)
        elif excinfo.errisinstance(py.compat.doctest.UnexpectedException):
            excinfo = py.code.ExceptionInfo(excinfo.value.exc_info)
            return super(DoctestItem, self).repr_failure(excinfo, outerr)
        else: 
            return super(DoctestItem, self).repr_failure(excinfo, outerr)

class DoctestTextfile(DoctestItem):
    def runtest(self):
        if not self._deprecated_testexecution():
            failed, tot = py.compat.doctest.testfile(
                str(self.fspath), module_relative=False, 
                raise_on_error=True, verbose=0)

class DoctestModule(DoctestItem):
    def runtest(self):
        module = self.fspath.pyimport()
        failed, tot = py.compat.doctest.testmod(
            module, raise_on_error=True, verbose=0)


#
# Plugin tests
#

class TestDoctests:
    def test_collect_testtextfile(self, testdir):
        testdir.plugins.append(DoctestPlugin())
        testdir.maketxtfile(whatever="")
        checkfile = testdir.maketxtfile(test_something="""
            alskdjalsdk
            >>> i = 5
            >>> i-1
            4
        """)
        for x in (testdir.tmpdir, checkfile): 
            #print "checking that %s returns custom items" % (x,) 
            items, events = testdir.inline_genitems(x)
            print events.events
            assert len(items) == 1
            assert isinstance(items[0], DoctestTextfile)

    def test_collect_module(self, testdir):
        testdir.plugins.append(DoctestPlugin())
        path = testdir.makepyfile(whatever="#")
        for p in (path, testdir.tmpdir): 
            items, evrec = testdir.inline_genitems(p, '--doctest-modules')
            print evrec.events
            assert len(items) == 1
            assert isinstance(items[0], DoctestModule)

    def test_simple_doctestfile(self, testdir):
        testdir.plugins.append(DoctestPlugin())
        p = testdir.maketxtfile(test_doc="""
            >>> x = 1
            >>> x == 1
            False
        """)
        sorter = testdir.inline_run(p)
        sorter.assertoutcome(failed=1)

    def test_doctest_unexpected_exception(self, testdir):
        from py.__.test.outcome import Failed 

        testdir.plugins.append(DoctestPlugin())
        p = testdir.maketxtfile("""
            >>> i = 0
            >>> i = 1 
            >>> x
            2
        """)
        sorter = testdir.inline_run(p)
        call = sorter.getcall("itemtestreport")
        assert call.rep.failed
        assert call.rep.longrepr 
        # XXX 
        #testitem, = items
        #excinfo = py.test.raises(Failed, "testitem.runtest()")
        #repr = testitem.repr_failure(excinfo, ("", ""))
        #assert repr.reprlocation 

    def test_doctestmodule(self, testdir):
        testdir.plugins.append(DoctestPlugin())
        p = testdir.makepyfile("""
            '''
                >>> x = 1
                >>> x == 1
                False

            '''
        """)
        sorter = testdir.inline_run(p, "--doctest-modules")
        sorter.assertoutcome(failed=1) 

    def test_txtfile_failing(self, testdir):
        testdir.plugins.append('pytest_doctest')
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


def test_generic(plugintester):
    plugintester.apicheck(DoctestPlugin)

