""" default hooks and general py.test options. """ 

import py

def pytest_pyfunc_call(__multicall__, pyfuncitem):
    if not __multicall__.execute():
        testfunction = pyfuncitem.obj 
        if pyfuncitem._isyieldedfunction():
            testfunction(*pyfuncitem._args)
        else:
            funcargs = pyfuncitem.funcargs
            testfunction(**funcargs)

def pytest_collect_file(path, parent):
    ext = path.ext 
    pb = path.purebasename
    if pb.startswith("test_") or pb.endswith("_test") or \
       path in parent.config.args:
        if ext == ".py":
            return parent.Module(path, parent=parent) 

def pytest_collect_directory(path, parent):
    # XXX reconsider the following comment 
    # not use parent.Directory here as we generally 
    # want dir/conftest.py to be able to 
    # define Directory(dir) already 
    if not parent.recfilter(path): # by default special ".cvs", ... 
        # check if cmdline specified this dir or a subdir directly
        for arg in parent.config.args:
            if path == arg or arg.relto(path):
                break
        else:
            return 
    Directory = parent.config.getvalue('Directory', path) 
    return Directory(path, parent=parent)

def pytest_report_iteminfo(item):
    return item.reportinfo()

def pytest_addoption(parser):
    group = parser.getgroup("general", "general testing options")
    group._addoption('-v', '--verbose', action="count", 
               dest="verbose", default=0, help="increase verbosity."),
    group._addoption('-x', '--exitfirst',
               action="store_true", dest="exitfirst", default=False,
               help="exit instantly on first error or failed test."),
    group._addoption('-k',
        action="store", dest="keyword", default='',
        help="only run test items matching the given "
             "space separated keywords.  precede a keyword with '-' to negate. "
             "Terminate the expression with ':' to treat a match as a signal "
             "to run all subsequent tests. ")
    group._addoption('-l', '--showlocals',
               action="store_true", dest="showlocals", default=False,
               help="show locals in tracebacks (disabled by default).")
    #group._addoption('--showskipsummary',
    #           action="store_true", dest="showskipsummary", default=False,
    #           help="always show summary of skipped tests") 
    group._addoption('--tb', metavar="style", 
               action="store", dest="tbstyle", default='long',
               type="choice", choices=['long', 'short', 'no'],
               help="traceback verboseness (long/short/no).")
    group._addoption('-p', action="append", dest="plugin", default = [],
               help=("load the specified plugin after command line parsing. "))
    group._addoption('-f', '--looponfail',
               action="store_true", dest="looponfail", default=False,
               help="run tests, re-run failing test set until all pass.")

    group = parser.addgroup("test process debugging")
    group.addoption('--basetemp', dest="basetemp", default=None, metavar="dir",
               help="base temporary directory for this test run.")

    group = parser.addgroup("dist", "distributed testing") #  see http://pytest.org/help/dist")
    group._addoption('--dist', metavar="distmode", 
               action="store", choices=['load', 'each', 'no'], 
               type="choice", dest="dist", default="no", 
               help=("set mode for distributing tests to exec environments.\n\n"
                     "each: send each test to each available environment.\n\n"
                     "load: send each test to available environment.\n\n"
                     "(default) no: run tests inprocess, don't distribute."))
    group._addoption('--tx', dest="tx", action="append", default=[], metavar="xspec",
               help=("add a test execution environment. some examples: "
                     "--tx popen//python=python2.5 --tx socket=192.168.1.102:8888 "
                     "--tx ssh=user@codespeak.net//chdir=testcache"))
    group._addoption('-d', 
               action="store_true", dest="distload", default=False,
               help="load-balance tests.  shortcut for '--dist=load'")
    group._addoption('-n', dest="numprocesses", metavar="numprocesses", 
               action="store", type="int", 
               help="shortcut for '--dist=load --tx=NUM*popen'")
    group.addoption('--rsyncdir', action="append", default=[], metavar="dir1", 
               help="add directory for rsyncing to remote tx nodes.")

def pytest_configure(config):
    fixoptions(config)
    setsession(config)
    #xxxloadplugins(config)

def fixoptions(config):
    if config.option.numprocesses:
        config.option.dist = "load"
        config.option.tx = ['popen'] * int(config.option.numprocesses)
    if config.option.distload:
        config.option.dist = "load"

def xxxloadplugins(config):
    for name in config.getvalue("plugin"):
        print "importing", name
        config.pluginmanager.import_plugin(name)

def setsession(config):
    val = config.getvalue
    if val("collectonly"):
        from py.__.test.session import Session
        config.setsessionclass(Session)
    else:
        if val("looponfail"):
            from py.__.test.looponfail.remote import LooponfailingSession
            config.setsessionclass(LooponfailingSession)
        elif val("dist") != "no":
            from py.__.test.dist.dsession import  DSession
            config.setsessionclass(DSession)

def test_implied_different_sessions(tmpdir):
    def x(*args):
        config = py.test.config._reparse([tmpdir] + list(args))
        try:
            config.pluginmanager.do_configure(config)
        except ValueError:
            return Exception
        return getattr(config._sessionclass, '__name__', None)
    assert x() == None
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
    assert config.option.plugin == ['default']
    config.pluginmanager.do_configure(config)


class TestDistOptions:
    def test_getxspecs(self, testdir):
        config = testdir.parseconfigure("--tx=popen", "--tx", "ssh=xyz")
        xspecs = config.getxspecs()
        assert len(xspecs) == 2
        print xspecs
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

def test_dist_options(testdir):
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
