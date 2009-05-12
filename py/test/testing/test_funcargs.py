import py
from py.__.test import funcargs

def test_getfuncargnames():
    def f(): pass
    assert not funcargs.getfuncargnames(f) 
    def g(arg): pass
    assert funcargs.getfuncargnames(g) == ['arg']
    def h(arg1, arg2="hello"): pass
    assert funcargs.getfuncargnames(h) == ['arg1']
    def h(arg1, arg2, arg3="hello"): pass
    assert funcargs.getfuncargnames(h) == ['arg1', 'arg2']
    class A:
        def f(self, arg1, arg2="hello"):
            pass
    assert funcargs.getfuncargnames(A().f) == ['arg1']
    assert funcargs.getfuncargnames(A.f) == ['arg1']

class TestFillFuncArgs:
    def test_funcarg_lookupfails(self, testdir):
        testdir.makeconftest("""
            class ConftestPlugin:
                def pytest_funcarg__xyzsomething(self, request):
                    return 42
        """)
        item = testdir.getitem("def test_func(some): pass")
        exc = py.test.raises(LookupError, "funcargs.fillfuncargs(item)")
        s = str(exc.value)
        assert s.find("xyzsomething") != -1

    def test_funcarg_lookup_default(self, testdir):
        item = testdir.getitem("def test_func(some, other=42): pass")
        class Provider:
            def pytest_funcarg__some(self, request):
                return request.function.__name__
        item.config.pluginmanager.register(Provider())
        funcargs.fillfuncargs(item)
        assert len(item.funcargs) == 1

    def test_funcarg_basic(self, testdir):
        item = testdir.getitem("def test_func(some, other): pass")
        class Provider:
            def pytest_funcarg__some(self, request):
                return request.function.__name__ 
            def pytest_funcarg__other(self, request):
                return 42
        item.config.pluginmanager.register(Provider())
        funcargs.fillfuncargs(item)
        assert len(item.funcargs) == 2
        assert item.funcargs['some'] == "test_func"
        assert item.funcargs['other'] == 42

    def test_funcarg_lookup_modulelevel(self, testdir):
        modcol = testdir.getmodulecol("""
            def pytest_funcarg__something(request):
                return request.function.__name__

            class TestClass:
                def test_method(self, something):
                    pass 
            def test_func(something):
                pass 
        """)
        item1, item2 = testdir.genitems([modcol])
        funcargs.fillfuncargs(item1)
        assert item1.funcargs['something'] ==  "test_method"
        funcargs.fillfuncargs(item2)
        assert item2.funcargs['something'] ==  "test_func"

class TestRequest:
    def test_request_attributes(self, testdir):
        item = testdir.getitem("""
            def pytest_funcarg__something(request): pass
            def test_func(something): pass
        """)
        req = funcargs.FuncargRequest(item, argname="other")
        assert req.argname == "other"
        assert req.function == item.obj 
        assert hasattr(req.module, 'test_func')
        assert req.cls is None
        assert req.function.__name__ == "test_func" 
        assert req.config == item.config 
        assert repr(req).find(req.function.__name__) != -1

    def test_request_attributes_method(self, testdir):
        item, = testdir.getitems("""
            class TestB:
                def test_func(self, something): 
                    pass
        """)
        req = funcargs.FuncargRequest(item, argname="something")
        assert req.cls.__name__ == "TestB"
        
    def test_request_contains_funcargs_provider(self, testdir):
        modcol = testdir.getmodulecol("""
            def pytest_funcarg__something(request):
                pass
            class TestClass:
                def test_method(self, something):
                    pass 
        """)
        item1, = testdir.genitems([modcol])
        assert item1.name == "test_method"
        provider = funcargs.FuncargRequest(item1, "something")._provider 
        assert len(provider) == 1
        assert provider[0].__name__ == "pytest_funcarg__something"

    def test_request_call_next_provider(self, testdir):
        item = testdir.getitem("""
            def pytest_funcarg__something(request): pass
            def test_func(something): pass
        """)
        req = funcargs.FuncargRequest(item, "something")
        val = req.call_next_provider()
        assert val is None
        py.test.raises(req.Error, "req.call_next_provider()")

    def test_request_addfinalizer(self, testdir):
        item = testdir.getitem("""
            def pytest_funcarg__something(request): pass
            def test_func(something): pass
        """)
        req = funcargs.FuncargRequest(item, "something")
        l = [1]
        req.addfinalizer(l.pop)
        item.teardown()

    def test_request_getmodulepath(self, testdir):
        modcol = testdir.getmodulecol("def test_somefunc(): pass")
        item, = testdir.genitems([modcol])
        req = funcargs.FuncargRequest(item, "xxx")
        assert req.fspath == modcol.fspath 

