"""Tests for fixtures with different scoping."""


def test_class_scope_with_normal_tests(testdir):
    testpath = testdir.makepyfile("""
        import pytest

        class Box:
            value = 0

        @pytest.fixture(scope='class')
        def a(request):
            Box.value += 1
            return Box.value

        def test_a(a):
            assert a == 1

        class Test1:
            def test_b(self, a):
                assert a == 2

        class Test2:
            def test_c(self, a):
                assert a == 3""")
    reprec = testdir.inline_run(testpath)
    for test in ['test_a', 'test_b', 'test_c']:
        assert reprec.matchreport(test).passed
