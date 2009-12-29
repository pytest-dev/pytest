import py


class TestConfigCmdlineParsing:
    def test_config_cmdline_options(self, testdir):
        testdir.makepyfile(conftest="""
            import py
            def _callback(option, opt_str, value, parser, *args, **kwargs):
                option.tdest = True
            Option = py.test.config.Option
            option = py.test.config.addoptions("testing group", 
                Option('-G', '--glong', action="store", default=42,
                       type="int", dest="gdest", help="g value."), 
                # XXX note: special case, option without a destination
                Option('-T', '--tlong', action="callback", callback=_callback,
                        help='t value'),
                )
            """)
        config = testdir.reparseconfig(['-G', '17'])
        assert config.option.gdest == 17 

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
        from py.impl.test.outcome import Skipped
        config = testdir.parseconfig()
        py.test.raises(Skipped, "config.getvalueorskip('hello')")
        verbose = config.getvalueorskip("verbose")
        assert verbose == config.option.verbose
        config.option.hello = None
        py.test.raises(Skipped, "config.getvalueorskip('hello')")

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


class TestConfigApi_getcolitems:
    def test_getcolitems_onedir(self, testdir):
        config = testdir.reparseconfig([testdir.tmpdir])
        colitems = config.getcolitems()
        assert len(colitems) == 1
        col = colitems[0]
        assert isinstance(col, py.test.collect.Directory)
        for col in col.listchain():
            assert col.config is config 

    def test_getcolitems_twodirs(self, testdir, tmpdir):
        config = testdir.reparseconfig([tmpdir, tmpdir])
        colitems = config.getcolitems()
        assert len(colitems) == 2
        col1, col2 = colitems 
        assert col1.name == col2.name 
        assert col1.parent == col2.parent 

    def test_getcolitems_curdir_and_subdir(self, testdir, tmpdir):
        a = tmpdir.ensure("a", dir=1)
        config = testdir.reparseconfig([tmpdir, a])
        colitems = config.getcolitems()
        assert len(colitems) == 2
        col1, col2 = colitems 
        assert col1.name == tmpdir.basename
        assert col2.name == 'a'
        for col in colitems:
            for subcol in col.listchain():
                assert col.config is config 

    def test__getcol_global_file(self, testdir, tmpdir):
        x = tmpdir.ensure("x.py")
        config = testdir.reparseconfig([x])
        col = config.getfsnode(x)
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == tmpdir.basename 
        assert col.parent.parent is None
        for col in col.listchain():
            assert col.config is config 

    def test__getcol_global_dir(self, testdir, tmpdir):
        x = tmpdir.ensure("a", dir=1)
        config = testdir.reparseconfig([x])
        col = config.getfsnode(x)
        assert isinstance(col, py.test.collect.Directory)
        print(col.listchain())
        assert col.name == 'a'
        assert col.parent is None
        assert col.config is config 

    def test__getcol_pkgfile(self, testdir, tmpdir):
        x = tmpdir.ensure("x.py")
        tmpdir.ensure("__init__.py")
        config = testdir.reparseconfig([x])
        col = config.getfsnode(x)
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == x.dirpath().basename 
        assert col.parent.parent is None
        for col in col.listchain():
            assert col.config is config 

class TestOptionEffects:
    def test_boxed_option_default(self, testdir):
        tmpdir = testdir.tmpdir.ensure("subdir", dir=1)
        config = testdir.reparseconfig()
        config.initsession()
        assert not config.option.boxed
        py.test.importorskip("execnet")
        config = testdir.reparseconfig(['-d', tmpdir])
        config.initsession()
        assert not config.option.boxed

    def test_is_not_boxed_by_default(self, testdir):
        config = testdir.reparseconfig([testdir.tmpdir])
        assert not config.option.boxed

class TestConfig_gettopdir:
    def test_gettopdir(self, testdir):
        from py.impl.test.config import gettopdir
        tmp = testdir.tmpdir
        assert gettopdir([tmp]) == tmp
        topdir = gettopdir([tmp.join("hello"), tmp.join("world")])
        assert topdir == tmp 
        somefile = tmp.ensure("somefile.py")
        assert gettopdir([somefile]) == tmp

    def test_gettopdir_pypkg(self, testdir):
        from py.impl.test.config import gettopdir
        tmp = testdir.tmpdir
        a = tmp.ensure('a', dir=1)
        b = tmp.ensure('a', 'b', '__init__.py')
        c = tmp.ensure('a', 'b', 'c.py')
        Z = tmp.ensure('Z', dir=1)
        assert gettopdir([c]) == a
        assert gettopdir([c, Z]) == tmp 


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

def test_ensuretemp():
    # XXX test for deprecation
    d1 = py.test.ensuretemp('hello') 
    d2 = py.test.ensuretemp('hello') 
    assert d1 == d2
    assert d1.check(dir=1) 
