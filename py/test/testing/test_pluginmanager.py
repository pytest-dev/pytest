import py, os
from py.__.test.pluginmanager import PluginManager, canonical_names
from py.__.test.pluginmanager import registerplugin, importplugin

class TestBootstrapping:
    def test_consider_env_fails_to_import(self, monkeypatch):
        pluginmanager = PluginManager()
        monkeypatch.setitem(os.environ, 'PYTEST_PLUGINS', 'nonexistingmodule')
        py.test.raises(ImportError, "pluginmanager.consider_env()")

    def test_preparse_args(self, monkeypatch):
        pluginmanager = PluginManager()
        py.test.raises(ImportError, """
            pluginmanager.consider_preparse(["xyz", "-p", "hello123"])
        """)

    def test_consider_env_plugin_instantiation(self, testdir, monkeypatch):
        pluginmanager = PluginManager()
        testdir.syspathinsert()
        testdir.makepyfile(pytest_xy123="class Xy123Plugin: pass")
        monkeypatch.setitem(os.environ, 'PYTEST_PLUGINS', 'xy123')
        l1 = len(pluginmanager.getplugins())
        pluginmanager.consider_env()
        l2 = len(pluginmanager.getplugins())
        assert l2 == l1 + 1 
        assert pluginmanager.getplugin('pytest_xy123') 
        pluginmanager.consider_env()
        l3 = len(pluginmanager.getplugins())
        assert l2 == l3

    def test_pluginmanager_ENV_startup(self, testdir, monkeypatch):
        x500 = testdir.makepyfile(pytest_x500="class X500Plugin: pass")
        p = testdir.makepyfile("""
            import py
            def test_hello():
                plugin = py.test.config.pluginmanager.getplugin('x500')
                assert plugin is not None
        """)
        new = str(x500.dirpath()) # "%s:%s" %(x500.dirpath(), os.environ.get('PYTHONPATH', ''))
        monkeypatch.setitem(os.environ, 'PYTHONPATH', new)
        monkeypatch.setitem(os.environ, 'PYTEST_PLUGINS', 'pytest_x500')
        result = testdir.runpytest(p)
        assert result.ret == 0
        extra = result.stdout.fnmatch_lines(["*1 passed in*"])

    def test_import_plugin_importname(self, testdir):
        pluginmanager = PluginManager()
        py.test.raises(ImportError, 'pluginmanager.import_plugin("x.y")')
        py.test.raises(ImportError, 'pluginmanager.import_plugin("pytest_x.y")')

        reset = testdir.syspathinsert()
        pluginname = "pytest_hello"
        testdir.makepyfile(**{pluginname: """
            class HelloPlugin:
                pass
        """})
        pluginmanager.import_plugin("hello")
        len1 = len(pluginmanager.getplugins())
        pluginmanager.import_plugin("pytest_hello")
        len2 = len(pluginmanager.getplugins())
        assert len1 == len2
        plugin1 = pluginmanager.getplugin("pytest_hello")
        assert plugin1.__class__.__name__ == 'HelloPlugin'
        plugin2 = pluginmanager.getplugin("hello")
        assert plugin2 is plugin1

    def test_consider_module(self, testdir):
        pluginmanager = PluginManager()
        testdir.syspathinsert()
        testdir.makepyfile(pytest_plug1="class Plug1Plugin: pass")
        testdir.makepyfile(pytest_plug2="class Plug2Plugin: pass")
        mod = py.std.new.module("temp")
        mod.pytest_plugins = ["pytest_plug1", "pytest_plug2"]
        pluginmanager.consider_module(mod)
        assert pluginmanager.getplugin("plug1").__class__.__name__ == "Plug1Plugin"
        assert pluginmanager.getplugin("plug2").__class__.__name__ == "Plug2Plugin"

    def test_consider_module_import_module(self, testdir):
        mod = py.std.new.module("x")
        mod.pytest_plugins = "pytest_a"
        aplugin = testdir.makepyfile(pytest_a="""class APlugin: pass""")
        pluginmanager = PluginManager() 
        sorter = testdir.geteventrecorder(pluginmanager)
        #syspath.prepend(aplugin.dirpath())
        py.std.sys.path.insert(0, str(aplugin.dirpath()))
        pluginmanager.consider_module(mod)
        call = sorter.getcall(pluginmanager.hook.pytest_plugin_registered.name)
        assert call.plugin.__class__.__name__ == "APlugin"

        # check that it is not registered twice 
        pluginmanager.consider_module(mod)
        l = sorter.getcalls("plugin_registered")
        assert len(l) == 1

    def test_consider_conftest(self, testdir):
        pp = PluginManager()
        mod = testdir.makepyfile("class ConftestPlugin: hello = 1").pyimport()
        pp.consider_conftest(mod)
        l = [x for x in pp.getplugins() if isinstance(x, mod.ConftestPlugin)]
        assert len(l) == 1
        assert l[0].hello == 1

        pp.consider_conftest(mod)
        l = [x for x in pp.getplugins() if isinstance(x, mod.ConftestPlugin)]
        assert len(l) == 1

    def test_config_sets_conftesthandle_onimport(self, testdir):
        config = testdir.parseconfig([])
        assert config._conftest._onimport == config._onimportconftest

    def test_consider_conftest_deps(self, testdir):
        mod = testdir.makepyfile("pytest_plugins='xyz'").pyimport()
        pp = PluginManager()
        py.test.raises(ImportError, "pp.consider_conftest(mod)")

    def test_registry(self):
        pp = PluginManager()
        a1, a2 = object(), object()
        pp.register(a1)
        assert pp.isregistered(a1)
        pp.register(a2)
        assert pp.isregistered(a2)
        assert pp.getplugins() == [a1, a2]
        pp.unregister(a1)
        assert not pp.isregistered(a1)
        pp.unregister(a2)
        assert not pp.isregistered(a2)

    def test_canonical_names(self):
        for name in 'xyz', 'pytest_xyz', 'pytest_Xyz', 'Xyz':
            impname, clsname = canonical_names(name)
            assert impname == "pytest_xyz"
            assert clsname == "XyzPlugin"

    def test_registerplugin(self):
        l = []
        registerfunc = l.append
        registerplugin(registerfunc, py.io, "TerminalWriter")
        assert len(l) == 1
        assert isinstance(l[0], py.io.TerminalWriter)

    def test_importplugin(self):
        assert importplugin("py") == py 
        py.test.raises(ImportError, "importplugin('laksjd.qwe')")
        mod = importplugin("pytest_terminal")
        assert mod is py.__.test.plugin.pytest_terminal 


