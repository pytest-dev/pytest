import pytest, py, os
from _pytest.core import PluginManager
from _pytest.core import MultiCall, HookRelay, varnames


class TestBootstrapping:
    def test_consider_env_fails_to_import(self, monkeypatch):
        pluginmanager = PluginManager()
        monkeypatch.setenv('PYTEST_PLUGINS', 'nonexisting', prepend=",")
        pytest.raises(ImportError, "pluginmanager.consider_env()")

    def test_preparse_args(self):
        pluginmanager = PluginManager()
        pytest.raises(ImportError, """
            pluginmanager.consider_preparse(["xyz", "-p", "hello123"])
        """)

    def test_plugin_prevent_register(self):
        pluginmanager = PluginManager()
        pluginmanager.consider_preparse(["xyz", "-p", "no:abc"])
        l1 = pluginmanager.getplugins()
        pluginmanager.register(42, name="abc")
        l2 = pluginmanager.getplugins()
        assert len(l2) == len(l1)

    def test_plugin_prevent_register_unregistered_alredy_registered(self):
        pluginmanager = PluginManager()
        pluginmanager.register(42, name="abc")
        l1 = pluginmanager.getplugins()
        assert 42 in l1
        pluginmanager.consider_preparse(["xyz", "-p", "no:abc"])
        l2 = pluginmanager.getplugins()
        assert 42 not in l2

    def test_plugin_skip(self, testdir, monkeypatch):
        p = testdir.makepyfile(skipping1="""
            import pytest
            pytest.skip("hello")
        """)
        p.copy(p.dirpath("skipping2.py"))
        monkeypatch.setenv("PYTEST_PLUGINS", "skipping2")
        result = testdir.runpytest("-p", "skipping1", "--traceconfig")
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            "*hint*skipping1*hello*",
            "*hint*skipping2*hello*",
        ])

    def test_consider_env_plugin_instantiation(self, testdir, monkeypatch):
        pluginmanager = PluginManager()
        testdir.syspathinsert()
        testdir.makepyfile(xy123="#")
        monkeypatch.setitem(os.environ, 'PYTEST_PLUGINS', 'xy123')
        l1 = len(pluginmanager.getplugins())
        pluginmanager.consider_env()
        l2 = len(pluginmanager.getplugins())
        assert l2 == l1 + 1
        assert pluginmanager.getplugin('xy123')
        pluginmanager.consider_env()
        l3 = len(pluginmanager.getplugins())
        assert l2 == l3

    def test_consider_setuptools_instantiation(self, monkeypatch):
        pkg_resources = py.test.importorskip("pkg_resources")
        def my_iter(name):
            assert name == "pytest11"
            class EntryPoint:
                name = "pytest_mytestplugin"
                dist = None
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

    def test_consider_setuptools_not_installed(self, monkeypatch):
        monkeypatch.setitem(py.std.sys.modules, 'pkg_resources',
            py.std.types.ModuleType("pkg_resources"))
        pluginmanager = PluginManager()
        pluginmanager.consider_setuptools_entrypoints()
        # ok, we did not explode

    def test_pluginmanager_ENV_startup(self, testdir, monkeypatch):
        x500 = testdir.makepyfile(pytest_x500="#")
        p = testdir.makepyfile("""
            import pytest
            def test_hello(pytestconfig):
                plugin = pytestconfig.pluginmanager.getplugin('pytest_x500')
                assert plugin is not None
        """)
        monkeypatch.setenv('PYTEST_PLUGINS', 'pytest_x500', prepend=",")
        result = testdir.runpytest(p)
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*1 passed in*"])

    def test_import_plugin_importname(self, testdir):
        pluginmanager = PluginManager()
        pytest.raises(ImportError, 'pluginmanager.import_plugin("qweqwex.y")')
        pytest.raises(ImportError, 'pluginmanager.import_plugin("pytest_qweqwx.y")')

        reset = testdir.syspathinsert()
        pluginname = "pytest_hello"
        testdir.makepyfile(**{pluginname: ""})
        pluginmanager.import_plugin("pytest_hello")
        len1 = len(pluginmanager.getplugins())
        pluginmanager.import_plugin("pytest_hello")
        len2 = len(pluginmanager.getplugins())
        assert len1 == len2
        plugin1 = pluginmanager.getplugin("pytest_hello")
        assert plugin1.__name__.endswith('pytest_hello')
        plugin2 = pluginmanager.getplugin("pytest_hello")
        assert plugin2 is plugin1

    def test_import_plugin_dotted_name(self, testdir):
        pluginmanager = PluginManager()
        pytest.raises(ImportError, 'pluginmanager.import_plugin("qweqwex.y")')
        pytest.raises(ImportError, 'pluginmanager.import_plugin("pytest_qweqwex.y")')

        reset = testdir.syspathinsert()
        testdir.mkpydir("pkg").join("plug.py").write("x=3")
        pluginname = "pkg.plug"
        pluginmanager.import_plugin(pluginname)
        mod = pluginmanager.getplugin("pkg.plug")
        assert mod.x == 3

    def test_consider_module(self, testdir):
        pluginmanager = PluginManager()
        testdir.syspathinsert()
        testdir.makepyfile(pytest_p1="#")
        testdir.makepyfile(pytest_p2="#")
        mod = py.std.types.ModuleType("temp")
        mod.pytest_plugins = ["pytest_p1", "pytest_p2"]
        pluginmanager.consider_module(mod)
        assert pluginmanager.getplugin("pytest_p1").__name__ == "pytest_p1"
        assert pluginmanager.getplugin("pytest_p2").__name__ == "pytest_p2"

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

    def test_config_sets_conftesthandle_onimport(self, testdir):
        config = testdir.parseconfig([])
        assert config._conftest._onimport == config._onimportconftest

    def test_consider_conftest_deps(self, testdir):
        mod = testdir.makepyfile("pytest_plugins='xyz'").pyimport()
        pp = PluginManager()
        pytest.raises(ImportError, "pp.consider_conftest(mod)")

    def test_pm(self):
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
        pp.unregister(name="hello")
        assert not pp.isregistered(a2)

    def test_pm_ordering(self):
        pp = PluginManager()
        class A: pass
        a1, a2 = A(), A()
        pp.register(a1)
        pp.register(a2, "hello")
        l = pp.getplugins()
        assert l.index(a1) < l.index(a2)
        a3 = A()
        pp.register(a3, prepend=True)
        l = pp.getplugins()
        assert l.index(a3) == 0

    def test_register_imported_modules(self):
        pp = PluginManager()
        mod = py.std.types.ModuleType("x.y.pytest_hello")
        pp.register(mod)
        assert pp.isregistered(mod)
        l = pp.getplugins()
        assert mod in l
        pytest.raises(AssertionError, "pp.register(mod)")
        mod2 = py.std.types.ModuleType("pytest_hello")
        #pp.register(mod2) # double pm
        pytest.raises(AssertionError, "pp.register(mod)")
        #assert not pp.isregistered(mod2)
        assert pp.getplugins() == l

    def test_canonical_import(self, monkeypatch):
        mod = py.std.types.ModuleType("pytest_xyz")
        monkeypatch.setitem(py.std.sys.modules, 'pytest_xyz', mod)
        pp = PluginManager()
        pp.import_plugin('pytest_xyz')
        assert pp.getplugin('pytest_xyz') == mod
        assert pp.isregistered(mod)

    def test_register_mismatch_method(self):
        pp = PluginManager(load=True)
        class hello:
            def pytest_gurgel(self):
                pass
        pytest.raises(Exception, "pp.register(hello())")

    def test_register_mismatch_arg(self):
        pp = PluginManager(load=True)
        class hello:
            def pytest_configure(self, asd):
                pass
        excinfo = pytest.raises(Exception, "pp.register(hello())")


    def test_notify_exception(self, capfd):
        pp = PluginManager()
        excinfo = pytest.raises(ValueError, "raise ValueError(1)")
        pp.notify_exception(excinfo)
        out, err = capfd.readouterr()
        assert "ValueError" in err
        class A:
            def pytest_internalerror(self, excrepr):
                return True
        pp.register(A())
        pp.notify_exception(excinfo)
        out, err = capfd.readouterr()
        assert not err

    def test_register(self):
        pm = PluginManager(load=False)
        class MyPlugin:
            pass
        my = MyPlugin()
        pm.register(my)
        assert pm.getplugins()
        my2 = MyPlugin()
        pm.register(my2)
        assert pm.getplugins()[1:] == [my, my2]

        assert pm.isregistered(my)
        assert pm.isregistered(my2)
        pm.unregister(my)
        assert not pm.isregistered(my)
        assert pm.getplugins()[1:] == [my2]

    def test_listattr(self):
        plugins = PluginManager()
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

    def test_hook_tracing(self):
        pm = PluginManager()
        saveindent = []
        class api1:
            x = 41
            def pytest_plugin_registered(self, plugin):
                saveindent.append(pm.trace.root.indent)
                raise ValueError(42)
        l = []
        pm.trace.root.setwriter(l.append)
        indent = pm.trace.root.indent
        p = api1()
        pm.register(p)

        assert pm.trace.root.indent == indent
        assert len(l) == 1
        assert 'pytest_plugin_registered' in l[0]
        pytest.raises(ValueError, lambda: pm.register(api1()))
        assert pm.trace.root.indent == indent
        assert saveindent[0] > indent

