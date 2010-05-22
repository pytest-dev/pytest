import py

from py._plugin.pytest_skipping import MarkEvaluator
from py._plugin.pytest_skipping import pytest_runtest_setup
from py._plugin.pytest_runner import runtestprotocol 

class TestEvaluator:
    def test_no_marker(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        evalskipif = MarkEvaluator(item, 'skipif')
        assert not evalskipif
        assert not evalskipif.istrue()

    def test_marked_no_args(self, testdir):
        item = testdir.getitem("""
            import py 
            @py.test.mark.xyz
            def test_func(): 
                pass
        """)
        ev = MarkEvaluator(item, 'xyz')
        assert ev
        assert ev.istrue()
        expl = ev.getexplanation()
        assert expl == ""
        assert not ev.get("run", False)

    def test_marked_one_arg(self, testdir):
        item = testdir.getitem("""
            import py 
            @py.test.mark.xyz("hasattr(os, 'sep')")
            def test_func(): 
                pass
        """)
        ev = MarkEvaluator(item, 'xyz')
        assert ev
        assert ev.istrue()
        expl = ev.getexplanation()
        assert expl == "condition: hasattr(os, 'sep')"

    def test_marked_one_arg_with_reason(self, testdir):
        item = testdir.getitem("""
            import py 
            @py.test.mark.xyz("hasattr(os, 'sep')", attr=2, reason="hello world")
            def test_func(): 
                pass
        """)
        ev = MarkEvaluator(item, 'xyz')
        assert ev
        assert ev.istrue()
        expl = ev.getexplanation()
        assert expl == "hello world"
        assert ev.get("attr") == 2

    def test_marked_one_arg_twice(self, testdir):
        lines = [
            '''@py.test.mark.skipif("not hasattr(os, 'murks')")''',
            '''@py.test.mark.skipif("hasattr(os, 'murks')")'''
        ]
        for i in range(0, 2):
            item = testdir.getitem("""
                import py 
                %s
                %s
                def test_func(): 
                    pass
            """ % (lines[i], lines[(i+1) %2]))
            ev = MarkEvaluator(item, 'skipif')
            assert ev
            assert ev.istrue()
            expl = ev.getexplanation()
            assert expl == "condition: not hasattr(os, 'murks')"

    def test_marked_one_arg_twice2(self, testdir):
        item = testdir.getitem("""
            import py 
            @py.test.mark.skipif("hasattr(os, 'murks')")
            @py.test.mark.skipif("not hasattr(os, 'murks')")
            def test_func(): 
                pass
        """)
        ev = MarkEvaluator(item, 'skipif')
        assert ev
        assert ev.istrue()
        expl = ev.getexplanation()
        assert expl == "condition: not hasattr(os, 'murks')"

    def test_skipif_class(self, testdir):
        item, = testdir.getitems("""
            import py
            class TestClass:
                pytestmark = py.test.mark.skipif("config._hackxyz")
                def test_func(self):
                    pass
        """)
        item.config._hackxyz = 3
        ev = MarkEvaluator(item, 'skipif')
        assert ev.istrue()
        expl = ev.getexplanation()
        assert expl == "condition: config._hackxyz"


class TestXFail:
    def test_xfail_simple(self, testdir):
        item = testdir.getitem("""
            import py 
            @py.test.mark.xfail
            def test_func(): 
                assert 0
        """)
        reports = runtestprotocol(item, log=False)
        assert len(reports) == 3
        callreport = reports[1]
        assert callreport.skipped 
        expl = callreport.keywords['xfail']
        assert expl == ""

    def test_xfail_xpassed(self, testdir):
        item = testdir.getitem("""
            import py 
            @py.test.mark.xfail
            def test_func(): 
                assert 1
        """)
        reports = runtestprotocol(item, log=False)
        assert len(reports) == 3
        callreport = reports[1]
        assert callreport.failed
        expl = callreport.keywords['xfail']
        assert expl == ""

    def test_xfail_run_anyway(self, testdir):
        testdir.makepyfile("""
            import py 
            @py.test.mark.xfail
            def test_func(): 
                assert 0
        """)
        result = testdir.runpytest("--runxfail")
        assert result.ret == 1
        result.stdout.fnmatch_lines([
            "*def test_func():*",
            "*assert 0*",
            "*1 failed*",
        ])

    def test_xfail_evalfalse_but_fails(self, testdir):
        item = testdir.getitem("""
            import py
            @py.test.mark.xfail('False')
            def test_func():
                assert 0
        """)
        reports = runtestprotocol(item, log=False)
        callreport = reports[1]
        assert callreport.failed 
        assert 'xfail' not in callreport.keywords

    def test_xfail_not_report_default(self, testdir):
        p = testdir.makepyfile(test_one="""
            import py
            @py.test.mark.xfail
            def test_this():
                assert 0
        """)
        result = testdir.runpytest(p, '-v')
        #result.stdout.fnmatch_lines([
        #    "*HINT*use*-r*"
        #])

    def test_xfail_not_run_xfail_reporting(self, testdir):
        p = testdir.makepyfile(test_one="""
            import py
            @py.test.mark.xfail(run=False, reason="noway")
            def test_this():
                assert 0
            @py.test.mark.xfail("True", run=False)
            def test_this_true():
                assert 0
            @py.test.mark.xfail("False", run=False, reason="huh")
            def test_this_false():
                assert 1
        """)
        result = testdir.runpytest(p, '--report=xfailed', )
        result.stdout.fnmatch_lines([
            "*test_one*test_this*NOTRUN*noway",
            "*test_one*test_this_true*NOTRUN*condition:*True*",
            "*1 passed*",
        ])

    def test_xfail_xpass(self, testdir):
        p = testdir.makepyfile(test_one="""
            import py
            @py.test.mark.xfail
            def test_that():
                assert 1
        """)
        result = testdir.runpytest(p, '-rX')
        result.stdout.fnmatch_lines([
            "*XPASS*test_that*",
            "*1 xpassed*"
        ])
        assert result.ret == 1

    def test_xfail_imperative(self, testdir):
        p = testdir.makepyfile("""
            import py
            def test_this():
                py.test.xfail("hello")
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            "*1 xfailed*",
        ])
        result = testdir.runpytest(p, "-rx")
        result.stdout.fnmatch_lines([
            "*XFAIL*test_this*reason:*hello*",
        ])
        result = testdir.runpytest(p, "--runxfail")
        result.stdout.fnmatch_lines([
            "*def test_this():*",
            "*py.test.xfail*",
        ])

    def test_xfail_imperative_in_setup_function(self, testdir):
        p = testdir.makepyfile("""
            import py
            def setup_function(function):
                py.test.xfail("hello")
            
            def test_this():
                assert 0
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            "*1 xfailed*",
        ])
        result = testdir.runpytest(p, "-rx")
        result.stdout.fnmatch_lines([
            "*XFAIL*test_this*reason:*hello*",
        ])
        result = testdir.runpytest(p, "--runxfail")
        result.stdout.fnmatch_lines([
            "*def setup_function(function):*",
            "*py.test.xfail*",
        ])





