from __future__ import generators
import py
from py.__.test import event, outcome 
from py.__.test.testing import suptest
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
    from py.__.test.collect import Collector, Item
    assert not issubclass(Collector, Item)
    assert not issubclass(Item, Collector)

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
    items = col.collect()
    names = [x.name for x in items]
    assert len(items) == 2
    assert 'normal' in names
    assert 'test_found.py' in names

class TestCollect(suptest.InlineCollection):
    def test_failing_import(self):
        modcol = self.getmodulecol("import alksdjalskdjalkjals")
        py.test.raises(ImportError, modcol.collect)
        py.test.raises(ImportError, modcol.collect)
        py.test.raises(ImportError, modcol.run)

    def test_syntax_error_in_module(self):
        modcol = self.getmodulecol("this is a syntax error") 
        py.test.raises(SyntaxError, modcol.collect)
        py.test.raises(SyntaxError, modcol.collect)
        py.test.raises(SyntaxError, modcol.run)

    def test_listnames_and__getitembynames(self):
        modcol = self.getmodulecol("pass")
        names = modcol.listnames()
        dircol = modcol._config.getfsnode(modcol._config.topdir)
        x = dircol._getitembynames(names)
        assert modcol.name == x.name 
        assert modcol.name == x.name 

    def test_listnames_getitembynames_custom(self):
        hello = self._makefile(".xxx", hello="world")
        self.makepyfile(conftest="""
            import py
            class CustomFile(py.test.collect.File):
                pass
            class MyDirectory(py.test.collect.Directory):
                def collect(self):
                    return [CustomFile(self.fspath.join("hello.xxx"), parent=self)]
            Directory = MyDirectory
        """)
        config = self.parseconfig(hello)
        node = config.getfsnode(hello)
        assert isinstance(node, py.test.collect.File)
        assert node.name == "hello.xxx"
        names = node.listnames()[1:]
        dircol = config.getfsnode(config.topdir) 
        node = dircol._getitembynames(names)
        assert isinstance(node, py.test.collect.File)

    def test_found_certain_testfiles(self): 
        p1 = self.makepyfile(test_found = "pass", found_test="pass")
        col = py.test.collect.Directory(p1.dirpath(), config=dummyconfig) 
        items = col.collect() # Directory collect returns files sorted by name
        assert len(items) == 2
        assert items[1].name == 'test_found.py'
        assert items[0].name == 'found_test.py'

    def test_disabled_class(self):
        modcol = self.getmodulecol("""
            class TestClass:
                disabled = True
                def test_method(self):
                    pass
        """)
        l = modcol.collect()
        assert len(l) == 1
        modcol = l[0]
        assert isinstance(modcol, py.test.collect.Class)
        assert not modcol.collect() 

    def test_disabled_module(self):
        modcol = self.getmodulecol("""
            disabled = True
            def setup_module(mod):
                raise ValueError
        """)
        assert not modcol.collect() 
        assert not modcol.run() 

    def test_generative_functions(self): 
        modcol = self.getmodulecol("""
            def func1(arg, arg2): 
                assert arg == arg2 

            def test_gen(): 
                yield func1, 17, 3*5
                yield func1, 42, 6*7
        """)
        colitems = modcol.collect()
        assert len(colitems) == 1
        gencol = colitems[0]
        assert isinstance(gencol, py.test.collect.Generator)
        gencolitems = gencol.collect()
        assert len(gencolitems) == 2
        assert isinstance(gencolitems[0], py.test.collect.Function)
        assert isinstance(gencolitems[1], py.test.collect.Function)
        assert gencolitems[0].name == '[0]'
        assert gencolitems[0].obj.func_name == 'func1'

    def test_generative_methods(self): 
        modcol = self.getmodulecol("""
            def func1(arg, arg2): 
                assert arg == arg2 
            class TestGenMethods: 
                def test_gen(self): 
                    yield func1, 17, 3*5
                    yield func1, 42, 6*7
        """)
        gencol = modcol.collect()[0].collect()[0].collect()[0]
        assert isinstance(gencol, py.test.collect.Generator)
        gencolitems = gencol.collect()
        assert len(gencolitems) == 2
        assert isinstance(gencolitems[0], py.test.collect.Function)
        assert isinstance(gencolitems[1], py.test.collect.Function)
        assert gencolitems[0].name == '[0]'
        assert gencolitems[0].obj.func_name == 'func1'

    def test_module_assertion_setup(self):
        modcol = self.getmodulecol("pass")
        from py.__.magic import assertion
        l = []
        py.magic.patch(assertion, "invoke", lambda: l.append(None))
        try:
            modcol.setup()
        finally:
            py.magic.revert(assertion, "invoke")
        x = l.pop()
        assert x is None
        py.magic.patch(assertion, "revoke", lambda: l.append(None))
        try:
            modcol.teardown()
        finally:
            py.magic.revert(assertion, "revoke")
        x = l.pop()
        assert x is None

    def test_check_equality_and_cmp_basic(self):
        modcol = self.getmodulecol("""
            def test_pass(): pass
            def test_fail(): assert 0
        """)
        fn1 = modcol.collect_by_name("test_pass")
        assert isinstance(fn1, py.test.collect.Function)
        fn2 = modcol.collect_by_name("test_pass")
        assert isinstance(fn2, py.test.collect.Function)

        assert fn1 == fn2
        assert fn1 != modcol 
        assert cmp(fn1, fn2) == 0
        assert hash(fn1) == hash(fn2) 

        fn3 = modcol.collect_by_name("test_fail")
        assert isinstance(fn3, py.test.collect.Function)
        assert not (fn1 == fn3) 
        assert fn1 != fn3
        assert cmp(fn1, fn3) == -1

        assert cmp(fn1, 10) == -1 
        assert cmp(fn2, 10) == -1 
        assert cmp(fn3, 10) == -1 
        for fn in fn1,fn2,fn3:
            assert fn != 3
            assert fn != modcol
            assert fn != [1,2,3]
            assert [1,2,3] != fn
            assert modcol != fn

    def test_directory_file_sorting(self):
        p1 = self.makepyfile(test_one="hello")
        p1.dirpath().mkdir("x")
        p1.dirpath().mkdir("dir1")
        self.makepyfile(test_two="hello")
        p1.dirpath().mkdir("dir2")
        config = self.parseconfig()
        col = config.getfsnode(p1.dirpath())
        names = [x.name for x in col.collect()]
        assert names == ["dir1", "dir2", "test_one.py", "test_two.py", "x"]

    def test_collector_deprecated_run_method(self):
        modcol = self.getmodulecol("pass")
        res1 = py.test.deprecated_call(modcol.run)
        res2 = modcol.collect()
        assert res1 == [x.name for x in res2]

