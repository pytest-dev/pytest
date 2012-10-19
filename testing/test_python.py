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

def test_getfuncargnames():
    def f(): pass
    assert not funcargs.getfuncargnames(f)
    def g(arg): pass
    assert funcargs.getfuncargnames(g) == ('arg',)
    def h(arg1, arg2="hello"): pass
    assert funcargs.getfuncargnames(h) == ('arg1',)
    def h(arg1, arg2, arg3="hello"): pass
    assert funcargs.getfuncargnames(h) == ('arg1', 'arg2')
    class A:
        def f(self, arg1, arg2="hello"):
            pass
    assert funcargs.getfuncargnames(A().f) == ('arg1',)
    if sys.version_info < (3,0):
        assert funcargs.getfuncargnames(A.f) == ('arg1',)


class TestFillFixtures:
    def test_fillfuncargs_exposed(self):
        # used by oejskit, kept for compatibility
        assert pytest._fillfuncargs == funcargs.fillfixtures

    def test_funcarg_lookupfails(self, testdir):
        testdir.makepyfile("""
            def pytest_funcarg__xyzsomething(request):
                return 42

            def test_func(some):
                pass
        """)
        result = testdir.runpytest() # "--collectonly")
        assert result.ret != 0
        result.stdout.fnmatch_lines([
            "*def test_func(some)*",
            "*fixture*some*not found*",
            "*xyzsomething*",
        ])

    def test_funcarg_basic(self, testdir):
        item = testdir.getitem("""
            def pytest_funcarg__some(request):
                return request.function.__name__
            def pytest_funcarg__other(request):
                return 42
            def test_func(some, other):
                pass
        """)
        funcargs.fillfixtures(item)
        del item.funcargs["request"]
        assert len(item.funcargs) == 2
        assert item.funcargs['some'] == "test_func"
        assert item.funcargs['other'] == 42

    def test_funcarg_lookup_modulelevel(self, testdir):
        testdir.makepyfile("""
            def pytest_funcarg__something(request):
                return request.function.__name__

            class TestClass:
                def test_method(self, something):
                    assert something == "test_method"
            def test_func(something):
                assert something == "test_func"
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=2)

    def test_funcarg_lookup_classlevel(self, testdir):
        p = testdir.makepyfile("""
            class TestClass:
                def pytest_funcarg__something(self, request):
                    return request.instance
                def test_method(self, something):
                    assert something is self
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            "*1 passed*"
        ])


class TestRequest:
    def test_request_attributes(self, testdir):
        item = testdir.getitem("""
            def pytest_funcarg__something(request): pass
            def test_func(something): pass
        """)
        req = funcargs.FixtureRequest(item)
        assert req.function == item.obj
        assert req.keywords == item.keywords
        assert hasattr(req.module, 'test_func')
        assert req.cls is None
        assert req.function.__name__ == "test_func"
        assert req.config == item.config
        assert repr(req).find(req.function.__name__) != -1

    def test_request_attributes_method(self, testdir):
        item, = testdir.getitems("""
            class TestB:
                def pytest_funcarg__something(self, request):
                    return 1
                def test_func(self, something):
                    pass
        """)
        req = item._request
        assert req.cls.__name__ == "TestB"
        assert req.instance.__class__ == req.cls

    def XXXtest_request_contains_funcarg_arg2fixturedefs(self, testdir):
        modcol = testdir.getmodulecol("""
            def pytest_funcarg__something(request):
                pass
            class TestClass:
                def test_method(self, something):
                    pass
        """)
        item1, = testdir.genitems([modcol])
        assert item1.name == "test_method"
        arg2fixturedefs = funcargs.FixtureRequest(item1)._arg2fixturedefs
        assert len(arg2fixturedefs) == 1
        assert arg2fixturedefs[0].__name__ == "pytest_funcarg__something"

    def test_getfuncargvalue_recursive(self, testdir):
        testdir.makeconftest("""
            def pytest_funcarg__something(request):
                return 1
        """)
        item = testdir.makepyfile("""
            def pytest_funcarg__something(request):
                return request.getfuncargvalue("something") + 1
            def test_func(something):
                assert something == 2
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_getfuncargvalue(self, testdir):
        item = testdir.getitem("""
            l = [2]
            def pytest_funcarg__something(request): return 1
            def pytest_funcarg__other(request):
                return l.pop()
            def test_func(something): pass
        """)
        req = item._request
        pytest.raises(FixtureLookupError, req.getfuncargvalue, "notexists")
        val = req.getfuncargvalue("something")
        assert val == 1
        val = req.getfuncargvalue("something")
        assert val == 1
        val2 = req.getfuncargvalue("other")
        assert val2 == 2
        val2 = req.getfuncargvalue("other")  # see about caching
        assert val2 == 2
        pytest._fillfuncargs(item)
        assert item.funcargs["something"] == 1
        assert len(item.funcargs) == 2
        assert "request" in item.funcargs
        #assert item.funcargs == {'something': 1, "other": 2}

    def test_request_addfinalizer(self, testdir):
        item = testdir.getitem("""
            teardownlist = []
            def pytest_funcarg__something(request):
                request.addfinalizer(lambda: teardownlist.append(1))
            def test_func(something): pass
        """)
        item.session._setupstate.prepare(item)
        pytest._fillfuncargs(item)
        # successively check finalization calls
        teardownlist = item.getparent(pytest.Module).obj.teardownlist
        ss = item.session._setupstate
        assert not teardownlist
        ss.teardown_exact(item, None)
        print(ss.stack)
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
        result.stdout.fnmatch_lines([
            "*1 error*"  # XXX the whole module collection fails
            ])

    def test_request_getmodulepath(self, testdir):
        modcol = testdir.getmodulecol("def test_somefunc(): pass")
        item, = testdir.genitems([modcol])
        req = funcargs.FixtureRequest(item)
        assert req.fspath == modcol.fspath

class TestMarking:
    def test_applymarker(self, testdir):
        item1,item2 = testdir.getitems("""
            def pytest_funcarg__something(request):
                pass
            class TestClass:
                def test_func1(self, something):
                    pass
                def test_func2(self, something):
                    pass
        """)
        req1 = funcargs.FixtureRequest(item1)
        assert 'xfail' not in item1.keywords
        req1.applymarker(pytest.mark.xfail)
        assert 'xfail' in item1.keywords
        assert 'skipif' not in item1.keywords
        req1.applymarker(pytest.mark.skipif)
        assert 'skipif' in item1.keywords
        pytest.raises(ValueError, "req1.applymarker(42)")

    def test_accesskeywords(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture()
            def keywords(request):
                return request.keywords
            @pytest.mark.XYZ
            def test_function(keywords):
                assert keywords["XYZ"]
                assert "abc" not in keywords
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_accessmarker_dynamic(self, testdir):
        testdir.makeconftest("""
            import pytest
            @pytest.fixture()
            def keywords(request):
                return request.keywords

            @pytest.fixture(scope="class", autouse=True)
            def marking(request):
                request.applymarker(pytest.mark.XYZ("hello"))
        """)
        testdir.makepyfile("""
            import pytest
            def test_fun1(keywords):
                assert keywords["XYZ"] is not None
                assert "abc" not in keywords
            def test_fun2(keywords):
                assert keywords["XYZ"] is not None
                assert "abc" not in keywords
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=2)


