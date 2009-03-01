
import py
import os
from py._com import PyPlugins, MultiCall

pytest_plugins = "xfail"

class TestMultiCall:
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
            def pyevent_plugin_registered(self, plugin):
                l.append(plugin)
            def pyevent_plugin_unregistered(self, plugin):
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
            x = 42
        class api2:
            x = 41
        plugins.register(api1())
        plugins.register(api2())
        l = list(plugins.listattr('x'))
        l.sort()
        assert l == [41, 42]

    def test_notify_anonymous_ordered(self):
        plugins = PyPlugins()
        l = []
        class api1:
            def pyevent_hello(self): 
                l.append("hellospecific")
        class api2:
            def pyevent(self, name, *args): 
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
            def pyevent_importingmodule(self, mod):
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
            py.process.cmdexec("python -c 'import py'")
        """)
        assert str(excinfo.value).find("ImportError") != -1
        assert str(excinfo.value).find("unknownconsider") != -1
    finally:
        old.chdir()

class TestPyPluginsEvents:
    def test_pyevent_named_dispatch(self):
        plugins = PyPlugins()
        l = []
        class A:
            def pyevent_name(self, x): 
                l.append(x)
        plugins.register(A())
        plugins.notify("name", 13)
        assert l == [13]

    def test_pyevent_anonymous_dispatch(self):
        plugins = PyPlugins()
        l = []
        class A:
            def pyevent(self, name, *args, **kwargs): 
                if name == "name":
                    l.extend([args, kwargs])

        plugins.register(A())
        plugins.notify("name", 13, x=15)
        assert l == [(13, ), {'x':15}]