class TestCustomConftests(suptest.InlineCollection):
    def test_extra_python_files_and_functions(self):
        self.makepyfile(conftest="""
            import py
            class MyFunction(py.test.collect.Function):
                pass
            class Directory(py.test.collect.Directory):
                def consider_file(self, path, usefilters=True):
                    if path.check(fnmatch="check_*.py"):
                        return self.Module(path, parent=self)
                    return super(Directory, self).consider_file(path, usefilters=usefilters)
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
        checkfile = self.makepyfile(check_file="""
            def check_func():
                assert 42 == 42
            class CustomTestClass:
                def check_method(self):
                    assert 23 == 23
        """)
        # check that directory collects "check_" files 
        config = self.parseconfig()
        col = config.getfsnode(checkfile.dirpath())
        colitems = col.collect()
        assert len(colitems) == 1
        assert isinstance(colitems[0], py.test.collect.Module)

        # check that module collects "check_" functions and methods
        config = self.parseconfig(checkfile)
        col = config.getfsnode(checkfile)
        assert isinstance(col, py.test.collect.Module)
        colitems = col.collect()
        assert len(colitems) == 2
        funccol = colitems[0]
        assert isinstance(funccol, py.test.collect.Function)
        assert funccol.name == "check_func"
        clscol = colitems[1]
        assert isinstance(clscol, py.test.collect.Class)
        colitems = clscol.collect()[0].collect()
        assert len(colitems) == 1
        assert colitems[0].name == "check_method"

    def test_non_python_files(self):
        self.makepyfile(conftest="""
            import py
            class CustomItem(py.test.collect.Item): 
                def run(self):
                    pass
            class Directory(py.test.collect.Directory):
                def consider_file(self, fspath, usefilters=True):
                    if fspath.ext == ".xxx":
                        return CustomItem(fspath.basename, parent=self)
        """)
        checkfile = self._makefile(ext="xxx", hello="world")
        self.makepyfile(x="")
        self.maketxtfile(x="")
        config = self.parseconfig()
        dircol = config.getfsnode(checkfile.dirpath())
        colitems = dircol.collect()
        assert len(colitems) == 1
        assert colitems[0].name == "hello.xxx"
        assert colitems[0].__class__.__name__ == "CustomItem"

        item = config.getfsnode(checkfile)
        assert item.name == "hello.xxx"
        assert item.__class__.__name__ == "CustomItem"

def test_module_file_not_found():
    fn = tmpdir.join('nada','no')
    col = py.test.collect.Module(fn, config=dummyconfig) 
    py.test.raises(py.error.ENOENT, col.collect) 


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

    def test_example_items1(self):
        self.tmp.ensure("test_example.py").write(py.code.Source('''
            def testone():
                pass

            class TestX:
                def testmethod_one(self):
                    pass

            class TestY(TestX):
                pass
        '''))
        items, events = self._genitems()
        assert len(items) == 3
        assert items[0].name == 'testone'
        assert items[1].name == 'testmethod_one'
        assert items[2].name == 'testmethod_one'

        # let's also test getmodpath here
        assert items[0].getmodpath() == "testone"
        assert items[1].getmodpath() == "TestX.testmethod_one"
        assert items[2].getmodpath() == "TestY.testmethod_one"

        s = items[0].getmodpath(stopatmodule=False)
        assert s == "test_example_items1.test_example.testone"
        print s

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
        classcol = modcol.collect_by_name("TestClass")
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
        gencol = modcol.collect_by_name("test_gen")
        info = gencol.repr_metainfo()
        assert info.fspath == modcol.fspath
        assert info.lineno == 1
        assert info.modpath == "test_gen"

        genitem = gencol.collect()[0]
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
        item = modcol1.collect_by_name("test_one")
        item2a = self.p1_to_p2(item)
        assert item is not item2a # of course
        assert item2a.name == item.name
        modback = self.p2_to_p1(item2a.parent)
        assert modback is modcol1

