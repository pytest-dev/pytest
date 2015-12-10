""" discover and run doctests in modules and test files."""
from __future__ import absolute_import
import traceback
import pytest, py
from _pytest.python import FixtureRequest
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
        self.obj = None
        self.fixture_request = None

    def setup(self):
        if self.dtest is not None:
            self.fixture_request = _setup_fixtures(self)
            globs = dict(getfixture=self.fixture_request.getfuncargvalue)
            self.dtest.globs.update(globs)

    def runtest(self):
        _check_all_skipped(self.dtest)
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
            checker = _get_unicode_checker()
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
                COMPARISON_FLAGS=doctest.COMPARISON_FLAGS,
                ALLOW_UNICODE=_get_allow_unicode_flag())


def get_optionflags(parent):
    optionflags_str = parent.config.getini("doctest_optionflags")
    flag_lookup_table = _get_flag_lookup()
    flag_acc = 0
    for flag in optionflags_str:
        flag_acc |= flag_lookup_table[flag]
    return flag_acc


class DoctestTextfile(DoctestItem, pytest.Module):

    def runtest(self):
        import doctest
        fixture_request = _setup_fixtures(self)

        # inspired by doctest.testfile; ideally we would use it directly,
        # but it doesn't support passing a custom checker
        text = self.fspath.read()
        filename = str(self.fspath)
        name = self.fspath.basename
        globs = dict(getfixture=fixture_request.getfuncargvalue)
        if '__name__' not in globs:
            globs['__name__'] = '__main__'

        optionflags = get_optionflags(self)
        runner = doctest.DebugRunner(verbose=0, optionflags=optionflags,
                                     checker=_get_unicode_checker())

        parser = doctest.DocTestParser()
        test = parser.get_doctest(text, globs, name, filename, 0)
        _check_all_skipped(test)
        runner.run(test)


def _check_all_skipped(test):
    """raises pytest.skip() if all examples in the given DocTest have the SKIP
    option set.
    """
    import doctest
    all_skipped = all(x.options.get(doctest.SKIP, False) for x in test.examples)
    if all_skipped:
        pytest.skip('all tests skipped by +SKIP option')


class DoctestModule(pytest.Module):
    def collect(self):
        import doctest
        if self.fspath.basename == "conftest.py":
            module = self.config.pluginmanager._importconftest(self.fspath)
        else:
            try:
                module = self.fspath.pyimport()
            except ImportError:
                if self.config.getvalue('doctest_ignore_import_errors'):
                    pytest.skip('unable to import module %r' % self.fspath)
                else:
                    raise
        # uses internal doctest module parsing mechanism
        finder = doctest.DocTestFinder()
        optionflags = get_optionflags(self)
        runner = doctest.DebugRunner(verbose=0, optionflags=optionflags,
                                     checker=_get_unicode_checker())
        for test in finder.find(module, module.__name__):
            if test.examples:  # skip empty doctests
                yield DoctestItem(test.name, self, runner, test)


def _setup_fixtures(doctest_item):
    """
    Used by DoctestTextfile and DoctestItem to setup fixture information.
    """
    def func():
        pass

    doctest_item.funcargs = {}
    fm = doctest_item.session._fixturemanager
    doctest_item._fixtureinfo = fm.getfixtureinfo(node=doctest_item, func=func,
                                                  cls=None, funcargs=False)
    fixture_request = FixtureRequest(doctest_item)
    fixture_request._fillfixtures()
    return fixture_request


def _get_unicode_checker():
    """
    Returns a doctest.OutputChecker subclass that takes in account the
    ALLOW_UNICODE option to ignore u'' prefixes in strings. Useful
    when the same doctest should run in Python 2 and Python 3.

    An inner class is used to avoid importing "doctest" at the module
    level.
    """
    if hasattr(_get_unicode_checker, 'UnicodeOutputChecker'):
        return _get_unicode_checker.UnicodeOutputChecker()

    import doctest
    import re

    class UnicodeOutputChecker(doctest.OutputChecker):
        """
        Copied from doctest_nose_plugin.py from the nltk project:
            https://github.com/nltk/nltk
        """

        _literal_re = re.compile(r"(\W|^)[uU]([rR]?[\'\"])", re.UNICODE)

        def check_output(self, want, got, optionflags):
            res = doctest.OutputChecker.check_output(self, want, got,
                                                     optionflags)
            if res:
                return True

            if not (optionflags & _get_allow_unicode_flag()):
                return False

            else:  # pragma: no cover
                # the code below will end up executed only in Python 2 in
                # our tests, and our coverage check runs in Python 3 only
                def remove_u_prefixes(txt):
                    return re.sub(self._literal_re, r'\1\2', txt)

                want = remove_u_prefixes(want)
                got = remove_u_prefixes(got)
                res = doctest.OutputChecker.check_output(self, want, got,
                                                         optionflags)
                return res

    _get_unicode_checker.UnicodeOutputChecker = UnicodeOutputChecker
    return _get_unicode_checker.UnicodeOutputChecker()


def _get_allow_unicode_flag():
    """
    Registers and returns the ALLOW_UNICODE flag.
    """
    import doctest
    return doctest.register_optionflag('ALLOW_UNICODE')
