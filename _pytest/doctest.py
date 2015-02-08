""" discover and run doctests in modules and test files."""
from __future__ import absolute_import
import traceback
import pytest, py
from _pytest.python import FixtureRequest, FuncFixtureInfo
from py._code.code import TerminalRepr, ReprFileLocation

def pytest_addoption(parser):
    parser.addini('doctest_optionflags', 'option flags for doctests',
        type="args", default=["ELLIPSIS"])
    group = parser.getgroup("collect")
    group.addoption("--doctest-modules",
        action="store_true", default=False,
        help="run doctests in all .py modules",
        dest="doctestmodules")
    group.addoption("--doctest-glob",
        action="store", default="test*.txt", metavar="pat",
        help="doctests file matching pattern, default: test*.txt",
        dest="doctestglob")
    group.addoption("--doctest-ignore-import-errors",
        action="store_true", default=False,
        help="ignore doctest ImportErrors",
        dest="doctest_ignore_import_errors")

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
        import doctest
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
            checker = doctest.OutputChecker()
            REPORT_UDIFF = doctest.REPORT_UDIFF
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
                lines += traceback.format_exception(*excinfo.value.exc_info)
            return ReprFailDoctest(reprlocation, lines)
        else:
            return super(DoctestItem, self).repr_failure(excinfo)

    def reportinfo(self):
        return self.fspath, None, "[doctest] %s" % self.name

def _get_flag_lookup():
    import doctest
    return dict(DONT_ACCEPT_TRUE_FOR_1=doctest.DONT_ACCEPT_TRUE_FOR_1,
                DONT_ACCEPT_BLANKLINE=doctest.DONT_ACCEPT_BLANKLINE,
                NORMALIZE_WHITESPACE=doctest.NORMALIZE_WHITESPACE,
                ELLIPSIS=doctest.ELLIPSIS,
                IGNORE_EXCEPTION_DETAIL=doctest.IGNORE_EXCEPTION_DETAIL,
                COMPARISON_FLAGS=doctest.COMPARISON_FLAGS)

def get_optionflags(parent):
    optionflags_str = parent.config.getini("doctest_optionflags")
    flag_lookup_table = _get_flag_lookup()
    flag_acc = 0
    for flag in optionflags_str:
        flag_acc |= flag_lookup_table[flag]
    return flag_acc

class DoctestTextfile(DoctestItem, pytest.File):
    def runtest(self):
        import doctest
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
            optionflags=get_optionflags(self),
            extraglobs=dict(getfixture=fixture_request.getfuncargvalue),
            raise_on_error=True, verbose=0)

class DoctestModule(pytest.File):
    def collect(self):
        import doctest
        if self.fspath.basename == "conftest.py":
            module = self.config._conftest.importconftest(self.fspath)
        else:
            try:
                module = self.fspath.pyimport()
            except ImportError:
                if self.config.getvalue('doctest_ignore_import_errors'):
                    pytest.skip('unable to import module %r' % self.fspath)
                else:
                    raise
        # satisfy `FixtureRequest` constructor...
        self.funcargs = {}
        self._fixtureinfo = FuncFixtureInfo((), [], {})
        fixture_request = FixtureRequest(self)
        doctest_globals = dict(getfixture=fixture_request.getfuncargvalue)
        # uses internal doctest module parsing mechanism
        finder = doctest.DocTestFinder()
        optionflags = get_optionflags(self)
        runner = doctest.DebugRunner(verbose=0, optionflags=optionflags)
        for test in finder.find(module, module.__name__,
                                extraglobs=doctest_globals):
            if test.examples:  # skip empty doctests
                yield DoctestItem(test.name, self, runner, test)
