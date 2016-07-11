

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


