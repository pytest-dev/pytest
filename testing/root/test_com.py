
import py
import os
from py.__._com import Registry, MultiCall, HookRelay, varnames

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

        class api4: 
            x = 44
        l = list(plugins.listattr('x', extra=(api4,)))
        assert l == [41,42,43,44]
        assert len(list(plugins)) == 3  # otherwise extra added

def test_api_and_defaults():
    assert isinstance(py._com.comregistry, Registry)

class TestHookRelay:
    def test_happypath(self):
        registry = Registry()
        class Api:
            def hello(self, arg):
                pass

        mcm = HookRelay(hookspecs=Api, registry=registry)
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
                pass
        mcm = HookRelay(hookspecs=Api, registry=registry)
        py.test.raises(TypeError, "mcm.hello(3)")

    def test_firstresult_definition(self):
        registry = Registry()
        class Api:
            def hello(self, arg): pass
            hello.firstresult = True

        mcm = HookRelay(hookspecs=Api, registry=registry)
        class Plugin:
            def hello(self, arg):
                return arg + 1
        registry.register(Plugin())
        res = mcm.hello(arg=3)
        assert res == 4

    def test_default_plugins(self):
        class Api: pass 
        mcm = HookRelay(hookspecs=Api, registry=py._com.comregistry)
        assert mcm._registry == py._com.comregistry

    def test_hooks_extra_plugins(self):
        registry = Registry()
        class Api:
            def hello(self, arg):
                pass
        hookrelay = HookRelay(hookspecs=Api, registry=registry)
        hook_hello = hookrelay.hello
        class Plugin:
            def hello(self, arg):
                return arg + 1
        registry.register(Plugin())
        class Plugin2:
            def hello(self, arg):
                return arg + 2
        newhook = hookrelay._makecall("hello", extralookup=Plugin2())
        l = newhook(arg=3)
        assert l == [5, 4]
        l2 = hook_hello(arg=3)
        assert l2 == [4]
        