class TestSkipif:
    def test_skipif_conditional(self, testdir):
        item = testdir.getitem("""
            import py 
            @py.test.mark.skipif("hasattr(os, 'sep')")
            def test_func(): 
                pass
        """)
        x = py.test.raises(py.test.skip.Exception, "pytest_runtest_setup(item)")
        assert x.value.msg == "condition: hasattr(os, 'sep')"


    def test_skipif_reporting(self, testdir):
        p = testdir.makepyfile("""
            import py
            @py.test.mark.skipif("hasattr(sys, 'platform')")
            def test_that():
                assert 0
        """)
        result = testdir.runpytest(p, '-s', '-rs')
        result.stdout.fnmatch_lines([
            "*SKIP*1*platform*",
            "*1 skipped*"
        ])
        assert result.ret == 0

def test_skip_not_report_default(testdir):
    p = testdir.makepyfile(test_one="""
        import py
        def test_this():
            py.test.skip("hello")
    """)
    result = testdir.runpytest(p, '-v')
    result.stdout.fnmatch_lines([
        #"*HINT*use*-r*",
        "*1 skipped*",
    ])


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
    result.stdout.fnmatch_lines([
        "*2 skipped*"
    ])


def test_skip_reasons_folding():
    from py._plugin import pytest_runner as runner 
    from py._plugin.pytest_skipping import folded_skips
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
    result.stdout.fnmatch_lines([
        "*test_one.py ss",
        "*test_two.py S",
        "*SKIP*3*conftest.py:3: 'test'", 
    ])
    assert result.ret == 0

def test_reportchars(testdir):
    testdir.makepyfile("""
        import py
        def test_1():
            assert 0
        @py.test.mark.xfail
        def test_2():
            assert 0
        @py.test.mark.xfail
        def test_3():
            pass
        def test_4():
            py.test.skip("four")
    """)
    result = testdir.runpytest("-rfxXs")
    result.stdout.fnmatch_lines([
        "FAIL*test_1*",
        "XFAIL*test_2*",
        "XPASS*test_3*",
        "SKIP*four*",
    ])
