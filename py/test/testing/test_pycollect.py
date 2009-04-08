import py

from py.__.test.outcome import Skipped

class TestModule:
    def test_module_file_not_found(self, testdir):
        tmpdir = testdir.tmpdir
        fn = tmpdir.join('nada','no')
        col = py.test.collect.Module(fn, config=testdir.parseconfig(tmpdir))
        py.test.raises(py.error.ENOENT, col.collect) 

    def test_failing_import(self, testdir):
        modcol = testdir.getmodulecol("import alksdjalskdjalkjals")
        py.test.raises(ImportError, modcol.collect)
        py.test.raises(ImportError, modcol.collect)
        py.test.raises(ImportError, modcol.run)

    def test_syntax_error_in_module(self, testdir):
        modcol = testdir.getmodulecol("this is a syntax error") 
        py.test.raises(SyntaxError, modcol.collect)
        py.test.raises(SyntaxError, modcol.collect)
        py.test.raises(SyntaxError, modcol.run)

    def test_module_assertion_setup(self, testdir, monkeypatch):
        modcol = testdir.getmodulecol("pass")
        from py.__.magic import assertion
        l = []
        monkeypatch.setattr(assertion, "invoke", lambda: l.append(None))
        modcol.setup()
        x = l.pop()
        assert x is None
        monkeypatch.setattr(assertion, "revoke", lambda: l.append(None))
        modcol.teardown()
        x = l.pop()
        assert x is None

    def test_module_participates_as_plugin(self, testdir):
        modcol = testdir.getmodulecol("")
        modcol.setup()
        assert modcol.config.pytestplugins.isregistered(modcol.obj)
        modcol.teardown()
        assert not modcol.config.pytestplugins.isregistered(modcol.obj)

    def test_module_considers_pytestplugins_at_import(self, testdir):
        modcol = testdir.getmodulecol("pytest_plugins='xasdlkj',")
        py.test.raises(ImportError, "modcol.obj")

    def test_disabled_module(self, testdir):
        modcol = testdir.getmodulecol("""
            disabled = True
            def setup_module(mod):
                raise ValueError
            def test_method():
                pass
        """)
        l = modcol.collect() 
        assert len(l) == 1
        py.test.raises(Skipped, "modcol.setup()")

class TestClass:
    def test_disabled_class(self, testdir):
        modcol = testdir.getmodulecol("""
            class TestClass:
                disabled = True
                def test_method(self):
                    pass
        """)
        l = modcol.collect()
        assert len(l) == 1
        modcol = l[0]
        assert isinstance(modcol, py.test.collect.Class)
        l = modcol.collect() 
        assert len(l) == 1
        py.test.raises(Skipped, "modcol.setup()")

