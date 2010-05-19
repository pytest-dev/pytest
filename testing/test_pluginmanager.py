import py, os
from py._test.pluginmanager import PluginManager, canonical_importname
from py._test.pluginmanager import Registry, MultiCall, HookRelay, varnames


class TestBootstrapping:
    def test_consider_env_fails_to_import(self, monkeypatch):
        pluginmanager = PluginManager()
        monkeypatch.setenv('PYTEST_PLUGINS', 'nonexisting', prepend=",")
        py.test.raises(ImportError, "pluginmanager.consider_env()")

    def test_preparse_args(self):
        pluginmanager = PluginManager()
        py.test.raises(ImportError, """
            pluginmanager.consider_preparse(["xyz", "-p", "hello123"])
        """)

    def test_plugin_skip(self, testdir, monkeypatch):
        p = testdir.makepyfile(pytest_skipping1="""
            import py
            py.test.skip("hello")
        """)
        p.copy(p.dirpath("pytest_skipping2.py"))
        monkeypatch.setenv("PYTEST_PLUGINS", "skipping2")
        result = testdir.runpytest("-p", "skipping1", "--traceconfig")
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            "*hint*skipping2*hello*",
            "*hint*skipping1*hello*",
        ])

    def test_consider_env_plugin_instantiation(self, testdir, monkeypatch):
        pluginmanager = PluginManager()
        testdir.syspathinsert()
        testdir.makepyfile(pytest_xy123="#")
        monkeypatch.setitem(os.environ, 'PYTEST_PLUGINS', 'xy123')
        l1 = len(pluginmanager.getplugins())
        pluginmanager.consider_env()
        l2 = len(pluginmanager.getplugins())
        assert l2 == l1 + 1 
        assert pluginmanager.getplugin('pytest_xy123') 
        pluginmanager.consider_env()
        l3 = len(pluginmanager.getplugins())
        assert l2 == l3

    def test_consider_setuptools_instantiation(self, monkeypatch):
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
        pluginmanager = PluginManager()
        pluginmanager.consider_setuptools_entrypoints()
        plugin = pluginmanager.getplugin("mytestplugin")
        assert plugin.x == 42
        plugin2 = pluginmanager.getplugin("pytest_mytestplugin")
        assert plugin2 == plugin

    def test_consider_setuptools_not_installed(self, monkeypatch):
        monkeypatch.setitem(py.std.sys.modules, 'pkg_resources', 
            py.std.types.ModuleType("pkg_resources"))
        pluginmanager = PluginManager()
        pluginmanager.consider_setuptools_entrypoints()
        # ok, we did not explode

    def test_pluginmanager_ENV_startup(self, testdir, monkeypatch):
        x500 = testdir.makepyfile(pytest_x500="#")
        p = testdir.makepyfile("""
            import py
            def test_hello(pytestconfig):
                plugin = pytestconfig.pluginmanager.getplugin('x500')
                assert plugin is not None
        """)
        monkeypatch.setenv('PYTEST_PLUGINS', 'pytest_x500', prepend=",")
        result = testdir.runpytest(p)
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*1 passed in*"])

    def test_import_plugin_importname(self, testdir):
        pluginmanager = PluginManager()
        py.test.raises(ImportError, 'pluginmanager.import_plugin("x.y")')
        py.test.raises(ImportError, 'pluginmanager.import_plugin("pytest_x.y")')

        reset = testdir.syspathinsert()
        pluginname = "pytest_hello"
        testdir.makepyfile(**{pluginname: ""})
        pluginmanager.import_plugin("hello")
        len1 = len(pluginmanager.getplugins())
        pluginmanager.import_plugin("pytest_hello")
        len2 = len(pluginmanager.getplugins())
        assert len1 == len2
        plugin1 = pluginmanager.getplugin("pytest_hello")
        assert plugin1.__name__.endswith('pytest_hello')
        plugin2 = pluginmanager.getplugin("hello")
        assert plugin2 is plugin1

    def test_consider_module(self, testdir):
        pluginmanager = PluginManager()
        testdir.syspathinsert()
        testdir.makepyfile(pytest_plug1="#")
        testdir.makepyfile(pytest_plug2="#")
        mod = py.std.types.ModuleType("temp")
        mod.pytest_plugins = ["pytest_plug1", "pytest_plug2"]
        pluginmanager.consider_module(mod)
        assert pluginmanager.getplugin("plug1").__name__ == "pytest_plug1"
        assert pluginmanager.getplugin("plug2").__name__ == "pytest_plug2"

    def test_consider_module_import_module(self, testdir):
        mod = py.std.types.ModuleType("x")
        mod.pytest_plugins = "pytest_a"
        aplugin = testdir.makepyfile(pytest_a="#")
        pluginmanager = PluginManager() 
        reprec = testdir.getreportrecorder(pluginmanager)
        #syspath.prepend(aplugin.dirpath())
        py.std.sys.path.insert(0, str(aplugin.dirpath()))
        pluginmanager.consider_module(mod)
        call = reprec.getcall(pluginmanager.hook.pytest_plugin_registered.name)
        assert call.plugin.__name__ == "pytest_a"

        # check that it is not registered twice 
        pluginmanager.consider_module(mod)
        l = reprec.getcalls("pytest_plugin_registered")
        assert len(l) == 1

    def test_consider_conftest_deprecated(self, testdir):
        pp = PluginManager()
        mod = testdir.makepyfile("class ConftestPlugin: pass").pyimport()
        call = py.test.raises(ValueError, pp.consider_conftest, mod)

    def test_config_sets_conftesthandle_onimport(self, testdir):
        config = testdir.parseconfig([])
        assert config._conftest._onimport == config._onimportconftest

    def test_consider_conftest_deps(self, testdir):
        mod = testdir.makepyfile("pytest_plugins='xyz'").pyimport()
        pp = PluginManager()
        py.test.raises(ImportError, "pp.consider_conftest(mod)")

    def test_registry(self):
        pp = PluginManager()
        class A: pass 
        a1, a2 = A(), A()
        pp.register(a1)
        assert pp.isregistered(a1)
        pp.register(a2, "hello")
        assert pp.isregistered(a2)
        l = pp.getplugins()
        assert a1 in l 
        assert a2 in l
        assert pp.getplugin('hello') == a2
        pp.unregister(a1)
        assert not pp.isregistered(a1)
        pp.unregister(a2)
        assert not pp.isregistered(a2)

    def test_register_imported_modules(self):
        pp = PluginManager()
        mod = py.std.types.ModuleType("x.y.pytest_hello")
        pp.register(mod)
        assert pp.isregistered(mod)
        l = pp.getplugins()
        assert mod in l 
        py.test.raises(AssertionError, "pp.register(mod)")
        mod2 = py.std.types.ModuleType("pytest_hello")
        #pp.register(mod2) # double registry 
        py.test.raises(AssertionError, "pp.register(mod)")
        #assert not pp.isregistered(mod2)
        assert pp.getplugins() == l

    def test_canonical_import(self, monkeypatch):
        mod = py.std.types.ModuleType("pytest_xyz")
        monkeypatch.setitem(py.std.sys.modules, 'pytest_xyz', mod)
        pp = PluginManager()
        pp.import_plugin('xyz')
        assert pp.getplugin('xyz') == mod
        assert pp.getplugin('pytest_xyz') == mod
        assert pp.isregistered(mod)

    def test_register_mismatch_method(self):
        pp = PluginManager()
        class hello:
            def pytest_gurgel(self):
                pass
        py.test.raises(Exception, "pp.register(hello())")

    def test_register_mismatch_arg(self):
        pp = PluginManager()
        class hello:
            def pytest_configure(self, asd):
                pass
        excinfo = py.test.raises(Exception, "pp.register(hello())")

    def test_canonical_importname(self):
        for name in 'xyz', 'pytest_xyz', 'pytest_Xyz', 'Xyz':
            impname = canonical_importname(name)