class TestRequestCachedSetup:
    def test_request_cachedsetup_defaultmodule(self, testdir):
        reprec = testdir.inline_runsource("""
            mysetup = ["hello",].pop

            def pytest_funcarg__something(request):
                return request.cached_setup(mysetup, scope="module")

            def test_func1(something):
                assert something == "hello"
            class TestClass:
                def test_func1a(self, something):
                    assert something == "hello"
        """)
        reprec.assertoutcome(passed=2)

    def test_request_cachedsetup_class(self, testdir):
        reprec = testdir.inline_runsource("""
            mysetup = ["hello", "hello2"].pop

            def pytest_funcarg__something(request):
                return request.cached_setup(mysetup, scope="class")
            def test_func1(something):
                assert something == "hello2"
            def test_func2(something):
                assert something == "hello2"
            class TestClass:
                def test_func1a(self, something):
                    assert something == "hello"
                def test_func2b(self, something):
                    assert something == "hello"
        """)
        reprec.assertoutcome(passed=4)

    def test_request_cachedsetup_extrakey(self, testdir):
        item1 = testdir.getitem("def test_func(): pass")
        req1 = funcargs.FixtureRequest(item1)
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

    def test_request_cachedsetup_cache_deletion(self, testdir):
        item1 = testdir.getitem("def test_func(): pass")
        req1 = funcargs.FixtureRequest(item1)
        l = []
        def setup():
            l.append("setup")
        def teardown(val):
            l.append("teardown")
        ret1 = req1.cached_setup(setup, teardown, scope="function")
        assert l == ['setup']
        # artificial call of finalizer
        setupstate = req1._pyfuncitem.session._setupstate
        setupstate._callfinalizers(item1)
        assert l == ["setup", "teardown"]
        ret2 = req1.cached_setup(setup, teardown, scope="function")
        assert l == ["setup", "teardown", "setup"]
        setupstate._callfinalizers(item1)
        assert l == ["setup", "teardown", "setup", "teardown"]

    def test_request_cached_setup_two_args(self, testdir):
        testdir.makepyfile("""
            def pytest_funcarg__arg1(request):
                return request.cached_setup(lambda: 42)
            def pytest_funcarg__arg2(request):
                return request.cached_setup(lambda: 17)
            def test_two_different_setups(arg1, arg2):
                assert arg1 != arg2
        """)
        result = testdir.runpytest("-v")
        result.stdout.fnmatch_lines([
            "*1 passed*"
        ])

    def test_request_cached_setup_getfuncargvalue(self, testdir):
        testdir.makepyfile("""
            def pytest_funcarg__arg1(request):
                arg1 = request.getfuncargvalue("arg2")
                return request.cached_setup(lambda: arg1 + 1)
            def pytest_funcarg__arg2(request):
                return request.cached_setup(lambda: 10)
            def test_two_funcarg(arg1):
                assert arg1 == 11
        """)
        result = testdir.runpytest("-v")
        result.stdout.fnmatch_lines([
            "*1 passed*"
        ])

    def test_request_cached_setup_functional(self, testdir):
        testdir.makepyfile(test_0="""
            l = []
            def pytest_funcarg__something(request):
                val = request.cached_setup(fsetup, fteardown)
                return val
            def fsetup(mycache=[1]):
                l.append(mycache.pop())
                return l
            def fteardown(something):
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
    def Metafunc(self, func):
        # the unit tests of this class check if things work correctly
        # on the funcarg level, so we don't need a full blown
        # initiliazation
        class FixtureInfo:
            name2fixturedefs = None
            def __init__(self, names):
                self.names_closure = names
        names = funcargs.getfuncargnames(func)
        fixtureinfo = FixtureInfo(names)
        return funcargs.Metafunc(func, fixtureinfo, None)

    def test_no_funcargs(self, testdir):
        def function(): pass
        metafunc = self.Metafunc(function)
        assert not metafunc.fixturenames
        repr(metafunc._calls)

    def test_function_basic(self):
        def func(arg1, arg2="qwe"): pass
        metafunc = self.Metafunc(func)
        assert len(metafunc.fixturenames) == 1
        assert 'arg1' in metafunc.fixturenames
        assert metafunc.function is func
        assert metafunc.cls is None

    def test_addcall_no_args(self):
        def func(arg1): pass
        metafunc = self.Metafunc(func)
        metafunc.addcall()
        assert len(metafunc._calls) == 1
        call = metafunc._calls[0]
        assert call.id == "0"
        assert not hasattr(call, 'param')

    def test_addcall_id(self):
        def func(arg1): pass
        metafunc = self.Metafunc(func)
        pytest.raises(ValueError, "metafunc.addcall(id=None)")

        metafunc.addcall(id=1)
        pytest.raises(ValueError, "metafunc.addcall(id=1)")
        pytest.raises(ValueError, "metafunc.addcall(id='1')")
        metafunc.addcall(id=2)
        assert len(metafunc._calls) == 2
        assert metafunc._calls[0].id == "1"
        assert metafunc._calls[1].id == "2"

    def test_addcall_param(self):
        def func(arg1): pass
        metafunc = self.Metafunc(func)
        class obj: pass
        metafunc.addcall(param=obj)
        metafunc.addcall(param=obj)
        metafunc.addcall(param=1)
        assert len(metafunc._calls) == 3
        assert metafunc._calls[0].getparam("arg1") == obj
        assert metafunc._calls[1].getparam("arg1") == obj
        assert metafunc._calls[2].getparam("arg1") == 1

    def test_addcall_funcargs(self):
        def func(x): pass
        metafunc = self.Metafunc(func)
        class obj: pass
        metafunc.addcall(funcargs={"x": 2})
        metafunc.addcall(funcargs={"x": 3})
        pytest.raises(pytest.fail.Exception, "metafunc.addcall({'xyz': 0})")
        assert len(metafunc._calls) == 2
        assert metafunc._calls[0].funcargs == {'x': 2}
        assert metafunc._calls[1].funcargs == {'x': 3}
        assert not hasattr(metafunc._calls[1], 'param')

    def test_parametrize_error(self):
        def func(x, y): pass
        metafunc = self.Metafunc(func)
        metafunc.parametrize("x", [1,2])
        pytest.raises(ValueError, lambda: metafunc.parametrize("x", [5,6]))
        pytest.raises(ValueError, lambda: metafunc.parametrize("x", [5,6]))
        metafunc.parametrize("y", [1,2])
        pytest.raises(ValueError, lambda: metafunc.parametrize("y", [5,6]))
        pytest.raises(ValueError, lambda: metafunc.parametrize("y", [5,6]))

    def test_parametrize_and_id(self):
        def func(x, y): pass
        metafunc = self.Metafunc(func)

        metafunc.parametrize("x", [1,2], ids=['basic', 'advanced'])
        metafunc.parametrize("y", ["abc", "def"])
        ids = [x.id for x in metafunc._calls]
        assert ids == ["basic-abc", "basic-def", "advanced-abc", "advanced-def"]

    def test_parametrize_with_userobjects(self):
        def func(x, y): pass
        metafunc = self.Metafunc(func)
        class A:
            pass
        metafunc.parametrize("x", [A(), A()])
        metafunc.parametrize("y", list("ab"))
        assert metafunc._calls[0].id == "x0-a"
        assert metafunc._calls[1].id == "x0-b"
        assert metafunc._calls[2].id == "x1-a"
        assert metafunc._calls[3].id == "x1-b"

    def test_idmaker_autoname(self):
        from _pytest.python import idmaker
        result = idmaker(("a", "b"), [("string", 1.0),
                                      ("st-ring", 2.0)])
        assert result == ["string-1.0", "st-ring-2.0"]

        result = idmaker(("a", "b"), [(object(), 1.0),
                                      (object(), object())])
        assert result == ["a0-1.0", "a1-b1"]


    def test_addcall_and_parametrize(self):
        def func(x, y): pass
        metafunc = self.Metafunc(func)
        metafunc.addcall({'x': 1})
        metafunc.parametrize('y', [2,3])
        assert len(metafunc._calls) == 2
        assert metafunc._calls[0].funcargs == {'x': 1, 'y': 2}
        assert metafunc._calls[1].funcargs == {'x': 1, 'y': 3}
        assert metafunc._calls[0].id == "0-2"
        assert metafunc._calls[1].id == "0-3"

    def test_parametrize_indirect(self):
        def func(x, y): pass
        metafunc = self.Metafunc(func)
        metafunc.parametrize('x', [1], indirect=True)
        metafunc.parametrize('y', [2,3], indirect=True)
        metafunc.parametrize('unnamed', [1], indirect=True)
        assert len(metafunc._calls) == 2
        assert metafunc._calls[0].funcargs == {}
        assert metafunc._calls[1].funcargs == {}
        assert metafunc._calls[0].params == dict(x=1,y=2, unnamed=1)
        assert metafunc._calls[1].params == dict(x=1,y=3, unnamed=1)

    def test_addcalls_and_parametrize_indirect(self):
        def func(x, y): pass
        metafunc = self.Metafunc(func)
        metafunc.addcall(param="123")
        metafunc.parametrize('x', [1], indirect=True)
        metafunc.parametrize('y', [2,3], indirect=True)
        assert len(metafunc._calls) == 2
        assert metafunc._calls[0].funcargs == {}
        assert metafunc._calls[1].funcargs == {}
        assert metafunc._calls[0].params == dict(x=1,y=2)
        assert metafunc._calls[1].params == dict(x=1,y=3)

    def test_parametrize_functional(self, testdir):
        testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.parametrize('x', [1,2], indirect=True)
                metafunc.parametrize('y', [2])
            def pytest_funcarg__x(request):
                return request.param * 10
            def pytest_funcarg__y(request):
                return request.param

            def test_simple(x,y):
                assert x in (10,20)
                assert y == 2
        """)
        result = testdir.runpytest("-v")
        result.stdout.fnmatch_lines([
            "*test_simple*1-2*",
            "*test_simple*2-2*",
            "*2 passed*",
        ])

    def test_parametrize_onearg(self):
        metafunc = self.Metafunc(lambda x: None)
        metafunc.parametrize("x", [1,2])
        assert len(metafunc._calls) == 2
        assert metafunc._calls[0].funcargs == dict(x=1)
        assert metafunc._calls[0].id == "1"
        assert metafunc._calls[1].funcargs == dict(x=2)
        assert metafunc._calls[1].id == "2"

    def test_parametrize_onearg_indirect(self):
        metafunc = self.Metafunc(lambda x: None)
        metafunc.parametrize("x", [1,2], indirect=True)
        assert metafunc._calls[0].params == dict(x=1)
        assert metafunc._calls[0].id == "1"
        assert metafunc._calls[1].params == dict(x=2)
        assert metafunc._calls[1].id == "2"

    def test_parametrize_twoargs(self):
        metafunc = self.Metafunc(lambda x,y: None)
        metafunc.parametrize(("x", "y"), [(1,2), (3,4)])
        assert len(metafunc._calls) == 2
        assert metafunc._calls[0].funcargs == dict(x=1, y=2)
        assert metafunc._calls[0].id == "1-2"
        assert metafunc._calls[1].funcargs == dict(x=3, y=4)
        assert metafunc._calls[1].id == "3-4"

    def test_parametrize_multiple_times(self, testdir):
        testdir.makepyfile("""
            import pytest
            pytestmark = pytest.mark.parametrize("x", [1,2])
            def test_func(x):
                assert 0, x
            class TestClass:
                pytestmark = pytest.mark.parametrize("y", [3,4])
                def test_meth(self, x, y):
                    assert 0, x
        """)
        result = testdir.runpytest()
        assert result.ret == 1
        result.stdout.fnmatch_lines([
            "*6 fail*",
        ])

    def test_parametrize_class_scenarios(self, testdir):
        testdir.makepyfile("""
        # same as doc/en/example/parametrize scenario example
        def pytest_generate_tests(metafunc):
            idlist = []
            argvalues = []
            for scenario in metafunc.cls.scenarios:
                idlist.append(scenario[0])
                items = scenario[1].items()
                argnames = [x[0] for x in items]
                argvalues.append(([x[1] for x in items]))
            metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")

        class Test(object):
               scenarios = [['1', {'arg': {1: 2}, "arg2": "value2"}],
                            ['2', {'arg':'value2', "arg2": "value2"}]]

               def test_1(self, arg, arg2):
                  pass

               def test_2(self, arg2, arg):
                  pass

               def test_3(self, arg, arg2):
                  pass
        """)
        result = testdir.runpytest("-v")
        assert result.ret == 0
        result.stdout.fnmatch_lines("""
            *test_1*1*
            *test_2*1*
            *test_3*1*
            *test_1*2*
            *test_2*2*
            *test_3*2*
            *6 passed*
        """)

