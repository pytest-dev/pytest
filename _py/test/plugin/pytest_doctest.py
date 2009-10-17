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
from _py.code.code import TerminalRepr, ReprFileLocation
import doctest

def pytest_addoption(parser):
    group = parser.getgroup("doctest options")
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
