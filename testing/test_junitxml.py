# -*- coding: utf-8 -*-

from xml.dom import minidom
from _pytest.main import EXIT_NOTESTSCOLLECTED
import py, sys, os
from _pytest.junitxml import LogXML
import pytest


def runandparse(testdir, *args):
    resultpath = testdir.tmpdir.join("junit.xml")
    result = testdir.runpytest("--junitxml=%s" % resultpath, *args)
    xmldoc = minidom.parse(str(resultpath))
    return result, xmldoc

def assert_attr(node, **kwargs):
    __tracebackhide__ = True
    for name, expected in kwargs.items():
        anode = node.getAttributeNode(name)
        assert anode, "node %r has no attribute %r" %(node, name)
        val = anode.value
        if val != str(expected):
            py.test.fail("%r != %r" %(str(val), str(expected)))

class TestPython:
    def test_summing_simple(self, testdir):
        testdir.makepyfile("""
            import pytest
            def test_pass():
                pass
            def test_fail():
                assert 0
            def test_skip():
                pytest.skip("")
            @pytest.mark.xfail
            def test_xfail():
                assert 0
            @pytest.mark.xfail
            def test_xpass():
                assert 1
        """)
        result, dom = runandparse(testdir)
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, name="pytest", errors=0, failures=1, skips=3, tests=2)

    def test_timing_function(self, testdir):
        testdir.makepyfile("""
            import time, pytest
            def setup_module():
                time.sleep(0.01)
            def teardown_module():
                time.sleep(0.01)
            def test_sleep():
                time.sleep(0.01)
        """)
        result, dom = runandparse(testdir)
        node = dom.getElementsByTagName("testsuite")[0]
        tnode = node.getElementsByTagName("testcase")[0]
        val = tnode.getAttributeNode("time").value
        assert round(float(val), 2) >= 0.03

    def test_setup_error(self, testdir):
        testdir.makepyfile("""
            def pytest_funcarg__arg(request):
                raise ValueError()
            def test_function(arg):
                pass
        """)
        result, dom = runandparse(testdir)
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, errors=1, tests=0)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            file="test_setup_error.py",
            line="2",
            classname="test_setup_error",
            name="test_function")
        fnode = tnode.getElementsByTagName("error")[0]
        assert_attr(fnode, message="test setup failure")
        assert "ValueError" in fnode.toxml()

    def test_skip_contains_name_reason(self, testdir):
        testdir.makepyfile("""
            import pytest
            def test_skip():
                pytest.skip("hello23")
        """)
        result, dom = runandparse(testdir)
        assert result.ret == 0
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, skips=1)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            file="test_skip_contains_name_reason.py",
            line="1",
            classname="test_skip_contains_name_reason",
            name="test_skip")
        snode = tnode.getElementsByTagName("skipped")[0]
        assert_attr(snode,
            type="pytest.skip",
            message="hello23",
            )

    def test_classname_instance(self, testdir):
        testdir.makepyfile("""
            class TestClass:
                def test_method(self):
                    assert 0
        """)
        result, dom = runandparse(testdir)
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, failures=1)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            file="test_classname_instance.py",
            line="1",
            classname="test_classname_instance.TestClass",
            name="test_method")

    def test_classname_nested_dir(self, testdir):
        p = testdir.tmpdir.ensure("sub", "test_hello.py")
        p.write("def test_func(): 0/0")
        result, dom = runandparse(testdir)
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, failures=1)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            file=os.path.join("sub", "test_hello.py"),
            line="0",
            classname="sub.test_hello",
            name="test_func")

    def test_internal_error(self, testdir):
        testdir.makeconftest("def pytest_runtest_protocol(): 0 / 0")
        testdir.makepyfile("def test_function(): pass")
        result, dom = runandparse(testdir)
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, errors=1, tests=0)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode, classname="pytest", name="internal")
        fnode = tnode.getElementsByTagName("error")[0]
        assert_attr(fnode, message="internal error")
        assert "Division" in fnode.toxml()

    def test_failure_function(self, testdir):
        testdir.makepyfile("""
            import sys
            def test_fail():
                print ("hello-stdout")
                sys.stderr.write("hello-stderr\\n")
                raise ValueError(42)
        """)

        result, dom = runandparse(testdir)
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, failures=1, tests=1)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            file="test_failure_function.py",
            line="1",
            classname="test_failure_function",
            name="test_fail")
        fnode = tnode.getElementsByTagName("failure")[0]
        assert_attr(fnode, message="ValueError: 42")
        assert "ValueError" in fnode.toxml()
        systemout = fnode.nextSibling
        assert systemout.tagName == "system-out"
        assert "hello-stdout" in systemout.toxml()
        systemerr = systemout.nextSibling
        assert systemerr.tagName == "system-err"
        assert "hello-stderr" in systemerr.toxml()

    def test_failure_verbose_message(self, testdir):
        testdir.makepyfile("""
            import sys
            def test_fail():
                assert 0, "An error"
        """)

        result, dom = runandparse(testdir)
        node = dom.getElementsByTagName("testsuite")[0]
        tnode = node.getElementsByTagName("testcase")[0]
        fnode = tnode.getElementsByTagName("failure")[0]
        assert_attr(fnode, message="AssertionError: An error assert 0")

    def test_failure_escape(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.mark.parametrize('arg1', "<&'", ids="<&'")
            def test_func(arg1):
                print(arg1)
                assert 0
        """)
        result, dom = runandparse(testdir)
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, failures=3, tests=3)

        for index, char in enumerate("<&'"):

            tnode = node.getElementsByTagName("testcase")[index]
            assert_attr(tnode,
                file="test_failure_escape.py",
                line="1",
                classname="test_failure_escape",
                name="test_func[%s]" % char)
            sysout = tnode.getElementsByTagName('system-out')[0]
            text = sysout.childNodes[0].wholeText
            assert text == '%s\n' % char


    def test_junit_prefixing(self, testdir):
        testdir.makepyfile("""
            def test_func():
                assert 0
            class TestHello:
                def test_hello(self):
                    pass
        """)
        result, dom = runandparse(testdir, "--junitprefix=xyz")
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, failures=1, tests=2)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            file="test_junit_prefixing.py",
            line="0",
            classname="xyz.test_junit_prefixing",
            name="test_func")
        tnode = node.getElementsByTagName("testcase")[1]
        assert_attr(tnode,
            file="test_junit_prefixing.py",
            line="3",
            classname="xyz.test_junit_prefixing."
                      "TestHello",
            name="test_hello")

    def test_xfailure_function(self, testdir):
        testdir.makepyfile("""
            import pytest
            def test_xfail():
                pytest.xfail("42")
        """)
        result, dom = runandparse(testdir)
        assert not result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, skips=1, tests=0)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            file="test_xfailure_function.py",
            line="1",
            classname="test_xfailure_function",
            name="test_xfail")
        fnode = tnode.getElementsByTagName("skipped")[0]
        assert_attr(fnode, message="expected test failure")
        #assert "ValueError" in fnode.toxml()

    def test_xfailure_xpass(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.mark.xfail
            def test_xpass():
                pass
        """)
        result, dom = runandparse(testdir)
        #assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, skips=1, tests=0)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            file="test_xfailure_xpass.py",
            line="1",
            classname="test_xfailure_xpass",
            name="test_xpass")
        fnode = tnode.getElementsByTagName("skipped")[0]
        assert_attr(fnode, message="xfail-marked test passes unexpectedly")
        #assert "ValueError" in fnode.toxml()

    def test_collect_error(self, testdir):
        testdir.makepyfile("syntax error")
        result, dom = runandparse(testdir)
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, errors=1, tests=0)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            file="test_collect_error.py",
            #classname="test_collect_error",
            name="test_collect_error")
        assert tnode.getAttributeNode("line") is None
        fnode = tnode.getElementsByTagName("error")[0]
        assert_attr(fnode, message="collection failure")
        assert "SyntaxError" in fnode.toxml()

    def test_collect_skipped(self, testdir):
        testdir.makepyfile("import pytest; pytest.skip('xyz')")
        result, dom = runandparse(testdir)
        assert result.ret == EXIT_NOTESTSCOLLECTED
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, skips=1, tests=0)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            file="test_collect_skipped.py",
            #classname="test_collect_error",
            name="test_collect_skipped")
        assert tnode.getAttributeNode("line") is None # py.test doesn't give us a line here.
        fnode = tnode.getElementsByTagName("skipped")[0]
        assert_attr(fnode, message="collection skipped")

    def test_unicode(self, testdir):
        value = 'hx\xc4\x85\xc4\x87\n'
        testdir.makepyfile("""
            # coding: latin1
            def test_hello():
                print (%r)
                assert 0
        """ % value)
        result, dom = runandparse(testdir)
        assert result.ret == 1
        tnode = dom.getElementsByTagName("testcase")[0]
        fnode = tnode.getElementsByTagName("failure")[0]
        if not sys.platform.startswith("java"):
            assert "hx" in fnode.toxml()

    def test_assertion_binchars(self, testdir):
        """this test did fail when the escaping wasnt strict"""
        testdir.makepyfile("""

            M1 = '\x01\x02\x03\x04'
            M2 = '\x01\x02\x03\x05'

            def test_str_compare():
                assert M1 == M2
            """)
        result, dom = runandparse(testdir)
        print(dom.toxml())

    def test_pass_captures_stdout(self, testdir):
        testdir.makepyfile("""
            def test_pass():
                print('hello-stdout')
        """)
        result, dom = runandparse(testdir)
        node = dom.getElementsByTagName("testsuite")[0]
        pnode = node.getElementsByTagName("testcase")[0]
        systemout = pnode.getElementsByTagName("system-out")[0]
        assert "hello-stdout" in systemout.toxml()

    def test_pass_captures_stderr(self, testdir):
        testdir.makepyfile("""
            import sys
            def test_pass():
                sys.stderr.write('hello-stderr')
        """)
        result, dom = runandparse(testdir)
        node = dom.getElementsByTagName("testsuite")[0]
        pnode = node.getElementsByTagName("testcase")[0]
        systemout = pnode.getElementsByTagName("system-err")[0]
        assert "hello-stderr" in systemout.toxml()

