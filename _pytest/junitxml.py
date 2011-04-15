""" report test results in JUnit-XML format, for use with Hudson and build integration servers.

Based on initial code from Ross Lawley.
"""

import py
import os
import re
import sys
import time


# Python 2.X and 3.X compatibility
try:
    unichr(65)
except NameError:
    unichr = chr
try:
    unicode('A')
except NameError:
    unicode = str
try:
    long(1)
except NameError:
    long = int


# We need to get the subset of the invalid unicode ranges according to
# XML 1.0 which are valid in this python build.  Hence we calculate
# this dynamically instead of hardcoding it.  The spec range of valid
# chars is: Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD]
#                    | [#x10000-#x10FFFF]
_illegal_unichrs = [(0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x19),
                   (0xD800, 0xDFFF), (0xFDD0, 0xFFFF)]
_illegal_ranges = [unicode("%s-%s") % (unichr(low), unichr(high))
                  for (low, high) in _illegal_unichrs
                  if low < sys.maxunicode]
illegal_xml_re = re.compile(unicode('[%s]') %
                            unicode('').join(_illegal_ranges))
del _illegal_unichrs
del _illegal_ranges


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting")
    group.addoption('--junitxml', action="store", dest="xmlpath",
           metavar="path", default=None,
           help="create junit-xml style report file at given path.")
    group.addoption('--junitprefix', action="store", dest="junitprefix",
           metavar="str", default=None,
           help="prepend prefix to classnames in junit-xml output")

def pytest_configure(config):
    xmlpath = config.option.xmlpath
    if xmlpath:
        config._xml = LogXML(xmlpath, config.option.junitprefix)
        config.pluginmanager.register(config._xml)

def pytest_unconfigure(config):
    xml = getattr(config, '_xml', None)
    if xml:
        del config._xml
        config.pluginmanager.unregister(xml)


class LogXML(object):
    def __init__(self, logfile, prefix):
        self.logfile = logfile
        self.prefix = prefix
        self.test_logs = []
        self.passed = self.skipped = 0
        self.failed = self.errors = 0
        self._durations = {}

    def _opentestcase(self, report):
        names = report.nodeid.split("::")
        names[0] = names[0].replace("/", '.')
        names = tuple(names)
        d = {'time': self._durations.pop(names, "0")}
        names = [x.replace(".py", "") for x in names if x != "()"]
        classnames = names[:-1]
        if self.prefix:
            classnames.insert(0, self.prefix)
        d['classname'] = ".".join(classnames)
        d['name'] = py.xml.escape(names[-1])
        attrs = ['%s="%s"' % item for item in sorted(d.items())]
        self.test_logs.append("\n<testcase %s>" % " ".join(attrs))

    def _closetestcase(self):
        self.test_logs.append("</testcase>")

    def appendlog(self, fmt, *args):
        def repl(matchobj):
            i = ord(matchobj.group())
            if i <= 0xFF:
                return unicode('#x%02X') % i
            else:
                return unicode('#x%04X') % i
        args = tuple([illegal_xml_re.sub(repl, py.xml.escape(arg))
                      for arg in args])
        self.test_logs.append(fmt % args)

    def append_pass(self, report):
        self.passed += 1
        self._opentestcase(report)
        self._closetestcase()

    def append_failure(self, report):
        self._opentestcase(report)
        #msg = str(report.longrepr.reprtraceback.extraline)
        if "xfail" in report.keywords:
            self.appendlog(
                '<skipped message="xfail-marked test passes unexpectedly"/>')
            self.skipped += 1
        else:
            self.appendlog('<failure message="test failure">%s</failure>',
                report.longrepr)
            self.failed += 1
        self._closetestcase()

    def append_collect_failure(self, report):
        self._opentestcase(report)
        #msg = str(report.longrepr.reprtraceback.extraline)
        self.appendlog('<failure message="collection failure">%s</failure>',
            report.longrepr)
        self._closetestcase()
        self.errors += 1

    def append_collect_skipped(self, report):
        self._opentestcase(report)
        #msg = str(report.longrepr.reprtraceback.extraline)
        self.appendlog('<skipped message="collection skipped">%s</skipped>',
            report.longrepr)
        self._closetestcase()
        self.skipped += 1

    def append_error(self, report):
        self._opentestcase(report)
        self.appendlog('<error message="test setup failure">%s</error>',
            report.longrepr)
        self._closetestcase()
        self.errors += 1

    def append_skipped(self, report):
        self._opentestcase(report)
        if "xfail" in report.keywords:
            self.appendlog(
                '<skipped message="expected test failure">%s</skipped>',
                report.keywords['xfail'])
        else:
            filename, lineno, skipreason = report.longrepr
            if skipreason.startswith("Skipped: "):
                skipreason = skipreason[9:]
            self.appendlog('<skipped type="pytest.skip" '
                           'message="%s">%s</skipped>',
                skipreason, "%s:%s: %s" % report.longrepr,
                )
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
        names = tuple(item.listnames())
        start = time.time()
        try:
            return __multicall__.execute()
        finally:
            self._durations[names] = time.time() - start

    def pytest_collectreport(self, report):
        if not report.passed:
            if report.failed:
                self.append_collect_failure(report)
            else:
                self.append_collect_skipped(report)

    def pytest_internalerror(self, excrepr):
        self.errors += 1
        data = py.xml.escape(excrepr)
        self.test_logs.append(
            '\n<testcase classname="pytest" name="internal">'
            '    <error message="internal error">'
            '%s</error></testcase>' % data)

    def pytest_sessionstart(self, session):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self, session, exitstatus, __multicall__):
        if py.std.sys.version_info[0] < 3:
            logfile = py.std.codecs.open(self.logfile, 'w', encoding='utf-8')
        else:
            logfile = open(self.logfile, 'w', encoding='utf-8')

        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = self.passed + self.failed
        logfile.write('<?xml version="1.0" encoding="utf-8"?>')
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

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep("-", "generated xml file: %s" % (self.logfile))
