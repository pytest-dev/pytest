
import py
import os
from py._com import PyPlugins, MultiCall
from py._com import PluginAPI

pytest_plugins = "xfail"

class TestMultiCall:
    def test_uses_copy_of_methods(self):
        l = [lambda: 42]
        mc = MultiCall(l)
        l[:] = []
        res = mc.execute()
        return res == 42

    def test_call_passing(self):
        class P1:
            def m(self, __call__, x):
                assert __call__.currentmethod == self.m 
                assert len(__call__.results) == 1
                assert not __call__.methods
                return 17

        class P2:
            def m(self, __call__, x):
                assert __call__.currentmethod == self.m 
                assert __call__.args
                assert __call__.results == []
                assert __call__.methods
                return 23 
               
        p1 = P1() 
        p2 = P2() 
        multicall = MultiCall([p1.m, p2.m], 23)
        reslist = multicall.execute()
        assert len(reslist) == 2
        # ensure reversed order 
        assert reslist == [23, 17]

    def test_optionalcallarg(self):
        class P1:
            def m(self, x):
                return x
        call = MultiCall([P1().m], 23)
        assert call.execute() == [23]
        assert call.execute(firstresult=True) == 23
 
    def test_call_subexecute(self):
        def m(__call__):
            subresult = __call__.execute(firstresult=True)
            return subresult + 1

        def n():
            return 1

        call = MultiCall([n, m])
        res = call.execute(firstresult=True)
        assert res == 2

    def test_call_exclude_other_results(self):
        def m(__call__):
            __call__.exclude_other_results()
            return 10

        def n():
            return 1

        call = MultiCall([n, n, m, n])
        res = call.execute()
        assert res == [10]
        # doesn't really make sense for firstresult-mode - because
        # we might not have had a chance to run at all. 
        #res = call.execute(firstresult=True)
        #assert res == 10
                

class TestPyPlugins:
    def test_MultiCall(self):
        plugins = PyPlugins()
        assert hasattr(plugins, "MultiCall")

    def test_register(self):
        plugins = PyPlugins()
        class MyPlugin:
            pass
        my = MyPlugin()
        plugins.register(my)
        assert plugins.getplugins() == [my]
        my2 = MyPlugin()
        plugins.register(my2)
        assert plugins.getplugins() == [my, my2]

        assert plugins.isregistered(my)
        assert plugins.isregistered(my2)
        plugins.unregister(my)
        assert not plugins.isregistered(my)
        assert plugins.getplugins() == [my2]

    def test_onregister(self):
        plugins = PyPlugins()
        l = []
        class MyApi:
            def pyevent__plugin_registered(self, plugin):
                l.append(plugin)
            def pyevent__plugin_unregistered(self, plugin):
                l.remove(plugin)
        myapi = MyApi()
        plugins.register(myapi)
        assert len(l) == 1
        assert l[0] is myapi 
        plugins.unregister(myapi)
        assert not l

    def test_call_methods(self):
        plugins = PyPlugins()
        class api1:
            def m(self, __call__, x):
                return x
        class api2:
            def m(self, __call__, x, y=33):
                return y 
        plugins.register(api1())
        plugins.register(api2())
        res = plugins.call_firstresult("m", x=5)
        assert plugins.call_firstresult("notexist") is None

        assert res == 33
        reslist = plugins.call_each("m", x=5)
        assert len(reslist) == 2
        assert 5 in reslist
        assert 33 in reslist
        assert plugins.call_each("notexist") == []

        assert plugins.call_plugin(api1(), 'm', x=12) == 12
        assert plugins.call_plugin(api2(), 't') is None

    def test_call_none_is_no_result(self):
        plugins = PyPlugins()
        class api1:
            def m(self):
                return None
        class api2:
            def m(self, __call__):
                return 41
        plugins.register(api1())
        plugins.register(api1())
        plugins.register(api2())
        assert plugins.call_firstresult('m') == 41
        assert plugins.call_each('m') == [41]

    def test_call_noneasresult(self):
        plugins = PyPlugins()
        class api1:
            def m(self, __call__):
                return __call__.NONEASRESULT
        plugins.register(api1())
        plugins.register(api1())
        assert plugins.call_firstresult('m') is None
        assert plugins.call_each('m') == [None, None]

    def test_listattr(self):
        plugins = PyPlugins()
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

    def test_notify_anonymous_ordered(self):
        plugins = PyPlugins()
        l = []
        class api1:
            def pyevent__hello(self): 
                l.append("hellospecific")
        class api2:
            def pyevent(self, name, args, kwargs): 
                if name == "hello":
                    l.append(name + "anonymous") 
        plugins.register(api1())
        plugins.register(api2())
        plugins.notify('hello')
        assert l == ["hellospecific", "helloanonymous"]

    def test_consider_env(self, monkeypatch):
        plugins = PyPlugins()
        monkeypatch.setitem(os.environ, 'PYLIB', "unknownconsider_env")
        py.test.raises(ImportError, "plugins.consider_env()")

    def test_consider_module(self):
        plugins = PyPlugins()
        mod = py.std.new.module("temp")
        mod.pylib = ["xxx nomod"]
        excinfo = py.test.raises(ImportError, "plugins.consider_module(mod)")
        mod.pylib = "os"
        class Events(list):
            def pyevent__importingmodule(self, mod):
                self.append(mod)
        l = Events()
        plugins.register(l)
        plugins.consider_module(mod)
        assert len(l) == 1
        assert l[0] == (mod.pylib)

