"""pylint plugin

XXX: Currently in progress, NOT IN WORKING STATE.
"""
import py

pylint = py.test.importorskip("pylint.lint") 

def pytest_addoption(parser):
    group = parser.getgroup('pylint options')
    group.addoption('--pylint', action='store_true',
                    default=False, dest='pylint',
                    help='run pylint on python files.')

def pytest_collect_file(path, parent):
    if path.ext == ".py":
        if parent.config.getvalue('pylint'):
            return PylintItem(path, parent)

#def pytest_terminal_summary(terminalreporter):
#    print 'placeholder for pylint output'

class PylintItem(py.test.collect.Item):
    def runtest(self):
        capture = py.io.StdCaptureFD()
        try:
            linter = pylint.lint.PyLinter()
            linter.check(str(self.fspath))
        finally:
            out, err = capture.reset()
        rating = out.strip().split('\n')[-1]
        sys.stdout.write(">>>")
        print(rating)
        assert 0