class TestGenerator:
    def test_generative_functions(self, testdir): 
        modcol = testdir.getmodulecol("""
            def func1(arg, arg2): 
                assert arg == arg2 

            def test_gen(): 
                yield func1, 17, 3*5
                yield func1, 42, 6*7
        """)
        colitems = modcol.collect()
        assert len(colitems) == 1
        gencol = colitems[0]
        assert isinstance(gencol, py.test.collect.Generator)
        gencolitems = gencol.collect()
        assert len(gencolitems) == 2
        assert isinstance(gencolitems[0], py.test.collect.Function)
        assert isinstance(gencolitems[1], py.test.collect.Function)
        assert gencolitems[0].name == '[0]'
        assert gencolitems[0].obj.func_name == 'func1'

    def test_generative_methods(self, testdir): 
        modcol = testdir.getmodulecol("""
            def func1(arg, arg2): 
                assert arg == arg2 
            class TestGenMethods: 
                def test_gen(self): 
                    yield func1, 17, 3*5
                    yield func1, 42, 6*7
        """)
        gencol = modcol.collect()[0].collect()[0].collect()[0]
        assert isinstance(gencol, py.test.collect.Generator)
        gencolitems = gencol.collect()
        assert len(gencolitems) == 2
        assert isinstance(gencolitems[0], py.test.collect.Function)
        assert isinstance(gencolitems[1], py.test.collect.Function)
        assert gencolitems[0].name == '[0]'
        assert gencolitems[0].obj.func_name == 'func1'

    def test_generative_functions_with_explicit_names(self, testdir):
        modcol = testdir.getmodulecol("""
            def func1(arg, arg2): 
                assert arg == arg2 

            def test_gen(): 
                yield "seventeen", func1, 17, 3*5
                yield "fortytwo", func1, 42, 6*7
        """)
        colitems = modcol.collect()
        assert len(colitems) == 1
        gencol = colitems[0]
        assert isinstance(gencol, py.test.collect.Generator)
        gencolitems = gencol.collect()
        assert len(gencolitems) == 2
        assert isinstance(gencolitems[0], py.test.collect.Function)
        assert isinstance(gencolitems[1], py.test.collect.Function)
        assert gencolitems[0].name == "['seventeen']"
        assert gencolitems[0].obj.func_name == 'func1'
        assert gencolitems[1].name == "['fortytwo']"
        assert gencolitems[1].obj.func_name == 'func1'        

    def test_generative_functions_unique_explicit_names(self, testdir):
        # generative 
        modcol = testdir.getmodulecol("""
            def func(): pass 
            def test_gen(): 
                yield "name", func
                yield "name", func
        """)
        colitems = modcol.collect()
        assert len(colitems) == 1
        gencol = colitems[0]
        assert isinstance(gencol, py.test.collect.Generator)
        py.test.raises(ValueError, "gencol.collect()")

    def test_generative_methods_with_explicit_names(self, testdir): 
        modcol = testdir.getmodulecol("""
            def func1(arg, arg2): 
                assert arg == arg2 
            class TestGenMethods: 
                def test_gen(self): 
                    yield "m1", func1, 17, 3*5
                    yield "m2", func1, 42, 6*7
        """)
        gencol = modcol.collect()[0].collect()[0].collect()[0]
        assert isinstance(gencol, py.test.collect.Generator)
        gencolitems = gencol.collect()
        assert len(gencolitems) == 2
        assert isinstance(gencolitems[0], py.test.collect.Function)
        assert isinstance(gencolitems[1], py.test.collect.Function)
        assert gencolitems[0].name == "['m1']"
        assert gencolitems[0].obj.func_name == 'func1'
        assert gencolitems[1].name == "['m2']"
        assert gencolitems[1].obj.func_name == 'func1'        

    def test_order_of_execution_generator_same_codeline(self, testdir, tmpdir):
        o = testdir.makepyfile("""
            def test_generative_order_of_execution():
                test_list = []
                expected_list = range(6)

                def list_append(item):
                    test_list.append(item)
                    
                def assert_order_of_execution():
                    print 'expected order', expected_list
                    print 'but got       ', test_list
                    assert test_list == expected_list
                
                for i in expected_list:
                    yield list_append, i
                yield assert_order_of_execution
        """)
        sorter = testdir.inline_run(o)
        passed, skipped, failed = sorter.countoutcomes() 
        assert passed == 7
        assert not skipped and not failed 

    def test_order_of_execution_generator_different_codeline(self, testdir):
        o = testdir.makepyfile("""
            def test_generative_tests_different_codeline():
                test_list = []
                expected_list = range(3)

                def list_append_2():
                    test_list.append(2)

                def list_append_1():
                    test_list.append(1)

                def list_append_0():
                    test_list.append(0)

                def assert_order_of_execution():
                    print 'expected order', expected_list
                    print 'but got       ', test_list
                    assert test_list == expected_list
                    
                yield list_append_0
                yield list_append_1
                yield list_append_2
                yield assert_order_of_execution   
        """)
        sorter = testdir.inline_run(o) # .events_from_cmdline([o])
        passed, skipped, failed = sorter.countoutcomes() 
        assert passed == 4
        assert not skipped and not failed 

