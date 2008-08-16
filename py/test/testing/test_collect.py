from __future__ import generators
import py
from py.__.test import event, outcome 
import setupdata, suptest
from py.__.test.conftesthandle import Conftest
from py.__.test.collect import SetupState
from test_config import getcolitems
from py.__.test.pycollect import DoctestFileContent

class DummyConfig:
    def __init__(self):
        self._conftest = Conftest()
        self._setupstate = SetupState()
        class dummyoption:
            nomagic = False
        self.option = dummyoption
    def getvalue(self, name, fspath):
        return self._conftest.rget(name, fspath)

def setup_module(mod):
    mod.tmpdir = py.test.ensuretemp(mod.__name__) 
    mod.dummyconfig = DummyConfig()

def test_collect_versus_item():
    path = setupdata.getexamplefile("filetest.py")
    col = py.test.collect.Module(path, config=dummyconfig) 
    assert not isinstance(col, py.test.collect.Item)
    item = col.join("test_one") 
    assert not hasattr(item, "join") 
    assert not isinstance(item, py.test.collect.Collector) 

def test_collector_deprecated_run_method():
    path = setupdata.getexamplefile("filetest.py")
    col = py.test.collect.Module(path, config=dummyconfig)
    res1 = py.test.deprecated_call(col.run)
    res2 = col.listdir()
    assert res1 == res2

def test_module_assertion_setup():
    path = setupdata.getexamplefile("filetest.py")
    col = py.test.collect.Module(path, config=dummyconfig) 
    from py.__.magic import assertion
    l = []
    py.magic.patch(assertion, "invoke", lambda: l.append(None))
    try:
        col.setup()
    finally:
        py.magic.revert(assertion, "invoke")
    x = l.pop()
    assert x is None
    py.magic.patch(assertion, "revoke", lambda: l.append(None))
    try:
        col.teardown()
    finally:
        py.magic.revert(assertion, "revoke")
    x = l.pop()
    assert x is None
    

def test_failing_import_execfile():
    dest = setupdata.getexamplefile('failingimport.py')
    col = py.test.collect.Module(dest, config=dummyconfig) 
    py.test.raises(ImportError, col.listdir)
    py.test.raises(ImportError, col.listdir)

def test_collect_listnames_and_back():
    path = setupdata.getexamplefile("filetest.py")
    col1 = py.test.collect.Directory(path.dirpath().dirpath(), 
                                      config=dummyconfig)
    col2 = col1.join(path.dirpath().basename) 
    col3 = col2.join(path.basename) 
    l = col3.listnames()
    assert len(l) == 3
    x = col1._getitembynames(l[1:])
    assert x.name == "filetest.py"
    l2 = x.listnames()
    assert len(l2) == 3

def test_finds_tests(): 
    fn = setupdata.getexamplefile('filetest.py') 
    col = py.test.collect.Module(fn, config=dummyconfig) 
    l = col.listdir() 
    assert len(l) == 2 
    assert l[0] == 'test_one' 
    assert l[1] == 'TestClass' 

def test_found_certain_testfiles(): 
    tmp = py.test.ensuretemp("found_certain_testfiles")
    tmp.ensure('test_found.py')
    tmp.ensure('found_test.py')

    col = py.test.collect.Directory(tmp, config=dummyconfig) 
    items = [col.join(x) for x in col.listdir()]

    assert len(items) == 2
    assert items[1].name == 'test_found.py'
    assert items[0].name == 'found_test.py'

def test_ignored_certain_directories(): 
    tmp = py.test.ensuretemp("ignore_certain_directories")
    tmp.ensure("_darcs", 'test_notfound.py')
    tmp.ensure("CVS", 'test_notfound.py')
    tmp.ensure("{arch}", 'test_notfound.py')
    tmp.ensure(".whatever", 'test_notfound.py')
    tmp.ensure(".bzr", 'test_notfound.py')
    tmp.ensure("normal", 'test_found.py')
    tmp.ensure('test_found.py')

    col = py.test.collect.Directory(tmp, config=dummyconfig) 
    items = col.listdir()
    assert len(items) == 2
    assert 'normal' in items 
    assert 'test_found.py' in items 

