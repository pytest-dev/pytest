
def test_xfail(testdir):
    p = testdir.makepyfile(test_one="""
        import py
        @py.test.mark.xfail
        def test_this():
            assert 0

        @py.test.mark.xfail
        def test_that():
            assert 1
    """)
    result = testdir.runpytest(p)
    extra = result.stdout.fnmatch_lines([
        "*expected failures*",
        "*test_one.test_this*test_one.py:4*",
        "*UNEXPECTEDLY PASSING*",
        "*test_that*",
    ])
    assert result.ret == 1

