import py

class TestFuncargs:
    def test_funcarg_lookupfails(self, testdir):
        testdir.makeconftest("""
            class ConftestPlugin:
                def pytest_funcarg__something(self, pyfuncitem):
                    return 42
        """)
        item = testdir.getitem("def test_func(some): pass")
        exc = py.test.raises(LookupError, "item.setupargs()")
        s = str(exc.value)
        assert s.find("something") != -1

    def test_funcarg_lookup_default(self, testdir):
        item = testdir.getitem("def test_func(some, other=42): pass")
        class Provider:
            def pytest_funcarg__some(self, pyfuncitem):
                return pyfuncitem.name 
        item.config.pluginmanager.register(Provider())
        item.setupargs()
        assert len(item.funcargs) == 1

    def test_funcarg_lookup_default_gets_overriden(self, testdir):
        item = testdir.getitem("def test_func(some=42, other=13): pass")
        class Provider:
            def pytest_funcarg__other(self, pyfuncitem):
                return pyfuncitem.name 
        item.config.pluginmanager.register(Provider())
        item.setupargs()
        assert len(item.funcargs) == 1
        name, value = item.funcargs.popitem()
        assert name == "other"
        assert value == item.name 

    def test_funcarg_basic(self, testdir):
        item = testdir.getitem("def test_func(some, other): pass")
        class Provider:
            def pytest_funcarg__some(self, pyfuncitem):
                return pyfuncitem.name 
            def pytest_funcarg__other(self, pyfuncitem):
                return 42
        item.config.pluginmanager.register(Provider())
        item.setupargs()
        assert len(item.funcargs) == 2
        assert item.funcargs['some'] == "test_func"
        assert item.funcargs['other'] == 42

    def test_funcarg_addfinalizer(self, testdir):
        item = testdir.getitem("def test_func(some): pass")
        l = []
        class Provider:
            def pytest_funcarg__some(self, pyfuncitem):
                pyfuncitem.addfinalizer(lambda: l.append(42))
                return 3
        item.config.pluginmanager.register(Provider())
        item.setupargs()
        assert len(item.funcargs) == 1
        assert item.funcargs['some'] == 3
        assert len(l) == 0
        item.teardown()
        assert len(l) == 1
        assert l[0] == 42

    def test_funcarg_lookup_modulelevel(self, testdir):
        modcol = testdir.getmodulecol("""
            def pytest_funcarg__something(pyfuncitem):
                return pyfuncitem.name

            class TestClass:
                def test_method(self, something):
                    pass 
            def test_func(something):
                pass 
        """)
        item1, item2 = testdir.genitems([modcol])
        modcol.setup()
        assert modcol.config.pluginmanager.isregistered(modcol.obj)
        item1.setupargs()
        assert item1.funcargs['something'] ==  "test_method"
        item2.setupargs()
        assert item2.funcargs['something'] ==  "test_func"
        modcol.teardown()
        assert not modcol.config.pluginmanager.isregistered(modcol.obj)

class TestRequest:
    def test_request_contains_funcargs_methods(self, testdir):
        modcol = testdir.getmodulecol("""
            def pytest_funcarg__something(request):
                pass
            class TestClass:
                def pytest_funcarg__something(self, request):
                    pass
                def test_method(self, something):
                    pass 
        """)
        item1, = testdir.genitems([modcol])
        assert item1.name == "test_method"
        methods = item1.getrequest("something")._methods 
        assert len(methods) == 2
        method1, method2 = methods 
        assert not hasattr(method1, 'im_self')
        assert method2.im_self is not None
