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


class Junit(py.xml.Namespace):
    pass


# We need to get the subset of the invalid unicode ranges according to
# XML 1.0 which are valid in this python build.  Hence we calculate
# this dynamically instead of hardcoding it.  The spec range of valid
# chars is: Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD]
#                    | [#x10000-#x10FFFF]
_legal_chars = (0x09, 0x0A, 0x0d)
_legal_ranges = (
    (0x20, 0x7E),
    (0x80, 0xD7FF),
    (0xE000, 0xFFFD),
    (0x10000, 0x10FFFF),
)
_legal_xml_re = [unicode("%s-%s") % (unichr(low), unichr(high))
                  for (low, high) in _legal_ranges
                  if low < sys.maxunicode]
_legal_xml_re = [unichr(x) for x in _legal_chars] + _legal_xml_re
illegal_xml_re = re.compile(unicode('[^%s]') %
                            unicode('').join(_legal_xml_re))
del _legal_chars
del _legal_ranges
del _legal_xml_re

def bin_xml_escape(arg):
    def repl(matchobj):
        i = ord(matchobj.group())
        if i <= 0xFF:
            return unicode('#x%02X') % i
        else:
            return unicode('#x%04X') % i
    return py.xml.raw(illegal_xml_re.sub(repl, py.xml.escape(arg)))

def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting")
    group.addoption('--junitxml', '--junit-xml', action="store",
           dest="xmlpath", metavar="path", default=None,
           help="create junit-xml style report file at given path.")
    group.addoption('--junitprefix', '--junit-prefix', action="store",
           metavar="str", default=None,
           help="prepend prefix to classnames in junit-xml output")

def pytest_configure(config):
    xmlpath = config.option.xmlpath
    # prevent opening xmllog on slave nodes (xdist)
    if xmlpath and not hasattr(config, 'slaveinput'):
        config._xml = LogXML(xmlpath, config.option.junitprefix)
        config.pluginmanager.register(config._xml)

def pytest_unconfigure(config):
    xml = getattr(config, '_xml', None)
    if xml:
        del config._xml
        config.pluginmanager.unregister(xml)


def mangle_testnames(names):
    names = [x.replace(".py", "") for x in names if x != '()']
    names[0] = names[0].replace("/", '.')
    return names

class LogXML(object):
    def __init__(self, logfile, prefix):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.prefix = prefix
        self.tests = []
        self.passed = self.skipped = 0
        self.failed = self.errors = 0

    def _opentestcase(self, report):
        names = mangle_testnames(report.nodeid.split("::"))
        classnames = names[:-1]
        if self.prefix:
            classnames.insert(0, self.prefix)
        self.tests.append(Junit.testcase(
            classname=".".join(classnames),
            name=bin_xml_escape(names[-1]),
            time=getattr(report, 'duration', 0)
        ))

    def _write_captured_output(self, report):
        sec = dict(report.sections)
        for name in ('out', 'err'):
            content = sec.get("Captured std%s" % name)
            if content:
                tag = getattr(Junit, 'system-'+name)
                self.append(tag(bin_xml_escape(content)))

    def append(self, obj):
        self.tests[-1].append(obj)

    def append_pass(self, report):
        self.passed += 1
        self._write_captured_output(report)

    def append_failure(self, report):
        #msg = str(report.longrepr.reprtraceback.extraline)
        if hasattr(report, "wasxfail"):
            self.append(
                Junit.skipped(message="xfail-marked test passes unexpectedly"))
            self.skipped += 1
        else:
            fail = Junit.failure(message="test failure")
            fail.append(bin_xml_escape(report.longrepr))
            self.append(fail)
            self.failed += 1
        self._write_captured_output(report)

    def append_collect_failure(self, report):
        #msg = str(report.longrepr.reprtraceback.extraline)
        self.append(Junit.failure(bin_xml_escape(report.longrepr),
                                  message="collection failure"))
        self.errors += 1

    def append_collect_skipped(self, report):
        #msg = str(report.longrepr.reprtraceback.extraline)
        self.append(Junit.skipped(bin_xml_escape(report.longrepr),
                                  message="collection skipped"))
        self.skipped += 1

    def append_error(self, report):
        self.append(Junit.error(bin_xml_escape(report.longrepr),
                                message="test setup failure"))
        self.errors += 1

    def append_skipped(self, report):
        if hasattr(report, "wasxfail"):
            self.append(Junit.skipped(bin_xml_escape(report.wasxfail),
                                      message="expected test failure"))
        else:
            filename, lineno, skipreason = report.longrepr
            if skipreason.startswith("Skipped: "):
                skipreason = bin_xml_escape(skipreason[9:])
            self.append(
                Junit.skipped("%s:%s: %s" % report.longrepr,
                              type="pytest.skip",
                              message=skipreason
                ))
        self.skipped += 1
        self._write_captured_output(report)

    def pytest_runtest_logreport(self, report):
        if report.passed:
            if report.when == "call": # ignore setup/teardown
                self._opentestcase(report)
                self.append_pass(report)
        elif report.failed:
            self._opentestcase(report)
            if report.when != "call":
                self.append_error(report)
            else:
                self.append_failure(report)
        elif report.skipped:
            self._opentestcase(report)
            self.append_skipped(report)

    def pytest_collectreport(self, report):
        if not report.passed:
            self._opentestcase(report)
            if report.failed:
                self.append_collect_failure(report)
            else:
                self.append_collect_skipped(report)

    def pytest_internalerror(self, excrepr):
        self.errors += 1
        data = bin_xml_escape(excrepr)
        self.tests.append(
            Junit.testcase(
                    Junit.error(data, message="internal error"),
                    classname="pytest",
                    name="internal"))

    def pytest_sessionstart(self):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self):
        if py.std.sys.version_info[0] < 3:
            logfile = py.std.codecs.open(self.logfile, 'w', encoding='utf-8')
        else:
            logfile = open(self.logfile, 'w', encoding='utf-8')

        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = self.passed + self.failed

        logfile.write('<?xml version="1.0" encoding="utf-8"?>')
        logfile.write(Junit.testsuite(
            self.tests,
            name="pytest",
            errors=self.errors,
            failures=self.failed,
            skips=self.skipped,
            tests=numtests,
            time="%.3f" % suite_time_delta,
        ).unicode(indent=0))
        logfile.close()

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep("-", "generated xml file: %s" % (self.logfile))
