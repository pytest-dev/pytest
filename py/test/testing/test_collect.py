import py

class TestCollector:
    def test_collect_versus_item(self):
        from py.__.test.collect import Collector, Item
        assert not issubclass(Collector, Item)
        assert not issubclass(Item, Collector)

    def test_check_equality_and_cmp_basic(self, testdir):
        modcol = testdir.getmodulecol("""
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

    def test_totrail_and_back(self, tmpdir):
        a = tmpdir.ensure("a", dir=1)
        tmpdir.ensure("a", "__init__.py")
        x = tmpdir.ensure("a", "trail.py")
        config = py.test.config._reparse([x])
        col = config.getfsnode(x)
        trail = col._totrail()
        assert len(trail) == 2
        assert trail[0] == a.relto(config.topdir)
        assert trail[1] == ('trail.py',)
        col2 = py.test.collect.Collector._fromtrail(trail, config)
        assert col2.listnames() == col.listnames()
       
    def test_totrail_topdir_and_beyond(self, tmpdir):
        config = py.test.config._reparse([tmpdir])
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
        

    def test_listnames_and__getitembynames(self, testdir):
        modcol = testdir.getmodulecol("pass", withinit=True)
        print modcol.config.pytestplugins.getplugins()
        names = modcol.listnames()
        print names
        dircol = modcol.config.getfsnode(modcol.config.topdir)
        x = dircol._getitembynames(names)
        assert modcol.name == x.name 

    def test_listnames_getitembynames_custom(self, testdir):
        hello = testdir.makefile(".xxx", hello="world")
        testdir.makepyfile(conftest="""
            import py
            class CustomFile(py.test.collect.File):
                pass
            class MyDirectory(py.test.collect.Directory):
                def collect(self):
                    return [CustomFile(self.fspath.join("hello.xxx"), parent=self)]
            Directory = MyDirectory
        """)
        config = testdir.parseconfig(hello)
        node = config.getfsnode(hello)
        assert isinstance(node, py.test.collect.File)
        assert node.name == "hello.xxx"
        names = node.listnames()[1:]
        dircol = config.getfsnode(config.topdir) 
        node = dircol._getitembynames(names)
        assert isinstance(node, py.test.collect.File)

class TestCollectFS:
    def test_ignored_certain_directories(self, testdir): 
        tmpdir = testdir.tmpdir
        tmpdir.ensure("_darcs", 'test_notfound.py')
        tmpdir.ensure("CVS", 'test_notfound.py')
        tmpdir.ensure("{arch}", 'test_notfound.py')
        tmpdir.ensure(".whatever", 'test_notfound.py')
        tmpdir.ensure(".bzr", 'test_notfound.py')
        tmpdir.ensure("normal", 'test_found.py')
        tmpdir.ensure('test_found.py')

        col = testdir.parseconfig(tmpdir).getfsnode(tmpdir)
        items = col.collect()
        names = [x.name for x in items]
        assert len(items) == 2
        assert 'normal' in names
        assert 'test_found.py' in names

    def test_found_certain_testfiles(self, testdir): 
        p1 = testdir.makepyfile(test_found = "pass", found_test="pass")
        col = testdir.parseconfig(p1).getfsnode(p1.dirpath())
        items = col.collect() # Directory collect returns files sorted by name
        assert len(items) == 2
        assert items[1].name == 'test_found.py'
        assert items[0].name == 'found_test.py'

    def test_directory_file_sorting(self, testdir):
        p1 = testdir.makepyfile(test_one="hello")
        p1.dirpath().mkdir("x")
        p1.dirpath().mkdir("dir1")
        testdir.makepyfile(test_two="hello")
        p1.dirpath().mkdir("dir2")
        config = testdir.parseconfig()
        col = config.getfsnode(p1.dirpath())
        names = [x.name for x in col.collect()]
        assert names == ["dir1", "dir2", "test_one.py", "test_two.py", "x"]

    def test_collector_deprecated_run_method(self, testdir):
        modcol = testdir.getmodulecol("pass")
        res1 = py.test.deprecated_call(modcol.run)
        res2 = modcol.collect()
        assert res1 == [x.name for x in res2]

class TestCollectPluginHooks:
    def test_pytest_collect_file(self, testdir):
        tmpdir = testdir.tmpdir
        wascalled = []
        class Plugin:
            def pytest_collect_file(self, path, parent):
                wascalled.append(path)
        config = testdir.Config()
        config.pytestplugins.register(Plugin())
        config.parse([tmpdir])
        col = config.getfsnode(tmpdir)
        testdir.makefile(".abc", "xyz")
        res = col.collect()
        assert len(wascalled) == 1
        assert wascalled[0].ext == '.abc'

    def test_pytest_collect_directory(self, testdir):
        tmpdir = testdir.tmpdir
        wascalled = []
        class Plugin:
            def pytest_collect_directory(self, path, parent):
                wascalled.append(path.basename)
                return parent.Directory(path, parent)
        testdir.plugins.append(Plugin())
        testdir.mkdir("hello")
        testdir.mkdir("world")
        sorter = testdir.inline_run()
        assert "hello" in wascalled
        assert "world" in wascalled
        # make sure the directories do not get double-appended 
        colreports = sorter.getreports(names="collectreport")
        names = [rep.colitem.name for rep in colreports]
        assert names.count("hello") == 1

class TestCustomConftests:
    def test_non_python_files(self, testdir):
        testdir.makepyfile(conftest="""
            import py
            class CustomItem(py.test.collect.Item): 
                def run(self):
                    pass
            class Directory(py.test.collect.Directory):
                def consider_file(self, fspath):
                    if fspath.ext == ".xxx":
                        return CustomItem(fspath.basename, parent=self)
        """)
        checkfile = testdir.makefile(ext="xxx", hello="world")
        testdir.makepyfile(x="")
        testdir.maketxtfile(x="")
        config = testdir.parseconfig()
        dircol = config.getfsnode(checkfile.dirpath())
        colitems = dircol.collect()
        assert len(colitems) == 1
        assert colitems[0].name == "hello.xxx"
        assert colitems[0].__class__.__name__ == "CustomItem"

        item = config.getfsnode(checkfile)
        assert item.name == "hello.xxx"
        assert item.__class__.__name__ == "CustomItem"

    def test_avoid_directory_on_option(self, testdir):
        testdir.makeconftest("""
            class ConftestPlugin:
                def pytest_addoption(self, parser):
                    parser.addoption("--XX", action="store_true", default=False)
                def pytest_collect_recurse(self, path, parent):
                    return parent.config.getvalue("XX")
        """)
        testdir.mkdir("hello")
        sorter = testdir.inline_run(testdir.tmpdir)
        names = [rep.colitem.name for rep in sorter.getreports("collectreport")]
        assert 'hello' not in names 
        evrec = testdir.inline_run(testdir.tmpdir, "--XX")
        names = [rep.colitem.name for rep in evrec.getreports("collectreport")]
        assert 'hello' in names 

class TestCollectorReprs:
    def test_repr_metainfo_basic_item(self, testdir):
        modcol = testdir.getmodulecol("")
        Item = py.test.collect.Item
        item = Item("virtual", parent=modcol)
        info = item.repr_metainfo() 
        assert info.fspath == modcol.fspath
        assert not info.lineno
        assert info.modpath == "Item"
        
    def test_repr_metainfo_func(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        info = item.repr_metainfo()
        assert info.fspath == item.fspath 
        assert info.lineno == 0
        assert info.modpath == "test_func"

    def test_repr_metainfo_class(self, testdir):
        modcol = testdir.getmodulecol("""
            # lineno 0
            class TestClass:
                def test_hello(self): pass
        """)
        classcol = modcol.collect_by_name("TestClass")
        info = classcol.repr_metainfo()
        assert info.fspath == modcol.fspath 
        assert info.lineno == 1
        assert info.modpath == "TestClass"

    def test_repr_metainfo_generator(self, testdir):
        modcol = testdir.getmodulecol("""
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
