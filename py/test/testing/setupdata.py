import py

#def setup_module(mod):
#    mod.datadir = setupdatadir()
#    mod.tmpdir = py.test.ensuretemp(mod.__name__) 

#def setupdatadir():
#    datadir = py.test.ensuretemp("datadir")
#    for name in namecontent:
#        getexamplefile(name)
#    return datadir

def getexamplefile(basename, tmpdir=None):
    if tmpdir is None: 
        tmpdir = py.test.ensuretemp("example") 
        tmpdir.ensure("__init__.py")
    path = tmpdir.join(basename) 
    if not path.check():
        path.write(py.code.Source(namecontent[basename]))
        print "creating testfile", path
    return path 

def getexamplecollector(names, tmpdir=None): 
    fn = getexamplefile(names[0], tmpdir=tmpdir)  
    config = py.test.config._reparse([fn.dirpath()])
    col = config.getfsnode(fn)
    return col._getitembynames(names[1:])

namecontent = {
    'syntax_error.py': "this is really not python\n",

    'disabled_module.py': '''
        disabled = True

        def setup_module(mod):
            raise ValueError

        class TestClassOne:
            def test_func(self):
                raise ValueError

        class TestClassTwo:
            def setup_class(cls):
                raise ValueError
            def test_func(self):
                raise ValueError
    ''', 

    'brokenrepr.py': '''
        import py

        class BrokenRepr1:
            """A broken class with lots of broken methods. Let's try to make the test framework 
            immune to these."""
            foo=0
            def __repr__(self):
                raise Exception("Ha Ha fooled you, I'm a broken repr().")

        class BrokenRepr2:
            """A broken class with lots of broken methods. Let's try to make the test framework 
            immune to these."""
            foo=0
            def __repr__(self):
                raise "Ha Ha fooled you, I'm a broken repr()."

            
        class TestBrokenClass:

            def test_explicit_bad_repr(self):
                t = BrokenRepr1()
                py.test.raises(Exception, 'repr(t)')
                
            def test_implicit_bad_repr1(self):
                t = BrokenRepr1()
                assert t.foo == 1

            def test_implicit_bad_repr2(self):
                t = BrokenRepr2()
                assert t.foo == 1
    ''', 

    'failingimport.py': "import gruetzelmuetzel\n", 

    'test_mod.py': """
        class TestA:
            def test_m1(self):
                pass
        def test_f1():
            pass
        def test_g1():
            yield lambda x: None, 42
    """,

    'file_test.py': """
        def test_one(): 
            assert 42 == 43

        class TestClass(object): 
            def test_method_one(self): 
                assert 42 == 43 

    """,

    'test_threepass.py': """
        def test_one():
            assert 1

        def test_two():
            assert 1

        def test_three():
            assert 1
    """,

    'testspecial_importerror.py': """

        import asdasd

    """,

    'disabled.py': """
        class TestDisabled:
            disabled = True
            def test_method(self): 
                pass
    """,

    'test_funcexamples.py': """
        import py
        import time
        def test_funcpassed(): 
            pass

        def test_funcfailed():
            raise AssertionError("hello world")

        def test_funcskipped():
            py.test.skip("skipped")

        def test_funcprint():
            print "samfing"

        def test_funcprinterr():
            print >>py.std.sys.stderr, "samfing"

        def test_funcprintfail():
            print "samfing elz"
            asddsa

        def test_funcexplicitfail():
            py.test.fail("3")

        def test_funcraisesfails():
            py.test.raises(ValueError, lambda: 123) 

        def test_funcoptioncustom():
            assert py.test.config.getvalue("custom")

        def test_funchang():
            import time
            time.sleep(1000)

        def test_funckill15():
            import os
            os.kill(os.getpid(), 15)
    """,

    'docexample.txt': """ 
        Aha!!!!!!
        =========
     """,

} 
