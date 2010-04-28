import py
from py._test.collect import RootCollector


class TestConfigCmdlineParsing:
    def test_parser_addoption_default_env(self, testdir, monkeypatch):
        import os
        config = testdir.Config()
        group = config._parser.getgroup("hello")

        monkeypatch.setitem(os.environ, 'PYTEST_OPTION_OPTION1', 'True')
        group.addoption("--option1", action="store_true")
        assert group.options[0].default == True

        monkeypatch.setitem(os.environ, 'PYTEST_OPTION_OPTION2', 'abc')
        group.addoption("--option2", action="store", default="x")
        assert group.options[1].default == "abc"

        monkeypatch.setitem(os.environ, 'PYTEST_OPTION_OPTION3', '32')
        group.addoption("--option3", action="store", type="int")
        assert group.options[2].default == 32

        group.addoption("--option4", action="store", type="int")
        assert group.options[3].default == ("NO", "DEFAULT")

    def test_parser_addoption_default_conftest(self, testdir, monkeypatch):
        import os
        testdir.makeconftest("option_verbose=True")
        config = testdir.parseconfig()
        assert config.option.verbose 

    def test_parsing_again_fails(self, testdir):
        config = testdir.reparseconfig([testdir.tmpdir])
        py.test.raises(AssertionError, "config.parse([])")


class TestConfigTmpdir:
    def test_getbasetemp(self, testdir):
        config = testdir.Config()
        config.basetemp = "hello"
        config.getbasetemp() == "hello"

    def test_mktemp(self, testdir):
        config = testdir.Config()
        config.basetemp = testdir.mkdir("hello")
        tmp = config.mktemp("world")
        assert tmp.relto(config.basetemp) == "world"
        tmp = config.mktemp("this", numbered=True)
        assert tmp.relto(config.basetemp).startswith("this")
        tmp2 = config.mktemp("this", numbered=True)
        assert tmp2.relto(config.basetemp).startswith("this")
        assert tmp2 != tmp

    def test_reparse(self, testdir):
        config2 = testdir.reparseconfig([])
        config3 = testdir.reparseconfig([])
        assert config2.getbasetemp() != config3.getbasetemp()
        assert not config2.getbasetemp().relto(config3.getbasetemp())
        assert not config3.getbasetemp().relto(config2.getbasetemp())

class TestConfigAPI: 

    def test_config_getvalue_honours_conftest(self, testdir):
        testdir.makepyfile(conftest="x=1")
        testdir.mkdir("sub").join("conftest.py").write("x=2 ; y = 3")
        config = testdir.parseconfig()
        o = testdir.tmpdir
        assert config.getvalue("x") == 1
        assert config.getvalue("x", o.join('sub')) == 2
        py.test.raises(KeyError, "config.getvalue('y')")
        config = testdir.reparseconfig([str(o.join('sub'))])
        assert config.getvalue("x") == 2
        assert config.getvalue("y") == 3
        assert config.getvalue("x", o) == 1
        py.test.raises(KeyError, 'config.getvalue("y", o)')

    def test_config_getvalueorskip(self, testdir):
        config = testdir.parseconfig()
        py.test.raises(py.test.skip.Exception, 
            "config.getvalueorskip('hello')")
        verbose = config.getvalueorskip("verbose")
        assert verbose == config.option.verbose
        config.option.hello = None
        py.test.raises(py.test.skip.Exception, 
            "config.getvalueorskip('hello')")

    def test_config_overwrite(self, testdir):
        o = testdir.tmpdir
        o.ensure("conftest.py").write("x=1")
        config = testdir.reparseconfig([str(o)])
        assert config.getvalue('x') == 1
        config.option.x = 2
        assert config.getvalue('x') == 2
        config = testdir.reparseconfig([str(o)])
        assert config.getvalue('x') == 1

    def test_getconftest_pathlist(self, testdir, tmpdir):
        somepath = tmpdir.join("x", "y", "z")
        p = tmpdir.join("conftest.py")
        p.write("pathlist = ['.', %r]" % str(somepath))
        config = testdir.reparseconfig([p])
        assert config.getconftest_pathlist('notexist') is None
        pl = config.getconftest_pathlist('pathlist')
        print(pl)
        assert len(pl) == 2
        assert pl[0] == tmpdir
        assert pl[1] == somepath

    def test_setsessionclass_and_initsession(self, testdir):
        config = testdir.Config()
        class Session1: 
            def __init__(self, config):
                self.config = config 
        config.setsessionclass(Session1)
        session = config.initsession()
        assert isinstance(session, Session1)
        assert session.config is config
        py.test.raises(ValueError, "config.setsessionclass(Session1)")


