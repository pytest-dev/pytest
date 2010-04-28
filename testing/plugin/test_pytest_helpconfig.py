import py, os
from py._plugin.pytest_helpconfig import collectattr

def test_version(testdir):
    assert py.version == py.__version__ 
    result = testdir.runpytest("--version")
    assert result.ret == 0
    #p = py.path.local(py.__file__).dirpath()
    result.stderr.fnmatch_lines([
        '*py.test*%s*imported from*' % (py.version, )
    ])

def test_helpconfig(testdir):
    result = testdir.runpytest("--help-config")
    assert result.ret == 0
    result.stdout.fnmatch_lines([
        "*cmdline*conftest*ENV*",
    ])

def test_collectattr():
    class A:
        def pytest_hello(self):
            pass
    class B(A):
        def pytest_world(self):
            pass
    methods = py.builtin.sorted(collectattr(B))
    assert list(methods) == ['pytest_hello', 'pytest_world']
    methods = py.builtin.sorted(collectattr(B()))
    assert list(methods) == ['pytest_hello', 'pytest_world']

def test_hookvalidation_unknown(testdir):
    testdir.makeconftest("""
        def pytest_hello(xyz):
            pass
    """)
    result = testdir.runpytest()
    assert result.ret != 0
    result.stderr.fnmatch_lines([
        '*unknown hook*pytest_hello*'
    ])

def test_hookvalidation_optional(testdir):
    testdir.makeconftest("""
        import py
        @py.test.mark.optionalhook 
        def pytest_hello(xyz):
            pass
    """)
    result = testdir.runpytest()
    assert result.ret == 0

