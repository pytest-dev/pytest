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
            def pytest_funcarg__xyzsomething(request):
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

    def test_funcarg_lookup_classlevel(self, testdir):
        p = testdir.makepyfile("""
            class TestClass:
                def pytest_funcarg__something(self, request):
                    return request.instance 
                def test_method(self, something):
                    assert something is self 
        """)
        result = testdir.runpytest(p)
        assert result.stdout.fnmatch_lines([
            "*1 passed*"
        ])

    def test_fillfuncargs_exposed(self, testdir):
        item = testdir.getitem("def test_func(some, other=42): pass")
        class Provider:
            def pytest_funcarg__some(self, request):
                return request.function.__name__
        item.config.pluginmanager.register(Provider())
        if hasattr(item, '_args'):
            del item._args
        py.test.collect._fillfuncargs(item)
        assert len(item.funcargs) == 1

class TestRequest:
    def test_request_attributes(self, testdir):
        item = testdir.getitem("""
            def pytest_funcarg__something(request): pass
            def test_func(something): pass
        """)
        req = funcargs.FuncargRequest(item)
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
        req = funcargs.FuncargRequest(item)
        assert req.cls.__name__ == "TestB"
        assert req.instance.__class__ == req.cls

    def XXXtest_request_contains_funcargs_provider(self, testdir):
        modcol = testdir.getmodulecol("""
            def pytest_funcarg__something(request):
                pass
            class TestClass:
                def test_method(self, something):
                    pass
        """)
        item1, = testdir.genitems([modcol])
        assert item1.name == "test_method"
        provider = funcargs.FuncargRequest(item1)._provider
        assert len(provider) == 1
        assert provider[0].__name__ == "pytest_funcarg__something"

    def test_getfuncargvalue_recursive(self, testdir):
        testdir.makeconftest("""
            def pytest_funcarg__something(request):
                return 1
        """)
        item = testdir.getitem("""
            def pytest_funcarg__something(request):
                return request.getfuncargvalue("something") + 1
            def test_func(something): 
                assert something == 2
        """)
        req = funcargs.FuncargRequest(item)
        val = req.getfuncargvalue("something") 
        assert val == 2

    def test_getfuncargvalue(self, testdir):
        item = testdir.getitem("""
            l = [2]
            def pytest_funcarg__something(request): return 1
            def pytest_funcarg__other(request): 
                return l.pop()
            def test_func(something): pass
        """)
        req = funcargs.FuncargRequest(item)
        py.test.raises(req.Error, req.getfuncargvalue, "notexists")
        val = req.getfuncargvalue("something") 
        assert val == 1
        val = req.getfuncargvalue("something") 
        assert val == 1
        val2 = req.getfuncargvalue("other")
        assert val2 == 2 
        val2 = req.getfuncargvalue("other")  # see about caching
        assert val2 == 2
        req._fillfuncargs()
        assert item.funcargs == {'something': 1}

    def test_request_addfinalizer(self, testdir):
        item = testdir.getitem("""
            teardownlist = []
            def pytest_funcarg__something(request): 
                request.addfinalizer(lambda: teardownlist.append(1))
            def test_func(something): pass
        """)
        req = funcargs.FuncargRequest(item)
        req.config._setupstate.prepare(item) # XXX 
        req._fillfuncargs()
        # successively check finalization calls 
        teardownlist = item.getparent(py.test.collect.Module).obj.teardownlist 
        ss = item.config._setupstate
        assert not teardownlist 
        ss.teardown_exact(item) 
        print ss.stack
        assert teardownlist == [1]

    def test_request_addfinalizer_partial_setup_failure(self, testdir):
        p = testdir.makepyfile("""
            l = []
            def pytest_funcarg__something(request): 
                request.addfinalizer(lambda: l.append(None))
            def test_func(something, missingarg): 
                pass
            def test_second():
                assert len(l) == 1
        """)
        result = testdir.runpytest(p)
        assert result.stdout.fnmatch_lines([
            "*1 passed*1 error*"
            ])

    def test_request_getmodulepath(self, testdir):
        modcol = testdir.getmodulecol("def test_somefunc(): pass")
        item, = testdir.genitems([modcol])
        req = funcargs.FuncargRequest(item)
        assert req.fspath == modcol.fspath 

