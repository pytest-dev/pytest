import py

from py._test.session import Collection, gettopdir

class TestCollection:
    def test_parsearg(self, testdir):
        p = testdir.makepyfile("def test_func(): pass")
        subdir = testdir.mkdir("sub")
        subdir.ensure("__init__.py")
        target = subdir.join(p.basename)
        p.move(target)
        testdir.chdir()
        subdir.chdir()
        config = testdir.parseconfig(p.basename)
        rcol = Collection(config=config)
        assert rcol.topdir == testdir.tmpdir
        parts = rcol._parsearg(p.basename)
        assert parts[0] ==  "sub"
        assert parts[1] ==  p.basename
        assert len(parts) == 2
        parts = rcol._parsearg(p.basename + "::test_func")
        assert parts[0] ==  "sub"
        assert parts[1] ==  p.basename
        assert parts[2] ==  "test_func"
        assert len(parts) == 3

    def test_collect_topdir(self, testdir):
        p = testdir.makepyfile("def test_func(): pass")
        id = "::".join([p.basename, "test_func"])
        config = testdir.parseconfig(id)
        topdir = testdir.tmpdir
        rcol = Collection(config)
        assert topdir == rcol.topdir
        hookrec = testdir.getreportrecorder(config)
        items = rcol.perform_collect()
        assert len(items) == 1
        root = items[0].listchain()[0]
        root_id = rcol.getid(root)
        root2 = rcol.getbyid(root_id)[0]
        assert root2.fspath == root.fspath

    def test_collect_protocol_single_function(self, testdir):
        p = testdir.makepyfile("def test_func(): pass")
        id = "::".join([p.basename, "test_func"])
        config = testdir.parseconfig(id)
        topdir = testdir.tmpdir
        rcol = Collection(config)
        assert topdir == rcol.topdir
        hookrec = testdir.getreportrecorder(config)
        items = rcol.perform_collect()
        assert len(items) == 1
        item = items[0]
        assert item.name == "test_func"
        newid = rcol.getid(item)
        assert newid == id
        py.std.pprint.pprint(hookrec.hookrecorder.calls)
        hookrec.hookrecorder.contains([
            ("pytest_collectstart", "collector.fspath == topdir"),
            ("pytest_make_collect_report", "collector.fspath == topdir"),
            ("pytest_collectstart", "collector.fspath == p"),
            ("pytest_make_collect_report", "collector.fspath == p"),
            ("pytest_pycollect_makeitem", "name == 'test_func'"),
            ("pytest_collectreport", "report.collector.fspath == p"),
            ("pytest_collectreport", "report.collector.fspath == topdir")
        ])

    def test_collect_protocol_method(self, testdir):
        p = testdir.makepyfile("""
            class TestClass:
                def test_method(self):
                    pass
        """)
        normid = p.basename + "::TestClass::test_method"
        for id in [p.basename,
                   p.basename + "::TestClass",
                   p.basename + "::TestClass::()",
                   p.basename + "::TestClass::()::test_method",
                   normid,
                   ]:
            config = testdir.parseconfig(id)
            rcol = Collection(config=config)
            nodes = rcol.perform_collect()
            assert len(nodes) == 1
            assert nodes[0].name == "test_method"
            newid = rcol.getid(nodes[0])
            assert newid == normid

    def test_collect_custom_nodes_multi_id(self, testdir):
        p = testdir.makepyfile("def test_func(): pass")
        testdir.makeconftest("""
            import py
            class SpecialItem(py.test.collect.Item):
                def runtest(self):
                    return # ok
            class SpecialFile(py.test.collect.File):
                def collect(self):
                    return [SpecialItem(name="check", parent=self)]
            def pytest_collect_file(path, parent):
                if path.basename == %r:
                    return SpecialFile(fspath=path, parent=parent)
        """ % p.basename)
        id = p.basename

        config = testdir.parseconfig(id)
        rcol = Collection(config)
        hookrec = testdir.getreportrecorder(config)
        items = rcol.perform_collect()
        py.std.pprint.pprint(hookrec.hookrecorder.calls)
        assert len(items) == 2
        hookrec.hookrecorder.contains([
            ("pytest_collectstart",
                "collector.fspath == collector.collection.topdir"),
            ("pytest_collectstart",
                "collector.__class__.__name__ == 'SpecialFile'"),
            ("pytest_collectstart",
                "collector.__class__.__name__ == 'Module'"),
            ("pytest_pycollect_makeitem", "name == 'test_func'"),
            ("pytest_collectreport", "report.collector.fspath == p"),
            ("pytest_collectreport",
                "report.collector.fspath == report.collector.collection.topdir")
        ])

    def test_collect_subdir_event_ordering(self, testdir):
        p = testdir.makepyfile("def test_func(): pass")
        aaa = testdir.mkpydir("aaa")
        test_aaa = aaa.join("test_aaa.py")
        p.move(test_aaa)
        config = testdir.parseconfig()
        rcol = Collection(config)
        hookrec = testdir.getreportrecorder(config)
        items = rcol.perform_collect()
        assert len(items) == 1
        py.std.pprint.pprint(hookrec.hookrecorder.calls)
        hookrec.hookrecorder.contains([
            ("pytest_collectstart", "collector.fspath == aaa"),
            ("pytest_collectstart", "collector.fspath == test_aaa"),
            ("pytest_pycollect_makeitem", "name == 'test_func'"),
            ("pytest_collectreport", "report.collector.fspath == test_aaa"),
            ("pytest_collectreport", "report.collector.fspath == aaa"),
        ])

    def test_collect_two_commandline_args(self, testdir):
        p = testdir.makepyfile("def test_func(): pass")
        aaa = testdir.mkpydir("aaa")
        bbb = testdir.mkpydir("bbb")
        p.copy(aaa.join("test_aaa.py"))
        p.move(bbb.join("test_bbb.py"))

        id = "."
        config = testdir.parseconfig(id)
        rcol = Collection(config)
        hookrec = testdir.getreportrecorder(config)
        items = rcol.perform_collect()
        assert len(items) == 2
        py.std.pprint.pprint(hookrec.hookrecorder.calls)
        hookrec.hookrecorder.contains([
            ("pytest_collectstart", "collector.fspath == aaa"),
            ("pytest_pycollect_makeitem", "name == 'test_func'"),
            ("pytest_collectreport", "report.collector.fspath == aaa"),
            ("pytest_collectstart", "collector.fspath == bbb"),
            ("pytest_pycollect_makeitem", "name == 'test_func'"),
            ("pytest_collectreport", "report.collector.fspath == bbb"),
        ])

    def test_serialization_byid(self, testdir):
        p = testdir.makepyfile("def test_func(): pass")
        config = testdir.parseconfig()
        rcol = Collection(config)
        items = rcol.perform_collect()
        assert len(items) == 1
        item, = items
        id = rcol.getid(item)
        newcol = Collection(config)
        item2, = newcol.getbyid(id)
        assert item2.name == item.name
        assert item2.fspath == item.fspath
        item2b, = newcol.getbyid(id)
        assert item2b is item2

