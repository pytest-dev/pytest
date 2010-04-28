import py
from py._plugin.pytest_default import pytest_report_iteminfo

def test_plugin_specify(testdir):
    testdir.chdir()
    config = py.test.raises(ImportError, """
            testdir.parseconfig("-p", "nqweotexistent")
    """)
    #py.test.raises(ImportError, 
    #    "config.pluginmanager.do_configure(config)"
    #)

def test_plugin_already_exists(testdir):
    config = testdir.parseconfig("-p", "default")
    assert config.option.plugins == ['default']
    config.pluginmanager.do_configure(config)

def test_exclude(testdir):
    hellodir = testdir.mkdir("hello")
    hellodir.join("test_hello.py").write("x y syntaxerror")
    hello2dir = testdir.mkdir("hello2")
    hello2dir.join("test_hello2.py").write("x y syntaxerror")
    testdir.makepyfile(test_ok="def test_pass(): pass")
    result = testdir.runpytest("--ignore=hello", "--ignore=hello2")
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*1 passed*"])

def test_pytest_report_iteminfo():
    class FakeItem(object):

        def reportinfo(self):
            return "-reportinfo-"

    res = pytest_report_iteminfo(FakeItem())
    assert res == "-reportinfo-"


def test_conftest_confcutdir(testdir):
    testdir.makeconftest("assert 0")
    x = testdir.mkdir("x")
    x.join("conftest.py").write(py.code.Source("""
        def pytest_addoption(parser):
            parser.addoption("--xyz", action="store_true")
    """))
    result = testdir.runpytest("-h", "--confcutdir=%s" % x, x)
    result.stdout.fnmatch_lines(["*--xyz*"])