class TestMetafunc:
    def test_no_funcargs(self, testdir):
        def function(): pass
        metafunc = funcargs.Metafunc(function)
        assert not metafunc.funcargnames

    def test_function_basic(self):
        def func(arg1, arg2="qwe"): pass
        metafunc = funcargs.Metafunc(func)
        assert len(metafunc.funcargnames) == 1
        assert 'arg1' in metafunc.funcargnames
        assert metafunc.function is func 
        assert metafunc.cls is None

    def test_addcall_no_args(self):
        def func(arg1): pass
        metafunc = funcargs.Metafunc(func)
        metafunc.addcall()
        assert len(metafunc._calls) == 1
        call = metafunc._calls[0]
        assert call.id == "0"
        assert not hasattr(call, 'param')

    def test_addcall_id(self):
        def func(arg1): pass
        metafunc = funcargs.Metafunc(func)
        metafunc.addcall(id=1)
        py.test.raises(ValueError, "metafunc.addcall(id=1)")
        py.test.raises(ValueError, "metafunc.addcall(id='1')")
        metafunc.addcall(id=2)
        assert len(metafunc._calls) == 2
        assert metafunc._calls[0].id == "1"
        assert metafunc._calls[1].id == "2"

    def test_addcall_param(self):
        def func(arg1): pass
        metafunc = funcargs.Metafunc(func)
        class obj: pass 
        metafunc.addcall(param=obj) 
        metafunc.addcall(param=obj) 
        metafunc.addcall(param=1) 
        assert len(metafunc._calls) == 3
        assert metafunc._calls[0].param == obj 
        assert metafunc._calls[1].param == obj 
        assert metafunc._calls[2].param == 1


class TestGenfuncFunctional:
    def test_attributes(self, testdir):
        p = testdir.makepyfile("""
            # assumes that generate/provide runs in the same process
            import py
            def pytest_generate_tests(metafunc):
                metafunc.addcall(param=metafunc) 

            def pytest_funcarg__metafunc(request):
                return request.param 

            def test_function(metafunc):
                assert metafunc.config == py.test.config
                assert metafunc.module.__name__ == __name__
                assert metafunc.function == test_function
                assert metafunc.cls is None

            class TestClass:
                def test_method(self, metafunc):
                    assert metafunc.config == py.test.config
                    assert metafunc.module.__name__ == __name__
                    # XXX actually have an unbound test function here?
                    assert metafunc.function == TestClass.test_method.im_func
                    assert metafunc.cls == TestClass
        """)
        result = testdir.runpytest(p, "-v")
        result.stdout.fnmatch_lines([
            "*2 passed in*",
        ])

    def test_two_functions(self, testdir):
        p = testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.addcall(param=10)
                metafunc.addcall(param=20) 

            def pytest_funcarg__arg1(request):
                return request.param

            def test_func1(arg1):
                assert arg1 == 10
            def test_func2(arg1):
                assert arg1 in (10, 20)
        """)
        result = testdir.runpytest("-v", p)
        assert result.stdout.fnmatch_lines([
            "*test_func1*0*PASS*", 
            "*test_func1*1*FAIL*", 
            "*test_func2*PASS*",
            "*1 failed, 3 passed*"
        ])

    def test_generate_plugin_and_module(self, testdir):
        testdir.makeconftest("""
            class ConftestPlugin:
                def pytest_generate_tests(self, metafunc):
                    assert "arg1" in metafunc.funcargnames 
                    metafunc.addcall(id="world", param=(2,100))
        """)
        p = testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.addcall(param=(1,1), id="hello")

            def pytest_funcarg__arg1(request):
                return request.param[0]
            def pytest_funcarg__arg2(request):
                return request.param[1]

            class TestClass:
                def test_myfunc(self, arg1, arg2):
                    assert arg1 == arg2 
        """)
        result = testdir.runpytest("-v", p)
        assert result.stdout.fnmatch_lines([
            "*test_myfunc*hello*PASS*", 
            "*test_myfunc*world*FAIL*", 
            "*1 failed, 1 passed*"
        ])
