import py

class DoctestText(py.test.collect.Item):

    def _setcontent(self, content):
        self._content = content 

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
        mod = py.std.types.ModuleType(self.name) 
        #for line in s.split('\n'): 
        #    if line.startswith(prefix): 
        #        exec py.code.Source(line[len(prefix):]).compile() in mod.__dict__ 
        #        line = ""
        #    else: 
        #        l.append(line)
        self.execute(mod, self._content) 
       
    def execute(self, mod, docstring):
        mod.__doc__ = docstring 
        failed, tot = py.compat.doctest.testmod(mod, verbose=1)
        if failed: 
            py.test.fail("doctest %s: %s failed out of %s" %(
                         self.fspath, failed, tot))