def test_failing_import_directory():
    class MyDirectory(py.test.collect.Directory):
        def filefilter(self, p):
            return p.check(fnmatch='testspecial*.py')
    filetest = setupdata.getexamplefile("testspecial_importerror.py")
    mydir = MyDirectory(filetest.dirpath(), config=dummyconfig)
    l = mydir.listdir() 
    assert len(l) == 1
    col = mydir.join(l[0])
    assert isinstance(col, py.test.collect.Module)
    py.test.raises(ImportError, col.listdir)

def test_module_file_not_found():
    fn = tmpdir.join('nada','no')
    col = py.test.collect.Module(fn, config=dummyconfig) 
    py.test.raises(py.error.ENOENT, col.listdir) 

def test_syntax_error_in_module():
    modpath = setupdata.getexamplefile("syntax_error.py")
    col = py.test.collect.Module(modpath, config=dummyconfig) 
    py.test.raises(SyntaxError, col.listdir)

def test_disabled_class():
    p = setupdata.getexamplefile('disabled.py')
    col = py.test.collect.Module(p, config=dummyconfig) 
    l = col.listdir() 
    assert len(l) == 1
    col = col.join(l[0])
    assert isinstance(col, py.test.collect.Class)
    assert not col.listdir() 

def test_disabled_module():
    p = setupdata.getexamplefile("disabled_module.py")
    col = py.test.collect.Module(p, config=dummyconfig) 
    l = col.listdir() 
    assert len(l) == 0

def test_generative_simple(): 
    tfile = setupdata.getexamplefile('test_generative.py')
    col = py.test.collect.Module(tfile, config=dummyconfig) 
    l = col.listdir() 
    assert len(l) == 2 
    l = col.multijoin(l) 

    generator = l[0]
    assert isinstance(generator, py.test.collect.Generator)
    l2 = generator.listdir() 
    assert len(l2) == 2 
    l2 = generator.multijoin(l2) 
    assert isinstance(l2[0], py.test.collect.Function)
    assert isinstance(l2[1], py.test.collect.Function)
    assert l2[0].name == '[0]'
    assert l2[1].name == '[1]'

    assert l2[0].obj.func_name == 'func1' 
 
    classlist = l[1].listdir() 
    assert len(classlist) == 1
    classlist = l[1].multijoin(classlist) 
    cls = classlist[0]
    generator = cls.join(cls.listdir()[0])
    assert isinstance(generator, py.test.collect.Generator)
    l2 = generator.listdir() 
    assert len(l2) == 2 
    l2 = generator.multijoin(l2) 
    assert isinstance(l2[0], py.test.collect.Function)
    assert isinstance(l2[1], py.test.collect.Function)
    assert l2[0].name == '[0]'
    assert l2[1].name == '[1]'


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
    sorter = suptest.events_from_cmdline([o])
    passed, skipped, failed = sorter.countoutcomes() 
    assert passed == 7
    assert not skipped and not failed 

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
    sorter = suptest.events_from_cmdline([o])
    passed, skipped, failed = sorter.countoutcomes() 
    assert passed == 4
    assert not skipped and not failed 

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
    col = py.test.collect.Directory(tmpdir, config=dummyconfig)
    names = col.listdir()
    assert names == fnames 

