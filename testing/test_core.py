import pytest, py, os
from _pytest.core import * # noqa
from _pytest.config import get_config


@pytest.fixture
def pm():
    return PluginManager("he")

@pytest.fixture
def pytestpm():
    return PytestPluginManager()


class TestPluginManager:
    def test_plugin_double_register(self, pm):
        pm.register(42, name="abc")
        with pytest.raises(ValueError):
            pm.register(42, name="abc")
        with pytest.raises(ValueError):
            pm.register(42, name="def")

    def test_pm(self, pm):
        class A: pass
        a1, a2 = A(), A()
        pm.register(a1)
        assert pm.is_registered(a1)
        pm.register(a2, "hello")
        assert pm.is_registered(a2)
        l = pm.get_plugins()
        assert a1 in l
        assert a2 in l
        assert pm.get_plugin('hello') == a2
        assert pm.unregister(a1) == a1
        assert not pm.is_registered(a1)

    def test_pm_name(self, pm):
        class A: pass
        a1 = A()
        name = pm.register(a1, name="hello")
        assert name == "hello"
        pm.unregister(a1)
        assert pm.get_plugin(a1) is None
        assert not pm.is_registered(a1)
        assert not pm.get_plugins()
        name2 = pm.register(a1, name="hello")
        assert name2 == name
        pm.unregister(name="hello")
        assert pm.get_plugin(a1) is None
        assert not pm.is_registered(a1)
        assert not pm.get_plugins()

    def test_set_blocked(self, pm):
        class A: pass
        a1 = A()
        name = pm.register(a1)
        assert pm.is_registered(a1)
        pm.set_blocked(name)
        assert not pm.is_registered(a1)

        pm.set_blocked("somename")
        assert not pm.register(A(), "somename")
        pm.unregister(name="somename")

    def test_register_mismatch_method(self, pytestpm):
        class hello:
            def pytest_gurgel(self):
                pass
        pytestpm.register(hello())
        with pytest.raises(PluginValidationError):
            pytestpm.check_pending()

    def test_register_mismatch_arg(self):
        pm = get_config().pluginmanager
        class hello:
            def pytest_configure(self, asd):
                pass
        pytest.raises(Exception, lambda: pm.register(hello()))

    def test_register(self):
        pm = get_config().pluginmanager
        class MyPlugin:
            pass
        my = MyPlugin()
        pm.register(my)
        assert pm.get_plugins()
        my2 = MyPlugin()
        pm.register(my2)
        assert set([my,my2]).issubset(pm.get_plugins())

        assert pm.is_registered(my)
        assert pm.is_registered(my2)
        pm.unregister(my)
        assert not pm.is_registered(my)
        assert my not in pm.get_plugins()

    def test_register_unknown_hooks(self, pm):
        class Plugin1:
            def he_method1(self, arg):
                return arg + 1

        pm.register(Plugin1())
        class Hooks:
            def he_method1(self, arg):
                pass
        pm.addhooks(Hooks)
        #assert not pm._unverified_hooks
        assert pm.hook.he_method1(arg=1) == [2]

    def test_register_historic(self, pm):
        class Hooks:
            @hookspec_opts(historic=True)
            def he_method1(self, arg):
                pass
        pm.addhooks(Hooks)

        pm.hook.he_method1.call_historic(kwargs=dict(arg=1))
        l = []
        class Plugin:
            def he_method1(self, arg):
                l.append(arg)

        pm.register(Plugin())
        assert l == [1]

        class Plugin2:
            def he_method1(self, arg):
                l.append(arg*10)
        pm.register(Plugin2())
        assert l == [1, 10]
        pm.hook.he_method1.call_historic(kwargs=dict(arg=12))
        assert l == [1, 10, 120, 12]

    def test_with_result_memorized(self, pm):
        class Hooks:
            @hookspec_opts(historic=True)
            def he_method1(self, arg):
                pass
        pm.addhooks(Hooks)

        he_method1 = pm.hook.he_method1
        he_method1.call_historic(lambda res: l.append(res), dict(arg=1))
        l = []
        class Plugin:
            def he_method1(self, arg):
                return arg * 10

        pm.register(Plugin())
        assert l == [10]

    def test_register_historic_incompat_hookwrapper(self, pm):
        class Hooks:
            @hookspec_opts(historic=True)
            def he_method1(self, arg):
                pass
        pm.addhooks(Hooks)

        l = []
        class Plugin:
            @hookimpl_opts(hookwrapper=True)
            def he_method1(self, arg):
                l.append(arg)

        with pytest.raises(PluginValidationError):
            pm.register(Plugin())

    def test_call_extra(self, pm):
        class Hooks:
            def he_method1(self, arg):
                pass
        pm.addhooks(Hooks)

        def he_method1(arg):
            return arg * 10

        l = pm.hook.he_method1.call_extra([he_method1], dict(arg=1))
        assert l == [10]

    def test_subset_hook_caller(self, pm):
        class Hooks:
            def he_method1(self, arg):
                pass
        pm.addhooks(Hooks)

        l = []
        class Plugin1:
            def he_method1(self, arg):
                l.append(arg)
        class Plugin2:
            def he_method1(self, arg):
                l.append(arg*10)
        class PluginNo:
            pass

        plugin1, plugin2, plugin3 = Plugin1(), Plugin2(), PluginNo()
        pm.register(plugin1)
        pm.register(plugin2)
        pm.register(plugin3)
        pm.hook.he_method1(arg=1)
        assert l == [10, 1]
        l[:] = []

        hc = pm.subset_hook_caller("he_method1", [plugin1])
        hc(arg=2)
        assert l == [20]
        l[:] = []

        hc = pm.subset_hook_caller("he_method1", [plugin2])
        hc(arg=2)
        assert l == [2]
        l[:] = []

        pm.unregister(plugin1)
        hc(arg=2)
        assert l == []
        l[:] = []

        pm.hook.he_method1(arg=1)
        assert l == [10]



