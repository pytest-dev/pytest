import py, os
from py.__.test.pytestplugin import PytestPlugins, canonical_names
from py.__.test.pytestplugin import registerplugin, importplugin

class TestBootstrapping:
    def test_consider_env_fails_to_import(self, monkeypatch):
        plugins = PytestPlugins()
        monkeypatch.setitem(os.environ, 'PYTEST_PLUGINS', 'nonexistingmodule')
        py.test.raises(ImportError, "plugins.consider_env()")

    def test_consider_env_plugin_instantiation(self, testdir, monkeypatch):
        plugins = PytestPlugins()
        testdir.syspathinsert()
        testdir.makepyfile(pytest_xy123="class Xy123Plugin: pass")
        monkeypatch.setitem(os.environ, 'PYTEST_PLUGINS', 'xy123')
        l1 = len(plugins.getplugins())
        plugins.consider_env()
        l2 = len(plugins.getplugins())
        assert l2 == l1 + 1 
        assert plugins.getplugin('pytest_xy123') 
        plugins.consider_env()
        l3 = len(plugins.getplugins())
        assert l2 == l3

    def test_pytestplugin_ENV_startup(self, testdir, monkeypatch):
        x500 = testdir.makepyfile(pytest_x500="class X500Plugin: pass")
        p = testdir.makepyfile("""
            import py
            def test_hello():
                plugin = py.test.config.pytestplugins.getplugin('x500')
                assert plugin is not None
        """)
        new = str(x500.dirpath()) # "%s:%s" %(x500.dirpath(), os.environ.get('PYTHONPATH', ''))
        monkeypatch.setitem(os.environ, 'PYTHONPATH', new)
        monkeypatch.setitem(os.environ, 'PYTEST_PLUGINS', 'pytest_x500')
        result = testdir.runpytest(p)
        assert result.ret == 0
        extra = result.stdout.fnmatch_lines(["*1 passed in*"])

    def test_import_plugin_importname(self, testdir):
        plugins = PytestPlugins()
        py.test.raises(ImportError, 'plugins.import_plugin("x.y")')
        py.test.raises(ImportError, 'plugins.import_plugin("pytest_x.y")')

        reset = testdir.syspathinsert()
        pluginname = "pytest_hello"
        testdir.makepyfile(**{pluginname: """
            class HelloPlugin:
                pass
        """})
        plugins.import_plugin("hello")
        len1 = len(plugins.getplugins())
        plugins.import_plugin("pytest_hello")
        len2 = len(plugins.getplugins())
        assert len1 == len2
        plugin1 = plugins.getplugin("pytest_hello")
        assert plugin1.__class__.__name__ == 'HelloPlugin'
        plugin2 = plugins.getplugin("hello")
        assert plugin2 is plugin1

    def test_consider_module(self, testdir):
        plugins = PytestPlugins()
        testdir.syspathinsert()
        testdir.makepyfile(pytest_plug1="class Plug1Plugin: pass")
        testdir.makepyfile(pytest_plug2="class Plug2Plugin: pass")
        mod = py.std.new.module("temp")
        mod.pytest_plugins = ["pytest_plug1", "pytest_plug2"]
        plugins.consider_module(mod)
        assert plugins.getplugin("plug1").__class__.__name__ == "Plug1Plugin"
        assert plugins.getplugin("plug2").__class__.__name__ == "Plug2Plugin"

    def test_consider_module_import_module(self, testdir, EventRecorder):
        mod = py.std.new.module("x")
        mod.pytest_plugins = "pytest_a"
        aplugin = testdir.makepyfile(pytest_a="""class APlugin: pass""")
        plugins = PytestPlugins() 
        sorter = EventRecorder(plugins)
        #syspath.prepend(aplugin.dirpath())
        py.std.sys.path.insert(0, str(aplugin.dirpath()))
        plugins.consider_module(mod)
        call = sorter.getcall("plugin_registered")
        assert call.plugin.__class__.__name__ == "APlugin"

        # check that it is not registered twice 
        plugins.consider_module(mod)
        l = sorter.getcalls("plugin_registered")
        assert len(l) == 1

    def test_consider_conftest(self, testdir):
        pp = PytestPlugins()
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
        pp = PytestPlugins()
        py.test.raises(ImportError, "pp.consider_conftest(mod)")

    def test_registry(self):
        pp = PytestPlugins()
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
        print config.pytestplugins.getplugins()
        config.parse([])
        assert not config.option.test123

    def test_do_option_postinitialize(self, testdir):
        from py.__.test.config import Config 
        config = Config() 
        config.parse([])
        config.pytestplugins.do_configure(config=config)
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
        events = []
        class A:
            def pytest_configure(self, config):
                l.append(self)
            def pyevent__hello(self, obj):
                events.append(obj)
                
        config.bus.register(A())
        assert len(l) == 0
        config.pytestplugins.do_configure(config=config)
        assert len(l) == 1
        config.bus.register(A())  # this should lead to a configured() plugin
        assert len(l) == 2
        assert l[0] != l[1]
        
        config.bus.notify("hello", 42)
        assert len(events) == 2
        assert events == [42,42]

        config.pytestplugins.do_unconfigure(config=config)
        config.bus.register(A())
        assert len(l) == 2

    def test_MultiCall(self):
        pp = PytestPlugins()
        assert hasattr(pp, 'MultiCall')

    # lower level API

    def test_getfirst(self):
        plugins = PytestPlugins()
        class My1:
            x = 1
        assert plugins.getfirst("x") is None
        plugins.register(My1())
        assert plugins.getfirst("x") == 1

    def test_call_each(self):
        plugins = PytestPlugins()
        class My:
            def method(self, arg):
                pass
        plugins.register(My())
        py.test.raises(TypeError, 'plugins.call_each("method")')
        l = plugins.call_each("method", arg=42)
        assert l == []
        py.test.raises(TypeError, 'plugins.call_each("method", arg=42, s=13)')

    def test_call_firstresult(self):
        plugins = PytestPlugins()
        class My1:
            def method(self):
                pass
        class My2:
            def method(self):
                return True 
        class My3:
            def method(self):
                return None
        assert plugins.call_firstresult("method") is None
        assert plugins.call_firstresult("methodnotexists") is None
        plugins.register(My1())
        assert plugins.call_firstresult("method") is None
        plugins.register(My2())
        assert plugins.call_firstresult("method") == True
        plugins.register(My3())
        assert plugins.call_firstresult("method") == True

    def test_listattr(self):
        plugins = PytestPlugins()
        class My2:
            x = 42
        plugins.register(My2())
        assert not plugins.listattr("hello")
        assert plugins.listattr("x") == [42]

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
        call = modcol.config.pytestplugins.setupcall(modcol, "pytest_method", 1)
        assert len(call.methods) == 3
        results = call.execute()
        assert results == [1,2,2]

