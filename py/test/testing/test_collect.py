from __future__ import generators
import py
from setupdata import setupdatadir
from py.__.test.outcome import Skipped, Failed, Passed, Outcome

def setup_module(mod):
    mod.datadir = setupdatadir()
    mod.tmpdir = py.test.ensuretemp('test_collect') 

def skipboxed():
    if py.test.config.option.boxed: 
        py.test.skip("test does not work with boxed tests")

def test_failing_import_execfile():
    dest = datadir / 'failingimport.py'
    col = py.test.collect.Module(dest) 
    py.test.raises(ImportError, col.run)
    py.test.raises(ImportError, col.run)

def test_collect_listnames_and_back():
    col1 = py.test.collect.Directory(datadir.dirpath())
    col2 = col1.join(datadir.basename) 
    col3 = col2.join('filetest.py')
    l = col3.listnames()
    assert len(l) == 3
    x = col1._getitembynames(l[1:])
    assert x.name == "filetest.py"
    x = col1._getitembynames("/".join(l[1:]))
    assert x.name == "filetest.py"
    l2 = x.listnames()
    assert len(l2) == 3

def test_finds_tests(): 
    fn = datadir / 'filetest.py'
    col = py.test.collect.Module(fn) 
    l = col.run() 
    assert len(l) == 2 
    assert l[0] == 'test_one' 
    assert l[1] == 'TestClass' 

def test_found_certain_testfiles(): 
    tmp = py.test.ensuretemp("found_certain_testfiles")
    tmp.ensure('test_found.py')
    tmp.ensure('found_test.py')

    colitem = py.test.collect.Directory(tmp) 
    items = list(colitem._tryiter(py.test.collect.Module))
    assert len(items) == 2
    items = [item.name for item in items]
    assert 'test_found.py' in items
    assert 'found_test.py' in items

def test_ignored_certain_directories(): 
    tmp = py.test.ensuretemp("ignore_certain_directories")
    tmp.ensure("_darcs", 'test_notfound.py')
    tmp.ensure("CVS", 'test_notfound.py')
    tmp.ensure("{arch}", 'test_notfound.py')
    tmp.ensure(".whatever", 'test_notfound.py')
    tmp.ensure(".bzr", 'test_notfound.py')
    tmp.ensure("normal", 'test_found.py')
    tmp.ensure('test_found.py')

    colitem = py.test.collect.Directory(tmp) 
    items = list(colitem._tryiter(py.test.collect.Module))
    assert len(items) == 2
    for item in items: 
        assert item.name == 'test_found.py' 

def test_failing_import_directory():
    class MyDirectory(py.test.collect.Directory):
        def filefilter(self, p):
            return p.check(fnmatch='testspecial*.py')
    mydir = MyDirectory(datadir)
    l = mydir.run() 
    assert len(l) == 1
    item = mydir.join(l[0])
    assert isinstance(item, py.test.collect.Module)
    py.test.raises(ImportError, item.run)

def test_module_file_not_found():
    fn = datadir.join('nada','no')
    col = py.test.collect.Module(fn) 
    py.test.raises(py.error.ENOENT, col.run) 

def test_syntax_error_in_module():
    p = py.test.ensuretemp("syntaxerror1").join('syntax_error.py')
    p.write("\nthis is really not python\n")
    modpath = datadir.join('syntax_error.py') 
    col = py.test.collect.Module(modpath) 
    py.test.raises(SyntaxError, col.run)

def test_disabled_class():
    col = py.test.collect.Module(datadir.join('disabled.py'))
    l = col.run() 
    assert len(l) == 1
    colitem = col.join(l[0])
    assert isinstance(colitem, py.test.collect.Class)
    assert not colitem.run() 

def test_disabled_module():
    col = py.test.collect.Module(datadir.join('disabled_module.py'))
    l = col.run() 
    assert len(l) == 0

class Testsomeclass:
    disabled = True
    def test_something():
        raise ValueError


#class TestWithCustomItem:
#    class Item(py.test.collect.Item):
#        flag = []
#        def execute(self, target, *args):
#            self.flag.append(42)
#            target(*args)
#
#    def test_hello(self):
#        assert self.Item.flag == [42]
#

