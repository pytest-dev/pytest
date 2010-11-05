import py

from pytest.plugin.config import getcfg, Config

class TestParseIni:
    def test_getcfg_and_config(self, tmpdir):
        sub = tmpdir.mkdir("sub")
        sub.chdir()
        tmpdir.join("setup.cfg").write(py.code.Source("""
            [pytest]
            name = value
        """))
        cfg = getcfg([sub], ["setup.cfg"])
        assert cfg['name'] == "value"
        config = Config()
        config._preparse([sub])
        assert config.inicfg['name'] == 'value'

    def test_append_parse_args(self, tmpdir):
        tmpdir.join("setup.cfg").write(py.code.Source("""
            [pytest]
            addopts = --verbose
        """))
        config = Config()
        config.parse([tmpdir])
        assert config.option.verbose
        config = Config()
        args = [tmpdir,]
        config._preparse(args, addopts=False)
        assert len(args) == 1

    def test_tox_ini_wrong_version(self, testdir):
        p = testdir.makefile('.ini', tox="""
            [pytest]
            minversion=9.0
        """)
        result = testdir.runpytest()
        assert result.ret != 0
        result.stderr.fnmatch_lines([
            "*tox.ini:2*requires*9.0*actual*"
        ])

class TestConfigCmdlineParsing:
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

    def test_reparse_filename_too_long(self, testdir):
        config = testdir.reparseconfig(["--basetemp=%s" % ("123"*300)])

class TestConfigAPI:

    def test_config_trace(self, testdir):
        config = testdir.Config()
        l = []
        config.trace.root.setwriter(l.append)
        config.trace("hello")
        assert len(l) == 1
        assert l[0] == "[pytest:config] hello\n"

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
        assert config._getconftest_pathlist('notexist') is None
        pl = config._getconftest_pathlist('pathlist')
        print(pl)
        assert len(pl) == 2
        assert pl[0] == tmpdir
        assert pl[1] == somepath

    def test_addini(self, testdir):
        testdir.makeconftest("""
            def pytest_addoption(parser):
                parser.addini("myname", "my new ini value")
        """)
        testdir.makeini("""
            [pytest]
            myname=hello
        """)
        config = testdir.parseconfig()
        val = config.getini("myname")
        assert val == "hello"
        py.test.raises(ValueError, config.getini, 'other')

    def test_addini_pathlist(self, testdir):
        testdir.makeconftest("""
            def pytest_addoption(parser):
                parser.addini("paths", "my new ini value", type="pathlist")
                parser.addini("abc", "abc value")
        """)
        p = testdir.makeini("""
            [pytest]
            paths=hello world/sub.py
        """)
        config = testdir.parseconfig()
        l = config.getini("paths")
        assert len(l) == 2
        assert l[0] == p.dirpath('hello')
        assert l[1] == p.dirpath('world/sub.py')
        py.test.raises(ValueError, config.getini, 'other')

    def test_addini_args(self, testdir):
        testdir.makeconftest("""
            def pytest_addoption(parser):
                parser.addini("args", "new args", type="args")
                parser.addini("a2", "", "args", default="1 2 3".split())
        """)
        p = testdir.makeini("""
            [pytest]
            args=123 "123 hello" "this"
        """)
        config = testdir.parseconfig()
        l = config.getini("args")
        assert len(l) == 3
        assert l == ["123", "123 hello", "this"]
        l = config.getini("a2")
        assert l == list("123")

    def test_addini_linelist(self, testdir):
        testdir.makeconftest("""
            def pytest_addoption(parser):
                parser.addini("xy", "", type="linelist")
                parser.addini("a2", "", "linelist")
        """)
        p = testdir.makeini("""
            [pytest]
            xy= 123 345
                second line
        """)
        config = testdir.parseconfig()
        l = config.getini("xy")
        assert len(l) == 2
        assert l == ["123 345", "second line"]
        l = config.getini("a2")
        assert l == []

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