class TestPytestPluginInteractions:

    def test_addhooks_conftestplugin(self, testdir):
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
        config = testdir.Config()
        config._conftest.importconftest(conf)
        print(config.pluginmanager.getplugins())
        res = config.hook.pytest_myhook(xyz=10)
        assert res == [11]

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

    def test_namespace_early_from_import(self, testdir):
        p = testdir.makepyfile("""
            from pytest import Item
            from pytest import Item as Item2
            assert Item is Item2
        """)
        result = testdir.runpython(p)
        assert result.ret == 0

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
        config = testdir.parseconfigure()
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
        config.pluginmanager.register(A())  # leads to a configured() plugin
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

    def test_listattr_tryfirst(self):
        class P1:
            @pytest.mark.tryfirst
            def m(self):
                return 17

        class P2:
            def m(self):
                return 23
        class P3:
            def m(self):
                return 19

        pluginmanager = PluginManager()
        p1 = P1()
        p2 = P2()
        p3 = P3()
        pluginmanager.register(p1)
        pluginmanager.register(p2)
        pluginmanager.register(p3)
        methods = pluginmanager.listattr('m')
        assert methods == [p2.m, p3.m, p1.m]
        # listattr keeps a cache and deleting
        # a function attribute requires clearing it
        pluginmanager._listattrcache.clear()
        del P1.m.__dict__['tryfirst']

        pytest.mark.trylast(getattr(P2.m, 'im_func', P2.m))
        methods = pluginmanager.listattr('m')
        assert methods == [p2.m, p1.m, p3.m]


