import py

class ResultlogPlugin:
    """resultlog plugin for machine-readable logging of test results. 
       Useful for buildbot integration code. 
    """ 
    def pytest_addoption(self, parser):
        group = parser.addgroup("resultlog", "resultlog plugin options")
        group.addoption('--resultlog', action="store", dest="resultlog", metavar="path",
               help="path for machine-readable result log.")
    
    def pytest_configure(self, config):
        resultlog = config.option.resultlog
        if resultlog:
            logfile = open(resultlog, 'w', 1) # line buffered
            self.resultlog = ResultLog(logfile) 
            config.bus.register(self.resultlog)

    def pytest_unconfigure(self, config):
        if hasattr(self, 'resultlog'):
            self.resultlog.logfile.close()
            del self.resultlog 
            #config.bus.unregister(self.resultlog)

def generic_path(item):
    chain = item.listchain()
    gpath = [chain[0].name]
    fspath = chain[0].fspath
    fspart = False
    for node in chain[1:]:
        newfspath = node.fspath
        if newfspath == fspath:
            if fspart:
                gpath.append(':')
                fspart = False
            else:
                gpath.append('.')            
        else:
            gpath.append('/')
            fspart = True
        name = node.name
        if name[0] in '([':
            gpath.pop()
        gpath.append(name)
        fspath = newfspath
    return ''.join(gpath)
        
class ResultLog(object):
    def __init__(self, logfile):
        self.logfile = logfile # preferably line buffered

    def write_log_entry(self, testpath, shortrepr, longrepr):
        print >>self.logfile, "%s %s" % (shortrepr, testpath)
        for line in longrepr.splitlines():
            print >>self.logfile, " %s" % line

    def log_outcome(self, event, shortrepr, longrepr):
        testpath = generic_path(event.colitem)
        self.write_log_entry(testpath, shortrepr, longrepr) 

    def pyevent__itemtestreport(self, rep):
        code = rep.shortrepr 
        if rep.passed:
            longrepr = ""
        elif rep.failed:
            longrepr = str(rep.longrepr) 
        elif rep.skipped:
            longrepr = str(rep.longrepr.reprcrash.message)
        self.log_outcome(rep, code, longrepr) 

    def pyevent__collectreport(self, rep):
        if not rep.passed:
            if rep.failed: 
                code = "F"
            else:
                assert rep.skipped
                code = "S"
            longrepr = str(rep.longrepr.reprcrash)
            self.log_outcome(rep, code, longrepr)    

    def pyevent__internalerror(self, excrepr):
        path = excrepr.reprcrash.path 
        self.write_log_entry(path, '!', str(excrepr))


# ===============================================================================
#
# plugin tests 
#
# ===============================================================================

import os, StringIO

def test_generic_path():
    from py.__.test.collect import Node, Item, FSCollector
    p1 = Node('a', config='dummy')
    assert p1.fspath is None
    p2 = Node('B', parent=p1)
    p3 = Node('()', parent = p2)
    item = Item('c', parent = p3)

    res = generic_path(item)
    assert res == 'a.B().c'

    p0 = FSCollector('proj/test', config='dummy')
    p1 = FSCollector('proj/test/a', parent=p0)
    p2 = Node('B', parent=p1)
    p3 = Node('()', parent = p2)
    p4 = Node('c', parent=p3)
    item = Item('[1]', parent = p4)

    res = generic_path(item)
    assert res == 'test/a:B().c[1]'

def test_write_log_entry():
    reslog = ResultLog(None)
    reslog.logfile = StringIO.StringIO()
    reslog.write_log_entry('name', '.', '')  
    entry = reslog.logfile.getvalue()
    assert entry[-1] == '\n'        
    entry_lines = entry.splitlines()
    assert len(entry_lines) == 1
    assert entry_lines[0] == '. name'

    reslog.logfile = StringIO.StringIO()
    reslog.write_log_entry('name', 's', 'Skipped')  
    entry = reslog.logfile.getvalue()
    assert entry[-1] == '\n'        
    entry_lines = entry.splitlines()
    assert len(entry_lines) == 2
    assert entry_lines[0] == 's name'
    assert entry_lines[1] == ' Skipped'

    reslog.logfile = StringIO.StringIO()
    reslog.write_log_entry('name', 's', 'Skipped\n')  
    entry = reslog.logfile.getvalue()
    assert entry[-1] == '\n'        
    entry_lines = entry.splitlines()
    assert len(entry_lines) == 2
    assert entry_lines[0] == 's name'
    assert entry_lines[1] == ' Skipped'

    reslog.logfile = StringIO.StringIO()
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
        args = ["--resultlog=%s" % resultlog] + [arg]
        testdir.runpytest(*args)
        return filter(None, resultlog.readlines(cr=0))
        
    def test_collection_report(self, plugintester):
        testdir = plugintester.testdir()
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

    def test_log_test_outcomes(self, plugintester):
        testdir = plugintester.testdir()
        mod = testdir.makepyfile(test_mod="""
            import py 
            def test_pass(): pass
            def test_skip(): py.test.skip("hello")
            def test_fail(): raise ValueError("val")
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
        tb = "".join(lines[4:])
        assert tb.find("ValueError") != -1 

    def test_internal_exception(self):
        # they are produced for example by a teardown failing
        # at the end of the run
        try:
            raise ValueError
        except ValueError:
            excinfo = py.code.ExceptionInfo()
        reslog = ResultLog(StringIO.StringIO())        
        reslog.pyevent__internalerror(excinfo.getrepr())
        entry = reslog.logfile.getvalue()
        entry_lines = entry.splitlines()

        assert entry_lines[0].startswith('! ')
        assert os.path.basename(__file__)[:-1] in entry_lines[0] #.py/.pyc
        assert entry_lines[-1][0] == ' '
        assert 'ValueError' in entry  

def test_generic(plugintester, LineMatcher):
    plugintester.apicheck(ResultlogPlugin)
    testdir = plugintester.testdir()
    testdir.makepyfile("""
        import py
        def test_pass():
            pass
        def test_fail():
            assert 0
        def test_skip():
            py.test.skip("")
    """)
    testdir.runpytest("--resultlog=result.log")
    lines = testdir.tmpdir.join("result.log").readlines(cr=0)
    LineMatcher(lines).fnmatch_lines([
        ". *:test_pass", 
        "F *:test_fail", 
        "s *:test_skip", 
    ])
    
