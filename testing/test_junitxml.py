
from xml.dom import minidom
import py, sys, os

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
        assert_attr(node, errors=0, failures=1, skips=3, tests=2)

    def test_timing_function(self, testdir):
        testdir.makepyfile("""
            import time, pytest
            def test_sleep():
                time.sleep(0.01)
        """)
        result, dom = runandparse(testdir)
        node = dom.getElementsByTagName("testsuite")[0]
        tnode = node.getElementsByTagName("testcase")[0]
        val = tnode.getAttributeNode("time").value
        assert float(val) >= 0.001

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
            classname="test_failure_function",
            name="test_fail")
        fnode = tnode.getElementsByTagName("failure")[0]
        assert_attr(fnode, message="test failure")
        assert "ValueError" in fnode.toxml()
        systemout = fnode.nextSibling
        assert systemout.tagName == "system-out"
        assert "hello-stdout" in systemout.toxml()
        systemerr = systemout.nextSibling
        assert systemerr.tagName == "system-err"
        assert "hello-stderr" in systemerr.toxml()

    def test_failure_escape(self, testdir):
        testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.addcall(id="<", funcargs=dict(arg1=42))
                metafunc.addcall(id="&", funcargs=dict(arg1=44))
            def test_func(arg1):
                assert 0
        """)
        result, dom = runandparse(testdir)
        assert result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, failures=2, tests=2)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            classname="test_failure_escape",
            name="test_func[<]")
        tnode = node.getElementsByTagName("testcase")[1]
        assert_attr(tnode,
            classname="test_failure_escape",
            name="test_func[&]")

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
            classname="xyz.test_junit_prefixing",
            name="test_func")
        tnode = node.getElementsByTagName("testcase")[1]
        assert_attr(tnode,
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
            #classname="test_collect_error",
            name="test_collect_error")
        fnode = tnode.getElementsByTagName("failure")[0]
        assert_attr(fnode, message="collection failure")
        assert "SyntaxError" in fnode.toxml()

    def test_collect_skipped(self, testdir):
        testdir.makepyfile("import pytest; pytest.skip('xyz')")
        result, dom = runandparse(testdir)
        assert not result.ret
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, skips=1, tests=0)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode,
            #classname="test_collect_error",
            name="test_collect_skipped")
        fnode = tnode.getElementsByTagName("skipped")[0]
        assert_attr(fnode, message="collection skipped")

    def test_unicode(self, testdir):
        value = 'hx\xc4\x85\xc4\x87\n'
        testdir.makepyfile("""
            # coding: utf-8
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
        assert_attr(fnode, message="test failure")
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
    result = testdir.runpytest('--junitxml=%s' % xmlf)
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
    result = testdir.runpytest('--junitxml=%s' % xmlf)
    text = xmlf.read()
    assert '#x0' in text


def test_invalid_xml_escape(testdir):
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
    u = py.builtin._totext
    invalid = (0x1, 0xB, 0xC, 0xE, 0x19,)
               # 0xD800, 0xDFFF, 0xFFFE, 0x0FFFF) #, 0x110000)
    valid = (0x9, 0xA, 0x20,) # 0xD, 0xD7FF, 0xE000, 0xFFFD, 0x10000, 0x10FFFF)
    all = invalid + valid
    prints = [u("    sys.stdout.write('''0x%X-->%s<--''')") % (i, unichr(i))
              for i in all]
    testdir.makepyfile(u("# -*- coding: UTF-8 -*-"),
                       u("import sys"),
                       u("def test_print_bytes():"),
                       u("\n").join(prints),
                       u("    assert False"))
    xmlf = testdir.tmpdir.join('junit.xml')
    result = testdir.runpytest('--junitxml=%s' % xmlf)
    text = xmlf.read()
    for i in invalid:
        if i <= 0xFF:
            assert '#x%02X' % i in text
        else:
            assert '#x%04X' % i in text
    for i in valid:
        assert chr(i) in text

def test_logxml_path_expansion():
    from _pytest.junitxml import LogXML

    home_tilde = os.path.normpath(os.path.expanduser('~/test.xml'))
    # this is here for when $HOME is not set correct
    home_var = os.path.normpath(os.path.expandvars('$HOME/test.xml'))

    xml_tilde = LogXML('~/test.xml', None)
    assert xml_tilde.logfile == home_tilde

    xml_var = LogXML('$HOME/test.xml', None)
    assert xml_var.logfile == home_var
