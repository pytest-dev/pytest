
""" Support module for running tests
"""

import py
from py.__.test.testing.setupdata import getexamplefile 

class DirSetup(object):
    def setup_method(self, method):
        name = "%s.%s" %(self.__class__.__name__, method.func_name)
        self.tmpdir = py.test.ensuretemp(name)
        self.source = self.tmpdir.ensure("source", dir=1)
        self.dest = self.tmpdir.join("dest")


class BasicRsessionTest(object):
    def setup_class(cls):
        path = getexamplefile("funcexamples.py")
        cls.config = py.test.config._reparse([path.dirpath()])
        cls.modulecol = cls.config.getfsnode(path)

    def setup_method(self, method):
        self.session = self.config.initsession()
        
    def getfunc(self, name):
        funcname = "func" + name
        col = self.modulecol.join(funcname) 
        assert col is not None, funcname
        return col

    def getdocexample(self):
        return getexamplefile("docexample.txt")