class TestPytestPluginInteractions:
    def test_do_option_conftestplugin(self, testdir):
        from py.__.test.config import Config 
        p = testdir.makepyfile("""
            class ConftestPlugin:
                def pytest_addoption(self, parser):
                    parser.addoption('--test123', action="store_true")
        """)
        config = Config() 
        config._conftest.importconftest(p)
        print config.pluginmanager.getplugins()
        config.parse([])
        assert not config.option.test123

    def test_do_option_postinitialize(self, testdir):
        from py.__.test.config import Config 
        config = Config() 
        config.parse([])
        config.pluginmanager.do_configure(config=config)
        assert not hasattr(config.option, 'test123')
        p = testdir.makepyfile("""
            class ConftestPlugin:
                def pytest_addoption(self, parser):
                    parser.addoption('--test123', action="store_true", 
                        default=True)
        """)
        config._conftest.importconftest(p)
        assert config.option.test123

    def test_configure(self, testdir):
        config = testdir.parseconfig()
        l = []
        class A:
            def pytest_configure(self, config):
                l.append(self)
                
        config.pluginmanager.register(A())
        assert len(l) == 0
        config.pluginmanager.do_configure(config=config)
        assert len(l) == 1
        config.pluginmanager.register(A())  # this should lead to a configured() plugin
        assert len(l) == 2
        assert l[0] != l[1]
       
        config.pluginmanager.do_unconfigure(config=config)
        config.pluginmanager.register(A())
        assert len(l) == 2

    def test_MultiCall(self):
        pp = PluginManager()
        assert hasattr(pp, 'MultiCall')

    # lower level API

    def test_getfirst(self):
        pluginmanager = PluginManager()
        class My1:
            x = 1
        assert pluginmanager.getfirst("x") is None
        pluginmanager.register(My1())
        assert pluginmanager.getfirst("x") == 1


    def test_call_firstresult(self):
        pluginmanager = PluginManager()
        class My1:
            def method(self):
                pass
        class My2:
            def method(self):
                return True 
        class My3:
            def method(self):
                return None
        assert pluginmanager.call_firstresult("method") is None
        assert pluginmanager.call_firstresult("methodnotexists") is None
        pluginmanager.register(My1())
        assert pluginmanager.call_firstresult("method") is None
        pluginmanager.register(My2())
        assert pluginmanager.call_firstresult("method") == True
        pluginmanager.register(My3())
        assert pluginmanager.call_firstresult("method") == True

    def test_listattr(self):
        pluginmanager = PluginManager()
        class My2:
            x = 42
        pluginmanager.register(My2())
        assert not pluginmanager.listattr("hello")
        assert pluginmanager.listattr("x") == [42]

    @py.test.mark(xfail="implement setupcall")
    def test_call_setup_participants(self, testdir):
        testdir.makepyfile(
            conftest="""
                import py
                def pytest_method(self, x):
                    return x+1
                pytest_plugin = "pytest_someplugin",
            """
        )
        testdir.makepyfile(pytest_someplugin="""
                def pytest_method(self, x):
                    return x+1
        """)
        modcol = testdir.getmodulecol("""
            def pytest_method(x):
                return x+0 
        """)
        l = []
        call = modcol.config.pluginmanager.setupcall(modcol, "pytest_method", 1)
        assert len(call.methods) == 3
        results = call.execute()
        assert results == [1,2,2]

