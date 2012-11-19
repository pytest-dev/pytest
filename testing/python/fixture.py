import pytest, py, sys
from _pytest import python as funcargs
from _pytest.python import FixtureLookupError

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

    def test_conftest_funcargs_only_available_in_subdir(self, testdir):
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

    def test_funcarg_lookup_error(self, testdir):
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

class TestRequestBasic:
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

    def test_request_fixturenames(self, testdir):
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

    def test_funcargnames_compatattr(self, testdir):
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

    def test_setupdecorator_and_xunit(self, testdir):
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

    def test_fixtures_sub_subdir_normalize_sep(self, testdir):
        # this tests that normlization of nodeids takes place
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

class TestRequestMarking:
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

    def test_issue117_sessionscopeteardown(self, testdir):
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

    def test_usefixtures_seen_in_showmarkers(self, testdir):
        result = testdir.runpytest("--markers")
        result.stdout.fnmatch_lines("""
            *usefixtures(fixturename1*mark tests*fixtures*
        """)

    def test_request_instance_issue203(self, testdir):
        testdir.makepyfile("""
            import pytest

            class TestClass:
                @pytest.fixture
                def setup1(self, request):
                    assert self == request.instance
                    self.arg1 = 1
                def test_hello(self, setup1):
                    assert self.arg1 == 1
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1)

class TestFixtureManagerParseFactories:
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

    def test_parsefactories_evil_objects_issue214(self, testdir):
        testdir.makepyfile("""
            class A:
                def __call__(self):
                    pass
                def __getattr__(self, name):
                    raise RuntimeError()
            a = A()
            def test_hello():
                pass
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=1, failed=0)

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
    def test_autouse_conftest_mid_directory(self, testdir):
        pkgdir = testdir.mkpydir("xyz123")
        pkgdir.join("conftest.py").write(py.code.Source("""
            import pytest
            @pytest.fixture(autouse=True)
            def app():
                import sys
                sys._myapp = "hello"
        """))
        t = pkgdir.ensure("tests", "test_app.py")
        t.write(py.code.Source("""
            import sys
            def test_app():
                assert sys._myapp == "hello"
        """))
        reprec = testdir.inline_run("-s")
        reprec.assertoutcome(passed=1)

    def test_autouse_honored_for_yield(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture(autouse=True)
            def tst():
                global x
                x = 3
            def test_gen():
                def f(hello):
                    assert x == abs(hello)
                yield f, 3
                yield f, -3
        """)
        reprec = testdir.inline_run()
        reprec.assertoutcome(passed=2)



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

    def test_ordering_autouse_before_explicit(self, testdir):
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

    @pytest.mark.issue226
    @pytest.mark.parametrize("param1", ["", "params=[1]"])
    @pytest.mark.parametrize("param2", ["", "params=[1]"])
    def test_ordering_dependencies_torndown_first(self, testdir, param1, param2):
        testdir.makepyfile("""
            import pytest
            l = []
            @pytest.fixture(%(param1)s)
            def arg1(request):
                request.addfinalizer(lambda: l.append("fin1"))
                l.append("new1")
            @pytest.fixture(%(param2)s)
            def arg2(request, arg1):
                request.addfinalizer(lambda: l.append("fin2"))
                l.append("new2")

            def test_arg(arg2):
                pass
            def test_check():
                assert l == ["new1", "new2", "fin2", "fin1"]
        """ % locals())
        reprec = testdir.inline_run("-s")
        reprec.assertoutcome(passed=2)

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

    def test_parametrized_fixture_teardown_order(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.fixture(params=[1,2], scope="class")
            def param1(request):
                return request.param

            l = []

            class TestClass:
                @classmethod
                @pytest.fixture(scope="class", autouse=True)
                def setup1(self, request, param1):
                    l.append(1)
                    request.addfinalizer(self.teardown1)
                @classmethod
                def teardown1(self):
                    assert l.pop() == 1
                @pytest.fixture(scope="class", autouse=True)
                def setup2(self, request, param1):
                    l.append(2)
                    request.addfinalizer(self.teardown2)
                @classmethod
                def teardown2(self):
                    assert l.pop() == 2
                def test(self):
                    pass

            def test_finish():
                assert not l
        """)
        result = testdir.runpytest("-v")
        result.stdout.fnmatch_lines("""
            *3 passed*
        """)
        assert "error" not in result.stdout.str()

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

class TestRequestScopeAccess:
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