class TestAddMethodOrdering:
    @pytest.fixture
    def hc(self, pm):
        class Hooks:
            def he_method1(self, arg):
                pass
        pm.addhooks(Hooks)
        return pm.hook.he_method1

    @pytest.fixture
    def addmeth(self, hc):
        def addmeth(tryfirst=False, trylast=False, hookwrapper=False):
            def wrap(func):
                if tryfirst:
                    func.tryfirst = True
                if trylast:
                    func.trylast = True
                if hookwrapper:
                    func.hookwrapper = True
                hc._add_method(func)
                return func
            return wrap
        return addmeth

    def test_adding_nonwrappers(self, hc, addmeth):
        @addmeth()
        def he_method1():
            pass

        @addmeth()
        def he_method2():
            pass

        @addmeth()
        def he_method3():
            pass
        assert hc._nonwrappers == [he_method1, he_method2, he_method3]

    def test_adding_nonwrappers_trylast(self, hc, addmeth):
        @addmeth()
        def he_method1_middle():
            pass

        @addmeth(trylast=True)
        def he_method1():
            pass

        @addmeth()
        def he_method1_b():
            pass
        assert hc._nonwrappers == [he_method1, he_method1_middle, he_method1_b]

    def test_adding_nonwrappers_trylast3(self, hc, addmeth):
        @addmeth()
        def he_method1_a():
            pass

        @addmeth(trylast=True)
        def he_method1_b():
            pass

        @addmeth()
        def he_method1_c():
            pass

        @addmeth(trylast=True)
        def he_method1_d():
            pass
        assert hc._nonwrappers == [he_method1_d, he_method1_b,
                                   he_method1_a, he_method1_c]


    def test_adding_nonwrappers_trylast2(self, hc, addmeth):
        @addmeth()
        def he_method1_middle():
            pass

        @addmeth()
        def he_method1_b():
            pass

        @addmeth(trylast=True)
        def he_method1():
            pass
        assert hc._nonwrappers == [he_method1, he_method1_middle, he_method1_b]

    def test_adding_nonwrappers_tryfirst(self, hc, addmeth):
        @addmeth(tryfirst=True)
        def he_method1():
            pass

        @addmeth()
        def he_method1_middle():
            pass

        @addmeth()
        def he_method1_b():
            pass
        assert hc._nonwrappers == [he_method1_middle, he_method1_b, he_method1]

    def test_adding_wrappers_ordering(self, hc, addmeth):
        @addmeth(hookwrapper=True)
        def he_method1():
            pass

        @addmeth()
        def he_method1_middle():
            pass

        @addmeth(hookwrapper=True)
        def he_method3():
            pass

        assert hc._nonwrappers == [he_method1_middle]
        assert hc._wrappers == [he_method1, he_method3]

    def test_hookspec_opts(self, pm):
        class HookSpec:
            @hookspec_opts()
            def he_myhook1(self, arg1):
                pass

            @hookspec_opts(firstresult=True)
            def he_myhook2(self, arg1):
                pass

            @hookspec_opts(firstresult=False)
            def he_myhook3(self, arg1):
                pass

        pm.addhooks(HookSpec)
        assert not pm.hook.he_myhook1.firstresult
        assert pm.hook.he_myhook2.firstresult
        assert not pm.hook.he_myhook3.firstresult


    def test_hookimpl_opts(self):
        for name in ["hookwrapper", "optionalhook", "tryfirst", "trylast"]:
            for val in [True, False]:
                @hookimpl_opts(**{name: val})
                def he_myhook1(self, arg1):
                    pass
                if val:
                    assert getattr(he_myhook1, name)
                else:
                    assert not hasattr(he_myhook1, name)

    def test_decorator_functional(self, pm):
        class HookSpec:
            @hookspec_opts(firstresult=True)
            def he_myhook(self, arg1):
                """ add to arg1 """
        pm.addhooks(HookSpec)

        class Plugin:
            @hookimpl_opts()
            def he_myhook(self, arg1):
                return arg1 + 1

        pm.register(Plugin())
        results = pm.hook.he_myhook(arg1=17)
        assert results == 18


