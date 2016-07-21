
def test_invocation_request(testdir):
    """
    Simple test case with session and module scopes requesting an
    invocation-scoped fixture.
    """
    testdir.makeconftest("""
        import pytest

        @pytest.fixture(scope='invocation')
        def my_name(request):
            if request.scope == 'function':
                return request.function.__name__
            elif request.scope == 'module':
                return request.module.__name__
            elif request.scope == 'session':
                return '<session>'

        @pytest.fixture(scope='session')
        def session_name(my_name):
            return my_name

        @pytest.fixture(scope='module')
        def module_name(my_name):
            return my_name
    """)
    testdir.makepyfile(test_module_foo="""
        def test_foo(my_name, module_name, session_name):
            assert my_name == 'test_foo'
            assert module_name == 'test_module_foo'
            assert session_name == '<session>'
    """)
    testdir.makepyfile(test_module_bar="""
        def test_bar(my_name, module_name, session_name):
            assert my_name == 'test_bar'
            assert module_name == 'test_module_bar'
            assert session_name == '<session>'
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*2 passed*'])


def test_override_invocation_scoped(testdir):
    """Test that it's possible to override invocation-scoped fixtures."""
    testdir.makeconftest("""
        import pytest

        @pytest.fixture(scope='invocation')
        def magic_value(request):
            if request.scope == 'function':
                return 1
            elif request.scope == 'module':
                return 100

        @pytest.fixture(scope='module')
        def module_magic_value(magic_value):
            return magic_value * 2
    """)
    testdir.makepyfile(test_module_override="""
        import pytest

        @pytest.fixture(scope='module')
        def magic_value():
            return 42

        def test_override(magic_value, module_magic_value):
            assert magic_value == 42
            assert module_magic_value == 42 * 2
    """)
    testdir.makepyfile(test_normal="""
        def test_normal(magic_value, module_magic_value):
            assert magic_value == 1
            assert module_magic_value == 200
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*2 passed*'])


class TestAcceptance:
    """
    Complete acceptance test for a invocation-scoped fixture.
    """

    def test_acceptance(self, testdir):
        """
        Tests a "stack" fixture which provides a separate list to each scope which uses it.

        Some notes:

        - For each scope, define 2 fixtures of the same scope which use the "stack" fixture,
          to ensure they get the same "stack" instance for that scope.
        - Creates multiple test files, which tests on each modifying and checking fixtures to
          ensure things are working properly.
        """
        testdir.makeconftest("""
            import pytest

            @pytest.fixture(scope='invocation')
            def stack():
                return []

            @pytest.fixture(scope='session')
            def session1_fix(stack):
                stack.append('session1_fix')
                return stack

            @pytest.fixture(scope='session')
            def session2_fix(stack):
                stack.append('session2_fix')
                return stack

            @pytest.fixture(scope='module')
            def module1_fix(stack):
                stack.append('module1_fix')
                return stack

            @pytest.fixture(scope='module')
            def module2_fix(stack):
                stack.append('module2_fix')
                return stack

            @pytest.fixture(scope='class')
            def class1_fix(stack):
                stack.append('class1_fix')
                return stack

            @pytest.fixture(scope='class')
            def class2_fix(stack):
                stack.append('class2_fix')
                return stack
        """)
        testdir.makepyfile(test_0="""
            import pytest

            @pytest.fixture
            def func_stack(stack):
                return stack

            def test_scoped_instances(session1_fix, session2_fix, module1_fix, module2_fix,
                                      class1_fix, class2_fix, stack, func_stack):
                assert session1_fix is session2_fix
                assert module1_fix is module2_fix
                assert class1_fix is class2_fix
                assert stack is func_stack

                assert session1_fix is not module2_fix
                assert module2_fix is not class1_fix
                assert class1_fix is not stack
        """)
        testdir.makepyfile(test_1="""
            def test_func_1(request, session1_fix, session2_fix, module1_fix, module2_fix, stack):
                assert stack == []

                assert session1_fix == ['session1_fix', 'session2_fix']
                session1_fix.append('test_1::test_func_1')

                assert module1_fix == ['module1_fix', 'module2_fix']
                module1_fix.append('test_1::test_func_1')


            class Test:

                def test_1(self, request, session1_fix, module1_fix, class1_fix, class2_fix, stack):
                    assert stack == []

                    assert session1_fix == ['session1_fix', 'session2_fix', 'test_1::test_func_1']
                    session1_fix.append('test_1::Test::test_1')

                    assert module1_fix == ['module1_fix', 'module2_fix', 'test_1::test_func_1']
                    module1_fix.append('test_1::test_func_1')

                    assert class1_fix == ['class1_fix', 'class2_fix']
                    class1_fix.append('test_1::Test::test_1')

                def test_2(self, request, class1_fix, class2_fix):
                    assert class1_fix == ['class1_fix', 'class2_fix', 'test_1::Test::test_1']
                    class1_fix.append('Test.test_2')


            def test_func_2(request, session1_fix, session2_fix, module1_fix, class1_fix, class2_fix, stack):
                assert stack == []
                assert session1_fix == ['session1_fix', 'session2_fix', 'test_1::test_func_1',
                                        'test_1::Test::test_1']
                session1_fix.append('test_1::test_func_2')

                assert module1_fix == ['module1_fix', 'module2_fix', 'test_1::test_func_1', 'test_1::test_func_1']

                assert class1_fix == ['class1_fix', 'class2_fix']
        """)
        testdir.makepyfile(test_2="""
            import pytest

            @pytest.fixture(scope='session')
            def another_session_stack(stack):
                stack.append('other_session_stack')
                return stack

            def test_func_2(request, another_session_stack, module1_fix, stack):
                assert stack == []
                assert another_session_stack == [
                    'session1_fix',
                    'session2_fix',
                    'test_1::test_func_1',
                    'test_1::Test::test_1',
                    'test_1::test_func_2',
                    'other_session_stack',
                    ]
                assert module1_fix == ['module1_fix']
        """)
        result = testdir.runpytest()
        assert result.ret == 0
        result.stdout.fnmatch_lines('* 6 passed in *')


