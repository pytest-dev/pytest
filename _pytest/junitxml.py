""" report test results in JUnit-XML format, for use with Hudson and build integration servers.

Output conforms to https://github.com/jenkinsci/xunit-plugin/blob/master/src/main/resources/org/jenkinsci/plugins/xunit/types/model/xsd/junit-10.xsd

Based on initial code from Ross Lawley.
"""
import py
import os
import re
import sys
import time
import pytest

# Python 2.X and 3.X compatibility
if sys.version_info[0] < 3:
    from codecs import open
else:
    unichr = chr
    unicode = str
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

@pytest.fixture
def record_xml_property(request):
    """Fixture that adds extra xml properties to the tag for the calling test.
    The fixture is callable with (name, value), with value being automatically
    xml-encoded.
    """
    def inner(name, value):
        if hasattr(request.config, "_xml"):
            request.config._xml.add_custom_property(name, value)
        msg = 'record_xml_property is an experimental feature'
        request.config.warn(code='C3', message=msg,
                            fslocation=request.node.location[:2])
    return inner

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
        self.tests_by_nodeid = {}  # nodeid -> Junit.testcase
        self.durations = {}  # nodeid -> total duration (setup+call+teardown)
        self.passed = self.skipped = 0
        self.failed = self.errors = 0
        self.custom_properties = {}

    def add_custom_property(self, name, value):
        self.custom_properties[str(name)] = bin_xml_escape(str(value))

    def _opentestcase(self, report):
        names = mangle_testnames(report.nodeid.split("::"))
        classnames = names[:-1]
        if self.prefix:
            classnames.insert(0, self.prefix)
        attrs = {
            "classname": ".".join(classnames),
            "name": bin_xml_escape(names[-1]),
            "file": report.location[0],
            "time": self.durations.get(report.nodeid, 0),
        }
        if report.location[1] is not None:
            attrs["line"] = report.location[1]
        testcase = Junit.testcase(**attrs)
        custom_properties = self.pop_custom_properties()
        if custom_properties:
            testcase.append(custom_properties)
        self.tests.append(testcase)
        self.tests_by_nodeid[report.nodeid] = testcase

    def _write_captured_output(self, report):
        for capname in ('out', 'err'):
            allcontent = ""
            for name, content in report.get_sections("Captured std%s" %
                                                    capname):
                allcontent += content
            if allcontent:
                tag = getattr(Junit, 'system-'+capname)
                self.append(tag(bin_xml_escape(allcontent)))

    def append(self, obj):
        self.tests[-1].append(obj)

    def pop_custom_properties(self):
        """Return a Junit node containing custom properties set for
        the current test, if any, and reset the current custom properties.
        """
        if self.custom_properties:
            result = Junit.properties(
                [
                    Junit.property(name=name, value=value)
                    for name, value in self.custom_properties.items()
                ]
            )
            self.custom_properties.clear()
            return result
        return None

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
            if hasattr(report.longrepr, "reprcrash"):
                message = report.longrepr.reprcrash.message
            elif isinstance(report.longrepr, (unicode, str)):
                message = report.longrepr
            else:
                message = str(report.longrepr)
            message = bin_xml_escape(message)
            fail = Junit.failure(message=message)
            fail.append(bin_xml_escape(report.longrepr))
            self.append(fail)
            self.failed += 1
        self._write_captured_output(report)

    def append_collect_error(self, report):
        #msg = str(report.longrepr.reprtraceback.extraline)
        self.append(Junit.error(bin_xml_escape(report.longrepr),
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
                Junit.skipped("%s:%s: %s" % (filename, lineno, skipreason),
                              type="pytest.skip",
                              message=skipreason
                ))
        self.skipped += 1
        self._write_captured_output(report)

    def pytest_runtest_logreport(self, report):
        """handle a setup/call/teardown report, generating the appropriate
        xml tags as necessary.

        note: due to plugins like xdist, this hook may be called in interlaced
        order with reports from other nodes. for example:

        usual call order:
            -> setup node1
            -> call node1
            -> teardown node1
            -> setup node2
            -> call node2
            -> teardown node2

        possible call order in xdist:
            -> setup node1
            -> call node1
            -> setup node2
            -> call node2
            -> teardown node2
            -> teardown node1
        """
        if report.passed:
            if report.when == "call":  # ignore setup/teardown
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
        self.update_testcase_duration(report)

    def update_testcase_duration(self, report):
        """accumulates total duration for nodeid from given report and updates
        the Junit.testcase with the new total if already created.
        """
        total = self.durations.get(report.nodeid, 0.0)
        total += getattr(report, 'duration', 0.0)
        self.durations[report.nodeid] = total

        testcase = self.tests_by_nodeid.get(report.nodeid)
        if testcase is not None:
            testcase.attr.time = total

    def pytest_collectreport(self, report):
        if not report.passed:
            self._opentestcase(report)
            if report.failed:
                self.append_collect_error(report)
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
        dirname = os.path.dirname(os.path.abspath(self.logfile))
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
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
