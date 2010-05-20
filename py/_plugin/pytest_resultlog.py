"""non-xml machine-readable logging of test results. 
   Useful for buildbot integration code.  See the `PyPy-test`_ 
   web page for post-processing. 

.. _`PyPy-test`: http://codespeak.net:8099/summary
 
""" 

import py
from py.builtin import print_

def pytest_addoption(parser):
    group = parser.getgroup("resultlog", "resultlog plugin options")
    group.addoption('--resultlog', action="store", dest="resultlog", metavar="path", default=None,
           help="path for machine-readable result log.")

def pytest_configure(config):
    resultlog = config.option.resultlog
    if resultlog:
        logfile = open(resultlog, 'w', 1) # line buffered
        config._resultlog = ResultLog(config, logfile) 
        config.pluginmanager.register(config._resultlog)

def pytest_unconfigure(config):
    resultlog = getattr(config, '_resultlog', None)
    if resultlog:
        resultlog.logfile.close()
        del config._resultlog 
        config.pluginmanager.unregister(resultlog)

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
    def __init__(self, config, logfile):
        self.config = config
        self.logfile = logfile # preferably line buffered

    def write_log_entry(self, testpath, shortrepr, longrepr):
        print_("%s %s" % (shortrepr, testpath), file=self.logfile)
        for line in longrepr.splitlines():
            print_(" %s" % line, file=self.logfile)

    def log_outcome(self, node, shortrepr, longrepr):
        testpath = generic_path(node)
        self.write_log_entry(testpath, shortrepr, longrepr) 

    def pytest_runtest_logreport(self, report):
        res = self.config.hook.pytest_report_teststatus(report=report)
        if res is not None:
            code = res[1]
        else:
            code = report.shortrepr
        if code == 'x':
            longrepr = str(report.longrepr)
        elif code == 'X':
            longrepr = ''
        elif report.passed:
            longrepr = ""
        elif report.failed:
            longrepr = str(report.longrepr) 
        elif report.skipped:
            longrepr = str(report.longrepr.reprcrash.message)
        self.log_outcome(report.item, code, longrepr) 

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
        self.write_log_entry(path, '!', str(excrepr))
