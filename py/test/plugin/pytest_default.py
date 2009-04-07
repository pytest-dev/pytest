import py

class DefaultPlugin:
    """ Plugin implementing defaults and general options. """ 

    def pytest_itemrun(self, item, pdb=None):
        from py.__.test.runner import basic_run_report, forked_run_report
        if item.config.option.boxed:
            runner = forked_run_report
        else:
            runner = basic_run_report
        report = runner(item, pdb=pdb) 
        item.config.pytestplugins.notify("itemtestreport", report) 
        return True

    def pytest_item_makereport(self, item, excinfo, when, outerr):
        from py.__.test import runner
        return runner.ItemTestReport(item, excinfo, when, outerr)

    def pytest_item_runtest_finished(self, item, excinfo, outerr):
        from py.__.test import runner
        rep = runner.ItemTestReport(item, excinfo, "execute", outerr)
        item.config.pytestplugins.notify("itemtestreport", rep) 

    def pytest_pyfunc_call(self, pyfuncitem, args, kwargs):
        pyfuncitem.obj(*args, **kwargs)

    def pytest_collect_file(self, path, parent):
        ext = path.ext 
        pb = path.purebasename
        if pb.startswith("test_") or pb.endswith("_test") or \
           path in parent.config.args:
            if ext == ".py":
                return parent.Module(path, parent=parent) 

    def pytest_collect_recurse(self, path, parent):
        #excludelist = parent._config.getvalue_pathlist('dir_exclude', path)
        #if excludelist and path in excludelist:
        #    return 
        if not parent.recfilter(path):
            # check if cmdline specified this dir or a subdir directly
            for arg in parent.config.args:
                if path == arg or arg.relto(path):
                    break
            else:
                return False 
        return True
      
    def pytest_collect_directory(self, path, parent):
        # XXX reconsider the following comment 
        # not use parent.Directory here as we generally 
        # want dir/conftest.py to be able to 
        # define Directory(dir) already 
        Directory = parent.config.getvalue('Directory', path) 
        return Directory(path, parent=parent)

    def pytest_addoption(self, parser):
        group = parser.addgroup("general", "test collection and failure interaction options")
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
        group._addoption('--pdb',
                   action="store_true", dest="usepdb", default=False,
                   help="start pdb (the Python debugger) on errors.")
        group._addoption('--tb', metavar="style", 
                   action="store", dest="tbstyle", default='long',
                   type="choice", choices=['long', 'short', 'no'],
                   help="traceback verboseness (long/short/no).")
        group._addoption('-s', 
                   action="store_true", dest="nocapture", default=False,
                   help="disable catching of stdout/stderr during test run.")
        group.addoption('--boxed',
                   action="store_true", dest="boxed", default=False,
                   help="box each test run in a separate process") 
        group._addoption('-p', action="append", dest="plugin", default = [],
                   help=("load the specified plugin after command line parsing. "
                         "Example: '-p hello' will trigger 'import pytest_hello' "
                         "and instantiate 'HelloPlugin' from the module."))
        group._addoption('-f', '--looponfail',
                   action="store_true", dest="looponfail", default=False,
                   help="run tests, re-run failing test set until all pass.")

        group = parser.addgroup("test process debugging")
        group.addoption('--collectonly',
            action="store_true", dest="collectonly",
            help="only collect tests, don't execute them."),
        group.addoption('--traceconfig',
                   action="store_true", dest="traceconfig", default=False,
                   help="trace considerations of conftest.py files."),
        group._addoption('--nomagic',
                   action="store_true", dest="nomagic", default=False,
                   help="don't reinterpret asserts, no traceback cutting. ")
        group._addoption('--fulltrace',
                   action="store_true", dest="fulltrace", default=False,
                   help="don't cut any tracebacks (default is to cut).")
        group.addoption('--basetemp', dest="basetemp", default=None, metavar="dir",
                   help="base temporary directory for this test run.")
        group._addoption('--iocapture', action="store", default="fd", metavar="method",
                   type="choice", choices=['fd', 'sys', 'no'],
                   help="set iocapturing method: fd|sys|no.")
        group.addoption('--debug',
                   action="store_true", dest="debug", default=False,
                   help="generate and show debugging information.")

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

    def pytest_configure(self, config):
        self.fixoptions(config)
        self.setsession(config)
        self.loadplugins(config)

    def fixoptions(self, config):
        if config.option.numprocesses:
            config.option.dist = "load"
            config.option.tx = ['popen'] * int(config.option.numprocesses)
        if config.option.distload:
            config.option.dist = "load"
        if config.getvalue("usepdb"):
            if config.getvalue("looponfail"):
                raise config.Error("--pdb incompatible with --looponfail.")
            if config.option.dist != "no":
                raise config.Error("--pdb incomptaible with distributing tests.")

    def loadplugins(self, config):
        for name in config.getvalue("plugin"):
            print "importing", name
            config.pytestplugins.import_plugin(name)

    def setsession(self, config):
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
            config.pytestplugins.do_configure(config)
        except ValueError:
            return Exception
        return getattr(config._sessionclass, '__name__', None)
    assert x() == None
    assert x('-d') == 'DSession'
    assert x('--dist=each') == 'DSession'
    assert x('-n3') == 'DSession'
    assert x('-f') == 'LooponfailingSession'

def test_generic(plugintester):
    plugintester.apicheck(DefaultPlugin)
    
def test_plugin_specify(testdir):
    testdir.chdir()
    config = testdir.parseconfig("-p", "nqweotexistent")
    py.test.raises(ImportError, 
        "config.pytestplugins.do_configure(config)"
    )

def test_plugin_already_exists(testdir):
    config = testdir.parseconfig("-p", "default")
    assert config.option.plugin == ['default']
    config.pytestplugins.do_configure(config)


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
    py.test.raises(Exception, "testdir.parseconfigure('--pdb', '--looponfail')")
    py.test.raises(Exception, "testdir.parseconfigure('--pdb', '-n 3')")
    py.test.raises(Exception, "testdir.parseconfigure('--pdb', '-d')")
    config = testdir.parseconfigure("-n 2")
    assert config.option.dist == "load"
    assert config.option.tx == ['popen'] * 2
    
    config = testdir.parseconfigure("-d")
    assert config.option.dist == "load"
