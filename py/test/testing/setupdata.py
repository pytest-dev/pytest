import py

def setup_module(mod):
    mod.datadir = setupdatadir()
    mod.tmpdir = py.test.ensuretemp(mod.__name__) 

def setupdatadir():
    datadir = py.test.ensuretemp("datadir")
    names = [x.basename for x in datadir.listdir()]
    for name, content in namecontent:
        if name not in names:
            datadir.join(name).write(content)
    return datadir

namecontent = [
('syntax_error.py', "this is really not python\n"),

('disabled_module.py', py.code.Source('''
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
''')),

('brokenrepr.py', py.code.Source('''

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
    ''')),

    ('failingimport.py', py.code.Source('''

     import gruetzelmuetzel

    ''')),

    ('filetest.py', py.code.Source('''
        def test_one(): 
            assert 42 == 43

        class TestClass(object): 
            def test_method_one(self): 
                assert 42 == 43 

    ''')),

    ('testspecial_importerror.py', py.code.Source('''

        import asdasd

    ''')),

    ('disabled.py', py.code.Source('''
        class TestDisabled:
            disabled = True
            def test_method(self): 
                pass
    ''')),
]    
   

 
