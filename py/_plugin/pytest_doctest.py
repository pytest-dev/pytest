"""
collect and execute doctests from modules and test files. 

Usage
-------------

By default all files matching the ``test*.txt`` pattern will 
be run through the python standard ``doctest`` module.  Issue::

    py.test --doctest-glob='*.rst'

to change the pattern.  Additionally you can trigger running of
tests in all python modules (including regular python test modules)::

    py.test --doctest-modules

You can also make these changes permanent in your project by 
putting them into a conftest.py file like this::

    # content of conftest.py 
    option_doctestmodules = True
    option_doctestglob = "*.rst"
"""

import py
from py._code.code import TerminalRepr, ReprFileLocation
import doctest

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
        if config.getvalue("doctestmodules"):
            return DoctestModule(path, parent)
    elif path.check(fnmatch=config.getvalue("doctestglob")):
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