class Test_gettopdir:
    def test_gettopdir(self, testdir):
        tmp = testdir.tmpdir
        assert gettopdir([tmp]) == tmp
        topdir = gettopdir([tmp.join("hello"), tmp.join("world")])
        assert topdir == tmp
        somefile = tmp.ensure("somefile.py")
        assert gettopdir([somefile]) == tmp

    def test_gettopdir_pypkg(self, testdir):
        tmp = testdir.tmpdir
        a = tmp.ensure('a', dir=1)
        b = tmp.ensure('a', 'b', '__init__.py')
        c = tmp.ensure('a', 'b', 'c.py')
        Z = tmp.ensure('Z', dir=1)
        assert gettopdir([c]) == a
        assert gettopdir([c, Z]) == tmp
        assert gettopdir(["%s::xyc" % c]) == a
        assert gettopdir(["%s::xyc::abc" % c]) == a
        assert gettopdir(["%s::xyc" % c, "%s::abc" % Z]) == tmp

class Test_getinitialnodes:
    def test_onedir(self, testdir):
        config = testdir.reparseconfig([testdir.tmpdir])
        colitems = Collection(config).getinitialnodes()
        assert len(colitems) == 1
        col = colitems[0]
        assert isinstance(col, py.test.collect.Directory)
        for col in col.listchain():
            assert col.config is config

    def test_twodirs(self, testdir, tmpdir):
        config = testdir.reparseconfig([tmpdir, tmpdir])
        colitems = Collection(config).getinitialnodes()
        assert len(colitems) == 2
        col1, col2 = colitems
        assert col1.name == col2.name
        assert col1.parent == col2.parent

    def test_curdir_and_subdir(self, testdir, tmpdir):
        a = tmpdir.ensure("a", dir=1)
        config = testdir.reparseconfig([tmpdir, a])
        colitems = Collection(config).getinitialnodes()
        assert len(colitems) == 2
        col1, col2 = colitems
        assert col1.name == tmpdir.basename
        assert col2.name == 'a'
        for col in colitems:
            for subcol in col.listchain():
                assert col.config is config

    def test_global_file(self, testdir, tmpdir):
        x = tmpdir.ensure("x.py")
        config = testdir.reparseconfig([x])
        col, = Collection(config).getinitialnodes()
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == tmpdir.basename
        assert col.parent.parent is None
        for col in col.listchain():
            assert col.config is config

    def test_global_dir(self, testdir, tmpdir):
        x = tmpdir.ensure("a", dir=1)
        config = testdir.reparseconfig([x])
        col, = Collection(config).getinitialnodes()
        assert isinstance(col, py.test.collect.Directory)
        print(col.listchain())
        assert col.name == 'a'
        assert col.parent is None
        assert col.config is config

    def test_pkgfile(self, testdir, tmpdir):
        tmpdir = tmpdir.join("subdir")
        x = tmpdir.ensure("x.py")
        tmpdir.ensure("__init__.py")
        config = testdir.reparseconfig([x])
        col, = Collection(config).getinitialnodes()
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == x.dirpath().basename
        assert col.parent.parent.parent is None
        for col in col.listchain():
            assert col.config is config