class TestRequestCachedSetup:
    def test_request_cachedsetup(self, testdir):
        item1,item2 = testdir.getitems("""
            class TestClass:
                def test_func1(self, something): 
                    pass
                def test_func2(self, something): 
                    pass
        """)
        req1 = funcargs.FuncargRequest(item1)
        l = ["hello"]
        def setup():
            return l.pop()
        ret1 = req1.cached_setup(setup)
        assert ret1 == "hello"
        ret1b = req1.cached_setup(setup)
        assert ret1 == ret1b
        req2 = funcargs.FuncargRequest(item2)
        ret2 = req2.cached_setup(setup)
        assert ret2 == ret1

    def test_request_cachedsetup_extrakey(self, testdir):
        item1 = testdir.getitem("def test_func(): pass")
        req1 = funcargs.FuncargRequest(item1)
        l = ["hello", "world"]
        def setup():
            return l.pop()
        ret1 = req1.cached_setup(setup, extrakey=1)
        ret2 = req1.cached_setup(setup, extrakey=2)
        assert ret2 == "hello"
        assert ret1 == "world"
        ret1b = req1.cached_setup(setup, extrakey=1)
        ret2b = req1.cached_setup(setup, extrakey=2)
        assert ret1 == ret1b
        assert ret2 == ret2b

    def test_request_cached_setup_functional(self, testdir):
        testdir.makepyfile(test_0="""
            l = []
            def pytest_funcarg__something(request):
                val = request.cached_setup(setup, teardown)
                return val 
            def setup(mycache=[1]):
                l.append(mycache.pop())
                return l 
            def teardown(something):
                l.remove(something[0])
                l.append(2)
            def test_list_once(something):
                assert something == [1]
            def test_list_twice(something):
                assert something == [1]
        """)
        testdir.makepyfile(test_1="""
            import test_0 # should have run already 
            def test_check_test0_has_teardown_correct():
                assert test_0.l == [2]
        """)
        result = testdir.runpytest("-v")
        result.stdout.fnmatch_lines([
            "*3 passed*"
        ])


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
        py.test.raises(ValueError, "metafunc.addcall(id=None)")

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

    def test_addcall_funcargs(self):
        def func(arg1): pass
        metafunc = funcargs.Metafunc(func)
        class obj: pass 
        metafunc.addcall(funcargs={"x": 2})
        metafunc.addcall(funcargs={"x": 3})
        assert len(metafunc._calls) == 2
        assert metafunc._calls[0].funcargs == {'x': 2}
        assert metafunc._calls[1].funcargs == {'x': 3}
        assert not hasattr(metafunc._calls[1], 'param')

class TestGenfuncFunctional:
    def test_attributes(self, testdir):
        p = testdir.makepyfile("""
            # assumes that generate/provide runs in the same process
            import py
            def pytest_generate_tests(metafunc):
                metafunc.addcall(param=metafunc) 

            def pytest_funcarg__metafunc(request):
                assert request._pyfuncitem._genid == "0"
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

    def test_addcall_with_funcargs_two(self, testdir):
        testdir.makeconftest("""
            def pytest_generate_tests(metafunc):
                assert "arg1" in metafunc.funcargnames 
                metafunc.addcall(funcargs=dict(arg1=1, arg2=2))
        """)
        p = testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.addcall(funcargs=dict(arg1=1, arg2=1))

            class TestClass:
                def test_myfunc(self, arg1, arg2):
                    assert arg1 == arg2 
        """)
        result = testdir.runpytest("-v", p)
        assert result.stdout.fnmatch_lines([
            "*test_myfunc*0*PASS*", 
            "*test_myfunc*1*FAIL*", 
            "*1 failed, 1 passed*"
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
            def pytest_generate_tests(metafunc):
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
