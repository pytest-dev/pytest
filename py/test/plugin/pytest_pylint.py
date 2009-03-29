"""pylint plugin


XXX: Currently in progress, NOT IN WORKING STATE.
"""
import py

class PylintPlugin:
    def pytest_addoption(self, parser):
        group = parser.addgroup('pylint options')
        group.addoption('--pylint', action='store_true',
                        default=False, dest='pylint',
                        help='Pylint coverate of test files.')

    def pytest_configure(self, config):
        if config.getvalue('pylint'):
            try:
                from pylint import lint
                self.lint = lint
            except ImportError:
                raise config.Error('Could not import pylint module')
            print "trying to configure pytest"

    def pytest_collect_file(self, path, parent):
        if path.ext == ".py":
            if parent.config.getvalue('pylint'):
                return PylintItem(path, parent, self.lint)

    def pytest_terminal_summary(self, terminalreporter):
        if hasattr(self, 'lint'):
            print 'placeholder for pylint output'



class PylintItem(py.test.collect.Item):
    def __init__(self, path, parent, lintlib):
        name = self.__class__.__name__ + ":" + path.basename
        super(PylintItem, self).__init__(name=name, parent=parent)
        self.fspath = path
        self.lint = lintlib

    def runtest(self):
        # run lint here
        capture = py.io.StdCaptureFD()
        #pylib.org has docs on py.io.stdcaptureFD
        self.linter = self.lint.PyLinter()  #TODO: should this be in the PylintPlugin?
        self.linter.check(str(self.fspath))
        out, err = capture.reset()
        rating = out.strip().split('\n')[-1]
        print ">>>",
        print rating

def test_generic(plugintester):
    plugintester.apicheck(PylintPlugin)

#def test_functional <pull from figleaf plugin>

