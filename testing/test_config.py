import py, pytest

from _pytest.config import getcfg

class TestParseIni:
    def test_getcfg_and_config(self, testdir, tmpdir):
        sub = tmpdir.mkdir("sub")
        sub.chdir()
        tmpdir.join("setup.cfg").write(py.code.Source("""
            [pytest]
            name = value
        """))
        cfg = getcfg([sub], ["setup.cfg"])
        assert cfg['name'] == "value"
        config = testdir.parseconfigure(sub)
        assert config.inicfg['name'] == 'value'

    def test_getcfg_empty_path(self, tmpdir):
        cfg = getcfg([''], ['setup.cfg']) #happens on py.test  ""

    def test_append_parse_args(self, testdir, tmpdir):
        tmpdir.join("setup.cfg").write(py.code.Source("""
            [pytest]
            addopts = --verbose
        """))
        config = testdir.parseconfig(tmpdir)
        assert config.option.verbose
        #config = testdir.Config()
        #args = [tmpdir,]
        #config._preparse(args, addopts=False)
        #assert len(args) == 1

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

    @pytest.mark.multi(name="setup.cfg tox.ini pytest.ini".split())
    def test_ini_names(self, testdir, name):
        testdir.tmpdir.join(name).write(py.std.textwrap.dedent("""
            [pytest]
            minversion = 1.0
        """))
        config = testdir.parseconfig()
        assert config.getini("minversion") == "1.0"

    def test_toxini_before_lower_pytestini(self, testdir):
        sub = testdir.tmpdir.mkdir("sub")
        sub.join("tox.ini").write(py.std.textwrap.dedent("""
            [pytest]
            minversion = 2.0
        """))
        testdir.tmpdir.join("pytest.ini").write(py.std.textwrap.dedent("""
            [pytest]
            minversion = 1.5
        """))
        config = testdir.parseconfigure(sub)
        assert config.getini("minversion") == "2.0"

    @pytest.mark.xfail(reason="probably not needed")
    def test_confcutdir(self, testdir):
        sub = testdir.mkdir("sub")
        sub.chdir()
        testdir.makeini("""
            [pytest]
            addopts = --qwe
        """)
        result = testdir.runpytest("--confcutdir=.")
        assert result.ret == 0

class TestConfigCmdlineParsing:
    def test_parsing_again_fails(self, testdir):
        config = testdir.parseconfig()
        pytest.raises(AssertionError, "config.parse([])")


class TestConfigAPI:
    def test_config_trace(self, testdir):
        config = testdir.Config()
        l = []
        config.trace.root.setwriter(l.append)
        config.trace("hello")
        assert len(l) == 1
        assert l[0] == "hello [config]\n"

    def test_config_getvalue_honours_conftest(self, testdir):
        testdir.makepyfile(conftest="x=1")
        testdir.mkdir("sub").join("conftest.py").write("x=2 ; y = 3")
        config = testdir.parseconfig()
        o = testdir.tmpdir
        assert config.getvalue("x") == 1
        assert config.getvalue("x", o.join('sub')) == 2
        pytest.raises(KeyError, "config.getvalue('y')")
        config = testdir.parseconfigure(str(o.join('sub')))
        assert config.getvalue("x") == 2
        assert config.getvalue("y") == 3
        assert config.getvalue("x", o) == 1
        pytest.raises(KeyError, 'config.getvalue("y", o)')

    def test_config_getvalueorskip(self, testdir):
        config = testdir.parseconfig()
        pytest.raises(pytest.skip.Exception,
            "config.getvalueorskip('hello')")
        verbose = config.getvalueorskip("verbose")
        assert verbose == config.option.verbose
        config.option.hello = None
        try:
            config.getvalueorskip('hello')
        except KeyboardInterrupt:
            raise
        except:
            excinfo = py.code.ExceptionInfo()
        frame = excinfo.traceback[-2].frame
        assert frame.code.name == "getvalueorskip"
        assert frame.eval("__tracebackhide__")

    def test_config_overwrite(self, testdir):
        o = testdir.tmpdir
        o.ensure("conftest.py").write("x=1")
        config = testdir.parseconfig(str(o))
        assert config.getvalue('x') == 1
        config.option.x = 2
        assert config.getvalue('x') == 2
        config = testdir.parseconfig([str(o)])
        assert config.getvalue('x') == 1

    def test_getconftest_pathlist(self, testdir, tmpdir):
        somepath = tmpdir.join("x", "y", "z")
        p = tmpdir.join("conftest.py")
        p.write("pathlist = ['.', %r]" % str(somepath))
        config = testdir.parseconfigure(p)
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
        pytest.raises(ValueError, config.getini, 'other')

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
        pytest.raises(ValueError, config.getini, 'other')

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

    def test_addinivalue_line_existing(self, testdir):
        testdir.makeconftest("""
            def pytest_addoption(parser):
                parser.addini("xy", "", type="linelist")
        """)
        p = testdir.makeini("""
            [pytest]
            xy= 123
        """)
        config = testdir.parseconfig()
        l = config.getini("xy")
        assert len(l) == 1
        assert l == ["123"]
        config.addinivalue_line("xy", "456")
        l = config.getini("xy")
        assert len(l) == 2
        assert l == ["123", "456"]

    def test_addinivalue_line_new(self, testdir):
        testdir.makeconftest("""
            def pytest_addoption(parser):
                parser.addini("xy", "", type="linelist")
        """)
        config = testdir.parseconfig()
        assert not config.getini("xy")
        config.addinivalue_line("xy", "456")
        l = config.getini("xy")
        assert len(l) == 1
        assert l == ["456"]
        config.addinivalue_line("xy", "123")
        l = config.getini("xy")
        assert len(l) == 2
        assert l == ["456", "123"]

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

def test_preparse_ordering_with_setuptools(testdir, monkeypatch):
    pkg_resources = py.test.importorskip("pkg_resources")
    def my_iter(name):
        assert name == "pytest11"
        class EntryPoint:
            name = "mytestplugin"
            class dist:
                pass
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

def test_plugin_preparse_prevents_setuptools_loading(testdir, monkeypatch):
    pkg_resources = py.test.importorskip("pkg_resources")
    def my_iter(name):
        assert name == "pytest11"
        class EntryPoint:
            name = "mytestplugin"
            def load(self):
                assert 0, "should not arrive here"
        return iter([EntryPoint()])
    monkeypatch.setattr(pkg_resources, 'iter_entry_points', my_iter)
    config = testdir.parseconfig("-p", "no:mytestplugin")
    plugin = config.pluginmanager.getplugin("mytestplugin")
    assert plugin == -1

def test_cmdline_processargs_simple(testdir):
    testdir.makeconftest("""
        def pytest_cmdline_preparse(args):
            args.append("-h")
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
        "*pytest*",
        "*-h*",
    ])
