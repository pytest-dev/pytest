import py

def test_xfail_not_report_default(testdir):
    p = testdir.makepyfile(test_one="""
        import py
        @py.test.mark.xfail
        def test_this():
            assert 0
    """)
    result = testdir.runpytest(p, '-v')
    extra = result.stdout.fnmatch_lines([
        "*1 expected failures*--report=xfailed*",
    ])

def test_skip_not_report_default(testdir):
    p = testdir.makepyfile(test_one="""
        import py
        def test_this():
            py.test.skip("hello")
    """)
    result = testdir.runpytest(p, '-v')
    extra = result.stdout.fnmatch_lines([
        "*1 skipped*--report=skipped*",
    ])

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
    result = testdir.runpytest(p, '--report=xfailed')
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
        import py
        pytestmark = py.test.mark.xfail('True')
        def test_intentional_xfail():
            assert 0
    """)
    result = testdir.runpytest(p, '--report=xfailed')
    extra = result.stdout.fnmatch_lines([
        "*expected failures*",
        "*test_intentional_xfail*:4*",
        "*1 xfailed*"
    ])
    assert result.ret == 0

def test_xfail_evalfalse_but_fails(testdir):
    p = testdir.makepyfile("""
        import py
        @py.test.mark.xfail('False')
        def test_fail():
            assert 0
    """)
    result = testdir.runpytest(p, '--report=xfailed')
    extra = result.stdout.fnmatch_lines([
        "*test_xfail_evalfalse_but_fails*:4*",
        "*1 failed*"
    ])
    assert result.ret == 1

def test_skipif_decorator(testdir):
    p = testdir.makepyfile("""
        import py
        @py.test.mark.skipif("hasattr(sys, 'platform')")
        def test_that():
            assert 0
    """)
    result = testdir.runpytest(p, '--report=skipped')
    extra = result.stdout.fnmatch_lines([
        "*Skipped*platform*",
        "*1 skipped*"
    ])
    assert result.ret == 0

def test_skipif_class(testdir):
    p = testdir.makepyfile("""
        import py
        
        class TestClass:
            pytestmark = py.test.mark.skipif("True")
            def test_that(self):
                assert 0
            def test_though(self):
                assert 0
    """)
    result = testdir.runpytest(p)
    extra = result.stdout.fnmatch_lines([
        "*2 skipped*"
    ])

def test_evalexpression_cls_config_example(testdir):
    from _py.test.plugin.pytest_skipping import evalexpression
    item, = testdir.getitems("""
        import py
        class TestClass:
            pytestmark = py.test.mark.skipif("config._hackxyz")
            def test_func(self):
                pass
    """)
    item.config._hackxyz = 3
    x, y = evalexpression(item, 'skipif')
    assert x == 'config._hackxyz'
    assert y == 3

def test_skip_reasons_folding():
    from _py.test.plugin import pytest_runner as runner 
    from _py.test.plugin.pytest_skipping import folded_skips
    class longrepr:
        class reprcrash:
            path = 'xyz'
            lineno = 3
            message = "justso"

    ev1 = runner.CollectReport(None, None)
    ev1.when = "execute"
    ev1.skipped = True
    ev1.longrepr = longrepr 
    
    ev2 = runner.ItemTestReport(None, excinfo=longrepr)
    ev2.skipped = True

    l = folded_skips([ev1, ev2])
    assert len(l) == 1
    num, fspath, lineno, reason = l[0]
    assert num == 2
    assert fspath == longrepr.reprcrash.path
    assert lineno == longrepr.reprcrash.lineno
    assert reason == longrepr.reprcrash.message

def test_skipped_reasons_functional(testdir):
    testdir.makepyfile(
        test_one="""
            from conftest import doskip
            def setup_function(func):
                doskip()
            def test_func():
                pass
            class TestClass:
                def test_method(self):
                    doskip()
       """,
       test_two = """
            from conftest import doskip
            doskip()
       """,
       conftest = """
            import py
            def doskip():
                py.test.skip('test')
        """
    )
    result = testdir.runpytest('--report=skipped') 
    extra = result.stdout.fnmatch_lines([
        "*test_one.py ss",
        "*test_two.py S",
        "___* skipped test summary *_", 
        "*conftest.py:3: *3* Skipped: 'test'", 
    ])
    assert result.ret == 0

