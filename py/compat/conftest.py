import py

class Directory(py.test.collect.Directory):
    def listdir(self):
        py.test.skip("compat tests currently need to be run manually")