def test_namespace_has_default_and_env_plugins(testdir):
    p = testdir.makepyfile("""
        import pytest
        pytest.mark
    """)
    result = testdir.runpython(p)
    assert result.ret == 0

def test_varnames():
    def f(x):
        i = 3
    class A:
        def f(self, y):
            pass
    class B(object):
        def __call__(self, z):
            pass
    assert varnames(f) == ("x",)
    assert varnames(A().f) == ('y',)
    assert varnames(B()) == ('z',)

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

    def test_keyword_args_with_defaultargs(self):
        def f(x, z=1):
            return x + z
        reslist = MultiCall([f], dict(x=23, y=24)).execute()
        assert reslist == [24]
        reslist = MultiCall([f], dict(x=23, z=2)).execute()
        assert reslist == [25]

    def test_tags_call_error(self):
        multicall = MultiCall([lambda x: x], {})
        pytest.raises(TypeError, "multicall.execute()")

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

class TestHookRelay:
    def test_happypath(self):
        pm = PluginManager()
        class Api:
            def hello(self, arg):
                "api hook 1"

        mcm = HookRelay(hookspecs=Api, pm=pm, prefix="he")
        assert hasattr(mcm, 'hello')
        assert repr(mcm.hello).find("hello") != -1
        class Plugin:
            def hello(self, arg):
                return arg + 1
        pm.register(Plugin())
        l = mcm.hello(arg=3)
        assert l == [4]
        assert not hasattr(mcm, 'world')

    def test_only_kwargs(self):
        pm = PluginManager()
        class Api:
            def hello(self, arg):
                "api hook 1"
        mcm = HookRelay(hookspecs=Api, pm=pm, prefix="he")
        pytest.raises(TypeError, "mcm.hello(3)")

    def test_firstresult_definition(self):
        pm = PluginManager()
        class Api:
            def hello(self, arg):
                "api hook 1"
            hello.firstresult = True

        mcm = HookRelay(hookspecs=Api, pm=pm, prefix="he")
        class Plugin:
            def hello(self, arg):
                return arg + 1
        pm.register(Plugin())
        res = mcm.hello(arg=3)
        assert res == 4