def test_check_equality_and_cmp_basic():
    path = setupdata.getexamplefile("funcexamples.py")
    col = py.test.collect.Module(path, config=dummyconfig)
    fn1 = col.join("funcpassed")
    assert isinstance(fn1, py.test.collect.Function)
    fn2 = col.join("funcpassed") 
    assert isinstance(fn2, py.test.collect.Function)

    assert fn1 == fn2
    assert fn1 != col 
    assert cmp(fn1, fn2) == 0
    assert hash(fn1) == hash(fn2) 

    fn3 = col.join("funcfailed")
    assert isinstance(fn3, py.test.collect.Function)
    assert not (fn1 == fn3) 
    assert fn1 != fn3
    assert cmp(fn1, fn3) == -1

    assert cmp(fn1, 10) == -1 
    assert cmp(fn2, 10) == -1 
    assert cmp(fn3, 10) == -1 
    for fn in fn1,fn2,fn3:
        assert fn != 3
        assert fn != col
        assert fn != [1,2,3]
        assert [1,2,3] != fn
        assert col != fn


def test_function_equality():
    config = py.test.config._reparse([tmpdir])
    f1 = py.test.collect.Function(name="name", config=config, 
                                  args=(1,), callobj=isinstance)
    f2 = py.test.collect.Function(name="name", config=config, 
                                  args=(1,), callobj=callable)
    assert not f1 == f2
    assert f1 != f2
    f3 = py.test.collect.Function(name="name", config=config, 
                                  args=(1,2), callobj=callable)
    assert not f3 == f2
    assert f3 != f2

    assert not f3 == f1
    assert f3 != f1

    f1_b = py.test.collect.Function(name="name", config=config, 
                                  args=(1,), callobj=isinstance)
    assert f1 == f1_b
    assert not f1 != f1_b
    
    