def test_mangle_testnames():
    from _pytest.junitxml import mangle_testnames
    names = ["a/pything.py", "Class", "()", "method"]
    newnames = mangle_testnames(names)
    assert newnames == ["a.pything", "Class", "method"]

def test_dont_configure_on_slaves(tmpdir):
    gotten = []
    class FakeConfig:
        def __init__(self):
            self.pluginmanager = self
            self.option = self
        junitprefix = None
        #XXX: shouldnt need tmpdir ?
        xmlpath = str(tmpdir.join('junix.xml'))
        register = gotten.append
    fake_config = FakeConfig()
    from _pytest import junitxml
    junitxml.pytest_configure(fake_config)
    assert len(gotten) == 1
    FakeConfig.slaveinput = None
    junitxml.pytest_configure(fake_config)
    assert len(gotten) == 1


class TestNonPython:
    def test_summing_simple(self, testdir):
        testdir.makeconftest("""
            import pytest
            def pytest_collect_file(path, parent):
                if path.ext == ".xyz":
                    return MyItem(path, parent)
            class MyItem(pytest.Item):
                def __init__(self, path, parent):
                    super(MyItem, self).__init__(path.basename, parent)
                    self.fspath = path
                def runtest(self):
                    raise ValueError(42)
                def repr_failure(self, excinfo):
                    return "custom item runtest failed"
        """)
        testdir.tmpdir.join("myfile.xyz").write("hello")
        result, dom = runandparse(testdir)
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, errors=0, failures=1, skips=0, tests=1)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            #classname="test_collect_error",
            name="myfile.xyz")
        fnode = tnode.getElementsByTagName("failure")[0]
        assert_attr(fnode, message="custom item runtest failed")
        assert "custom item runtest failed" in fnode.toxml()


