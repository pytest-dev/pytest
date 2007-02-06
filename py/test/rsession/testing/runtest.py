
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
        tmptop = py.test.ensuretemp("test_suite")
        name = cls.__name__
        tmpdir = tmptop.ensure(name, dir=1)
        source = py.code.Source(func_source)[1:].deindent()
        tmpdir.ensure("test_one.py").write(source)
        tmpdir.ensure("__init__.py")
        cls.rootdir = tmpdir
        cls.config = py.test.config._reparse([cls.rootdir])
        cls.rootcol = cls.config._getcollector(tmpdir)
        #cls.rootcol._config = cls.config
        BASE = "test_one.py/"
        cls.funcpass_spec = (BASE + "funcpass").split("/")
        cls.funcfail_spec = (BASE + "funcfail").split("/")
        cls.funcskip_spec = (BASE + "funcskip").split("/")
        cls.funcprint_spec = (BASE + "funcprint").split("/")
        cls.funcprintfail_spec = (BASE + "funcprintfail").split("/")
        cls.funcoptioncustom_spec = (BASE + "funcoptioncustom").split("/")
        cls.funchang_spec = (BASE + "funchang").split("/")
        cls.mod_spec = BASE[:-1].split("/")