class Testgenitems: 
    def setup_class(cls):
        cls.classtemp = py.test.ensuretemp(cls.__name__)
            
    def setup_method(self, method):
        self.tmp = self.classtemp.mkdir(method.func_name)

    def _genitems(self, tmp=None):
        if tmp is None:
            tmp = self.tmp 
        print "using tempdir", tmp 
        config = py.test.config._reparse([tmp])
        session = config.initsession()
        l = suptest.eventappender(session)
        items = list(session.genitems(getcolitems(config)))
        return items, l 

    def test_check_collect_hashes(self):
        one = self.tmp.ensure("test_check_collect_hashes.py")
        one.write(py.code.Source("""
            def test_1():
                pass

            def test_2():
                pass
        """))
        one.copy(self.tmp.join("test_check_collect_hashes_2.py"))
        items, events = self._genitems()
        assert len(items) == 4
        for numi, i in enumerate(items):
            for numj, j in enumerate(items):
                if numj != numi:
                    assert hash(i) != hash(j)
                    assert i != j
       
    def test_skip_by_conftest_directory(self):
        from py.__.test import outcome
        self.tmp.ensure("subdir", "conftest.py").write(py.code.Source("""
            import py
            class Directory(py.test.collect.Directory):
                def listdir(self):
                    py.test.skip("intentional")
        """))
        items, events = self._genitems()
        assert len(items) == 0
        skips = [x for x in events
                    if isinstance(x, event.CollectionReport)
                       and x.colitem.name == 'subdir']
        assert len(skips) == 1
        assert skips[0].skipped 

    def test_root_conftest_syntax_error(self): 
        # do we want to unify behaviour with
        # test_subdir_conftest_error? 
        self.tmp.ensure("conftest.py").write("raise SyntaxError\n")
        py.test.raises(SyntaxError, self._genitems)
       
    def test_subdir_conftest_error(self):
        self.tmp.ensure("sub", "conftest.py").write("raise SyntaxError\n")
        items, events = self._genitems()
        failures = [x for x in events 
                      if isinstance(x, event.CollectionReport)
                           and x.failed]
        assert len(failures) == 1
        ev = failures[0] 
        assert ev.outcome.longrepr.reprcrash.message.startswith("SyntaxError")

    def test_skip_at_module_level(self):
        self.tmp.ensure("test_module.py").write(py.code.Source("""
            import py
            py.test.skip('xxx')
        """))
        items, events = self._genitems()
        funcs = [x for x in items if isinstance(x, event.ItemStart)]
        assert not funcs 
        assert not items 
        l = [x for x in events 
                if isinstance(x, event.CollectionReport)
                   and x.colitem.name == 'test_module.py']
        assert len(l) == 1
        ev = l[0]
        assert ev.skipped 

    def test_example_items1(self):
        self.tmp.ensure("test_example.py").write(py.code.Source('''
            def test_one():
                pass

            class TestX:
                def test_method_one(self):
                    pass

            class TestY(TestX):
                pass
        '''))
        items, events = self._genitems()
        assert len(items) == 3
        assert items[0].name == 'test_one'
        assert items[1].name == 'test_method_one'
        assert items[2].name == 'test_method_one'

    def test_custom_python_collection_from_conftest(self):
        checkfile = setupdata.setup_customconfigtest(self.tmp) 
        for x in (self.tmp, checkfile, checkfile.dirpath()): 
            items, events = self._genitems(x)
            assert len(items) == 2
            #assert items[1].__class__.__name__ == 'MyFunction'

        return None # XXX shift below to session test? 
        # test that running a session works from the directories
        old = o.chdir() 
        try: 
            sorter = suptest.events_from_cmdline([])
            passed, skipped, failed = sorter.countoutcomes()
            assert passed == 2
            assert skipped == failed == 0 
        finally: 
            old.chdir() 

        # test that running the file directly works 
        sorter = suptest.events_from_cmdline([str(checkfile)])
        passed, skipped, failed = sorter.countoutcomes()
        assert passed == 2
        assert skipped == failed == 0 

    def test_custom_NONpython_collection_from_conftest(self):
        checkfile = setupdata.setup_non_python_dir(self.tmp)
       
        for x in (self.tmp, checkfile, checkfile.dirpath()): 
            print "checking that %s returns custom items" % (x,) 
            items, events = self._genitems(x)
            assert len(items) == 1
            assert items[0].__class__.__name__ == 'CustomItem'

        return None # XXX shift below to session tests? 

        # test that running a session works from the directories
        old = self.tmp.chdir() 
        try: 
            sorter = suptest.events_from_cmdline([])
            passed, skipped, failed = sorter.countoutcomes()
            assert passed == 1
            assert skipped == failed == 0 
        finally:
            old.chdir() 

        # test that running the file directly works 
        sorter = suptest.events_from_cmdline([str(checkfile)])
        passed, skipped, failed = sorter.countoutcomes()
        assert passed == 1
        assert skipped == failed == 0 

    def test_collect_doctest_files_with_test_prefix(self):
        self.tmp.ensure("whatever.txt")
        checkfile = self.tmp.ensure("test_something.txt")
        checkfile.write(py.code.Source("""
            alskdjalsdk
            >>> i = 5
            >>> i-1
            4
        """))
        for x in (self.tmp, checkfile): 
            #print "checking that %s returns custom items" % (x,) 
            items, events = self._genitems(x)
            assert len(items) == 1
            assert isinstance(items[0], DoctestFileContent)

class TestCollector:
    def setup_method(self, method):
        self.tmpdir = py.test.ensuretemp("%s_%s" % 
            (self.__class__.__name__, method.__name__))

    def test_totrail_and_back(self):
        a = self.tmpdir.ensure("a", dir=1)
        self.tmpdir.ensure("a", "__init__.py")
        x = self.tmpdir.ensure("a", "trail.py")
        config = py.test.config._reparse([x])
        col = config.getfsnode(x)
        trail = col._totrail()
        assert len(trail) == 2
        assert trail[0] == a.relto(config.topdir)
        assert trail[1] == ('trail.py',)
        col2 = py.test.collect.Collector._fromtrail(trail, config)
        assert col2.listnames() == col.listnames()
       
    def test_totrail_topdir_and_beyond(self):
        config = py.test.config._reparse([self.tmpdir])
        col = config.getfsnode(config.topdir)
        trail = col._totrail()
        assert len(trail) == 2
        assert trail[0] == '.'
        assert trail[1] == ()
        col2 = py.test.collect.Collector._fromtrail(trail, config)
        assert col2.fspath == config.topdir
        assert len(col2.listchain()) == 1
        col3 = config.getfsnode(config.topdir.dirpath())
        py.test.raises(ValueError, 
              "col3._totrail()")
        
