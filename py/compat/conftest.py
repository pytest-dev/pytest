import py

class Directory(py.test.collect.Directory):
    def collect(self):
        py.test.skip("compat tests need to be run manually")
