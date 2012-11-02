import pytest, py, sys
from _pytest import python as funcargs
from _pytest.python import FixtureLookupError

class TestModule:
    def test_failing_import(self, testdir):
        modcol = testdir.getmodulecol("import alksdjalskdjalkjals")
        pytest.raises(ImportError, modcol.collect)
        pytest.raises(ImportError, modcol.collect)

    def test_import_duplicate(self, testdir):
        a = testdir.mkdir("a")
        b = testdir.mkdir("b")
        p = a.ensure("test_whatever.py")
        p.pyimport()
        del py.std.sys.modules['test_whatever']
        b.ensure("test_whatever.py")
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*import*mismatch*",
            "*imported*test_whatever*",
            "*%s*" % a.join("test_whatever.py"),
            "*not the same*",
            "*%s*" % b.join("test_whatever.py"),
            "*HINT*",
        ])

    def test_syntax_error_in_module(self, testdir):
        modcol = testdir.getmodulecol("this is a syntax error")
        pytest.raises(modcol.CollectError, modcol.collect)
        pytest.raises(modcol.CollectError, modcol.collect)

    def test_module_considers_pluginmanager_at_import(self, testdir):
        modcol = testdir.getmodulecol("pytest_plugins='xasdlkj',")
        pytest.raises(ImportError, "modcol.obj")

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

    def test_class_subclassobject(self, testdir):
        testdir.getmodulecol("""
            class test(object):
                pass
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*collected 0*",
        ])

    def test_setup_teardown_class_as_classmethod(self, testdir):
        testdir.makepyfile(test_mod1="""
            class TestClassMethod:
                @classmethod
                def setup_class(cls):
                    pass
                def test_1(self):
                    pass
                @classmethod
                def teardown_class(cls):
                    pass
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*1 passed*",
        ])


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
        assert isinstance(gencol, pytest.Generator)
        gencolitems = gencol.collect()
        assert len(gencolitems) == 2
        assert isinstance(gencolitems[0], pytest.Function)
        assert isinstance(gencolitems[1], pytest.Function)
        assert gencolitems[0].name == '[0]'
        assert gencolitems[0].obj.__name__ == 'func1'

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
        assert isinstance(gencol, pytest.Generator)
        gencolitems = gencol.collect()
        assert len(gencolitems) == 2
        assert isinstance(gencolitems[0], pytest.Function)
        assert isinstance(gencolitems[1], pytest.Function)
        assert gencolitems[0].name == '[0]'
        assert gencolitems[0].obj.__name__ == 'func1'

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
        assert isinstance(gencol, pytest.Generator)
        gencolitems = gencol.collect()
        assert len(gencolitems) == 2
        assert isinstance(gencolitems[0], pytest.Function)
        assert isinstance(gencolitems[1], pytest.Function)
        assert gencolitems[0].name == "['seventeen']"
        assert gencolitems[0].obj.__name__ == 'func1'
        assert gencolitems[1].name == "['fortytwo']"
        assert gencolitems[1].obj.__name__ == 'func1'

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
        assert isinstance(gencol, pytest.Generator)
        pytest.raises(ValueError, "gencol.collect()")

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
        assert isinstance(gencol, pytest.Generator)
        gencolitems = gencol.collect()
        assert len(gencolitems) == 2
        assert isinstance(gencolitems[0], pytest.Function)
        assert isinstance(gencolitems[1], pytest.Function)
        assert gencolitems[0].name == "['m1']"
        assert gencolitems[0].obj.__name__ == 'func1'
        assert gencolitems[1].name == "['m2']"
        assert gencolitems[1].obj.__name__ == 'func1'

    def test_order_of_execution_generator_same_codeline(self, testdir, tmpdir):
        o = testdir.makepyfile("""
            def test_generative_order_of_execution():
                import py, pytest
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
                import py, pytest
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

    def test_setupstate_is_preserved_134(self, testdir):
        # yield-based tests are messy wrt to setupstate because
        # during collection they already invoke setup functions
        # and then again when they are run.  For now, we want to make sure
        # that the old 1.3.4 behaviour is preserved such that all
        # yielded functions all share the same "self" instance that
        # has been used during collection.
        o = testdir.makepyfile("""
            setuplist = []
            class TestClass:
                def setup_method(self, func):
                    #print "setup_method", self, func
                    setuplist.append(self)
                    self.init = 42

                def teardown_method(self, func):
                    self.init = None

                def test_func1(self):
                    pass

                def test_func2(self):
                    yield self.func2
                    yield self.func2

                def func2(self):
                    assert self.init

            def test_setuplist():
                # once for test_func2 during collection
                # once for test_func1 during test run
                # once for test_func2 during test run
                #print setuplist
                assert len(setuplist) == 3, len(setuplist)
                assert setuplist[0] == setuplist[2], setuplist
                assert setuplist[1] != setuplist[2], setuplist
        """)
        reprec = testdir.inline_run(o, '-v')
        passed, skipped, failed = reprec.countoutcomes()
        assert passed == 4
        assert not skipped and not failed


class TestFunction:
    def test_getmodulecollector(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        modcol = item.getparent(pytest.Module)
        assert isinstance(modcol, pytest.Module)
        assert hasattr(modcol.obj, 'test_func')

    def test_function_equality(self, testdir, tmpdir):
        from _pytest.python import FixtureManager
        config = testdir.parseconfigure()
        session = testdir.Session(config)
        session._fixturemanager = FixtureManager(session)
        def func1():
            pass
        def func2():
            pass
        f1 = pytest.Function(name="name", parent=session, config=config,
                args=(1,), callobj=func1)
        f2 = pytest.Function(name="name",config=config,
                args=(1,), callobj=func2, parent=session)
        assert not f1 == f2
        assert f1 != f2
        f3 = pytest.Function(name="name", parent=session, config=config,
                args=(1,2), callobj=func2)
        assert not f3 == f2
        assert f3 != f2

        assert not f3 == f1
        assert f3 != f1

        f1_b = pytest.Function(name="name", parent=session, config=config,
              args=(1,), callobj=func1)
        assert f1 == f1_b
        assert not f1 != f1_b

    def test_issue197_parametrize_emptyset(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.mark.parametrize('arg', [])
            def test_function(arg):
                pass
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(skipped=1)

    def test_issue213_parametrize_value_no_equal(self, testdir):
        testdir.makepyfile("""
            import pytest
            class A:
                def __eq__(self, other):
                    raise ValueError("not possible")
            @pytest.mark.parametrize('arg', [A()])
            def test_function(arg):
                assert arg.__class__.__name__ == "A"
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_function_equality_with_callspec(self, testdir, tmpdir):
        items = testdir.getitems("""
            import pytest
            @pytest.mark.parametrize('arg', [1,2])
            def test_function(arg):
                pass
        """)
        assert items[0] != items[1]
        assert not (items[0] == items[1])

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
        fn1 = testdir.collect_by_name(modcol, "test_pass")
        assert isinstance(fn1, pytest.Function)
        fn2 = testdir.collect_by_name(modcol, "test_pass")
        assert isinstance(fn2, pytest.Function)

        assert fn1 == fn2
        assert fn1 != modcol
        if py.std.sys.version_info < (3, 0):
            assert cmp(fn1, fn2) == 0
        assert hash(fn1) == hash(fn2)

        fn3 = testdir.collect_by_name(modcol, "test_fail")
        assert isinstance(fn3, pytest.Function)
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
            import pytest
            class MyModule(pytest.Module):
                pass
            def pytest_pycollect_makemodule(path, parent):
                if path.basename == "test_xyz.py":
                    return MyModule(path, parent)
        """)
        testdir.makepyfile("def test_some(): pass")
        testdir.makepyfile(test_xyz="def test_func(): pass")
        result = testdir.runpytest("--collectonly")
        result.stdout.fnmatch_lines([
            "*<Module*test_pytest*",
            "*<MyModule*xyz*",
        ])

    def test_customized_pymakemodule_issue205_subdir(self, testdir):
        b = testdir.mkdir("a").mkdir("b")
        b.join("conftest.py").write(py.code.Source("""
            def pytest_pycollect_makemodule(__multicall__):
                mod = __multicall__.execute()
                mod.obj.hello = "world"
                return mod
        """))
        b.join("test_module.py").write(py.code.Source("""
            def test_hello():
                assert hello == "world"
        """))
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_customized_pymakeitem(self, testdir):
        b = testdir.mkdir("a").mkdir("b")
        b.join("conftest.py").write(py.code.Source("""
            def pytest_pycollect_makeitem(__multicall__):
                result = __multicall__.execute()
                if result:
                    for func in result:
                        func._some123 = "world"
                return result
        """))
        b.join("test_module.py").write(py.code.Source("""
            import pytest

            @pytest.fixture()
            def obj(request):
                return request.node._some123
            def test_hello(obj):
                assert obj == "world"
        """))
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_pytest_pycollect_makeitem(self, testdir):
        testdir.makeconftest("""
            import pytest
            class MyFunction(pytest.Function):
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
        monkeypatch.setattr(pytest.Module, 'makeitem',
            lambda self, name, obj: l.append(name))
        l = modcol.collect()
        assert '_hello' not in l

def test_setup_only_available_in_subdir(testdir):
    sub1 = testdir.mkpydir("sub1")
    sub2 = testdir.mkpydir("sub2")
    sub1.join("conftest.py").write(py.code.Source("""
        import pytest
        def pytest_runtest_setup(item):
            assert item.fspath.purebasename == "test_in_sub1"
        def pytest_runtest_call(item):
            assert item.fspath.purebasename == "test_in_sub1"
        def pytest_runtest_teardown(item):
            assert item.fspath.purebasename == "test_in_sub1"
    """))
    sub2.join("conftest.py").write(py.code.Source("""
        import pytest
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

def test_modulecol_roundtrip(testdir):
    modcol = testdir.getmodulecol("pass", withinit=True)
    trail = modcol.nodeid
    newcol = modcol.session.perform_collect([trail], genitems=0)[0]
    assert modcol.name == newcol.name


class TestTracebackCutting:
    def test_skip_simple(self):
        excinfo = pytest.raises(pytest.skip.Exception, 'pytest.skip("xxx")')
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
        assert numentries > 3

    def test_traceback_error_during_import(self, testdir):
        testdir.makepyfile("""
            x = 1
            x = 2
            x = 17
            asd
        """)
        result = testdir.runpytest()
        assert result.ret != 0
        out = result.stdout.str()
        assert "x = 1" not in out
        assert "x = 2" not in out
        result.stdout.fnmatch_lines([
            ">*asd*",
            "E*NameError*",
        ])
        result = testdir.runpytest("--fulltrace")
        out = result.stdout.str()
        assert "x = 1" in out
        assert "x = 2" in out
        result.stdout.fnmatch_lines([
            ">*asd*",
            "E*NameError*",
        ])

class TestReportInfo:
    def test_itemreport_reportinfo(self, testdir, linecomp):
        testdir.makeconftest("""
            import pytest
            class MyFunction(pytest.Function):
                def reportinfo(self):
                    return "ABCDE", 42, "custom"
            def pytest_pycollect_makeitem(collector, name, obj):
                if name == "test_func":
                    return MyFunction(name, parent=collector)
        """)
        item = testdir.getitem("def test_func(): pass")
        runner = item.config.pluginmanager.getplugin("runner")
        assert item.location == ("ABCDE", 42, "custom")

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
        classcol = testdir.collect_by_name(modcol, "TestClass")
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
        gencol = testdir.collect_by_name(modcol, "test_gen")
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


def test_customized_python_discovery(testdir):
    testdir.makeini("""
        [pytest]
        python_files=check_*.py
        python_classes=Check
        python_functions=check
    """)
    p = testdir.makepyfile("""
        def check_simple():
            pass
        class CheckMyApp:
            def check_meth(self):
                pass
    """)
    p2 = p.new(basename=p.basename.replace("test", "check"))
    p.move(p2)
    result = testdir.runpytest("--collectonly", "-s")
    result.stdout.fnmatch_lines([
        "*check_customized*",
        "*check_simple*",
        "*CheckMyApp*",
        "*check_meth*",
    ])

    result = testdir.runpytest()
    assert result.ret == 0
    result.stdout.fnmatch_lines([
        "*2 passed*",
    ])

def test_collector_attributes(testdir):
    testdir.makeconftest("""
        import pytest
        def pytest_pycollect_makeitem(collector):
            assert collector.Function == pytest.Function
            assert collector.Class == pytest.Class
            assert collector.Instance == pytest.Instance
            assert collector.Module == pytest.Module
    """)
    testdir.makepyfile("""
         def test_hello():
            pass
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
        "*1 passed*",
    ])

def test_customize_through_attributes(testdir):
    testdir.makeconftest("""
        import pytest
        class MyFunction(pytest.Function):
            pass
        class MyInstance(pytest.Instance):
            Function = MyFunction
        class MyClass(pytest.Class):
            Instance = MyInstance

        def pytest_pycollect_makeitem(collector, name, obj):
            if name.startswith("MyTestClass"):
                return MyClass(name, parent=collector)
    """)
    testdir.makepyfile("""
         class MyTestClass:
            def test_hello(self):
                pass
    """)
    result = testdir.runpytest("--collectonly")
    result.stdout.fnmatch_lines([
        "*MyClass*",
        "*MyInstance*",
        "*MyFunction*test_hello*",
    ])


def test_unorderable_types(testdir):
    testdir.makepyfile("""
        class TestJoinEmpty:
            pass

        def make_test():
            class Test:
                pass
            Test.__name__ = "TestFoo"
            return Test
        TestFoo = make_test()
    """)
    result = testdir.runpytest()
    assert "TypeError" not in result.stdout.str()
    assert result.ret == 0