class TestMetafuncFunctional:
    def test_attributes(self, testdir):
        p = testdir.makepyfile("""
            # assumes that generate/provide runs in the same process
            import py, pytest
            def pytest_generate_tests(metafunc):
                metafunc.addcall(param=metafunc)

            def pytest_funcarg__metafunc(request):
                assert request._pyfuncitem._genid == "0"
                return request.param

            def test_function(metafunc, pytestconfig):
                assert metafunc.config == pytestconfig
                assert metafunc.module.__name__ == __name__
                assert metafunc.function == test_function
                assert metafunc.cls is None

            class TestClass:
                def test_method(self, metafunc, pytestconfig):
                    assert metafunc.config == pytestconfig
                    assert metafunc.module.__name__ == __name__
                    if py.std.sys.version_info > (3, 0):
                        unbound = TestClass.test_method
                    else:
                        unbound = TestClass.test_method.im_func
                    # XXX actually have an unbound test function here?
                    assert metafunc.function == unbound
                    assert metafunc.cls == TestClass
        """)
        result = testdir.runpytest(p, "-v")
        result.stdout.fnmatch_lines([
            "*2 passed in*",
        ])

    def test_addcall_with_two_funcargs_generators(self, testdir):
        testdir.makeconftest("""
            def pytest_generate_tests(metafunc):
                assert "arg1" in metafunc.fixturenames
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
        result.stdout.fnmatch_lines([
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
        result.stdout.fnmatch_lines([
            "*test_func1*0*PASS*",
            "*test_func1*1*FAIL*",
            "*test_func2*PASS*",
            "*1 failed, 3 passed*"
        ])

    def test_noself_in_method(self, testdir):
        p = testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                assert 'xyz' not in metafunc.fixturenames

            class TestHello:
                def test_hello(xyz):
                    pass
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            "*1 pass*",
        ])


    def test_generate_plugin_and_module(self, testdir):
        testdir.makeconftest("""
            def pytest_generate_tests(metafunc):
                assert "arg1" in metafunc.fixturenames
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
        result.stdout.fnmatch_lines([
            "*test_myfunc*hello*PASS*",
            "*test_myfunc*world*FAIL*",
            "*1 failed, 1 passed*"
        ])

    def test_generate_tests_in_class(self, testdir):
        p = testdir.makepyfile("""
            class TestClass:
                def pytest_generate_tests(self, metafunc):
                    metafunc.addcall(funcargs={'hello': 'world'}, id="hello")

                def test_myfunc(self, hello):
                    assert hello == "world"
        """)
        result = testdir.runpytest("-v", p)
        result.stdout.fnmatch_lines([
            "*test_myfunc*hello*PASS*",
            "*1 passed*"
        ])

    def test_two_functions_not_same_instance(self, testdir):
        p = testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.addcall({'arg1': 10})
                metafunc.addcall({'arg1': 20})

            class TestClass:
                def test_func(self, arg1):
                    assert not hasattr(self, 'x')
                    self.x = 1
        """)
        result = testdir.runpytest("-v", p)
        result.stdout.fnmatch_lines([
            "*test_func*0*PASS*",
            "*test_func*1*PASS*",
            "*2 pass*",
        ])

    def test_issue28_setup_method_in_generate_tests(self, testdir):
        p = testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.addcall({'arg1': 1})

            class TestClass:
                def test_method(self, arg1):
                    assert arg1 == self.val
                def setup_method(self, func):
                    self.val = 1
            """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            "*1 pass*",
        ])

    def test_parametrize_functional2(self, testdir):
        testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.parametrize("arg1", [1,2])
                metafunc.parametrize("arg2", [4,5])
            def test_hello(arg1, arg2):
                assert 0, (arg1, arg2)
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*(1, 4)*",
            "*(1, 5)*",
            "*(2, 4)*",
            "*(2, 5)*",
            "*4 failed*",
        ])

    def test_parametrize_and_inner_getfuncargvalue(self, testdir):
        p = testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.parametrize("arg1", [1], indirect=True)
                metafunc.parametrize("arg2", [10], indirect=True)

            def pytest_funcarg__arg1(request):
                x = request.getfuncargvalue("arg2")
                return x + request.param

            def pytest_funcarg__arg2(request):
                return request.param

            def test_func1(arg1, arg2):
                assert arg1 == 11
        """)
        result = testdir.runpytest("-v", p)
        result.stdout.fnmatch_lines([
            "*test_func1*1*PASS*",
            "*1 passed*"
        ])

    def test_parametrize_on_setup_arg(self, testdir):
        p = testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                assert "arg1" in metafunc.fixturenames
                metafunc.parametrize("arg1", [1], indirect=True)

            def pytest_funcarg__arg1(request):
                return request.param

            def pytest_funcarg__arg2(request, arg1):
                return 10 * arg1

            def test_func(arg2):
                assert arg2 == 10
        """)
        result = testdir.runpytest("-v", p)
        result.stdout.fnmatch_lines([
            "*test_func*1*PASS*",
            "*1 passed*"
        ])

    def test_parametrize_with_ids(self, testdir):
        testdir.makepyfile("""
            import pytest
            def pytest_generate_tests(metafunc):
                metafunc.parametrize(("a", "b"), [(1,1), (1,2)],
                                     ids=["basic", "advanced"])

            def test_function(a, b):
                assert a == b
        """)
        result = testdir.runpytest("-v")
        assert result.ret == 1
        result.stdout.fnmatch_lines_random([
            "*test_function*basic*PASSED",
            "*test_function*advanced*FAILED",
        ])

    def test_parametrize_without_ids(self, testdir):
        testdir.makepyfile("""
            import pytest
            def pytest_generate_tests(metafunc):
                metafunc.parametrize(("a", "b"),
                                     [(1,object()), (1.3,object())])

            def test_function(a, b):
                assert 1
        """)
        result = testdir.runpytest("-v")
        result.stdout.fnmatch_lines("""
            *test_function*1-b0*
            *test_function*1.3-b1*
        """)



    @pytest.mark.parametrize(("scope", "length"),
                             [("module", 2), ("function", 4)])
    def test_parametrize_scope_overrides(self, testdir, scope, length):
        testdir.makepyfile("""
            import pytest
            l = []
            def pytest_generate_tests(metafunc):
                if "arg" in metafunc.funcargnames:
                    metafunc.parametrize("arg", [1,2], indirect=True,
                                         scope=%r)
            def pytest_funcarg__arg(request):
                l.append(request.param)
                return request.param
            def test_hello(arg):
                assert arg in (1,2)
            def test_world(arg):
                assert arg in (1,2)
            def test_checklength():
                assert len(l) == %d
        """ % (scope, length))
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=5)

    def test_usefixtures_seen_in_generate_tests(self, testdir):
        testdir.makepyfile("""
            import pytest
            def pytest_generate_tests(metafunc):
                assert "abc" in metafunc.fixturenames
                metafunc.parametrize("abc", [1])

            @pytest.mark.usefixtures("abc")
            def test_function():
                pass
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_usefixtures_seen_in_showmarkers(self, testdir):
        result = testdir.runpytest("--markers")
        result.stdout.fnmatch_lines("""
            *usefixtures(fixturename1*mark tests*fixtures*
        """)

    def test_generate_tests_only_done_in_subdir(self, testdir):
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


def test_conftest_funcargs_only_available_in_subdir(testdir):
    sub1 = testdir.mkpydir("sub1")
    sub2 = testdir.mkpydir("sub2")
    sub1.join("conftest.py").write(py.code.Source("""
        import pytest
        def pytest_funcarg__arg1(request):
            pytest.raises(Exception, "request.getfuncargvalue('arg2')")
    """))
    sub2.join("conftest.py").write(py.code.Source("""
        import pytest
        def pytest_funcarg__arg2(request):
            pytest.raises(Exception, "request.getfuncargvalue('arg1')")
    """))

    sub1.join("test_in_sub1.py").write("def test_1(arg1): pass")
    sub2.join("test_in_sub2.py").write("def test_2(arg2): pass")
    result = testdir.runpytest("-v")
    result.stdout.fnmatch_lines([
        "*2 passed*"
    ])

class TestOEJSKITSpecials:
    def test_funcarg_non_pycollectobj(self, testdir): # rough jstests usage
        testdir.makeconftest("""
            import pytest
            def pytest_pycollect_makeitem(collector, name, obj):
                if name == "MyClass":
                    return MyCollector(name, parent=collector)
            class MyCollector(pytest.Collector):
                def reportinfo(self):
                    return self.fspath, 3, "xyz"
        """)
        modcol = testdir.getmodulecol("""
            def pytest_funcarg__arg1(request):
                return 42
            class MyClass:
                pass
        """)
        # this hook finds funcarg factories
        rep = modcol.ihook.pytest_make_collect_report(collector=modcol)
        clscol = rep.result[0]
        clscol.obj = lambda arg1: None
        clscol.funcargs = {}
        funcargs.fillfixtures(clscol)
        assert clscol.funcargs['arg1'] == 42

    def test_autouse_fixture(self, testdir): # rough jstests usage
        testdir.makeconftest("""
            import pytest
            def pytest_pycollect_makeitem(collector, name, obj):
                if name == "MyClass":
                    return MyCollector(name, parent=collector)
            class MyCollector(pytest.Collector):
                def reportinfo(self):
                    return self.fspath, 3, "xyz"
        """)
        modcol = testdir.getmodulecol("""
            import pytest
            @pytest.fixture(autouse=True)
            def hello():
                pass
            def pytest_funcarg__arg1(request):
                return 42
            class MyClass:
                pass
        """)
        # this hook finds funcarg factories
        rep = modcol.ihook.pytest_make_collect_report(collector=modcol)
        clscol = rep.result[0]
        clscol.obj = lambda: None
        clscol.funcargs = {}
        funcargs.fillfixtures(clscol)
        assert not clscol.funcargs



def test_funcarg_lookup_error(testdir):
    p = testdir.makepyfile("""
        def test_lookup_error(unknown):
            pass
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
        "*ERROR*test_lookup_error*",
        "*def test_lookup_error(unknown):*",
        "*fixture*unknown*not found*",
        "*available fixtures*",
        "*1 error*",
    ])
    assert "INTERNAL" not in result.stdout.str()

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