class TestTracer:
    def test_simple(self):
        from _pytest.core import TagTracer
        rootlogger = TagTracer()
        log = rootlogger.get("pytest")
        log("hello")
        l = []
        rootlogger.setwriter(l.append)
        log("world")
        assert len(l) == 1
        assert l[0] == "world [pytest]\n"
        sublog = log.get("collection")
        sublog("hello")
        assert l[1] == "hello [pytest:collection]\n"

    def test_indent(self):
        from _pytest.core import TagTracer
        rootlogger = TagTracer()
        log = rootlogger.get("1")
        l = []
        log.root.setwriter(lambda arg: l.append(arg))
        log("hello")
        log.root.indent += 1
        log("line1")
        log("line2")
        log.root.indent += 1
        log("line3")
        log("line4")
        log.root.indent -= 1
        log("line5")
        log.root.indent -= 1
        log("last")
        assert len(l) == 7
        names = [x[:x.rfind(' [')] for x in l]
        assert names == ['hello', '  line1', '  line2',
                     '    line3', '    line4', '  line5', 'last']

    def test_setprocessor(self):
        from _pytest.core import TagTracer
        rootlogger = TagTracer()
        log = rootlogger.get("1")
        log2 = log.get("2")
        assert log2.tags  == tuple("12")
        l = []
        rootlogger.setprocessor(tuple("12"), lambda *args: l.append(args))
        log("not seen")
        log2("seen")
        assert len(l) == 1
        tags, args = l[0]
        assert "1" in tags
        assert "2" in tags
        assert args == ("seen",)
        l2 = []
        rootlogger.setprocessor("1:2", lambda *args: l2.append(args))
        log2("seen")
        tags, args = l2[0]
        assert args == ("seen",)


    def test_setmyprocessor(self):
        from _pytest.core import TagTracer
        rootlogger = TagTracer()
        log = rootlogger.get("1")
        log2 = log.get("2")
        l = []
        log2.setmyprocessor(lambda *args: l.append(args))
        log("not seen")
        assert not l
        log2(42)
        assert len(l) == 1
        tags, args = l[0]
        assert "1" in tags
        assert "2" in tags
        assert args == (42,)

def test_default_markers(testdir):
    result = testdir.runpytest("--markers")
    result.stdout.fnmatch_lines([
        "*tryfirst*first*",
        "*trylast*last*",
    ])
