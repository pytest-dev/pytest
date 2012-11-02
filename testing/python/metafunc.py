import pytest, py, sys
from _pytest import python as funcargs
from _pytest.python import FixtureLookupError

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