class TestShowFixtures:
    def test_funcarg_compat(self, testdir):
        config = testdir.parseconfigure("--funcargs")
        assert config.option.showfixtures

    def test_show_fixtures(self, testdir):
        result = testdir.runpytest("--fixtures")
        result.stdout.fnmatch_lines([
                "*tmpdir*",
                "*temporary directory*",
            ]
        )

    def test_show_fixtures_verbose(self, testdir):
        result = testdir.runpytest("--fixtures", "-v")
        result.stdout.fnmatch_lines([
                "*tmpdir*--*tmpdir.py*",
                "*temporary directory*",
            ]
        )

    def test_show_fixtures_testmodule(self, testdir):
        p = testdir.makepyfile('''
            import pytest
            @pytest.fixture
            def _arg0():
                """ hidden """
            @pytest.fixture
            def arg1():
                """  hello world """
        ''')
        result = testdir.runpytest("--fixtures", p)
        result.stdout.fnmatch_lines("""
            *tmpdir
            *fixtures defined from*
            *arg1*
            *hello world*
        """)
        assert "arg0" not in result.stdout.str()

    @pytest.mark.parametrize("testmod", [True, False])
    def test_show_fixtures_conftest(self, testdir, testmod):
        testdir.makeconftest('''
            import pytest
            @pytest.fixture
            def arg1():
                """  hello world """
        ''')
        if testmod:
            testdir.makepyfile("""
                def test_hello():
                    pass
            """)
        result = testdir.runpytest("--fixtures")
        result.stdout.fnmatch_lines("""
            *tmpdir*
            *fixtures defined from*conftest*
            *arg1*
            *hello world*
        """)



