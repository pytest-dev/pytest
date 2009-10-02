import py
from _py.test.plugin.pytest_default import pytest_report_iteminfo

def test_implied_different_sessions(tmpdir):
    def x(*args):
        config = py.test.config._reparse([tmpdir] + list(args))
        try:
            config.pluginmanager.do_configure(config)
        except ValueError:
            return Exception
        return getattr(config._sessionclass, '__name__', None)
    assert x() == None
    py.test.importorskip("execnet")
    assert x('-d') == 'DSession'
    assert x('--dist=each') == 'DSession'
    assert x('-n3') == 'DSession'
    assert x('-f') == 'LooponfailingSession'

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


class TestDistOptions:
    def setup_method(self, method):
        py.test.importorskip("execnet")
    def test_getxspecs(self, testdir):
        config = testdir.parseconfigure("--tx=popen", "--tx", "ssh=xyz")
        xspecs = config.getxspecs()
        assert len(xspecs) == 2
        print(xspecs)
        assert xspecs[0].popen 
        assert xspecs[1].ssh == "xyz"

    def test_xspecs_multiplied(self, testdir):
        xspecs = testdir.parseconfigure("--tx=3*popen",).getxspecs()
        assert len(xspecs) == 3
        assert xspecs[1].popen 

    def test_getrsyncdirs(self, testdir):
        config = testdir.parseconfigure('--rsyncdir=' + str(testdir.tmpdir))
        roots = config.getrsyncdirs()
        assert len(roots) == 1 + 1 
        assert testdir.tmpdir in roots

    def test_getrsyncdirs_with_conftest(self, testdir):
        p = py.path.local()
        for bn in 'x y z'.split():
            p.mkdir(bn)
        testdir.makeconftest("""
            rsyncdirs= 'x', 
        """)
        config = testdir.parseconfigure(testdir.tmpdir, '--rsyncdir=y', '--rsyncdir=z')
        roots = config.getrsyncdirs()
        assert len(roots) == 3 + 1 
        assert py.path.local('y') in roots 
        assert py.path.local('z') in roots 
        assert testdir.tmpdir.join('x') in roots 

    def test_dist_options(self, testdir):
        config = testdir.parseconfigure("-n 2")
        assert config.option.dist == "load"
        assert config.option.tx == ['popen'] * 2
        
        config = testdir.parseconfigure("-d")
        assert config.option.dist == "load"

def test_pytest_report_iteminfo():
    class FakeItem(object):

        def reportinfo(self):
            return "-reportinfo-"

    res = pytest_report_iteminfo(FakeItem())
    assert res == "-reportinfo-"