def test_nullbyte(testdir):
    # A null byte can not occur in XML (see section 2.2 of the spec)
    testdir.makepyfile("""
        import sys
        def test_print_nullbyte():
            sys.stdout.write('Here the null -->' + chr(0) + '<--')
            sys.stdout.write('In repr form -->' + repr(chr(0)) + '<--')
            assert False
    """)
    xmlf = testdir.tmpdir.join('junit.xml')
    testdir.runpytest('--junitxml=%s' % xmlf)
    text = xmlf.read()
    assert '\x00' not in text
    assert '#x00' in text


def test_nullbyte_replace(testdir):
    # Check if the null byte gets replaced
    testdir.makepyfile("""
        import sys
        def test_print_nullbyte():
            sys.stdout.write('Here the null -->' + chr(0) + '<--')
            sys.stdout.write('In repr form -->' + repr(chr(0)) + '<--')
            assert False
    """)
    xmlf = testdir.tmpdir.join('junit.xml')
    testdir.runpytest('--junitxml=%s' % xmlf)
    text = xmlf.read()
    assert '#x0' in text

def test_invalid_xml_escape():
    # Test some more invalid xml chars, the full range should be
    # tested really but let's just thest the edges of the ranges
    # intead.
    # XXX This only tests low unicode character points for now as
    #     there are some issues with the testing infrastructure for
    #     the higher ones.
    # XXX Testing 0xD (\r) is tricky as it overwrites the just written
    #     line in the output, so we skip it too.
    global unichr
    try:
        unichr(65)
    except NameError:
        unichr = chr
    invalid = (0x00, 0x1, 0xB, 0xC, 0xE, 0x19,
                27, # issue #126
               0xD800, 0xDFFF, 0xFFFE, 0x0FFFF) #, 0x110000)
    valid = (0x9, 0xA, 0x20,) # 0xD, 0xD7FF, 0xE000, 0xFFFD, 0x10000, 0x10FFFF)

    from _pytest.junitxml import bin_xml_escape


    for i in invalid:
        got = bin_xml_escape(unichr(i)).uniobj
        if i <= 0xFF:
            expected = '#x%02X' % i
        else:
            expected = '#x%04X' % i
        assert got == expected
    for i in valid:
        assert chr(i) == bin_xml_escape(unichr(i)).uniobj

