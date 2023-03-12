def test_tbh_chained(testdir):
    """Ensure chained exceptions whose frames contain "__tracebackhide__" are not shown (#1904)."""
    p = testdir.makepyfile(
        """
        import pytest

        def f1():
            __tracebackhide__ = True
            try:
                return f1.meh
            except AttributeError:
                pytest.fail("fail")

        @pytest.fixture
        def fix():
            f1()


        def test(fix):
            pass
        """
    )
    result = testdir.runpytest(str(p))
    assert "'function' object has no attribute 'meh'" not in result.stdout.str()
    assert result.ret == 1