def test_api_and_defaults():
    assert isinstance(py._com.pyplugins, PyPlugins)

def test_subprocess_env(testdir, monkeypatch):
    plugins = PyPlugins()
    old = py.path.local(py.__file__).dirpath().dirpath().chdir()
    try:
        monkeypatch.setitem(os.environ, "PYLIB", 'unknownconsider')
        excinfo = py.test.raises(py.process.cmdexec.Error, """
            py.process.cmdexec('%s -c "import py"')
        """ % py.std.sys.executable)
        assert str(excinfo.value).find("ImportError") != -1
        assert str(excinfo.value).find("unknownconsider") != -1
    finally:
        old.chdir()

class TestPyPluginsEvents:
    def test_pyevent__named_dispatch(self):
        plugins = PyPlugins()
        l = []
        class A:
            def pyevent__name(self, x): 
                l.append(x)
        plugins.register(A())
        plugins.notify("name", 13)
        assert l == [13]

    def test_pyevent__anonymous_dispatch(self):
        plugins = PyPlugins()
        l = []
        class A:
            def pyevent(self, name, args, kwargs): 
                if name == "name":
                    l.extend([args, kwargs])

        plugins.register(A())
        plugins.notify("name", 13, x=15)
        assert l == [(13, ), {'x':15}]


class TestPluginAPI:
    def test_happypath(self):
        plugins = PyPlugins()
        class Api:
            def hello(self, arg):
                pass

        mcm = PluginAPI(apiclass=Api, plugins=plugins)
        assert hasattr(mcm, 'hello')
        assert repr(mcm.hello).find("hello") != -1
        class Plugin:
            def hello(self, arg):
                return arg + 1
        plugins.register(Plugin())
        l = mcm.hello(3)
        assert l == [4]
        assert not hasattr(mcm, 'world')

    def test_firstresult(self):
        plugins = PyPlugins()
        class Api:
            def hello(self, arg): pass
            hello.firstresult = True

        mcm = PluginAPI(apiclass=Api, plugins=plugins)
        class Plugin:
            def hello(self, arg):
                return arg + 1
        plugins.register(Plugin())
        res = mcm.hello(3)
        assert res == 4

    def test_default_plugins(self):
        class Api: pass 
        mcm = PluginAPI(apiclass=Api)
        assert mcm._plugins == py._com.pyplugins