class TestConfigApi_getinitialnodes:
    def test_onedir(self, testdir):
        config = testdir.reparseconfig([testdir.tmpdir])
        colitems = config.getinitialnodes()
        assert len(colitems) == 1
        col = colitems[0]
        assert isinstance(col, py.test.collect.Directory)
        for col in col.listchain():
            assert col.config is config 

    def test_twodirs(self, testdir, tmpdir):
        config = testdir.reparseconfig([tmpdir, tmpdir])
        colitems = config.getinitialnodes()
        assert len(colitems) == 2
        col1, col2 = colitems 
        assert col1.name == col2.name 
        assert col1.parent == col2.parent 

    def test_curdir_and_subdir(self, testdir, tmpdir):
        a = tmpdir.ensure("a", dir=1)
        config = testdir.reparseconfig([tmpdir, a])
        colitems = config.getinitialnodes()
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
        col, = config.getinitialnodes()
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == tmpdir.basename 
        assert isinstance(col.parent.parent, RootCollector)
        for col in col.listchain():
            assert col.config is config 

    def test_global_dir(self, testdir, tmpdir):
        x = tmpdir.ensure("a", dir=1)
        config = testdir.reparseconfig([x])
        col, = config.getinitialnodes()
        assert isinstance(col, py.test.collect.Directory)
        print(col.listchain())
        assert col.name == 'a'
        assert isinstance(col.parent, RootCollector)
        assert col.config is config 

    def test_pkgfile(self, testdir, tmpdir):
        tmpdir = tmpdir.join("subdir")
        x = tmpdir.ensure("x.py")
        tmpdir.ensure("__init__.py")
        config = testdir.reparseconfig([x])
        col, = config.getinitialnodes()
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == x.dirpath().basename 
        assert isinstance(col.parent.parent.parent, RootCollector)
        for col in col.listchain():
            assert col.config is config 

class TestConfig_gettopdir:
    def test_gettopdir(self, testdir):
        from py._test.config import gettopdir
        tmp = testdir.tmpdir
        assert gettopdir([tmp]) == tmp
        topdir = gettopdir([tmp.join("hello"), tmp.join("world")])
        assert topdir == tmp 
        somefile = tmp.ensure("somefile.py")
        assert gettopdir([somefile]) == tmp

    def test_gettopdir_pypkg(self, testdir):
        from py._test.config import gettopdir
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

def test_options_on_small_file_do_not_blow_up(testdir):
    def runfiletest(opts):
        reprec = testdir.inline_run(*opts)
        passed, skipped, failed = reprec.countoutcomes()
        assert failed == 2 
        assert skipped == passed == 0
    path = testdir.makepyfile("""
        def test_f1(): assert 0
        def test_f2(): assert 0
    """)

    for opts in ([], ['-l'], ['-s'], ['--tb=no'], ['--tb=short'], 
                 ['--tb=long'], ['--fulltrace'], ['--nomagic'], 
                 ['--traceconfig'], ['-v'], ['-v', '-v']):
        runfiletest(opts + [path])

def test_ensuretemp(recwarn):
    #py.test.deprecated_call(py.test.ensuretemp, 'hello')
    d1 = py.test.ensuretemp('hello') 
    d2 = py.test.ensuretemp('hello') 
    assert d1 == d2
    assert d1.check(dir=1) 

def test_preparse_ordering(testdir, monkeypatch):
    pkg_resources = py.test.importorskip("pkg_resources")
    def my_iter(name):
        assert name == "pytest11"
        class EntryPoint:
            name = "mytestplugin"
            def load(self):
                class PseudoPlugin:
                    x = 42
                return PseudoPlugin()
        return iter([EntryPoint()])
    monkeypatch.setattr(pkg_resources, 'iter_entry_points', my_iter)
    testdir.makeconftest("""
        pytest_plugins = "mytestplugin",
    """)
    monkeypatch.setenv("PYTEST_PLUGINS", "mytestplugin")
    config = testdir.parseconfig()
    plugin = config.pluginmanager.getplugin("mytestplugin")
    assert plugin.x == 42