class TestPytestPluginInteractions:

    def test_addhooks_conftestplugin(self, testdir):
        testdir.makepyfile(newhooks="""
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
        config = get_config()
        pm = config.pluginmanager
        pm.hook.pytest_addhooks.call_historic(
                                kwargs=dict(pluginmanager=config.pluginmanager))
        config.pluginmanager._importconftest(conf)
        #print(config.pluginmanager.get_plugins())
        res = config.hook.pytest_myhook(xyz=10)
        assert res == [11]

    def test_addhooks_nohooks(self, testdir):
        testdir.makeconftest("""
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
            from pytest import hello
            import pytest
            def test_hello():
                assert hello == "world"
                assert 'hello' in pytest.__all__
        """)
        reprec = testdir.inline_run(p)
        reprec.assertoutcome(passed=1)

    def test_do_option_postinitialize(self, testdir):
        config = testdir.parseconfigure()
        assert not hasattr(config.option, 'test123')
        p = testdir.makepyfile("""
            def pytest_addoption(parser):
                parser.addoption('--test123', action="store_true",
                    default=True)
        """)
        config.pluginmanager._importconftest(p)
        assert config.option.test123

    def test_configure(self, testdir):
        config = testdir.parseconfig()
        l = []
        class A:
            def pytest_configure(self, config):
                l.append(self)

        config.pluginmanager.register(A())
        assert len(l) == 0
        config._do_configure()
        assert len(l) == 1
        config.pluginmanager.register(A())  # leads to a configured() plugin
        assert len(l) == 2
        assert l[0] != l[1]

        config._ensure_unconfigure()
        config.pluginmanager.register(A())
        assert len(l) == 2

    def test_hook_tracing(self):
        pytestpm = get_config().pluginmanager  # fully initialized with plugins
        saveindent = []
        class api1:
            def pytest_plugin_registered(self):
                saveindent.append(pytestpm.trace.root.indent)
        class api2:
            def pytest_plugin_registered(self):
                saveindent.append(pytestpm.trace.root.indent)
                raise ValueError()
        l = []
        pytestpm.trace.root.setwriter(l.append)
        undo = pytestpm.enable_tracing()
        try:
            indent = pytestpm.trace.root.indent
            p = api1()
            pytestpm.register(p)
            assert pytestpm.trace.root.indent == indent
            assert len(l) >= 2
            assert 'pytest_plugin_registered' in l[0]
            assert 'finish' in l[1]

            l[:] = []
            with pytest.raises(ValueError):
                pytestpm.register(api2())
            assert pytestpm.trace.root.indent == indent
            assert saveindent[0] > indent
        finally:
            undo()


def test_namespace_has_default_and_env_plugins(testdir):
    p = testdir.makepyfile("""
        import pytest
        pytest.mark
    """)
    result = testdir.runpython(p)
    assert result.ret == 0

def test_varnames():
    def f(x):
        i = 3  # noqa
    class A:
        def f(self, y):
            pass
    class B(object):
        def __call__(self, z):
            pass
    assert varnames(f) == ("x",)
    assert varnames(A().f) == ('y',)
    assert varnames(B()) == ('z',)

def test_varnames_default():
    def f(x, y=3):
        pass
    assert varnames(f) == ("x",)

def test_varnames_class():
    class C:
        def __init__(self, x):
            pass
    class D:
        pass
    assert varnames(C) == ("x",)
    assert varnames(D) == ()

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

    def test_tags_call_error(self):
        multicall = MultiCall([lambda x: x], {})
        pytest.raises(KeyError, multicall.execute)

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

    def test_hookwrapper(self):
        l = []
        def m1():
            l.append("m1 init")
            yield None
            l.append("m1 finish")
        m1.hookwrapper = True

        def m2():
            l.append("m2")
            return 2
        res = MultiCall([m2, m1], {}).execute()
        assert res == [2]
        assert l == ["m1 init", "m2", "m1 finish"]
        l[:] = []
        res = MultiCall([m2, m1], {}, firstresult=True).execute()
        assert res == 2
        assert l == ["m1 init", "m2", "m1 finish"]

    def test_hookwrapper_order(self):
        l = []
        def m1():
            l.append("m1 init")
            yield 1
            l.append("m1 finish")
        m1.hookwrapper = True

        def m2():
            l.append("m2 init")
            yield 2
            l.append("m2 finish")
        m2.hookwrapper = True
        res = MultiCall([m2, m1], {}).execute()
        assert res == []
        assert l == ["m1 init", "m2 init", "m2 finish", "m1 finish"]

    def test_hookwrapper_not_yield(self):
        def m1():
            pass
        m1.hookwrapper = True

        mc = MultiCall([m1], {})
        with pytest.raises(TypeError):
            mc.execute()

    def test_hookwrapper_too_many_yield(self):
        def m1():
            yield 1
            yield 2
        m1.hookwrapper = True

        mc = MultiCall([m1], {})
        with pytest.raises(RuntimeError) as ex:
            mc.execute()
        assert "m1" in str(ex.value)
        assert "test_core.py:" in str(ex.value)

    @pytest.mark.parametrize("exc", [ValueError, SystemExit])
    def test_hookwrapper_exception(self, exc):
        l = []
        def m1():
            l.append("m1 init")
            yield None
            l.append("m1 finish")
        m1.hookwrapper = True

        def m2():
            raise exc
        with pytest.raises(exc):
            MultiCall([m2, m1], {}).execute()
        assert l == ["m1 init", "m1 finish"]


class TestHookRelay:
    def test_hapmypath(self):
        class Api:
            def hello(self, arg):
                "api hook 1"
        pm = PluginManager("he")
        pm.addhooks(Api)
        hook = pm.hook
        assert hasattr(hook, 'hello')
        assert repr(hook.hello).find("hello") != -1
        class Plugin:
            def hello(self, arg):
                return arg + 1
        plugin = Plugin()
        pm.register(plugin)
        l = hook.hello(arg=3)
        assert l == [4]
        assert not hasattr(hook, 'world')
        pm.unregister(plugin)
        assert hook.hello(arg=3) == []

    def test_argmismatch(self):
        class Api:
            def hello(self, arg):
                "api hook 1"
        pm = PluginManager("he")
        pm.addhooks(Api)
        class Plugin:
            def hello(self, argwrong):
                return arg + 1
        with pytest.raises(PluginValidationError) as exc:
            pm.register(Plugin())
        assert "argwrong" in str(exc.value)

    def test_only_kwargs(self):
        pm = PluginManager("he")
        class Api:
            def hello(self, arg):
                "api hook 1"
        pm.addhooks(Api)
        pytest.raises(TypeError, lambda: pm.hook.hello(3))

    def test_firstresult_definition(self):
        class Api:
            def hello(self, arg):
                "api hook 1"
            hello.firstresult = True
        pm = PluginManager("he")
        pm.addhooks(Api)
        class Plugin:
            def hello(self, arg):
                return arg + 1
        pm.register(Plugin())
        res = pm.hook.hello(arg=3)
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

    def test_readable_output_dictargs(self):
        from _pytest.core import TagTracer
        rootlogger = TagTracer()

        out = rootlogger.format_message(['test'], [1])
        assert out == ['1 [test]\n']

        out2= rootlogger.format_message(['test'], ['test', {'a':1}])
        assert out2 ==[
            'test [test]\n',
            '    a: 1\n'
        ]

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

def test_importplugin_issue375(testdir, pytestpm):
    testdir.syspathinsert(testdir.tmpdir)
    testdir.makepyfile(qwe="import aaaa")
    with pytest.raises(ImportError) as excinfo:
        pytestpm.import_plugin("qwe")
    assert "qwe" not in str(excinfo.value)
    assert "aaaa" in str(excinfo.value)


### to be shifted to own test file
from _pytest.config import PytestPluginManager

class TestPytestPluginManager:
    def test_register_imported_modules(self):
        pm = PytestPluginManager()
        mod = py.std.types.ModuleType("x.y.pytest_hello")
        pm.register(mod)
        assert pm.is_registered(mod)
        l = pm.get_plugins()
        assert mod in l
        pytest.raises(ValueError, "pm.register(mod)")
        pytest.raises(ValueError, lambda: pm.register(mod))
        #assert not pm.is_registered(mod2)
        assert pm.get_plugins() == l

    def test_canonical_import(self, monkeypatch):
        mod = py.std.types.ModuleType("pytest_xyz")
        monkeypatch.setitem(py.std.sys.modules, 'pytest_xyz', mod)
        pm = PytestPluginManager()
        pm.import_plugin('pytest_xyz')
        assert pm.get_plugin('pytest_xyz') == mod
        assert pm.is_registered(mod)

    def test_consider_module(self, testdir, pytestpm):
        testdir.syspathinsert()
        testdir.makepyfile(pytest_p1="#")
        testdir.makepyfile(pytest_p2="#")
        mod = py.std.types.ModuleType("temp")
        mod.pytest_plugins = ["pytest_p1", "pytest_p2"]
        pytestpm.consider_module(mod)
        assert pytestpm.get_plugin("pytest_p1").__name__ == "pytest_p1"
        assert pytestpm.get_plugin("pytest_p2").__name__ == "pytest_p2"

    def test_consider_module_import_module(self, testdir):
        pytestpm = get_config().pluginmanager
        mod = py.std.types.ModuleType("x")
        mod.pytest_plugins = "pytest_a"
        aplugin = testdir.makepyfile(pytest_a="#")
        reprec = testdir.make_hook_recorder(pytestpm)
        #syspath.prepend(aplugin.dirpath())
        py.std.sys.path.insert(0, str(aplugin.dirpath()))
        pytestpm.consider_module(mod)
        call = reprec.getcall(pytestpm.hook.pytest_plugin_registered.name)
        assert call.plugin.__name__ == "pytest_a"

        # check that it is not registered twice
        pytestpm.consider_module(mod)
        l = reprec.getcalls("pytest_plugin_registered")
        assert len(l) == 1

    def test_consider_env_fails_to_import(self, monkeypatch, pytestpm):
        monkeypatch.setenv('PYTEST_PLUGINS', 'nonexisting', prepend=",")
        with pytest.raises(ImportError):
            pytestpm.consider_env()

    def test_plugin_skip(self, testdir, monkeypatch):
        p = testdir.makepyfile(skipping1="""
            import pytest
            pytest.skip("hello")
        """)
        p.copy(p.dirpath("skipping2.py"))
        monkeypatch.setenv("PYTEST_PLUGINS", "skipping2")
        result = testdir.runpytest("-rw", "-p", "skipping1", "--traceconfig")
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            "WI1*skipped plugin*skipping1*hello*",
            "WI1*skipped plugin*skipping2*hello*",
        ])

    def test_consider_env_plugin_instantiation(self, testdir, monkeypatch, pytestpm):
        testdir.syspathinsert()
        testdir.makepyfile(xy123="#")
        monkeypatch.setitem(os.environ, 'PYTEST_PLUGINS', 'xy123')
        l1 = len(pytestpm.get_plugins())
        pytestpm.consider_env()
        l2 = len(pytestpm.get_plugins())
        assert l2 == l1 + 1
        assert pytestpm.get_plugin('xy123')
        pytestpm.consider_env()
        l3 = len(pytestpm.get_plugins())
        assert l2 == l3

    def test_consider_setuptools_instantiation(self, monkeypatch, pytestpm):
        pkg_resources = pytest.importorskip("pkg_resources")
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
        pytestpm.consider_setuptools_entrypoints()
        plugin = pytestpm.get_plugin("pytest_mytestplugin")
        assert plugin.x == 42

    def test_consider_setuptools_not_installed(self, monkeypatch, pytestpm):
        monkeypatch.setitem(py.std.sys.modules, 'pkg_resources',
            py.std.types.ModuleType("pkg_resources"))
        pytestpm.consider_setuptools_entrypoints()
        # ok, we did not explode

    def test_pluginmanager_ENV_startup(self, testdir, monkeypatch):
        testdir.makepyfile(pytest_x500="#")
        p = testdir.makepyfile("""
            import pytest
            def test_hello(pytestconfig):
                plugin = pytestconfig.pluginmanager.get_plugin('pytest_x500')
                assert plugin is not None
        """)
        monkeypatch.setenv('PYTEST_PLUGINS', 'pytest_x500', prepend=",")
        result = testdir.runpytest(p)
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*1 passed in*"])

    def test_import_plugin_importname(self, testdir, pytestpm):
        pytest.raises(ImportError, 'pytestpm.import_plugin("qweqwex.y")')
        pytest.raises(ImportError, 'pytestpm.import_plugin("pytest_qweqwx.y")')

        testdir.syspathinsert()
        pluginname = "pytest_hello"
        testdir.makepyfile(**{pluginname: ""})
        pytestpm.import_plugin("pytest_hello")
        len1 = len(pytestpm.get_plugins())
        pytestpm.import_plugin("pytest_hello")
        len2 = len(pytestpm.get_plugins())
        assert len1 == len2
        plugin1 = pytestpm.get_plugin("pytest_hello")
        assert plugin1.__name__.endswith('pytest_hello')
        plugin2 = pytestpm.get_plugin("pytest_hello")
        assert plugin2 is plugin1

    def test_import_plugin_dotted_name(self, testdir, pytestpm):
        pytest.raises(ImportError, 'pytestpm.import_plugin("qweqwex.y")')
        pytest.raises(ImportError, 'pytestpm.import_plugin("pytest_qweqwex.y")')

        testdir.syspathinsert()
        testdir.mkpydir("pkg").join("plug.py").write("x=3")
        pluginname = "pkg.plug"
        pytestpm.import_plugin(pluginname)
        mod = pytestpm.get_plugin("pkg.plug")
        assert mod.x == 3

    def test_consider_conftest_deps(self, testdir, pytestpm):
        mod = testdir.makepyfile("pytest_plugins='xyz'").pyimport()
        with pytest.raises(ImportError):
            pytestpm.consider_conftest(mod)


class TestPytestPluginManagerBootstrapming:
    def test_preparse_args(self, pytestpm):
        pytest.raises(ImportError, lambda:
            pytestpm.consider_preparse(["xyz", "-p", "hello123"]))

    def test_plugin_prevent_register(self, pytestpm):
        pytestpm.consider_preparse(["xyz", "-p", "no:abc"])
        l1 = pytestpm.get_plugins()
        pytestpm.register(42, name="abc")
        l2 = pytestpm.get_plugins()
        assert len(l2) == len(l1)
        assert 42 not in l2

    def test_plugin_prevent_register_unregistered_alredy_registered(self, pytestpm):
        pytestpm.register(42, name="abc")
        l1 = pytestpm.get_plugins()
        assert 42 in l1
        pytestpm.consider_preparse(["xyz", "-p", "no:abc"])
        l2 = pytestpm.get_plugins()
        assert 42 not in l2