class TestFunction:
    def test_function_equality(self, tmpdir):
        config = py.test.config._reparse([tmpdir])
        f1 = py.test.collect.Function(name="name", config=config, 
                                      args=(1,), callobj=isinstance)
        f2 = py.test.collect.Function(name="name", config=config, 
                                      args=(1,), callobj=callable)
        assert not f1 == f2
        assert f1 != f2
        f3 = py.test.collect.Function(name="name", config=config, 
                                      args=(1,2), callobj=callable)
        assert not f3 == f2
        assert f3 != f2

        assert not f3 == f1
        assert f3 != f1

        f1_b = py.test.collect.Function(name="name", config=config, 
                                      args=(1,), callobj=isinstance)
        assert f1 == f1_b
        assert not f1 != f1_b

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
        item.config.pytestplugins.register(Provider())
        item.setupargs()
        assert len(item.funcargs) == 1

    def test_funcarg_lookup_default_gets_overriden(self, testdir):
        item = testdir.getitem("def test_func(some=42, other=13): pass")
        class Provider:
            def pytest_funcarg__other(self, pyfuncitem):
                return pyfuncitem.name 
        item.config.pytestplugins.register(Provider())
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
        item.config.pytestplugins.register(Provider())
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
        item.config.pytestplugins.register(Provider())
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
        assert modcol.config.pytestplugins.isregistered(modcol.obj)
        item1.setupargs()
        assert item1.funcargs['something'] ==  "test_method"
        item2.setupargs()
        assert item2.funcargs['something'] ==  "test_func"
        modcol.teardown()
        assert not modcol.config.pytestplugins.isregistered(modcol.obj)

class TestSorting:
    def test_check_equality_and_cmp_basic(self, testdir):
        modcol = testdir.getmodulecol("""
            def test_pass(): pass
            def test_fail(): assert 0
        """)
        fn1 = modcol.collect_by_name("test_pass")
        assert isinstance(fn1, py.test.collect.Function)
        fn2 = modcol.collect_by_name("test_pass")
        assert isinstance(fn2, py.test.collect.Function)

        assert fn1 == fn2
        assert fn1 != modcol 
        assert cmp(fn1, fn2) == 0
        assert hash(fn1) == hash(fn2) 

        fn3 = modcol.collect_by_name("test_fail")
        assert isinstance(fn3, py.test.collect.Function)
        assert not (fn1 == fn3) 
        assert fn1 != fn3
        assert cmp(fn1, fn3) == -1

        assert cmp(fn1, 10) == -1 
        assert cmp(fn2, 10) == -1 
        assert cmp(fn3, 10) == -1 
        for fn in fn1,fn2,fn3:
            assert fn != 3
            assert fn != modcol
            assert fn != [1,2,3]
            assert [1,2,3] != fn
            assert modcol != fn

    def test_allow_sane_sorting_for_decorators(self, testdir):
        modcol = testdir.getmodulecol("""
            def dec(f):
                g = lambda: f(2)
                g.place_as = f
                return g


            def test_a(y):
                pass
            test_a = dec(test_a)

            def test_b(y):
                pass
            test_b = dec(test_b)
        """)
        colitems = modcol.collect()
        assert len(colitems) == 2
        f1, f2 = colitems
        assert cmp(f2, f1) > 0

class TestConftestCustomization:
    def test_extra_python_files_and_functions(self, testdir):
        testdir.makepyfile(conftest="""
            import py
            class MyFunction(py.test.collect.Function):
                pass
            class Directory(py.test.collect.Directory):
                def consider_file(self, path):
                    if path.check(fnmatch="check_*.py"):
                        return self.Module(path, parent=self)
                    return super(Directory, self).consider_file(path)
            class myfuncmixin: 
                Function = MyFunction
                def funcnamefilter(self, name): 
                    return name.startswith('check_') 
            class Module(myfuncmixin, py.test.collect.Module):
                def classnamefilter(self, name): 
                    return name.startswith('CustomTestClass') 
            class Instance(myfuncmixin, py.test.collect.Instance):
                pass 
        """)
        checkfile = testdir.makepyfile(check_file="""
            def check_func():
                assert 42 == 42
            class CustomTestClass:
                def check_method(self):
                    assert 23 == 23
        """)
        # check that directory collects "check_" files 
        config = testdir.parseconfig()
        col = config.getfsnode(checkfile.dirpath())
        colitems = col.collect()
        assert len(colitems) == 1
        assert isinstance(colitems[0], py.test.collect.Module)

        # check that module collects "check_" functions and methods
        config = testdir.parseconfig(checkfile)
        col = config.getfsnode(checkfile)
        assert isinstance(col, py.test.collect.Module)
        colitems = col.collect()
        assert len(colitems) == 2
        funccol = colitems[0]
        assert isinstance(funccol, py.test.collect.Function)
        assert funccol.name == "check_func"
        clscol = colitems[1]
        assert isinstance(clscol, py.test.collect.Class)
        colitems = clscol.collect()[0].collect()
        assert len(colitems) == 1
        assert colitems[0].name == "check_method"

