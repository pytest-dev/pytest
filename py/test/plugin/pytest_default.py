import py

class DefaultPlugin:
    """ Plugin implementing defaults and general options. """ 

    def pytest_pyfunc_call(self, pyfuncitem, args, kwargs):
        pyfuncitem.obj(*args, **kwargs)
        return 

    def pytest_collect_file(self, path, parent):
        ext = path.ext 
        pb = path.purebasename
        if pb.startswith("test_") or pb.endswith("_test") or \
           path in parent.config.args:
            if ext == ".py":
                return parent.Module(path, parent=parent) 
      
    def pytest_collect_directory(self, path, parent):
        #excludelist = parent._config.getvalue_pathlist('dir_exclude', path)
        #if excludelist and path in excludelist:
        #    return 
        if not parent.recfilter(path):
            # check if cmdline specified this dir or a subdir directly
            for arg in parent.config.args:
                if path == arg or arg.relto(path):
                    break
            else:
                return 
        # not use parent.Directory here as we generally 
        # want dir/conftest.py to be able to 
        # define Directory(dir) already 
        Directory = parent.config.getvalue('Directory', path) 
        return Directory(path, parent=parent)

    def pytest_addoption(self, parser):
        group = parser.addgroup("general", "test selection and failure debug options")
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
        group._addoption('--showskipsummary',
                   action="store_true", dest="showskipsummary", default=False,
                   help="always show summary of skipped tests") 
        group._addoption('--pdb',
                   action="store_true", dest="usepdb", default=False,
                   help="start pdb (the Python debugger) on errors.")
        group._addoption('--tb',
                   action="store", dest="tbstyle", default='long',
                   type="choice", choices=['long', 'short', 'no'],
                   help="traceback verboseness (long/short/no).")
        group._addoption('--fulltrace',
                   action="store_true", dest="fulltrace", default=False,
                   help="don't cut any tracebacks (default is to cut).")
        group._addoption('-s', '--nocapture',
                   action="store_true", dest="nocapture", default=False,
                   help="disable catching of sys.stdout/stderr output."),
        group.addoption('--basetemp', dest="basetemp", default=None, metavar="dir",
                   help="temporary directory for this test run.")
        group.addoption('--boxed',
                   action="store_true", dest="boxed", default=False,
                   help="box each test run in a separate process") 
        group._addoption('-p', action="append", dest="plugin", default = [],
                   help=("load the specified plugin after command line parsing. "
                         "Example: '-p hello' will trigger 'import pytest_hello' "
                         "and instantiate 'HelloPlugin' from the module."))
        group._addoption('-f', '--looponfailing',
                   action="store_true", dest="looponfailing", default=False,
                   help="loop on failing test set.")

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
        group.addoption('--debug',
                   action="store_true", dest="debug", default=False,
                   help="generate and show debugging information.")

        group = parser.addgroup("xplatform", "distributed/cross platform testing")
        group._addoption('-d', '--dist',
                   action="store_true", dest="dist", default=False,
                   help="ad-hoc distribute tests across machines (requires conftest settings)") 
        group._addoption('-n', '--numprocesses', dest="numprocesses", default=0, metavar="num", 
                   action="store", type="int", 
                   help="number of local test processes. conflicts with --dist.")
        group.addoption('--rsyncdirs', dest="rsyncdirs", default=None, metavar="dir1,dir2,...", 
                   help="comma-separated list of directories to rsync. All those roots will be rsynced "
                        "into a corresponding subdir on the remote sides. ")
        group._addoption('--tx', dest="xspec", action="append", 
                   help=("add a test environment, specified in XSpec syntax. examples: "
                         "--tx popen//python=python2.5 --tx socket=192.168.1.102"))
        #group._addoption('--rest',
        #           action='store_true', dest="restreport", default=False,
        #           help="restructured text output reporting."),

    def pytest_configure(self, config):
        self.setsession(config)
        self.loadplugins(config)
        self.fixoptions(config)

    def fixoptions(self, config):
        if config.getvalue("usepdb"):
            if config.getvalue("looponfailing"):
                raise config.Error("--pdb incompatible with --looponfailing.")
            if config.getvalue("dist"):
                raise config.Error("--pdb incomptaible with distributed testing.")

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
            if val("looponfailing"):
                from py.__.test.looponfail.remote import LooponfailingSession
                config.setsessionclass(LooponfailingSession)
            elif val("numprocesses") or val("dist"):
                from py.__.test.dsession.dsession import  DSession
                config.setsessionclass(DSession)

    def pytest_item_makereport(self, item, excinfo, when, outerr):
        from py.__.test import event
        return event.ItemTestReport(item, excinfo, when, outerr)

def test_implied_different_sessions(tmpdir):
    def x(*args):
        config = py.test.config._reparse([tmpdir] + list(args))
        try:
            config.pytestplugins.do_configure(config)
        except ValueError:
            return Exception
        return getattr(config._sessionclass, '__name__', None)
    assert x() == None
    assert x('--dist') == 'DSession'
    assert x('-n3') == 'DSession'
    assert x('-f') == 'LooponfailingSession'
    assert x('--dist', '--collectonly') == 'Session'

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

def test_conflict_options():
    def check_conflict_option(opts):
        print "testing if options conflict:", " ".join(opts)
        config = py.test.config._reparse(opts)
        py.test.raises(config.Error, 
            "config.pytestplugins.do_configure(config)")
    conflict_options = (
        '--looponfailing --pdb',
        '--dist --pdb', 
    )
    for spec in conflict_options: 
        opts = spec.split()
        yield check_conflict_option, opts