def test_generative_simple(): 
    o = tmpdir.ensure('generativetest', dir=1)
    tfile = o.join('test_generative.py')
    tfile.write(py.code.Source("""
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
    """))
    col = py.test.collect.Module(tfile) 
    l = col.run() 
    assert len(l) == 2 
    l = col.multijoin(l) 

    generator = l[0]
    assert isinstance(generator, py.test.collect.Generator)
    l2 = generator.run() 
    assert len(l2) == 2 
    l2 = generator.multijoin(l2) 
    assert isinstance(l2[0], py.test.collect.Function)
    assert isinstance(l2[1], py.test.collect.Function)
    assert l2[0].name == '[0]'
    assert l2[1].name == '[1]'

    assert l2[0].obj.func_name == 'func1' 
 
    classlist = l[1].run() 
    assert len(classlist) == 1
    classlist = l[1].multijoin(classlist) 
    cls = classlist[0]
    generator = cls.join(cls.run()[0])
    assert isinstance(generator, py.test.collect.Generator)
    l2 = generator.run() 
    assert len(l2) == 2 
    l2 = generator.multijoin(l2) 
    assert isinstance(l2[0], py.test.collect.Function)
    assert isinstance(l2[1], py.test.collect.Function)
    assert l2[0].name == '[0]'
    assert l2[1].name == '[1]'
   
def test_custom_python_collection_from_conftest():
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

    for x in (o, checkfile, checkfile.dirpath()): 
        config = py.test.config._reparse([x])
        #print "checking that %s returns custom items" % (x,) 
        col = config._getcollector(x)
        assert len(list(col._tryiter(py.test.collect.Item))) == 2 
        #assert items[1].__class__.__name__ == 'MyFunction'

    # test that running a session works from the directories
    old = o.chdir() 
    try: 
        config = py.test.config._reparse([]) 
        out = py.std.cStringIO.StringIO()
        session = config._getsessionclass()(config, out) 
        session.main() 
        l = session.getitemoutcomepairs(Passed) 
        assert len(l) == 2
    finally: 
        old.chdir() 

    # test that running the file directly works 
    config = py.test.config._reparse([str(checkfile)]) 
    out = py.std.cStringIO.StringIO()
    session = config._getsessionclass()(config, out) 
    session.main() 
    l = session.getitemoutcomepairs(Passed) 
    assert len(l) == 2

def test_custom_NONpython_collection_from_conftest():
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

    for x in (o, checkfile, checkfile.dirpath()): 
        print "checking that %s returns custom items" % (x,) 
        config = py.test.config._reparse([x])
        col = config._getcollector(x)
        assert len(list(col._tryiter(py.test.collect.Item))) == 1
        #assert items[1].__class__.__name__ == 'MyFunction'

    # test that running a session works from the directories
    old = o.chdir() 
    try: 
        config = py.test.config._reparse([]) 
        out = py.std.cStringIO.StringIO()
        session = config._getsessionclass()(config, out) 
        session.main() 
        l = session.getitemoutcomepairs(Passed) 
        assert len(l) == 1
    finally: 
        old.chdir() 

    # test that running the file directly works 
    config = py.test.config._reparse([str(checkfile)]) 
    out = py.std.cStringIO.StringIO()
    session = config._getsessionclass()(config, out) 
    session.main() 
    l = session.getitemoutcomepairs(Passed) 
    assert len(l) == 1

def test_order_of_execution_generator_same_codeline():
    o = tmpdir.ensure('genorder1', dir=1)
    o.join("test_order1.py").write(py.code.Source("""
    def test_generative_order_of_execution():
        test_list = []
        expected_list = range(6)

        def list_append(item):
            test_list.append(item)
            
        def assert_order_of_execution():
            print 'expected order', expected_list
            print 'but got       ', test_list
            assert test_list == expected_list
        
        for i in expected_list:
            yield list_append, i
        yield assert_order_of_execution
    """))
    config = py.test.config._reparse([o])
    session = config.initsession()
    session.main()
    l = session.getitemoutcomepairs(Passed) 
    assert len(l) == 7

def test_order_of_execution_generator_different_codeline():
    o = tmpdir.ensure('genorder2', dir=2)
    o.join("test_genorder2.py").write(py.code.Source("""
    def test_generative_tests_different_codeline():
        test_list = []
        expected_list = range(3)

        def list_append_2():
            test_list.append(2)

        def list_append_1():
            test_list.append(1)

        def list_append_0():
            test_list.append(0)

        def assert_order_of_execution():
            print 'expected order', expected_list
            print 'but got       ', test_list
            assert test_list == expected_list
            
        yield list_append_0
        yield list_append_1
        yield list_append_2
        yield assert_order_of_execution   
    """))
    config = py.test.config._reparse([o])
    session = config.initsession()
    session.main()
    l = session.getitemoutcomepairs(Passed) 
    assert len(l) == 4
    


