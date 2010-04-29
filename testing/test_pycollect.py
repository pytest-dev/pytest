import py

class TestModule:
    def test_module_file_not_found(self, testdir):
        tmpdir = testdir.tmpdir
        fn = tmpdir.join('nada','no')
        col = py.test.collect.Module(fn, config=testdir.Config())
        col.config = testdir.parseconfig(tmpdir)
        py.test.raises(py.error.ENOENT, col.collect) 

    def test_failing_import(self, testdir):
        modcol = testdir.getmodulecol("import alksdjalskdjalkjals")
        py.test.raises(ImportError, modcol.collect)
        py.test.raises(ImportError, modcol.collect)
        py.test.raises(ImportError, modcol.run)

    def test_import_duplicate(self, testdir):
        a = testdir.mkdir("a")
        b = testdir.mkdir("b")
        p = a.ensure("test_whatever.py")
        p.pyimport()
        del py.std.sys.modules['test_whatever']
        b.ensure("test_whatever.py")
        result = testdir.runpytest()
        s = result.stdout.str()
        assert 'mismatch' in s
        assert 'test_whatever' in s

    def test_syntax_error_in_module(self, testdir):
        modcol = testdir.getmodulecol("this is a syntax error") 
        py.test.raises(SyntaxError, modcol.collect)
        py.test.raises(SyntaxError, modcol.collect)
        py.test.raises(SyntaxError, modcol.run)

    def test_module_considers_pluginmanager_at_import(self, testdir):
        modcol = testdir.getmodulecol("pytest_plugins='xasdlkj',")
        py.test.raises(ImportError, "modcol.obj")

class TestClass:
    def test_class_with_init_not_collected(self, testdir):
        modcol = testdir.getmodulecol("""
            class TestClass1:
                def __init__(self):
                    pass 
            class TestClass2(object):
                def __init__(self):
                    pass 
        """)
        l = modcol.collect() 
        assert len(l) == 0

if py.std.sys.version_info > (3, 0):
    _func_name_attr = "__name__"
else:
    _func_name_attr = "func_name"

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
        assert getattr(gencolitems[0].obj, _func_name_attr) == 'func1'

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
        assert getattr(gencolitems[0].obj, _func_name_attr) == 'func1'

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
        assert getattr(gencolitems[0].obj, _func_name_attr) == 'func1'
        assert gencolitems[1].name == "['fortytwo']"
        assert getattr(gencolitems[1].obj, _func_name_attr) == 'func1'        

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
        assert getattr(gencolitems[0].obj, _func_name_attr) == 'func1'
        assert gencolitems[1].name == "['m2']"
        assert getattr(gencolitems[1].obj, _func_name_attr) == 'func1'        

    def test_order_of_execution_generator_same_codeline(self, testdir, tmpdir):
        o = testdir.makepyfile("""
            def test_generative_order_of_execution():
                import py
                test_list = []
                expected_list = list(range(6))

                def list_append(item):
                    test_list.append(item)
                    
                def assert_order_of_execution():
                    py.builtin.print_('expected order', expected_list)
                    py.builtin.print_('but got       ', test_list)
                    assert test_list == expected_list
                
                for i in expected_list:
                    yield list_append, i
                yield assert_order_of_execution
        """)
        reprec = testdir.inline_run(o)
        passed, skipped, failed = reprec.countoutcomes() 
        assert passed == 7
        assert not skipped and not failed 

    def test_order_of_execution_generator_different_codeline(self, testdir):
        o = testdir.makepyfile("""
            def test_generative_tests_different_codeline():
                import py
                test_list = []
                expected_list = list(range(3))

                def list_append_2():
                    test_list.append(2)

                def list_append_1():
                    test_list.append(1)

                def list_append_0():
                    test_list.append(0)

                def assert_order_of_execution():
                    py.builtin.print_('expected order', expected_list)
                    py.builtin.print_('but got       ', test_list)
                    assert test_list == expected_list
                    
                yield list_append_0
                yield list_append_1
                yield list_append_2
                yield assert_order_of_execution   
        """)
        reprec = testdir.inline_run(o) 
        passed, skipped, failed = reprec.countoutcomes() 
        assert passed == 4
        assert not skipped and not failed 

