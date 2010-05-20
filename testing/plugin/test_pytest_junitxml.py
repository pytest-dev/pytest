
from xml.dom import minidom
import py, sys

def runandparse(testdir, *args):
    resultpath = testdir.tmpdir.join("junit.xml")
    result = testdir.runpytest("--junitxml=%s" % resultpath, *args)
    xmldoc = minidom.parse(str(resultpath))
    return result, xmldoc

def assert_attr(node, **kwargs):
    for name, expected in kwargs.items():
        anode = node.getAttributeNode(name)
        assert anode, "node %r has no attribute %r" %(node, name)
        val = anode.value 
        assert val == str(expected)

class TestPython:
    def test_summing_simple(self, testdir):
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
            @py.test.mark.xfail
            def test_xpass():
                assert 1
        """)
        result, dom = runandparse(testdir)
        assert result.ret 
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, errors=0, failures=1, skips=3, tests=2)

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
            classname="test_setup_error.test_setup_error", 
            name="test_function")
        fnode = tnode.getElementsByTagName("error")[0]
        assert_attr(fnode, message="test setup failure")
        assert "ValueError" in fnode.toxml()

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
            classname="test_classname_instance.test_classname_instance.TestClass",
            name="test_method")

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
        testdir.makepyfile("def test_fail(): raise ValueError(42)")
        result, dom = runandparse(testdir)
        assert result.ret 
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, failures=1, tests=1)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode, 
            classname="test_failure_function.test_failure_function", 
            name="test_fail")
        fnode = tnode.getElementsByTagName("failure")[0]
        assert_attr(fnode, message="test failure")
        assert "ValueError" in fnode.toxml()

    def test_xfailure_function(self, testdir):
        testdir.makepyfile("""
            import py
            def test_xfail():
                py.test.xfail("42")
        """)
        result, dom = runandparse(testdir)
        assert not result.ret 
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, skips=1, tests=0)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode, 
            classname="test_xfailure_function.test_xfailure_function",
            name="test_xfail")
        fnode = tnode.getElementsByTagName("skipped")[0]
        assert_attr(fnode, message="expected test failure")
        #assert "ValueError" in fnode.toxml()

    def test_xfailure_xpass(self, testdir):
        testdir.makepyfile("""
            import py
            @py.test.mark.xfail
            def test_xpass():
                pass
        """)
        result, dom = runandparse(testdir)
        #assert result.ret 
        node = dom.getElementsByTagName("testsuite")[0]
        assert_attr(node, skips=1, tests=0)
        tnode = node.getElementsByTagName("testcase")[0]
        assert_attr(tnode, 
            classname="test_xfailure_xpass.test_xfailure_xpass",
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
        testdir.makepyfile("import py ; py.test.skip('xyz')")
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
            import py
            def pytest_collect_file(path, parent):
                if path.ext == ".xyz":
                    return MyItem(path, parent)
            class MyItem(py.test.collect.Item):
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
        
