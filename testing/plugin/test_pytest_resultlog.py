import py
import os
from py._plugin.pytest_resultlog import generic_path, ResultLog
from py._test.collect import Node, Item, FSCollector

def test_generic_path(testdir):
    config = testdir.parseconfig()
    p1 = Node('a', parent=config._rootcol)
    #assert p1.fspath is None
    p2 = Node('B', parent=p1)
    p3 = Node('()', parent = p2)
    item = Item('c', parent = p3)

    res = generic_path(item)
    assert res == 'a.B().c'

    p0 = FSCollector('proj/test', parent=config._rootcol)
    p1 = FSCollector('proj/test/a', parent=p0)
    p2 = Node('B', parent=p1)
    p3 = Node('()', parent = p2)
    p4 = Node('c', parent=p3)
    item = Item('[1]', parent = p4)

    res = generic_path(item)
    assert res == 'test/a:B().c[1]'

def test_write_log_entry():
    reslog = ResultLog(None, None)
    reslog.logfile = py.io.TextIO()
    reslog.write_log_entry('name', '.', '')  
    entry = reslog.logfile.getvalue()
    assert entry[-1] == '\n'        
    entry_lines = entry.splitlines()
    assert len(entry_lines) == 1
    assert entry_lines[0] == '. name'

    reslog.logfile = py.io.TextIO()
    reslog.write_log_entry('name', 's', 'Skipped')  
    entry = reslog.logfile.getvalue()
    assert entry[-1] == '\n'        
    entry_lines = entry.splitlines()
    assert len(entry_lines) == 2
    assert entry_lines[0] == 's name'
    assert entry_lines[1] == ' Skipped'

    reslog.logfile = py.io.TextIO()
    reslog.write_log_entry('name', 's', 'Skipped\n')  
    entry = reslog.logfile.getvalue()
    assert entry[-1] == '\n'        
    entry_lines = entry.splitlines()
    assert len(entry_lines) == 2
    assert entry_lines[0] == 's name'
    assert entry_lines[1] == ' Skipped'

    reslog.logfile = py.io.TextIO()
    longrepr = ' tb1\n tb 2\nE tb3\nSome Error'
    reslog.write_log_entry('name', 'F', longrepr)
    entry = reslog.logfile.getvalue()
    assert entry[-1] == '\n'        
    entry_lines = entry.splitlines()
    assert len(entry_lines) == 5
    assert entry_lines[0] == 'F name'
    assert entry_lines[1:] == [' '+line for line in longrepr.splitlines()]

    
class TestWithFunctionIntegration:
    # XXX (hpk) i think that the resultlog plugin should
    # provide a Parser object so that one can remain 
    # ignorant regarding formatting details.  
    def getresultlog(self, testdir, arg):
        resultlog = testdir.tmpdir.join("resultlog")
        testdir.plugins.append("resultlog")
        args = ["--resultlog=%s" % resultlog] + [arg]
        testdir.runpytest(*args)
        return [x for x in resultlog.readlines(cr=0) if x]
        
    def test_collection_report(self, testdir):
        ok = testdir.makepyfile(test_collection_ok="")
        skip = testdir.makepyfile(test_collection_skip="import py ; py.test.skip('hello')")
        fail = testdir.makepyfile(test_collection_fail="XXX")
        lines = self.getresultlog(testdir, ok) 
        assert not lines

        lines = self.getresultlog(testdir, skip)
        assert len(lines) == 2
        assert lines[0].startswith("S ")
        assert lines[0].endswith("test_collection_skip.py")
        assert lines[1].startswith(" ")
        assert lines[1].endswith("test_collection_skip.py:1: Skipped: 'hello'")

        lines = self.getresultlog(testdir, fail)
        assert lines
        assert lines[0].startswith("F ")
        assert lines[0].endswith("test_collection_fail.py"), lines[0]
        for x in lines[1:]:
            assert x.startswith(" ")
        assert "XXX" in "".join(lines[1:])

    def test_log_test_outcomes(self, testdir):
        mod = testdir.makepyfile(test_mod="""
            import py 
            def test_pass(): pass
            def test_skip(): py.test.skip("hello")
            def test_fail(): raise ValueError("FAIL")

            @py.test.mark.xfail
            def test_xfail(): raise ValueError("XFAIL")
            @py.test.mark.xfail
            def test_xpass(): pass            
            
        """)
        lines = self.getresultlog(testdir, mod)
        assert len(lines) >= 3
        assert lines[0].startswith(". ")
        assert lines[0].endswith("test_pass")
        assert lines[1].startswith("s "), lines[1]
        assert lines[1].endswith("test_skip") 
        assert lines[2].find("hello") != -1
       
        assert lines[3].startswith("F ")
        assert lines[3].endswith("test_fail")
        tb = "".join(lines[4:8])
        assert tb.find('raise ValueError("FAIL")') != -1

        assert lines[8].startswith('x ')
        tb = "".join(lines[8:14])
        assert tb.find('raise ValueError("XFAIL")') != -1

        assert lines[14].startswith('X ')
        assert len(lines) == 15

    def test_internal_exception(self):
        # they are produced for example by a teardown failing
        # at the end of the run
        try:
            raise ValueError
        except ValueError:
            excinfo = py.code.ExceptionInfo()
        reslog = ResultLog(None, py.io.TextIO())        
        reslog.pytest_internalerror(excinfo.getrepr())
        entry = reslog.logfile.getvalue()
        entry_lines = entry.splitlines()

        assert entry_lines[0].startswith('! ')
        assert os.path.basename(__file__)[:-9] in entry_lines[0] #.pyc/class
        assert entry_lines[-1][0] == ' '
        assert 'ValueError' in entry  

def test_generic(testdir, LineMatcher):
    testdir.plugins.append("resultlog")
    testdir.makepyfile("""
        import py
        def test_pass():
            pass
        def test_fail():
            assert 0
        def test_skip():
            py.test.skip("")
        @py.test.mark.xfail
        def test_xfail():
            assert 0
        @py.test.mark.xfail(run=False)
        def test_xfail_norun():
            assert 0
    """)
    testdir.runpytest("--resultlog=result.log")
    lines = testdir.tmpdir.join("result.log").readlines(cr=0)
    LineMatcher(lines).fnmatch_lines([
        ". *:test_pass", 
        "F *:test_fail", 
        "s *:test_skip",
        "x *:test_xfail", 
        "x *:test_xfail_norun", 
    ])
    