def test_documentation_virtual_collector_interaction():
    rootdir = py.path.local(py.__file__).dirpath("doc")
    # HACK 
    from py.__.doc import conftest as conf
    old = conf.option.forcegen
    try:
        conf.option.forcegen = 1
        col = py.test.collect.Directory(rootdir)
        x = list(col._tryiter(yieldtype=py.test.collect.Function))
    finally:
        conf.option.forcegen = old
    

def test__tryiter_ignores_skips():
    tmp = py.test.ensuretemp("_tryiterskip")
    tmp.ensure("subdir", "conftest.py").write(py.code.Source("""
        import py
        class Directory(py.test.collect.Directory):
            def run(self):
                py.test.skip("intentional")
    """))
    col = py.test.collect.Directory(tmp)
    try:
        list(col._tryiter())
    except KeyboardInterrupt: 
        raise
    except:
        exc = py.code.ExceptionInfo() 
        py.test.fail("should not have raised: %s"  %(exc,))
    
    
def test__tryiter_ignores_failing_collectors(): 
    tmp = py.test.ensuretemp("_tryiterfailing")
    tmp.ensure("subdir", "conftest.py").write(py.code.Source("""
        bla bla bla
    """))
    col = py.test.collect.Directory(tmp)
    try:
        list(col._tryiter())
    except KeyboardInterrupt: 
        raise
    except:
        exc = py.code.ExceptionInfo() 
        py.test.fail("should not have raised: %s"  %(exc,))

    l = []
    list(col._tryiter(reporterror=l.append))
    assert len(l) == 2
    excinfo, item = l[-1]
    assert isinstance(excinfo, py.code.ExceptionInfo)

def test_tryiter_handles_keyboardinterrupt(): 
    tmp = py.test.ensuretemp("tryiterkeyboard")
    tmp.ensure("subdir", "conftest.py").write(py.code.Source("""
        raise KeyboardInterrupt() 
    """))
    col = py.test.collect.Directory(tmp)
    py.test.raises(KeyboardInterrupt, list, col._tryiter())

def test_check_random_inequality():
    tmp = py.test.ensuretemp("ineq")
    tmp.ensure("test_x.py").write(py.code.Source("""def test_one():
        pass
    """))
    col = py.test.collect.Directory(tmp)
    fn = col._tryiter().next()
    assert fn != 3
    assert fn != col
    assert fn != [1,2,3]
    assert [1,2,3] != fn
    assert col != fn

def test_check_generator_collect_problems():
    tmp = py.test.ensuretemp("gener_coll")
    tmp.ensure("test_one.py").write(py.code.Source("""
        def setup_module(mod):
            mod.x = [1,2,3]
        
        def check(zzz):
            assert zzz
        
        def test_one():
            for i in x:
                yield check, i
    """))
    tmp.ensure("__init__.py")
    col = py.test.collect.Module(tmp.join("test_one.py"))
    errors = []
    l = list(col._tryiter(reporterror=errors.append))
    assert len(errors) == 2

def test_check_collect_hashes():
    tmp = py.test.ensuretemp("check_collect_hashes")
    tmp.ensure("test_one.py").write(py.code.Source("""
        def test_1():
            pass
        
        def test_2():
            pass
    """))
    tmp.ensure("test_two.py").write(py.code.Source("""
        def test_1():
            pass
        
        def test_2():
            pass
    """))
    tmp.ensure("__init__.py")
    col = py.test.collect.Directory(tmp)
    l = list(col._tryiter())
    assert len(l) == 4
    for numi, i in enumerate(l):
        for numj, j in enumerate(l):
            if numj != numi:
                assert hash(i) != hash(j)
                assert i != j


def test_check_directory_ordered():
    tmpdir = py.test.ensuretemp("test_check_directory_ordered")
    fnames = []
    for i in range(9, -1, -1):
        x = tmpdir.ensure("xdir%d" %(i, ), dir=1)
        fnames.append(x.basename)
    for i in range(9, -1, -1):
        x = tmpdir.ensure("test_file%d.py" % (i,))
        fnames.append(x.basename)
    fnames.sort()
    tmpdir.ensure('adir', dir=1)
    fnames.insert(10, 'adir')
    col = py.test.collect.Directory(tmpdir)
    names = col.run()
    assert names == fnames 
        
        
