"""
   logxml plugin for machine-readable logging of test results. 
   Based on initial code from Ross Lawley.
"""

import py
import time

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption('--xml', action="store", dest="xmlpath", 
           metavar="path", default=None,
           help="create junit-xml style report file at the given path.")

def pytest_configure(config):
    xmlpath = config.option.xmlpath
    if xmlpath:
        config._xml = LogXML(xmlpath)
        config.pluginmanager.register(config._xml)

def pytest_unconfigure(config):
    xml = getattr(config, '_xml', None)
    if xml:
        del config._xml 
        config.pluginmanager.unregister(xml)

class LogXML(object):
    def __init__(self, logfile):
        self.logfile = logfile
        self.test_logs = []
        self.passed = self.skipped = 0
        self.failed = self.errors = 0
        self._durations = {}
  
    def _opentestcase(self, report):
        node = report.item 
        d = {'time': self._durations.pop(report.item, "0")}
        names = [x.replace(".py", "") for x in node.listnames()]
        d['classname'] = ".".join(names[:-1])
        d['name'] = names[-1]
        attrs = ['%s="%s"' % item for item in sorted(d.items())]
        self.test_logs.append("\n<testcase %s>" % " ".join(attrs))

    def _closetestcase(self):
        self.test_logs.append("</testcase>")
         
    def append_pass(self, report):
        self.passed += 1
        self._opentestcase(report)
        self._closetestcase()

    def append_failure(self, report):
        self._opentestcase(report)
        s = py.xml.escape(str(report.longrepr))
        #msg = str(report.longrepr.reprtraceback.extraline)
        self.test_logs.append(
            '<failure message="test failure">%s</failure>' % (s))
        self._closetestcase()
        self.failed += 1

    def _opentestcase_collectfailure(self, report):
        node = report.collector
        d = {'time': '???'}
        names = [x.replace(".py", "") for x in node.listnames()]
        d['classname'] = ".".join(names[:-1])
        d['name'] = names[-1]
        attrs = ['%s="%s"' % item for item in sorted(d.items())]
        self.test_logs.append("\n<testcase %s>" % " ".join(attrs))

    def append_collect_failure(self, report):
        self._opentestcase_collectfailure(report)
        s = py.xml.escape(str(report.longrepr))
        #msg = str(report.longrepr.reprtraceback.extraline)
        self.test_logs.append(
            '<failure message="collection failure">%s</failure>' % (s))
        self._closetestcase()
        self.errors += 1

    def append_collect_skipped(self, report):
        self._opentestcase_collectfailure(report)
        s = py.xml.escape(str(report.longrepr))
        #msg = str(report.longrepr.reprtraceback.extraline)
        self.test_logs.append(
            '<skipped message="collection skipped">%s</skipped>' % (s))
        self._closetestcase()
        self.skipped += 1

    def append_error(self, report):
        self._opentestcase(report)
        s = py.xml.escape(str(report.longrepr))
        self.test_logs.append(
            '<error message="test setup failure">%s</error>' % s)
        self._closetestcase()
        self.errors += 1

    def append_skipped(self, report):
        self._opentestcase(report)
        self.test_logs.append("<skipped/>")
        self._closetestcase()
        self.skipped += 1

    def pytest_runtest_logreport(self, report):
        if report.passed:
            self.append_pass(report)
        elif report.failed:
            if report.when != "call":
                self.append_error(report)
            else:
                self.append_failure(report)
        elif report.skipped:
            self.append_skipped(report)
        
    def pytest_runtest_call(self, item, __multicall__):
        start = time.time()
        try:
            return __multicall__.execute()
        finally:
            self._durations[item] = time.time() - start
    
    def pytest_collectreport(self, report):
        if not report.passed:
            if report.failed:
                self.append_collect_failure(report)
            else:
                self.append_collect_skipped(report)

    def pytest_internalerror(self, excrepr):
        self.errors += 1
        data = py.xml.escape(str(excrepr))
        self.test_logs.append(
            '\n<testcase classname="pytest" name="internal">'
            '    <error message="internal error">'
            '%s</error></testcase>' % data)

    def pytest_sessionstart(self, session):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self, session, exitstatus, __multicall__):
        logfile = open(self.logfile, 'w', 1) # line buffered
        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = self.passed + self.failed
        logfile.write('<testsuite ')
        logfile.write('name="" ')
        logfile.write('errors="%i" ' % self.errors)
        logfile.write('failures="%i" ' % self.failed)
        logfile.write('skips="%i" ' % self.skipped)
        logfile.write('tests="%i" ' % numtests)
        logfile.write('time="%.3f"' % suite_time_delta)
        logfile.write(' >')
        logfile.writelines(self.test_logs)
        logfile.write('</testsuite>')
        logfile.close()
        tw = session.config.pluginmanager.getplugin("terminalreporter")._tw
        tw.line()
        tw.sep("-", "generated xml file: %s" %(self.logfile))
