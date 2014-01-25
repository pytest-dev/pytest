""" discover and run doctests in modules and test files."""

import pytest, py
from _pytest.python import FixtureRequest, FuncFixtureInfo
from py._code.code import TerminalRepr, ReprFileLocation

def pytest_addoption(parser):
    group = parser.getgroup("collect")
    group.addoption("--doctest-modules",
        action="store_true", default=False,
        help="run doctests in all .py modules",
        dest="doctestmodules")
    group.addoption("--doctest-glob",
        action="store", default="test*.txt", metavar="pat",
        help="doctests file matching pattern, default: test*.txt",
        dest="doctestglob")

def pytest_collect_file(path, parent):
    config = parent.config
    if path.ext == ".py":
        if config.option.doctestmodules:
            return DoctestModule(path, parent)
    elif (path.ext in ('.txt', '.rst') and parent.session.isinitpath(path)) or \
        path.check(fnmatch=config.getvalue("doctestglob")):
        return DoctestTextfile(path, parent)

class ReprFailDoctest(TerminalRepr):
    def __init__(self, reprlocation, lines):
        self.reprlocation = reprlocation
        self.lines = lines
    def toterminal(self, tw):
        for line in self.lines:
            tw.line(line)
        self.reprlocation.toterminal(tw)

class DoctestItem(pytest.Item):
    def __init__(self, name, parent, runner=None, dtest=None):
        super(DoctestItem, self).__init__(name, parent)
        self.runner = runner
        self.dtest = dtest

    def runtest(self):
        self.runner.run(self.dtest)

    def repr_failure(self, excinfo):
        doctest = py.std.doctest
        if excinfo.errisinstance((doctest.DocTestFailure,
                                  doctest.UnexpectedException)):
            doctestfailure = excinfo.value
            example = doctestfailure.example
            test = doctestfailure.test
            filename = test.filename
            if test.lineno is None:
                lineno = None
            else:
                lineno = test.lineno + example.lineno + 1
            message = excinfo.type.__name__
            reprlocation = ReprFileLocation(filename, lineno, message)
            checker = py.std.doctest.OutputChecker()
            REPORT_UDIFF = py.std.doctest.REPORT_UDIFF
            filelines = py.path.local(filename).readlines(cr=0)
            lines = []
            if lineno is not None:
                i = max(test.lineno, max(0, lineno - 10)) # XXX?
                for line in filelines[i:lineno]:
                    lines.append("%03d %s" % (i+1, line))
                    i += 1
            else:
                lines.append('EXAMPLE LOCATION UNKNOWN, not showing all tests of that example')
                indent = '>>>'
                for line in example.source.splitlines():
                    lines.append('??? %s %s' % (indent, line))
                    indent = '...'
            if excinfo.errisinstance(doctest.DocTestFailure):
                lines += checker.output_difference(example,
                        doctestfailure.got, REPORT_UDIFF).split("\n")
            else:
                inner_excinfo = py.code.ExceptionInfo(excinfo.value.exc_info)
                lines += ["UNEXPECTED EXCEPTION: %s" %
                            repr(inner_excinfo.value)]
                lines += py.std.traceback.format_exception(*excinfo.value.exc_info)
            return ReprFailDoctest(reprlocation, lines)
        else:
            return super(DoctestItem, self).repr_failure(excinfo)

    def reportinfo(self):
        return self.fspath, None, "[doctest] %s" % self.name

class DoctestTextfile(DoctestItem, pytest.File):
    def runtest(self):
        doctest = py.std.doctest
        # satisfy `FixtureRequest` constructor...
        self.funcargs = {}
        fm = self.session._fixturemanager
        def func():
            pass
        self._fixtureinfo = fm.getfixtureinfo(node=self, func=func,
                                              cls=None, funcargs=False)
        fixture_request = FixtureRequest(self)
        fixture_request._fillfixtures()
        failed, tot = doctest.testfile(
            str(self.fspath), module_relative=False,
            optionflags=doctest.ELLIPSIS,
            extraglobs=dict(getfixture=fixture_request.getfuncargvalue),
            raise_on_error=True, verbose=0)

class DoctestModule(pytest.File):
    def collect(self):
        doctest = py.std.doctest
        if self.fspath.basename == "conftest.py":
            module = self.config._conftest.importconftest(self.fspath)
        else:
            module = self.fspath.pyimport()
        # satisfy `FixtureRequest` constructor...
        self.funcargs = {}
        self._fixtureinfo = FuncFixtureInfo((), [], {})
        fixture_request = FixtureRequest(self)
        doctest_globals = dict(getfixture=fixture_request.getfuncargvalue)
        # uses internal doctest module parsing mechanism
        finder = doctest.DocTestFinder()
        runner = doctest.DebugRunner(verbose=0, optionflags=doctest.ELLIPSIS)
        for test in finder.find(module, module.__name__,
                                extraglobs=doctest_globals):
            if test.examples: # skip empty doctests
                yield DoctestItem(test.name, self, runner, test)
