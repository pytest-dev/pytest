import py

class DoctestFileContent(py.test.collect.Item):

    #def buildname2items(self):
    #    parser = py.compat.doctest.DoctestParser()
    #    l = parser.get_examples(self._content)
    #    d = {}
    #    globs = {}
    #    locs
    #    for i, example in py.builtin.enumerate(l):
    #        ex = ExampleItem(example)
    #        d[str(i)] = ex

    def run(self):
        self.execute()
       
    def execute(self):
        failed, tot = py.compat.doctest.testfile(str(self.fspath), module_relative=False, verbose=1)
        #mod.__file__ = str(self.fspath)
        #failed, tot = py.compat.doctest.testmod(mod, verbose=1)
        if failed: 
            py.test.fail("doctest %s: %s failed out of %s" %(
                         self.fspath, failed, tot))
