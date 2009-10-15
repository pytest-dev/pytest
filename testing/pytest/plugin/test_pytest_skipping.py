import py

def test_xfail_decorator(testdir):
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
        "*1 xfailed*"
    ])
    assert result.ret == 1

def test_xfail_at_module(testdir):
    p = testdir.makepyfile("""
        xfail = 'True'

        def test_intentional_xfail():
            assert 0
    """)
    result = testdir.runpytest(p)
    extra = result.stdout.fnmatch_lines([
        "*expected failures*",
        "*test_intentional_xfail*:4*",
        "*1 xfailed*"
    ])
    assert result.ret == 0

def test_skipif_decorator(testdir):
    p = testdir.makepyfile("""
        import py
        @py.test.mark.skipif("hasattr(sys, 'platform')")
        def test_that():
            assert 0
    """)
    result = testdir.runpytest(p)
    extra = result.stdout.fnmatch_lines([
        "*Skipped*platform*",
        "*1 skipped*"
    ])
    assert result.ret == 0

def test_skipif_class(testdir):
    p = testdir.makepyfile("""
        import py
        class TestClass:
            skipif = "True"
            def test_that(self):
                assert 0
            def test_though(self):
                assert 0
    """)
    result = testdir.runpytest(p)
    extra = result.stdout.fnmatch_lines([
        "*2 skipped*"
    ])

def test_getexpression(testdir):
    from _py.test.plugin.pytest_skipping import getexpression
    l = testdir.getitems("""
        import py
        mod = 5
        class TestClass:
            cls = 4
            @py.test.mark.func(3)
            def test_func(self):
                pass
            @py.test.mark.just
            def test_other(self):
                pass
    """)
    item, item2 = l
    assert getexpression(item, 'xyz') is None
    assert getexpression(item, 'func') == 3
    assert getexpression(item, 'cls') == 4
    assert getexpression(item, 'mod') == 5

    assert getexpression(item2, 'just')

def test_evalexpression_cls_config_example(testdir):
    from _py.test.plugin.pytest_skipping import evalexpression
    item, = testdir.getitems("""
        class TestClass:
            skipif = "config._hackxyz"
            def test_func(self):
                pass
    """)
    item.config._hackxyz = 3
    x, y = evalexpression(item, 'skipif')
    assert x == 'config._hackxyz'
    assert y == 3
