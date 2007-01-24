import py

class Directory(py.test.collect.Directory):
    def run(self):
        py.test.skip("compat tests currently need to be run manually")
