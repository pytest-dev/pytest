"""
   xmlresult plugin for machine-readable logging of test results. 
   Useful for cruisecontrol integration code.
   
   An adaptation of pytest_resultlog.py
"""

import time

def pytest_addoption(parser):
    group = parser.addgroup("xmlresult", "xmlresult plugin options")
    group.addoption('--xmlresult', action="store", dest="xmlresult", metavar="path", default=None,
           help="path for machine-readable xml result log.")

def pytest_configure(config):
    xmlresult = config.option.xmlresult
    if xmlresult:
        logfile = open(xmlresult, 'w', 1) # line buffered
        config._xmlresult = XMLResult(logfile) 
        config.pluginmanager.register(config._xmlresult)

def pytest_unconfigure(config):
    xmlresult = getattr(config, '_xmlresult', None)
    if xmlresult:
        xmlresult.logfile.close()
        del config._xmlresult 
        config.pluginmanager.unregister(xmlresult)

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
        
class XMLResult(object):
    test_start_time = 0.0
    test_taken_time = 0.0
    test_count = 0
    error_count = 0
    failure_count = 0
    skip_count = 0
    
    def __init__(self, logfile):
        self.logfile = logfile
        self.test_logs = []
    
    def write_log_entry(self, testpath, shortrepr, longrepr):
        self.test_count += 1
        # Create an xml log entry for the tests
        self.test_logs.append('<testcase test_method="%s" name="%s" time="%.3f">' % (testpath.split(':')[-1], testpath, self.test_taken_time))
        
        # Do we have any other data to capture for Errors, Fails and Skips
        if shortrepr in ['E', 'F', 'S']:
            
            if shortrepr == 'E':
                self.error_count += 1
            elif shortrepr == 'F':
                self.failure_count += 1
            elif shortrepr == 'S':
                self.skip_count += 1
            
            tag_map = {'E': 'error', 'F': 'failure', 'S': 'skipped'}
            self.test_logs.append("<%s>" % tag_map[shortrepr])
            
            # Output any more information
            for line in longrepr.splitlines():
                self.test_logs.append("<![CDATA[%s\n]]>" % line)
            self.test_logs.append("</%s>" % tag_map[shortrepr])
        self.test_logs.append("</testcase>")

    def log_outcome(self, node, shortrepr, longrepr):
        self.write_log_entry(node.name, shortrepr, longrepr)

    def pytest_runtest_logreport(self, report):
        code = report.shortrepr 
        if report.passed:
            longrepr = ""
            code = "."
        elif report.failed:
            longrepr = str(report.longrepr)
            code = "F"
        elif report.skipped:
            code = "S"
            longrepr = str(report.longrepr.reprcrash.message)
        self.log_outcome(report.item, code, longrepr)
        
    def pytest_runtest_setup(self, item):
        self.test_start_time = time.time()
    
    def pytest_runtest_teardown(self, item):
        self.test_taken_time = time.time() - self.test_start_time
        
    def pytest_collectreport(self, report):
        if not report.passed:
            if report.failed:
                code = "F"
            else:
                assert report.skipped
                code = "S"
            longrepr = str(report.longrepr.reprcrash)
            self.log_outcome(report.collector, code, longrepr)

    def pytest_internalerror(self, excrepr):
        path = excrepr.reprcrash.path
        self.errors += 1
        self.write_log_entry(path, '!', str(excrepr))

    def pytest_sessionstart(self, session):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self, session, exitstatus):
        """
        Write the xml output
        """
        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        self.logfile.write('<testsuite ')
        self.logfile.write('errors="%i" ' % self.error_count)
        self.logfile.write('failures="%i" ' % self.failure_count)
        self.logfile.write('skips="%i" ' % self.skip_count)
        self.logfile.write('name="" ')
        self.logfile.write('tests="%i" ' % self.test_count)
        self.logfile.write('time="%.3f"' % suite_time_delta)
        self.logfile.write(' >')
        self.logfile.writelines(self.test_logs)
        self.logfile.write('</testsuite>')
        self.logfile.close()


# Tests
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
    """)
    testdir.runpytest("--xmlresult=result.xml")
    lines = testdir.tmpdir.join("result.xml").readlines(cr=0)
    LineMatcher(lines).fnmatch_lines([
        '*testsuite errors="0" failures="1" skips="1" name="" tests="3"*'
    ])
    LineMatcher(lines).fnmatch_lines([
        '*<failure><![CDATA[def test_fail():*'
    ])
    LineMatcher(lines).fnmatch_lines([
        '*<skipped><![CDATA[Skipped: <Skipped instance>*'
    ])

def test_generic_path():
    from py.__.test.collect import Node, Item, FSCollector
    p1 = Node('a')
    assert p1.fspath is None
    p2 = Node('B', parent=p1)
    p3 = Node('()', parent = p2)
    item = Item('c', parent = p3)
    res = generic_path(item)
    assert res == 'a.B().c'

    p0 = FSCollector('proj/test')
    p1 = FSCollector('proj/test/a', parent=p0)
    p2 = Node('B', parent=p1)
    p3 = Node('()', parent = p2)
    p4 = Node('c', parent=p3)
    item = Item('[1]', parent = p4)

    res = generic_path(item)
    assert res == 'test/a:B().c[1]'