class Test_genitems:
    def test_check_collect_hashes(self, testdir):
        p = testdir.makepyfile("""
            def test_1():
                pass

            def test_2():
                pass
        """)
        p.copy(p.dirpath(p.purebasename + "2" + ".py"))
        items, reprec = testdir.inline_genitems(p.dirpath())
        assert len(items) == 4
        for numi, i in enumerate(items):
            for numj, j in enumerate(items):
                if numj != numi:
                    assert hash(i) != hash(j)
                    assert i != j

    def test_root_conftest_syntax_error(self, testdir):
        # do we want to unify behaviour with
        # test_subdir_conftest_error?
        p = testdir.makepyfile(conftest="raise SyntaxError\n")
        py.test.raises(SyntaxError, testdir.inline_genitems, p.dirpath())

    def test_example_items1(self, testdir):
        p = testdir.makepyfile('''
            def testone():
                pass

            class TestX:
                def testmethod_one(self):
                    pass

            class TestY(TestX):
                pass
        ''')
        items, reprec = testdir.inline_genitems(p)
        assert len(items) == 3
        assert items[0].name == 'testone'
        assert items[1].name == 'testmethod_one'
        assert items[2].name == 'testmethod_one'

        # let's also test getmodpath here
        assert items[0].getmodpath() == "testone"
        assert items[1].getmodpath() == "TestX.testmethod_one"
        assert items[2].getmodpath() == "TestY.testmethod_one"

        s = items[0].getmodpath(stopatmodule=False)
        assert s.endswith("test_example_items1.testone")
        print(s)
