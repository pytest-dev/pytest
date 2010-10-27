# content of conftest.py

import py

def pytest_collect_file(path, parent):
    if path.ext == ".yml" and path.basename.startswith("test"):
        return YamlFile(path, parent)
            
class YamlFile(py.test.collect.File):
    def collect(self):
        import yaml # we need a yaml parser, e.g. PyYAML
        raw = yaml.load(self.fspath.open())
        for name, spec in raw.items():
            yield UsecaseItem(name, self, spec)

class UsecaseItem(py.test.collect.Item):
    def __init__(self, name, parent, spec):
        super(UsecaseItem, self).__init__(name, parent)
        self.spec = spec
    
    def runtest(self):
        for name, value in self.spec.items():
            # some custom test execution (dumb example follows)
            if name != value:
                raise UsecaseException(self, name, value)

    def repr_failure(self, excinfo):
        """ called when self.runtest() raises an exception. """
        if excinfo.errisinstance(UsecaseException):
            return "\n".join([
                "usecase execution failed",
                "   spec failed: %r: %r" % excinfo.value.args[1:3],
                "   no further details known at this point."
            ])

    def reportinfo(self):
        return self.fspath, 0, "usecase: %s" % self.name

class UsecaseException(Exception):
    """ custom exception for error reporting. """
