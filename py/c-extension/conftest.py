import py

class Directory(py.test.collect.Directory):
    # XXX see in which situations/platforms we want
    #     run tests here 
    #def recfilter(self, path):
    #    if py.std.sys.platform == 'linux2': 
    #        if path.basename == 'greenlet':
    #            return False
    #    return super(Directory, self).recfilter(path)
    
    #def run(self): 
    #    py.test.skip("c-extension testing needs platform selection") 
    pass
