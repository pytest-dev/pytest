import py

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