def test_logxml_path_expansion(tmpdir, monkeypatch):
    home_tilde = py.path.local(os.path.expanduser('~')).join('test.xml')

    xml_tilde = LogXML('~%stest.xml' % tmpdir.sep, None)
    assert xml_tilde.logfile == home_tilde

    # this is here for when $HOME is not set correct
    monkeypatch.setenv("HOME", tmpdir)
    home_var = os.path.normpath(os.path.expandvars('$HOME/test.xml'))

    xml_var = LogXML('$HOME%stest.xml' % tmpdir.sep, None)
    assert xml_var.logfile == home_var

def test_logxml_changingdir(testdir):
    testdir.makepyfile("""
        def test_func():
            import os
            os.chdir("a")
    """)
    testdir.tmpdir.mkdir("a")
    result = testdir.runpytest("--junitxml=a/x.xml")
    assert result.ret == 0
    assert testdir.tmpdir.join("a/x.xml").check()

def test_logxml_makedir(testdir):
    """--junitxml should automatically create directories for the xml file"""
    testdir.makepyfile("""
        def test_pass():
            pass
    """)
    result = testdir.runpytest("--junitxml=path/to/results.xml")
    assert result.ret == 0
    assert testdir.tmpdir.join("path/to/results.xml").check()

def test_escaped_parametrized_names_xml(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.mark.parametrize('char', ["\\x00"])
        def test_func(char):
            assert char
    """)
    result, dom = runandparse(testdir)
    assert result.ret == 0
    node = dom.getElementsByTagName("testcase")[0]
    assert_attr(node,
        name="test_func[#x00]")

def test_unicode_issue368(testdir):
    path = testdir.tmpdir.join("test.xml")
    log = LogXML(str(path), None)
    ustr = py.builtin._totext("ВНИ!", "utf-8")
    from _pytest.runner import BaseReport
    class Report(BaseReport):
        longrepr = ustr
        sections = []
        nodeid = "something"
        location = 'tests/filename.py', 42, 'TestClass.method'
    report = Report()

    # hopefully this is not too brittle ...
    log.pytest_sessionstart()
    log._opentestcase(report)
    log.append_failure(report)
    log.append_collect_error(report)
    log.append_collect_skipped(report)
    log.append_error(report)
    report.longrepr = "filename", 1, ustr
    log.append_skipped(report)
    report.longrepr = "filename", 1, "Skipped: 卡嘣嘣"
    log.append_skipped(report)
    report.wasxfail = ustr
    log.append_skipped(report)
    log.pytest_sessionfinish()


def test_record_property(testdir):
    testdir.makepyfile("""
        def test_record(record_xml_property):
            record_xml_property("foo", "<1");
    """)
    result, dom = runandparse(testdir, '-rw')
    node = dom.getElementsByTagName("testsuite")[0]
    tnode = node.getElementsByTagName("testcase")[0]
    psnode = tnode.getElementsByTagName('properties')[0]
    pnode = psnode.getElementsByTagName('property')[0]
    assert_attr(pnode, name="foo", value="<1")
    result.stdout.fnmatch_lines('*C3*test_record_property.py*experimental*')


def test_random_report_log_xdist(testdir):
    """xdist calls pytest_runtest_logreport as they are executed by the slaves,
    with nodes from several nodes overlapping, so junitxml must cope with that
    to produce correct reports. #1064
    """
    pytest.importorskip('xdist')
    testdir.makepyfile("""
        import pytest, time
        @pytest.mark.parametrize('i', list(range(30)))
        def test_x(i):
            assert i != 22
    """)
    _, dom = runandparse(testdir, '-n2')
    suite_node = dom.getElementsByTagName("testsuite")[0]
    failed = []
    for case_node in suite_node.getElementsByTagName("testcase"):
        if case_node.getElementsByTagName('failure'):
            failed.append(case_node.getAttributeNode('name').value)

    assert failed == ['test_x[22]']