class TestCollectorReprs(suptest.InlineCollection):
    def test_repr_metainfo_basic_item(self):
        modcol = self.getmodulecol("")
        Item = py.test.collect.Item
        item = Item("virtual", parent=modcol)
        info = item.repr_metainfo() 
        assert info.fspath == modcol.fspath
        assert not info.lineno
        assert info.modpath == "Item"
        
    def test_repr_metainfo_func(self):
        item = self.getitem("def test_func(): pass")
        info = item.repr_metainfo()
        assert info.fspath == item.fspath 
        assert info.lineno == 0
        assert info.modpath == "test_func"

    def test_repr_metainfo_class(self):
        modcol = self.getmodulecol("""
            # lineno 0
            class TestClass:
                def test_hello(self): pass
        """)
        classcol = modcol.join("TestClass")
        info = classcol.repr_metainfo()
        assert info.fspath == modcol.fspath 
        assert info.lineno == 1
        assert info.modpath == "TestClass"

    def test_repr_metainfo_generator(self):
        modcol = self.getmodulecol("""
            # lineno 0
            def test_gen(): 
                def check(x): 
                    assert x
                yield check, 3
        """)
        gencol = modcol.join("test_gen")
        info = gencol.repr_metainfo()
        assert info.fspath == modcol.fspath
        assert info.lineno == 1
        assert info.modpath == "test_gen"

        genitem = gencol.join(gencol.listdir()[0])
        info = genitem.repr_metainfo()
        assert info.fspath == modcol.fspath
        assert info.lineno == 2
        assert info.modpath == "test_gen[0]"
        """
            def test_func():
                pass
            def test_genfunc():
                def check(x):
                    pass
                yield check, 3
            class TestClass:
                def test_method(self):
                    pass
       """

from py.__.test.dsession.mypickle import ImmutablePickler
class PickleTransport:
    def __init__(self):
        self.p1 = ImmutablePickler(uneven=0)
        self.p2 = ImmutablePickler(uneven=1)

    def p1_to_p2(self, obj):
        return self.p2.loads(self.p1.dumps(obj))

    def p2_to_p1(self, obj):
        return self.p1.loads(self.p2.dumps(obj))

class TestPickling(suptest.InlineCollection):
    def setup_method(self, method):
        super(TestPickling, self).setup_method(method)
        pt = PickleTransport()
        self.p1_to_p2 = pt.p1_to_p2
        self.p2_to_p1 = pt.p2_to_p1

    def unifyconfig(self, config):
        p2config = self.p1_to_p2(config)
        p2config._initafterpickle(config.topdir)
        return p2config

    def test_pickle_config(self):
        config1 = py.test.config._reparse([])
        p2config = self.unifyconfig(config1)
        assert p2config.topdir == config1.topdir
        config_back = self.p2_to_p1(p2config)
        assert config_back is config1

    def test_pickle_module(self):
        modcol1 = self.getmodulecol("def test_one(): pass")
        self.unifyconfig(modcol1._config) 

        modcol2a = self.p1_to_p2(modcol1)
        modcol2b = self.p1_to_p2(modcol1)
        assert modcol2a is modcol2b

        modcol1_back = self.p2_to_p1(modcol2a)
        assert modcol1_back

    def test_pickle_func(self):
        modcol1 = self.getmodulecol("def test_one(): pass")
        self.unifyconfig(modcol1._config) 
        item = modcol1.join("test_one")
        item2a = self.p1_to_p2(item)
        assert item is not item2a # of course
        assert item2a.name == item.name
        modback = self.p2_to_p1(item2a.parent)
        assert modback is modcol1

