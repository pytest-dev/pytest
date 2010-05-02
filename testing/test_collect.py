import py

class TestCollector:
    def test_collect_versus_item(self):
        from py._test.collect import Collector, Item
        assert not issubclass(Collector, Item)
        assert not issubclass(Item, Collector)

    def test_check_equality(self, testdir):
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
        if py.std.sys.version_info < (3, 0):
            assert cmp(fn1, fn2) == 0
        assert hash(fn1) == hash(fn2) 

        fn3 = modcol.collect_by_name("test_fail")
        assert isinstance(fn3, py.test.collect.Function)
        assert not (fn1 == fn3) 
        assert fn1 != fn3

        for fn in fn1,fn2,fn3:
            assert fn != 3
            assert fn != modcol
            assert fn != [1,2,3]
            assert [1,2,3] != fn
            assert modcol != fn

    def test_getparent(self, testdir):
        modcol = testdir.getmodulecol("""
            class TestClass:
                 def test_foo():
                     pass
        """)
        cls = modcol.collect_by_name("TestClass")
        fn = cls.collect_by_name("()").collect_by_name("test_foo")
        
        parent = fn.getparent(py.test.collect.Module)
        assert parent is modcol

        parent = fn.getparent(py.test.collect.Function)
        assert parent is fn

        parent = fn.getparent(py.test.collect.Class)
        assert parent is cls     


    def test_getcustomfile_roundtrip(self, testdir):
        hello = testdir.makefile(".xxx", hello="world")
        testdir.makepyfile(conftest="""
            import py
            class CustomFile(py.test.collect.File):
                pass
            class MyDirectory(py.test.collect.Directory):
                def collect(self):
                    return [CustomFile(self.fspath.join("hello.xxx"), parent=self)]
            def pytest_collect_directory(path, parent):
                return MyDirectory(path, parent=parent)
        """)
        config = testdir.parseconfig(hello)
        node = config.getnode(hello)
        assert isinstance(node, py.test.collect.File)
        assert node.name == "hello.xxx"
        names = config._rootcol.totrail(node)
        node = config._rootcol.getbynames(names)
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

        col = testdir.parseconfig(tmpdir).getnode(tmpdir)
        items = col.collect()
        names = [x.name for x in items]
        assert len(items) == 2
        assert 'normal' in names
        assert 'test_found.py' in names

    def test_found_certain_testfiles(self, testdir): 
        p1 = testdir.makepyfile(test_found = "pass", found_test="pass")
        col = testdir.parseconfig(p1).getnode(p1.dirpath())
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
        col = config.getnode(p1.dirpath())
        names = [x.name for x in col.collect()]
        assert names == ["dir1", "dir2", "test_one.py", "test_two.py", "x"]

class TestCollectPluginHookRelay:
    def test_pytest_collect_file(self, testdir):
        tmpdir = testdir.tmpdir
        wascalled = []
        class Plugin:
            def pytest_collect_file(self, path, parent):
                wascalled.append(path)
        config = testdir.Config()
        config.pluginmanager.register(Plugin())
        config.parse([tmpdir])
        col = config.getnode(tmpdir)
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
        reprec = testdir.inline_run()
        assert "hello" in wascalled
        assert "world" in wascalled
        # make sure the directories do not get double-appended 
        colreports = reprec.getreports("pytest_collectreport")
        names = [rep.collector.name for rep in colreports]
        assert names.count("hello") == 1

class TestPrunetraceback:
    def test_collection_error(self, testdir):
        p = testdir.makepyfile("""
            import not_exists
        """)
        result = testdir.runpytest(p)
        assert "__import__" not in result.stdout.str(), "too long traceback"
        result.stdout.fnmatch_lines([
            "*ERROR during collection*",
            "*mport*not_exists*"
        ])

class TestCustomConftests:
    def test_ignore_collect_path(self, testdir):
        testdir.makeconftest("""
            def pytest_ignore_collect(path, config):
                return path.basename.startswith("x") or \
                       path.basename == "test_one.py"
        """)
        testdir.mkdir("xy123").ensure("test_hello.py").write(
            "syntax error"
        )
        testdir.makepyfile("def test_hello(): pass")
        testdir.makepyfile(test_one="syntax error")
        result = testdir.runpytest()
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*1 passed*"])

    def test_collectignore_exclude_on_option(self, testdir):
        testdir.makeconftest("""
            collect_ignore = ['hello', 'test_world.py']
            def pytest_addoption(parser):
                parser.addoption("--XX", action="store_true", default=False)
            def pytest_configure(config):
                if config.getvalue("XX"):
                    collect_ignore[:] = []
        """)
        testdir.mkdir("hello")
        testdir.makepyfile(test_world="#")
        reprec = testdir.inline_run(testdir.tmpdir)
        names = [rep.collector.name for rep in reprec.getreports("pytest_collectreport")]
        assert 'hello' not in names 
        assert 'test_world.py' not in names 
        reprec = testdir.inline_run(testdir.tmpdir, "--XX")
        names = [rep.collector.name for rep in reprec.getreports("pytest_collectreport")]
        assert 'hello' in names 
        assert 'test_world.py' in names 

    def test_pytest_fs_collect_hooks_are_seen(self, testdir):
        testdir.makeconftest("""
            import py
            class MyDirectory(py.test.collect.Directory):
                pass
            class MyModule(py.test.collect.Module):
                pass
            def pytest_collect_directory(path, parent):
                return MyDirectory(path, parent)
            def pytest_collect_file(path, parent):
                return MyModule(path, parent)
        """)
        testdir.makepyfile("def test_x(): pass")
        result = testdir.runpytest("--collectonly")
        result.stdout.fnmatch_lines([
            "*MyDirectory*",
            "*MyModule*",
            "*test_x*"
        ])

class TestRootCol:
    def test_totrail_and_back(self, testdir, tmpdir):
        a = tmpdir.ensure("a", dir=1)
        tmpdir.ensure("a", "__init__.py")
        x = tmpdir.ensure("a", "trail.py")
        config = testdir.reparseconfig([x])
        col = config.getnode(x)
        trail = config._rootcol.totrail(col)
        col2 = config._rootcol.fromtrail(trail)
        assert col2 == col 
       
    def test_totrail_topdir_and_beyond(self, testdir, tmpdir):
        config = testdir.reparseconfig()
        col = config.getnode(config.topdir)
        trail = config._rootcol.totrail(col)
        col2 = config._rootcol.fromtrail(trail)
        assert col2.fspath == config.topdir
        assert len(col2.listchain()) == 1
        py.test.raises(config.Error, "config.getnode(config.topdir.dirpath())")
        #col3 = config.getnode(config.topdir.dirpath())
        #py.test.raises(ValueError, 
        #      "col3._totrail()")
        
    def test_argid(self, testdir, tmpdir):
        cfg = testdir.parseconfig()
        p = testdir.makepyfile("def test_func(): pass")
        item = cfg.getnode("%s::test_func" % p)
        assert item.name == "test_func"

    def test_argid_with_method(self, testdir, tmpdir):
        cfg = testdir.parseconfig()
        p = testdir.makepyfile("""
            class TestClass:
                def test_method(self): pass
        """)
        item = cfg.getnode("%s::TestClass::()::test_method" % p)
        assert item.name == "test_method"
        item = cfg.getnode("%s::TestClass::test_method" % p)
        assert item.name == "test_method"