class TestFunction:
    def test_getmodulecollector(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        modcol = item.getparent(py.test.collect.Module)
        assert isinstance(modcol, py.test.collect.Module)
        assert hasattr(modcol.obj, 'test_func')
        
    def test_function_equality(self, testdir, tmpdir):
        config = testdir.reparseconfig()
        f1 = py.test.collect.Function(name="name", config=config,
                                      args=(1,), callobj=isinstance)
        f2 = py.test.collect.Function(name="name",config=config, 
                                      args=(1,), callobj=py.builtin.callable)
        assert not f1 == f2
        assert f1 != f2
        f3 = py.test.collect.Function(name="name", config=config, 
                                      args=(1,2), callobj=py.builtin.callable)
        assert not f3 == f2
        assert f3 != f2

        assert not f3 == f1
        assert f3 != f1

        f1_b = py.test.collect.Function(name="name", config=config, 
                                      args=(1,), callobj=isinstance)
        assert f1 == f1_b
        assert not f1 != f1_b

    def test_function_equality_with_callspec(self, testdir, tmpdir):
        config = testdir.reparseconfig()
        class callspec1:
            param = 1
            funcargs = {}
            id = "hello"
        class callspec2:
            param = 1
            funcargs = {}
            id = "world"
        f5 = py.test.collect.Function(name="name", config=config, 
                                      callspec=callspec1, callobj=isinstance)
        f5b = py.test.collect.Function(name="name", config=config, 
                                      callspec=callspec2, callobj=isinstance)
        assert f5 != f5b
        assert not (f5 == f5b)

    def test_pyfunc_call(self, testdir):
        item = testdir.getitem("def test_func(): raise ValueError")
        config = item.config
        class MyPlugin1:
            def pytest_pyfunc_call(self, pyfuncitem):
                raise ValueError
        class MyPlugin2:
            def pytest_pyfunc_call(self, pyfuncitem):
                return True
        config.pluginmanager.register(MyPlugin1())
        config.pluginmanager.register(MyPlugin2())
        config.hook.pytest_pyfunc_call(pyfuncitem=item)

class TestSorting:
    def test_check_equality(self, testdir):
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
        if py.std.sys.version_info < (3, 0):
            assert cmp(fn1, fn2) == 0
        assert hash(fn1) == hash(fn2) 

        fn3 = modcol.collect_by_name("test_fail")
        assert isinstance(fn3, py.test.collect.Function)
        assert not (fn1 == fn3) 
        assert fn1 != fn3

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


            def test_b(y):
                pass
            test_b = dec(test_b)

            def test_a(y):
                pass
            test_a = dec(test_a)
        """)
        colitems = modcol.collect()
        assert len(colitems) == 2
        assert [item.name for item in colitems] == ['test_b', 'test_a']


class TestConftestCustomization:
    def test_pytest_pycollect_module(self, testdir):
        testdir.makeconftest("""
            import py
            class MyModule(py.test.collect.Module):
                pass
            def pytest_pycollect_makemodule(path, parent):
                if path.basename == "test_xyz.py":
                    return MyModule(path, parent)
        """)
        testdir.makepyfile("def some(): pass")
        testdir.makepyfile(test_xyz="")
        result = testdir.runpytest("--collectonly")
        result.stdout.fnmatch_lines([
            "*<Module*test_pytest*",
            "*<MyModule*xyz*",
        ])

    def test_pytest_pycollect_makeitem(self, testdir):
        testdir.makeconftest("""
            import py
            class MyFunction(py.test.collect.Function):
                pass
            def pytest_pycollect_makeitem(collector, name, obj):
                if name == "some":
                    return MyFunction(name, collector)
        """)
        testdir.makepyfile("def some(): pass")
        result = testdir.runpytest("--collectonly")
        result.stdout.fnmatch_lines([
            "*MyFunction*some*",
        ])
        
    def test_makeitem_non_underscore(self, testdir, monkeypatch):
        modcol = testdir.getmodulecol("def _hello(): pass")
        l = []
        monkeypatch.setattr(py.test.collect.Module, 'makeitem', 
            lambda self, name, obj: l.append(name))
        l = modcol.collect()
        assert '_hello' not in l


class TestReportinfo:
        
    def test_func_reportinfo(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        fspath, lineno, modpath = item.reportinfo()
        assert fspath == item.fspath 
        assert lineno == 0
        assert modpath == "test_func"

    def test_class_reportinfo(self, testdir):
        modcol = testdir.getmodulecol("""
            # lineno 0
            class TestClass:
                def test_hello(self): pass
        """)
        classcol = modcol.collect_by_name("TestClass")
        fspath, lineno, msg = classcol.reportinfo()
        assert fspath == modcol.fspath 
        assert lineno == 1
        assert msg == "TestClass"

    def test_generator_reportinfo(self, testdir):
        modcol = testdir.getmodulecol("""
            # lineno 0
            def test_gen(): 
                def check(x): 
                    assert x
                yield check, 3
        """)
        gencol = modcol.collect_by_name("test_gen")
        fspath, lineno, modpath = gencol.reportinfo()
        assert fspath == modcol.fspath
        assert lineno == 1
        assert modpath == "test_gen"

        genitem = gencol.collect()[0]
        fspath, lineno, modpath = genitem.reportinfo()
        assert fspath == modcol.fspath
        assert lineno == 2
        assert modpath == "test_gen[0]"
        """
            def test_func():
                pass
            def test_genfunc():
                def check(x):
                    pass
                yield check, 3
            class TestClass:
                def test_method(self):
                    pass
       """

def test_setup_only_available_in_subdir(testdir):
    sub1 = testdir.mkpydir("sub1")
    sub2 = testdir.mkpydir("sub2")
    sub1.join("conftest.py").write(py.code.Source("""
        import py
        def pytest_runtest_setup(item):
            assert item.fspath.purebasename == "test_in_sub1"
        def pytest_runtest_call(item):
            assert item.fspath.purebasename == "test_in_sub1"
        def pytest_runtest_teardown(item):
            assert item.fspath.purebasename == "test_in_sub1"
    """))
    sub2.join("conftest.py").write(py.code.Source("""
        import py
        def pytest_runtest_setup(item):
            assert item.fspath.purebasename == "test_in_sub2"
        def pytest_runtest_call(item):
            assert item.fspath.purebasename == "test_in_sub2"
        def pytest_runtest_teardown(item):
            assert item.fspath.purebasename == "test_in_sub2"
    """))
    sub1.join("test_in_sub1.py").write("def test_1(): pass")
    sub2.join("test_in_sub2.py").write("def test_2(): pass")
    result = testdir.runpytest("-v", "-s")
    result.stdout.fnmatch_lines([
        "*2 passed*"
    ])

def test_generate_tests_only_done_in_subdir(testdir):
    sub1 = testdir.mkpydir("sub1")
    sub2 = testdir.mkpydir("sub2")
    sub1.join("conftest.py").write(py.code.Source("""
        def pytest_generate_tests(metafunc):
            assert metafunc.function.__name__ == "test_1"
    """))
    sub2.join("conftest.py").write(py.code.Source("""
        def pytest_generate_tests(metafunc):
            assert metafunc.function.__name__ == "test_2"
    """))
    sub1.join("test_in_sub1.py").write("def test_1(): pass")
    sub2.join("test_in_sub2.py").write("def test_2(): pass")
    result = testdir.runpytest("-v", "-s", sub1, sub2, sub1)
    result.stdout.fnmatch_lines([
        "*3 passed*"
    ])

def test_modulecol_roundtrip(testdir):
    modcol = testdir.getmodulecol("pass", withinit=True)
    trail = modcol.config._rootcol.totrail(modcol)
    newcol = modcol.config._rootcol.fromtrail(trail)
    assert modcol.name == newcol.name


class TestTracebackCutting:
    def test_skip_simple(self):
        excinfo = py.test.raises(py.test.skip.Exception, 'py.test.skip("xxx")')
        assert excinfo.traceback[-1].frame.code.name == "skip"
        assert excinfo.traceback[-1].ishidden()

    def test_traceback_argsetup(self, testdir):
        testdir.makeconftest("""
            def pytest_funcarg__hello(request):
                raise ValueError("xyz")
        """)
        p = testdir.makepyfile("def test(hello): pass")
        result = testdir.runpytest(p)
        assert result.ret != 0
        out = result.stdout.str()
        assert out.find("xyz") != -1
        assert out.find("conftest.py:2: ValueError") != -1
        numentries = out.count("_ _ _") # separator for traceback entries
        assert numentries == 0

        result = testdir.runpytest("--fulltrace", p)
        out = result.stdout.str()
        assert out.find("conftest.py:2: ValueError") != -1
        numentries = out.count("_ _ _ _") # separator for traceback entries
        assert numentries >3