class TestPytestPluginInteractions:

    def test_addhooks_conftestplugin(self, testdir):
        from py._test.config import Config 
        newhooks = testdir.makepyfile(newhooks="""
            def pytest_myhook(xyz):
                "new hook"
        """)
        conf = testdir.makeconftest("""
            import sys ; sys.path.insert(0, '.')
            import newhooks
            def pytest_addhooks(pluginmanager):
                pluginmanager.addhooks(newhooks)
            def pytest_myhook(xyz):
                return xyz + 1
        """)
        config = Config() 
        config._conftest.importconftest(conf)
        print(config.pluginmanager.getplugins())
        res = config.hook.pytest_myhook(xyz=10)
        assert res == [11]

    def test_addhooks_docstring_error(self, testdir):
        newhooks = testdir.makepyfile(newhooks="""
            class A: # no pytest_ prefix
                pass
            def pytest_myhook(xyz):
                pass
        """)
        conf = testdir.makeconftest("""
            import sys ; sys.path.insert(0, '.')
            import newhooks
            def pytest_addhooks(pluginmanager):
                pluginmanager.addhooks(newhooks)
        """)
        res = testdir.runpytest()
        assert res.ret != 0
        res.stderr.fnmatch_lines([
            "*docstring*pytest_myhook*newhooks*"
        ])

    def test_addhooks_nohooks(self, testdir):
        conf = testdir.makeconftest("""
            import sys 
            def pytest_addhooks(pluginmanager):
                pluginmanager.addhooks(sys)
        """)
        res = testdir.runpytest()
        assert res.ret != 0
        res.stderr.fnmatch_lines([
            "*did not find*sys*"
        ])

    def test_do_option_conftestplugin(self, testdir):
        from py._test.config import Config 
        p = testdir.makepyfile("""
            def pytest_addoption(parser):
                parser.addoption('--test123', action="store_true")
        """)
        config = Config() 
        config._conftest.importconftest(p)
        print(config.pluginmanager.getplugins())
        config.parse([])
        assert not config.option.test123

    def test_do_ext_namespace(self, testdir):
        testdir.makeconftest("""
            def pytest_namespace():
                return {'hello': 'world'}
        """)
        p = testdir.makepyfile("""
            from py.test import hello 
            import py
            def test_hello():
                assert hello == "world" 
                assert 'hello' in py.test.__all__
        """)
        result = testdir.runpytest(p) 
        result.stdout.fnmatch_lines([
            "*1 passed*"
        ])

    def test_do_option_postinitialize(self, testdir):
        from py._test.config import Config 
        config = Config() 
        config.parse([])
        config.pluginmanager.do_configure(config=config)
        assert not hasattr(config.option, 'test123')
        p = testdir.makepyfile("""
            def pytest_addoption(parser):
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

    # lower level API

    def test_listattr(self):
        pluginmanager = PluginManager()
        class My2:
            x = 42
        pluginmanager.register(My2())
        assert not pluginmanager.listattr("hello")
        assert pluginmanager.listattr("x") == [42]

def test_namespace_has_default_and_env_plugins(testdir):
    p = testdir.makepyfile("""
        import py
        py.test.mark 
    """)
    result = testdir.runpython(p)
    assert result.ret == 0

def test_varnames():
    def f(x):
        pass
    class A:
        def f(self, y):
            pass
    assert varnames(f) == ("x",)
    assert varnames(A().f) == ('y',)
    
class TestMultiCall:
    def test_uses_copy_of_methods(self):
        l = [lambda: 42]
        mc = MultiCall(l, {})
        repr(mc)
        l[:] = []
        res = mc.execute()
        return res == 42

    def test_call_passing(self):
        class P1:
            def m(self, __multicall__, x):
                assert len(__multicall__.results) == 1
                assert not __multicall__.methods
                return 17

        class P2:
            def m(self, __multicall__, x):
                assert __multicall__.results == []
                assert __multicall__.methods
                return 23 
               
        p1 = P1() 
        p2 = P2() 
        multicall = MultiCall([p1.m, p2.m], {'x': 23})
        assert "23" in repr(multicall)
        reslist = multicall.execute()
        assert len(reslist) == 2
        # ensure reversed order 
        assert reslist == [23, 17]

    def test_keyword_args(self):
        def f(x): 
            return x + 1
        class A:
            def f(self, x, y):
                return x + y
        multicall = MultiCall([f, A().f], dict(x=23, y=24))
        assert "'x': 23" in repr(multicall)
        assert "'y': 24" in repr(multicall)
        reslist = multicall.execute()
        assert reslist == [24+23, 24]
        assert "2 results" in repr(multicall)

    def test_keywords_call_error(self):
        multicall = MultiCall([lambda x: x], {})
        py.test.raises(TypeError, "multicall.execute()")

    def test_call_subexecute(self):
        def m(__multicall__):
            subresult = __multicall__.execute()
            return subresult + 1

        def n():
            return 1

        call = MultiCall([n, m], {}, firstresult=True)
        res = call.execute()
        assert res == 2

    def test_call_none_is_no_result(self):
        def m1():
            return 1
        def m2():
            return None
        res = MultiCall([m1, m2], {}, firstresult=True).execute()
        assert res == 1
        res = MultiCall([m1, m2], {}).execute()
        assert res == [1]

class TestRegistry:

    def test_register(self):
        registry = Registry()
        class MyPlugin:
            pass
        my = MyPlugin()
        registry.register(my)
        assert list(registry) == [my]
        my2 = MyPlugin()
        registry.register(my2)
        assert list(registry) == [my, my2]

        assert registry.isregistered(my)
        assert registry.isregistered(my2)
        registry.unregister(my)
        assert not registry.isregistered(my)
        assert list(registry) == [my2]

    def test_listattr(self):
        plugins = Registry()
        class api1:
            x = 41
        class api2:
            x = 42
        class api3:
            x = 43
        plugins.register(api1())
        plugins.register(api2())
        plugins.register(api3())
        l = list(plugins.listattr('x'))
        assert l == [41, 42, 43]
        l = list(plugins.listattr('x', reverse=True))
        assert l == [43, 42, 41]

class TestHookRelay:
    def test_happypath(self):
        registry = Registry()
        class Api:
            def hello(self, arg):
                "api hook 1"

        mcm = HookRelay(hookspecs=Api, registry=registry, prefix="he")
        assert hasattr(mcm, 'hello')
        assert repr(mcm.hello).find("hello") != -1
        class Plugin:
            def hello(self, arg):
                return arg + 1
        registry.register(Plugin())
        l = mcm.hello(arg=3)
        assert l == [4]
        assert not hasattr(mcm, 'world')

    def test_only_kwargs(self):
        registry = Registry()
        class Api:
            def hello(self, arg):
                "api hook 1"
        mcm = HookRelay(hookspecs=Api, registry=registry, prefix="he")
        py.test.raises(TypeError, "mcm.hello(3)")

    def test_firstresult_definition(self):
        registry = Registry()
        class Api:
            def hello(self, arg): 
                "api hook 1"
            hello.firstresult = True

        mcm = HookRelay(hookspecs=Api, registry=registry, prefix="he")
        class Plugin:
            def hello(self, arg):
                return arg + 1
        registry.register(Plugin())
        res = mcm.hello(arg=3)
        assert res == 4

