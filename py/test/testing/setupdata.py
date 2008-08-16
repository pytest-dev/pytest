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

    'mod.py': """
        class TestA:
            def test_m1(self):
                pass
        def test_f1():
            pass
        def test_g1():
            yield lambda x: None, 42
    """,

    'filetest.py': """
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

    'funcexamples.py': """
        import py
        import time
        def funcpassed(): 
            pass

        def funcfailed():
            raise AssertionError("hello world")

        def funcskipped():
            py.test.skip("skipped")

        def funcprint():
            print "samfing"

        def funcprinterr():
            print >>py.std.sys.stderr, "samfing"

        def funcprintfail():
            print "samfing elz"
            asddsa

        def funcexplicitfail():
            py.test.fail("3")

        def funcraisesfails():
            py.test.raises(ValueError, lambda: 123) 

        def funcoptioncustom():
            assert py.test.config.getvalue("custom")

        def funchang():
            import time
            time.sleep(1000)

        def funckill15():
            import os
            os.kill(os.getpid(), 15)
    """,
    
    'test_generative.py': """ 
        from __future__ import generators # python2.2!
        def func1(arg, arg2): 
            assert arg == arg2 

        def test_gen(): 
            yield func1, 17, 3*5
            yield func1, 42, 6*7

        class TestGenMethods: 
            def test_gen(self): 
                yield func1, 17, 3*5
                yield func1, 42, 6*7
    """, 

    'docexample.txt': """ 
        Aha!!!!!!
        =========
     """,

} 

def setup_customconfigtest(tmpdir):
    o = tmpdir.ensure('customconfigtest', dir=1)
    o.ensure('conftest.py').write("""if 1:
        import py
        class MyFunction(py.test.collect.Function):
            pass
        class Directory(py.test.collect.Directory):
            def filefilter(self, fspath):
                return fspath.check(basestarts='check_', ext='.py')
        class myfuncmixin: 
            Function = MyFunction
            def funcnamefilter(self, name): 
                return name.startswith('check_') 

        class Module(myfuncmixin, py.test.collect.Module):
            def classnamefilter(self, name): 
                return name.startswith('CustomTestClass') 
        class Instance(myfuncmixin, py.test.collect.Instance):
            pass 
        """)
    checkfile = o.ensure('somedir', 'check_something.py')
    checkfile.write("""if 1:
        def check_func():
            assert 42 == 42
        class CustomTestClass:
            def check_method(self):
                assert 23 == 23
        """)
    return checkfile 

def setup_non_python_dir(tmpdir): 
    o = tmpdir.ensure('customconfigtest_nonpython', dir=1)
    o.ensure('conftest.py').write("""if 1:
        import py
        class CustomItem(py.test.collect.Item): 
            def run(self):
                pass

        class Directory(py.test.collect.Directory):
            def filefilter(self, fspath):
                return fspath.check(basestarts='check_', ext='.txt')
            def join(self, name):
                if not name.endswith('.txt'): 
                    return super(Directory, self).join(name) 
                p = self.fspath.join(name) 
                if p.check(file=1): 
                    return CustomItem(p, parent=self)
        """)
    checkfile = o.ensure('somedir', 'moredir', 'check_something.txt')
    return checkfile 

    
