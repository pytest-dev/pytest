
""" Support module for running tests
"""

import py

def func_source():
    import py
    import time
    def funcpass(): 
        pass

    def funcfail():
        raise AssertionError("hello world")

    def funcskip():
        py.test.skip("skipped")

    def funcprint():
        print "samfing"

    def funcprintfail():
        print "samfing elz"
        asddsa

    def funcoptioncustom():
        assert py.test.config.getvalue("custom")

    def funchang():
        import time
        time.sleep(1000)

class BasicRsessionTest(object):
    def setup_class(cls):
        tmpdir = py.test.ensuretemp(cls.__name__) 
        source = py.code.Source(func_source)[1:].deindent()
        testonepath = tmpdir.ensure("test_one.py")
        testonepath.write(source)
        cls.config = py.test.config._reparse([tmpdir])
        cls.collector_test_one = cls.config._getcollector(testonepath)

    def getexample(self, name):
        funcname = "func" + name
        col = self.collector_test_one.join(funcname)
        assert col is not None, funcname
        return col 

    def getmod(self):
        return self.collector_test_one