class TestRaises:
    def test_raises(self):
        source = "int('qwe')"
        excinfo = pytest.raises(ValueError, source)
        code = excinfo.traceback[-1].frame.code
        s = str(code.fullsource)
        assert s == source

    def test_raises_exec(self):
        pytest.raises(ValueError, "a,x = []")

    def test_raises_syntax_error(self):
        pytest.raises(SyntaxError, "qwe qwe qwe")

    def test_raises_function(self):
        pytest.raises(ValueError, int, 'hello')

    def test_raises_callable_no_exception(self):
        class A:
            def __call__(self):
                pass
        try:
            pytest.raises(ValueError, A())
        except pytest.raises.Exception:
            pass

    def test_raises_flip_builtin_AssertionError(self):
        # we replace AssertionError on python level
        # however c code might still raise the builtin one
        from _pytest.assertion.util import BuiltinAssertionError
        pytest.raises(AssertionError,"""
            raise BuiltinAssertionError
        """)

    @pytest.mark.skipif('sys.version < "2.5"')
    def test_raises_as_contextmanager(self, testdir):
        testdir.makepyfile("""
            from __future__ import with_statement
            import py, pytest

            def test_simple():
                with pytest.raises(ZeroDivisionError) as excinfo:
                    assert isinstance(excinfo, py.code.ExceptionInfo)
                    1/0
                print (excinfo)
                assert excinfo.type == ZeroDivisionError

            def test_noraise():
                with pytest.raises(pytest.raises.Exception):
                    with pytest.raises(ValueError):
                           int()

            def test_raise_wrong_exception_passes_by():
                with pytest.raises(ZeroDivisionError):
                    with pytest.raises(ValueError):
                           1/0
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            '*3 passed*',
        ])



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

def test_issue117_sessionscopeteardown(testdir):
    testdir.makepyfile("""
        def pytest_funcarg__app(request):
            app = request.cached_setup(
                scope='session',
                setup=lambda: 0,
                teardown=lambda x: 3/x)
            return app
        def test_func(app):
            pass
    """)
    result = testdir.runpytest()
    assert result.ret != 0
    result.stdout.fnmatch_lines([
        "*3/x*",
        "*ZeroDivisionError*",
    ])


class TestFixtureUsages:
    def test_noargfixturedec(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture
            def arg1():
                return 1

            def test_func(arg1):
                assert arg1 == 1
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_receives_funcargs(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture()
            def arg1():
                return 1

            @pytest.fixture()
            def arg2(arg1):
                return arg1 + 1

            def test_add(arg2):
                assert arg2 == 2
            def test_all(arg1, arg2):
                assert arg1 == 1
                assert arg2 == 2
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=2)

    def test_receives_funcargs_scope_mismatch(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture(scope="function")
            def arg1():
                return 1

            @pytest.fixture(scope="module")
            def arg2(arg1):
                return arg1 + 1

            def test_add(arg2):
                assert arg2 == 2
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*ScopeMismatch*involved factories*",
            "* def arg2*",
            "* def arg1*",
            "*1 error*"
        ])

    def test_funcarg_parametrized_and_used_twice(self, testdir):
        testdir.makepyfile("""
            import pytest
            l = []
            @pytest.fixture(params=[1,2])
            def arg1(request):
                l.append(1)
                return request.param

            @pytest.fixture()
            def arg2(arg1):
                return arg1 + 1

            def test_add(arg1, arg2):
                assert arg2 == arg1 + 1
                assert len(l) == arg1
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*2 passed*"
        ])

    def test_factory_uses_unknown_funcarg_as_dependency_error(self, testdir):
        testdir.makepyfile("""
            import pytest

            @pytest.fixture()
            def fail(missing):
                return

            @pytest.fixture()
            def call_fail(fail):
                return

            def test_missing(call_fail):
                pass
            """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines("""
            *pytest.fixture()*
            *def call_fail(fail)*
            *pytest.fixture()*
            *def fail*
            *fixture*'missing'*not found*
        """)

    def test_factory_setup_as_classes_fails(self, testdir):
        testdir.makepyfile("""
            import pytest
            class arg1:
                def __init__(self, request):
                    self.x = 1
            arg1 = pytest.fixture()(arg1)

        """)
        reprec = testdir.inline_run()
        l = reprec.getfailedcollections()
        assert len(l) == 1

    def test_request_can_be_overridden(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture()
            def request(request):
                request.a = 1
                return request
            def test_request(request):
                assert request.a == 1
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_usefixtures_marker(self, testdir):
        testdir.makepyfile("""
            import pytest

            l = []

            @pytest.fixture(scope="class")
            def myfix(request):
                request.cls.hello = "world"
                l.append(1)

            class TestClass:
                def test_one(self):
                    assert self.hello == "world"
                    assert len(l) == 1
                def test_two(self):
                    assert self.hello == "world"
                    assert len(l) == 1
            pytest.mark.usefixtures("myfix")(TestClass)
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=2)

    def test_usefixtures_ini(self, testdir):
        testdir.makeini("""
            [pytest]
            usefixtures = myfix
        """)
        testdir.makeconftest("""
            import pytest

            @pytest.fixture(scope="class")
            def myfix(request):
                request.cls.hello = "world"

        """)
        testdir.makepyfile("""
            class TestClass:
                def test_one(self):
                    assert self.hello == "world"
                def test_two(self):
                    assert self.hello == "world"
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=2)

class TestFixtureManager:
    def pytest_funcarg__testdir(self, request):
        testdir = request.getfuncargvalue("testdir")
        testdir.makeconftest("""
            def pytest_funcarg__hello(request):
                return "conftest"

            def pytest_funcarg__fm(request):
                return request._fixturemanager

            def pytest_funcarg__item(request):
                return request._pyfuncitem
        """)
        return testdir

    def test_parsefactories_conftest(self, testdir):
        testdir.makepyfile("""
            def test_hello(item, fm):
                for name in ("fm", "hello", "item"):
                    faclist = fm.getfixturedefs(name, item.nodeid)
                    assert len(faclist) == 1
                    fac = faclist[0]
                    assert fac.func.__name__ == "pytest_funcarg__" + name
        """)
        reprec = testdir.inline_run("-s")
        reprec.assertoutcome(passed=1)

    def test_parsefactories_conftest_and_module_and_class(self, testdir):
        testdir.makepyfile("""
            def pytest_funcarg__hello(request):
                return "module"
            class TestClass:
                def pytest_funcarg__hello(self, request):
                    return "class"
                def test_hello(self, item, fm):
                    faclist = fm.getfixturedefs("hello", item.nodeid)
                    print (faclist)
                    assert len(faclist) == 3
                    assert faclist[0].func(item._request) == "conftest"
                    assert faclist[1].func(item._request) == "module"
                    assert faclist[2].func(item._request) == "class"
        """)
        reprec = testdir.inline_run("-s")
        reprec.assertoutcome(passed=1)

class TestAutouseDiscovery:
    def pytest_funcarg__testdir(self, testdir):
        testdir.makeconftest("""
            import pytest
            @pytest.fixture(autouse=True)
            def perfunction(request, tmpdir):
                pass

            @pytest.fixture()
            def arg1(tmpdir):
                pass
            @pytest.fixture(autouse=True)
            def perfunction2(arg1):
                pass

            def pytest_funcarg__fm(request):
                return request._fixturemanager

            def pytest_funcarg__item(request):
                return request._pyfuncitem
        """)
        return testdir

    def test_parsefactories_conftest(self, testdir):
        testdir.makepyfile("""
            def test_check_setup(item, fm):
                autousenames = fm._getautousenames(item.nodeid)
                assert len(autousenames) == 2
                assert "perfunction2" in autousenames
                assert "perfunction" in autousenames
        """)
        reprec = testdir.inline_run("-s")
        reprec.assertoutcome(passed=1)

    def test_two_classes_separated_autouse(self, testdir):
        testdir.makepyfile("""
            import pytest
            class TestA:
                l = []
                @pytest.fixture(autouse=True)
                def setup1(self):
                    self.l.append(1)
                def test_setup1(self):
                    assert self.l == [1]
            class TestB:
                l = []
                @pytest.fixture(autouse=True)
                def setup2(self):
                    self.l.append(1)
                def test_setup2(self):
                    assert self.l == [1]
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=2)

    def test_setup_at_classlevel(self, testdir):
        testdir.makepyfile("""
            import pytest
            class TestClass:
                @pytest.fixture(autouse=True)
                def permethod(self, request):
                    request.instance.funcname = request.function.__name__
                def test_method1(self):
                    assert self.funcname == "test_method1"
                def test_method2(self):
                    assert self.funcname == "test_method2"
        """)
        reprec = testdir.inline_run("-s")
        reprec.assertoutcome(passed=2)

    @pytest.mark.xfail(reason="'enabled' feature not implemented")
    def test_setup_enabled_functionnode(self, testdir):
        testdir.makepyfile("""
            import pytest

            def enabled(parentnode, markers):
                return "needsdb" in markers

            @pytest.fixture(params=[1,2])
            def db(request):
                return request.param

            @pytest.fixture(enabled=enabled, autouse=True)
            def createdb(db):
                pass

            def test_func1(request):
                assert "db" not in request.fixturenames

            @pytest.mark.needsdb
            def test_func2(request):
                assert "db" in request.fixturenames
        """)
        reprec = testdir.inline_run("-s")
        reprec.assertoutcome(passed=2)

    def test_callables_nocode(self, testdir):
        """
        a imported mock.call would break setup/factory discovery
        due to it being callable and __code__ not being a code object
        """
        testdir.makepyfile("""
           class _call(tuple):
               def __call__(self, *k, **kw):
                   pass
               def __getattr__(self, k):
                   return self

           call = _call()
        """)
        reprec = testdir.inline_run("-s")
        reprec.assertoutcome(failed=0, passed=0)

    def test_autouse_in_conftests(self, testdir):
        a = testdir.mkdir("a")
        b = testdir.mkdir("a1")
        conftest = testdir.makeconftest("""
            import pytest
            @pytest.fixture(autouse=True)
            def hello():
                xxx
        """)
        conftest.move(a.join(conftest.basename))
        a.join("test_something.py").write("def test_func(): pass")
        b.join("test_otherthing.py").write("def test_func(): pass")
        result = testdir.runpytest()
        result.stdout.fnmatch_lines("""
            *1 passed*1 error*
        """)

    def test_autouse_in_module_and_two_classes(self, testdir):
        testdir.makepyfile("""
            import pytest
            l = []
            @pytest.fixture(autouse=True)
            def append1():
                l.append("module")
            def test_x():
                assert l == ["module"]

            class TestA:
                @pytest.fixture(autouse=True)
                def append2(self):
                    l.append("A")
                def test_hello(self):
                    assert l == ["module", "module", "A"], l
            class TestA2:
                def test_world(self):
                    assert l == ["module", "module", "A", "module"], l
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=3)

class TestAutouseManagement:
    def test_funcarg_and_setup(self, testdir):
        testdir.makepyfile("""
            import pytest
            l = []
            @pytest.fixture(scope="module")
            def arg():
                l.append(1)
                return 0
            @pytest.fixture(scope="class", autouse=True)
            def something(arg):
                l.append(2)

            def test_hello(arg):
                assert len(l) == 2
                assert l == [1,2]
                assert arg == 0

            def test_hello2(arg):
                assert len(l) == 2
                assert l == [1,2]
                assert arg == 0
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=2)

    def test_uses_parametrized_resource(self, testdir):
        testdir.makepyfile("""
            import pytest
            l = []
            @pytest.fixture(params=[1,2])
            def arg(request):
                return request.param

            @pytest.fixture(autouse=True)
            def something(arg):
                l.append(arg)

            def test_hello():
                if len(l) == 1:
                    assert l == [1]
                elif len(l) == 2:
                    assert l == [1, 2]
                else:
                    0/0

        """)
        reprec = testdir.inline_run("-s")
        reprec.assertoutcome(passed=2)

    def test_session_parametrized_function(self, testdir):
        testdir.makepyfile("""
            import pytest

            l = []

            @pytest.fixture(scope="session", params=[1,2])
            def arg(request):
               return request.param

            @pytest.fixture(scope="function", autouse=True)
            def append(request, arg):
                if request.function.__name__ == "test_some":
                    l.append(arg)

            def test_some():
                pass

            def test_result(arg):
                assert len(l) == arg
                assert l[:arg] == [1,2][:arg]
        """)
        reprec = testdir.inline_run("-v", "-s")
        reprec.assertoutcome(passed=4)

    def test_class_function_parametrization_finalization(self, testdir):
        p = testdir.makeconftest("""
            import pytest
            import pprint

            l = []

            @pytest.fixture(scope="function", params=[1,2])
            def farg(request):
                return request.param

            @pytest.fixture(scope="class", params=list("ab"))
            def carg(request):
                return request.param

            @pytest.fixture(scope="function", autouse=True)
            def append(request, farg, carg):
                def fin():
                    l.append("fin_%s%s" % (carg, farg))
                request.addfinalizer(fin)
        """)
        testdir.makepyfile("""
            import pytest

            class TestClass:
                def test_1(self):
                    pass
            class TestClass2:
                def test_2(self):
                    pass
        """)
        reprec = testdir.inline_run("-v","-s")
        reprec.assertoutcome(passed=8)
        config = reprec.getcalls("pytest_unconfigure")[0].config
        l = config._conftest.getconftestmodules(p)[0].l
        assert l == ["fin_a1", "fin_a2", "fin_b1", "fin_b2"] * 2

    def test_scope_ordering(self, testdir):
        testdir.makepyfile("""
            import pytest
            l = []
            @pytest.fixture(scope="function", autouse=True)
            def fappend2():
                l.append(2)
            @pytest.fixture(scope="class", autouse=True)
            def classappend3():
                l.append(3)
            @pytest.fixture(scope="module", autouse=True)
            def mappend():
                l.append(1)

            class TestHallo:
                def test_method(self):
                    assert l == [1,3,2]
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)


    def test_parametrization_setup_teardown_ordering(self, testdir):
        testdir.makepyfile("""
            import pytest
            l = []
            def pytest_generate_tests(metafunc):
                if metafunc.cls is not None:
                    metafunc.parametrize("item", [1,2], scope="class")
            class TestClass:
                @pytest.fixture(scope="class", autouse=True)
                def addteardown(self, item, request):
                    l.append("setup-%d" % item)
                    request.addfinalizer(lambda: l.append("teardown-%d" % item))
                def test_step1(self, item):
                    l.append("step1-%d" % item)
                def test_step2(self, item):
                    l.append("step2-%d" % item)

            def test_finish():
                assert l == ["setup-1", "step1-1", "step2-1", "teardown-1",
                             "setup-2", "step1-2", "step2-2", "teardown-2",]
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=5)


class TestFixtureMarker:
    def test_parametrize(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture(params=["a", "b", "c"])
            def arg(request):
                return request.param
            l = []
            def test_param(arg):
                l.append(arg)
            def test_result():
                assert l == list("abc")
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=4)

    def test_scope_session(self, testdir):
        testdir.makepyfile("""
            import pytest
            l = []
            @pytest.fixture(scope="module")
            def arg():
                l.append(1)
                return 1

            def test_1(arg):
                assert arg == 1
            def test_2(arg):
                assert arg == 1
                assert len(l) == 1
            class TestClass:
                def test3(self, arg):
                    assert arg == 1
                    assert len(l) == 1
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=3)

    def test_scope_module_uses_session(self, testdir):
        testdir.makepyfile("""
            import pytest
            l = []
            @pytest.fixture(scope="module")
            def arg():
                l.append(1)
                return 1

            def test_1(arg):
                assert arg == 1
            def test_2(arg):
                assert arg == 1
                assert len(l) == 1
            class TestClass:
                def test3(self, arg):
                    assert arg == 1
                    assert len(l) == 1
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=3)

    def test_scope_module_and_finalizer(self, testdir):
        testdir.makeconftest("""
            import pytest
            finalized = []
            created = []
            @pytest.fixture(scope="module")
            def arg(request):
                created.append(1)
                assert request.scope == "module"
                request.addfinalizer(lambda: finalized.append(1))
            def pytest_funcarg__created(request):
                return len(created)
            def pytest_funcarg__finalized(request):
                return len(finalized)
        """)
        testdir.makepyfile(
            test_mod1="""
                def test_1(arg, created, finalized):
                    assert created == 1
                    assert finalized == 0
                def test_2(arg, created, finalized):
                    assert created == 1
                    assert finalized == 0""",
            test_mod2="""
                def test_3(arg, created, finalized):
                    assert created == 2
                    assert finalized == 1""",
            test_mode3="""
                def test_4(arg, created, finalized):
                    assert created == 3
                    assert finalized == 2
            """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=4)

    @pytest.mark.parametrize("method", [
        'request.getfuncargvalue("arg")',
        'request.cached_setup(lambda: None, scope="function")',
    ], ids=["getfuncargvalue", "cached_setup"])
    def test_scope_mismatch(self, testdir, method):
        testdir.makeconftest("""
            import pytest
            finalized = []
            created = []
            @pytest.fixture(scope="function")
            def arg(request):
                pass
        """)
        testdir.makepyfile(
            test_mod1="""
                import pytest
                @pytest.fixture(scope="session")
                def arg(request):
                    %s
                def test_1(arg):
                    pass
            """ % method)
        result = testdir.runpytest()
        assert result.ret != 0
        result.stdout.fnmatch_lines([
            "*ScopeMismatch*You tried*function*session*request*",
        ])

    def test_register_only_with_mark(self, testdir):
        testdir.makeconftest("""
            import pytest
            @pytest.fixture()
            def arg():
                return 1
        """)
        testdir.makepyfile(
            test_mod1="""
                import pytest
                @pytest.fixture()
                def arg(arg):
                    return arg + 1
                def test_1(arg):
                    assert arg == 2
            """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_parametrize_and_scope(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture(scope="module", params=["a", "b", "c"])
            def arg(request):
                return request.param
            l = []
            def test_param(arg):
                l.append(arg)
        """)
        reprec = testdir.inline_run("-v")
        reprec.assertoutcome(passed=3)
        l = reprec.getcalls("pytest_runtest_call")[0].item.module.l
        assert len(l) == 3
        assert "a" in l
        assert "b" in l
        assert "c" in l

    def test_scope_mismatch(self, testdir):
        testdir.makeconftest("""
            import pytest
            @pytest.fixture(scope="function")
            def arg(request):
                pass
        """)
        testdir.makepyfile("""
            import pytest
            @pytest.fixture(scope="session")
            def arg(arg):
                pass
            def test_mismatch(arg):
                pass
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*ScopeMismatch*",
            "*1 error*",
        ])

    def test_parametrize_separated_order(self, testdir):
        testdir.makepyfile("""
            import pytest

            @pytest.fixture(scope="module", params=[1, 2])
            def arg(request):
                return request.param

            l = []
            def test_1(arg):
                l.append(arg)
            def test_2(arg):
                l.append(arg)
        """)
        reprec = testdir.inline_run("-v")
        reprec.assertoutcome(passed=4)
        l = reprec.getcalls("pytest_runtest_call")[0].item.module.l
        assert l == [1,1,2,2]

    def test_module_parametrized_ordering(self, testdir):
        testdir.makeconftest("""
            import pytest

            @pytest.fixture(scope="session", params="s1 s2".split())
            def sarg():
                pass
            @pytest.fixture(scope="module", params="m1 m2".split())
            def marg():
                pass
        """)
        testdir.makepyfile(test_mod1="""
            def test_func(sarg):
                pass
            def test_func1(marg):
                pass
        """, test_mod2="""
            def test_func2(sarg):
                pass
            def test_func3(sarg, marg):
                pass
            def test_func3b(sarg, marg):
                pass
            def test_func4(marg):
                pass
        """)
        result = testdir.runpytest("-v")
        result.stdout.fnmatch_lines("""
            test_mod1.py:1: test_func[s1] PASSED
            test_mod2.py:1: test_func2[s1] PASSED
            test_mod2.py:3: test_func3[s1-m1] PASSED
            test_mod2.py:5: test_func3b[s1-m1] PASSED
            test_mod2.py:3: test_func3[s1-m2] PASSED
            test_mod2.py:5: test_func3b[s1-m2] PASSED
            test_mod1.py:1: test_func[s2] PASSED
            test_mod2.py:1: test_func2[s2] PASSED
            test_mod2.py:3: test_func3[s2-m1] PASSED
            test_mod2.py:5: test_func3b[s2-m1] PASSED
            test_mod2.py:7: test_func4[m1] PASSED
            test_mod2.py:3: test_func3[s2-m2] PASSED
            test_mod2.py:5: test_func3b[s2-m2] PASSED
            test_mod2.py:7: test_func4[m2] PASSED
            test_mod1.py:3: test_func1[m1] PASSED
            test_mod1.py:3: test_func1[m2] PASSED
        """)

    def test_class_ordering(self, testdir):
        p = testdir.makeconftest("""
            import pytest

            l = []

            @pytest.fixture(scope="function", params=[1,2])
            def farg(request):
                return request.param

            @pytest.fixture(scope="class", params=list("ab"))
            def carg(request):
                return request.param

            @pytest.fixture(scope="function", autouse=True)
            def append(request, farg, carg):
                def fin():
                    l.append("fin_%s%s" % (carg, farg))
                request.addfinalizer(fin)
        """)
        testdir.makepyfile("""
            import pytest

            class TestClass2:
                def test_1(self):
                    pass
                def test_2(self):
                    pass
            class TestClass:
                def test_3(self):
                    pass
        """)
        result = testdir.runpytest("-vs")
        result.stdout.fnmatch_lines("""
            test_class_ordering.py:4: TestClass2.test_1[1-a] PASSED
            test_class_ordering.py:4: TestClass2.test_1[2-a] PASSED
            test_class_ordering.py:6: TestClass2.test_2[1-a] PASSED
            test_class_ordering.py:6: TestClass2.test_2[2-a] PASSED
            test_class_ordering.py:4: TestClass2.test_1[1-b] PASSED
            test_class_ordering.py:4: TestClass2.test_1[2-b] PASSED
            test_class_ordering.py:6: TestClass2.test_2[1-b] PASSED
            test_class_ordering.py:6: TestClass2.test_2[2-b] PASSED
            test_class_ordering.py:9: TestClass.test_3[1-a] PASSED
            test_class_ordering.py:9: TestClass.test_3[2-a] PASSED
            test_class_ordering.py:9: TestClass.test_3[1-b] PASSED
            test_class_ordering.py:9: TestClass.test_3[2-b] PASSED
        """)

    def test_parametrize_separated_order_higher_scope_first(self, testdir):
        testdir.makepyfile("""
            import pytest

            @pytest.fixture(scope="function", params=[1, 2])
            def arg(request):
                param = request.param
                request.addfinalizer(lambda: l.append("fin:%s" % param))
                l.append("create:%s" % param)
                return request.param

            @pytest.fixture(scope="module", params=["mod1", "mod2"])
            def modarg(request):
                param = request.param
                request.addfinalizer(lambda: l.append("fin:%s" % param))
                l.append("create:%s" % param)
                return request.param

            l = []
            def test_1(arg):
                l.append("test1")
            def test_2(modarg):
                l.append("test2")
            def test_3(arg, modarg):
                l.append("test3")
            def test_4(modarg, arg):
                l.append("test4")
            def test_5():
                assert len(l) == 12 * 3
                expected = [
                    'create:1', 'test1', 'fin:1', 'create:2', 'test1',
                    'fin:2', 'create:mod1', 'test2', 'create:1', 'test3',
                    'fin:1', 'create:2', 'test3', 'fin:2', 'create:1',
                    'test4', 'fin:1', 'create:2', 'test4', 'fin:2',
                    'fin:mod1', 'create:mod2', 'test2', 'create:1', 'test3',
                    'fin:1', 'create:2', 'test3', 'fin:2', 'create:1',
                    'test4', 'fin:1', 'create:2', 'test4', 'fin:2',
                'fin:mod2']
                import pprint
                pprint.pprint(list(zip(l, expected)))
                assert l == expected
        """)
        reprec = testdir.inline_run("-v")
        reprec.assertoutcome(passed=12+1)

    def test_parametrize_separated_lifecycle(self, testdir):
        testdir.makepyfile("""
            import pytest

            @pytest.fixture(scope="module", params=[1, 2])
            def arg(request):
                request.config.l = l # to access from outer
                x = request.param
                request.addfinalizer(lambda: l.append("fin%s" % x))
                return request.param

            l = []
            def test_1(arg):
                l.append(arg)
            def test_2(arg):
                l.append(arg)
        """)
        reprec = testdir.inline_run("-v")
        reprec.assertoutcome(passed=4)
        l = reprec.getcalls("pytest_configure")[0].config.l
        import pprint
        pprint.pprint(l)
        assert len(l) == 6
        assert l[0] == l[1] == 1
        assert l[2] == "fin1"
        assert l[3] == l[4] == 2
        assert l[5] == "fin2"


    def test_parametrize_function_scoped_finalizers_called(self, testdir):
        testdir.makepyfile("""
            import pytest

            @pytest.fixture(scope="function", params=[1, 2])
            def arg(request):
                x = request.param
                request.addfinalizer(lambda: l.append("fin%s" % x))
                return request.param

            l = []
            def test_1(arg):
                l.append(arg)
            def test_2(arg):
                l.append(arg)
            def test_3():
                assert len(l) == 8
                assert l == [1, "fin1", 2, "fin2", 1, "fin1", 2, "fin2"]
        """)
        reprec = testdir.inline_run("-v")
        reprec.assertoutcome(passed=5)

    def test_parametrize_setup_function(self, testdir):
        testdir.makepyfile("""
            import pytest

            @pytest.fixture(scope="module", params=[1, 2])
            def arg(request):
                return request.param

            @pytest.fixture(scope="module", autouse=True)
            def mysetup(request, arg):
                request.addfinalizer(lambda: l.append("fin%s" % arg))
                l.append("setup%s" % arg)

            l = []
            def test_1(arg):
                l.append(arg)
            def test_2(arg):
                l.append(arg)
            def test_3():
                import pprint
                pprint.pprint(l)
                if arg == 1:
                    assert l == ["setup1", 1, 1, ]
                elif arg == 2:
                    assert l == ["setup1", 1, 1, "fin1",
                                 "setup2", 2, 2, ]

        """)
        reprec = testdir.inline_run("-v")
        reprec.assertoutcome(passed=6)

class TestTestContextScopeAccess:
    pytestmark = pytest.mark.parametrize(("scope", "ok", "error"),[
        ["session", "", "fspath class function module"],
        ["module", "module fspath", "cls function"],
        ["class", "module fspath cls", "function"],
        ["function", "module fspath cls function", ""]
    ])

    def test_setup(self, testdir, scope, ok, error):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture(scope=%r, autouse=True)
            def myscoped(request):
                for x in %r:
                    assert hasattr(request, x)
                for x in %r:
                    pytest.raises(AttributeError, lambda:
                        getattr(request, x))
                assert request.session
                assert request.config
            def test_func():
                pass
        """ %(scope, ok.split(), error.split()))
        reprec = testdir.inline_run("-l")
        reprec.assertoutcome(passed=1)

    def test_funcarg(self, testdir, scope, ok, error):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture(scope=%r)
            def arg(request):
                for x in %r:
                    assert hasattr(request, x)
                for x in %r:
                    pytest.raises(AttributeError, lambda:
                        getattr(request, x))
                assert request.session
                assert request.config
            def test_func(arg):
                pass
        """ %(scope, ok.split(), error.split()))
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)


class TestErrors:
    def test_subfactory_missing_funcarg(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture()
            def gen(qwe123):
                return 1
            def test_something(gen):
                pass
        """)
        result = testdir.runpytest()
        assert result.ret != 0
        result.stdout.fnmatch_lines([
            "*def gen(qwe123):*",
            "*fixture*qwe123*not found*",
            "*1 error*",
        ])

    def test_setupfunc_missing_funcarg(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture(autouse=True)
            def gen(qwe123):
                return 1
            def test_something():
                pass
        """)
        result = testdir.runpytest()
        assert result.ret != 0
        result.stdout.fnmatch_lines([
            "*def gen(qwe123):*",
            "*fixture*qwe123*not found*",
            "*1 error*",
        ])


class TestTestContextVarious:
    def test_newstyle_with_request(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture()
            def arg(request):
                pass
            def test_1(arg):
                pass
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

    def test_setupcontext_no_param(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture(params=[1,2])
            def arg(request):
                return request.param

            @pytest.fixture(autouse=True)
            def mysetup(request, arg):
                assert not hasattr(request, "param")
            def test_1(arg):
                assert arg in (1,2)
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=2)

def test_setupdecorator_and_xunit(testdir):
    testdir.makepyfile("""
        import pytest
        l = []
        @pytest.fixture(scope='module', autouse=True)
        def setup_module():
            l.append("module")
        @pytest.fixture(autouse=True)
        def setup_function():
            l.append("function")

        def test_func():
            pass

        class TestClass:
            @pytest.fixture(scope="class", autouse=True)
            def setup_class(self):
                l.append("class")
            @pytest.fixture(autouse=True)
            def setup_method(self):
                l.append("method")
            def test_method(self):
                pass
        def test_all():
            assert l == ["module", "function", "class",
                         "function", "method", "function"]
    """)
    reprec = testdir.inline_run()
    reprec.assertoutcome(passed=3)



def test_setup_funcarg_order(testdir):
    testdir.makepyfile("""
        import pytest

        l = []
        @pytest.fixture(autouse=True)
        def fix1():
            l.append(1)
        @pytest.fixture()
        def arg1():
            l.append(2)
        def test_hello(arg1):
            assert l == [1,2]
    """)
    reprec = testdir.inline_run()
    reprec.assertoutcome(passed=1)


def test_request_fixturenames(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture()
        def arg1():
            pass
        @pytest.fixture()
        def farg(arg1):
            pass
        @pytest.fixture(autouse=True)
        def sarg(tmpdir):
            pass
        def test_function(request, farg):
            assert set(request.fixturenames) == \
                   set(["tmpdir", "sarg", "arg1", "request", "farg"])
    """)
    reprec = testdir.inline_run()
    reprec.assertoutcome(passed=1)

def test_funcargnames_compatattr(testdir):
    testdir.makepyfile("""
        def pytest_generate_tests(metafunc):
            assert metafunc.funcargnames == metafunc.fixturenames
        def pytest_funcarg__fn(request):
            assert request._pyfuncitem.funcargnames == \
                   request._pyfuncitem.fixturenames
            return request.funcargnames, request.fixturenames

        def test_hello(fn):
            assert fn[0] == fn[1]
    """)
    reprec = testdir.inline_run()
    reprec.assertoutcome(passed=1)

def test_fixtures_sub_subdir_normalize_sep(testdir):
    # this makes sure that normlization of nodeids takes place
    b = testdir.mkdir("tests").mkdir("unit")
    b.join("conftest.py").write(py.code.Source("""
        def pytest_funcarg__arg1():
            pass
    """))
    p = b.join("test_module.py")
    p.write("def test_func(arg1): pass")
    result = testdir.runpytest(p, "--fixtures")
    assert result.ret == 0
    result.stdout.fnmatch_lines("""
        *fixtures defined*conftest*
        *arg1*
    """)