import pickle
class TestConfigPickling:
    def pytest_funcarg__testdir(self, request):
        oldconfig = py.test.config 
        print("setting py.test.config to None")
        py.test.config = None
        def resetglobals():
            py.builtin.print_("setting py.test.config to", oldconfig)
            py.test.config = oldconfig
        request.addfinalizer(resetglobals)
        return request.getfuncargvalue("testdir")

    def test_config_getstate_setstate(self, testdir):
        from py._test.config import Config
        testdir.makepyfile(__init__="", conftest="x=1; y=2")
        hello = testdir.makepyfile(hello="")
        tmp = testdir.tmpdir
        testdir.chdir()
        config1 = testdir.parseconfig(hello)
        config2 = Config()
        config2.__setstate__(config1.__getstate__())
        assert config2.topdir == py.path.local()
        config2_relpaths = [py.path.local(x).relto(config2.topdir) 
                                for x in config2.args]
        config1_relpaths = [py.path.local(x).relto(config1.topdir) 
                                for x in config1.args]

        assert config2_relpaths == config1_relpaths
        for name, value in config1.option.__dict__.items():
            assert getattr(config2.option, name) == value
        assert config2.getvalue("x") == 1

    def test_config_pickling_customoption(self, testdir):
        testdir.makeconftest("""
            def pytest_addoption(parser):
                group = parser.getgroup("testing group")
                group.addoption('-G', '--glong', action="store", default=42, 
                    type="int", dest="gdest", help="g value.")
        """)
        config = testdir.parseconfig("-G", "11")
        assert config.option.gdest == 11
        repr = config.__getstate__()

        config = testdir.Config()
        py.test.raises(AttributeError, "config.option.gdest")

        config2 = testdir.Config()
        config2.__setstate__(repr) 
        assert config2.option.gdest == 11

    def test_config_pickling_and_conftest_deprecated(self, testdir):
        tmp = testdir.tmpdir.ensure("w1", "w2", dir=1)
        tmp.ensure("__init__.py")
        tmp.join("conftest.py").write(py.code.Source("""
            def pytest_addoption(parser):
                group = parser.getgroup("testing group")
                group.addoption('-G', '--glong', action="store", default=42, 
                    type="int", dest="gdest", help="g value.")
        """))
        config = testdir.parseconfig(tmp, "-G", "11")
        assert config.option.gdest == 11
        repr = config.__getstate__()

        config = testdir.Config()
        py.test.raises(AttributeError, "config.option.gdest")

        config2 = testdir.Config()
        config2.__setstate__(repr) 
        assert config2.option.gdest == 11
       
        option = config2.addoptions("testing group", 
                config2.Option('-G', '--glong', action="store", default=42,
                       type="int", dest="gdest", help="g value."))
        assert option.gdest == 11

    def test_config_picklability(self, testdir):
        config = testdir.parseconfig()
        s = pickle.dumps(config)
        newconfig = pickle.loads(s)
        assert hasattr(newconfig, "topdir")
        assert newconfig.topdir == py.path.local()

    def test_collector_implicit_config_pickling(self, testdir):
        tmpdir = testdir.tmpdir
        testdir.chdir()
        testdir.makepyfile(hello="def test_x(): pass")
        config = testdir.parseconfig(tmpdir)
        col = config.getnode(config.topdir)
        io = py.io.BytesIO()
        pickler = pickle.Pickler(io)
        pickler.dump(col)
        io.seek(0) 
        unpickler = pickle.Unpickler(io)
        col2 = unpickler.load()
        assert col2.name == col.name 
        assert col2.listnames() == col.listnames()

    def test_config_and_collector_pickling(self, testdir):
        tmpdir = testdir.tmpdir
        dir1 = tmpdir.ensure("sourcedir", "somedir", dir=1)
        config = testdir.parseconfig()
        assert config.topdir == tmpdir
        col = config.getnode(dir1.dirpath())
        col1 = config.getnode(dir1)
        assert col1.parent == col 
        io = py.io.BytesIO()
        pickler = pickle.Pickler(io)
        pickler.dump(col)
        pickler.dump(col1)
        pickler.dump(col)
        io.seek(0) 
        unpickler = pickle.Unpickler(io)
        newtopdir = tmpdir.ensure("newtopdir", dir=1)
        newtopdir.mkdir("sourcedir").mkdir("somedir")
        old = newtopdir.chdir()
        try:
            newcol = unpickler.load()
            newcol2 = unpickler.load()
            newcol3 = unpickler.load()
            assert newcol2.config is newcol.config
            assert newcol2.parent == newcol 
            assert newcol2.config.topdir.realpath() == newtopdir.realpath()
            newsourcedir = newtopdir.join("sourcedir")
            assert newcol.fspath.realpath() == newsourcedir.realpath()
            assert newcol2.fspath.basename == dir1.basename
            assert newcol2.fspath.relto(newcol2.config.topdir)
        finally:
            old.chdir() 
