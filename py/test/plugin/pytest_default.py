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
           path in parent._config.args:
            if ext == ".py":
                return parent.Module(path, parent=parent) 
      
    def pytest_collect_directory(self, path, parent):
        if not parent.recfilter(path):
            # check if cmdline specified this dir or a subdir
            for arg in parent._config.args:
                if path == arg or arg.relto(path):
                    break
            else:
                return 
        # not use parent.Directory here as we want
        # dir/conftest.py to be able to 
        # define Directory(dir) already 
        Directory = parent._config.getvalue('Directory', path) 
        return Directory(path, parent=parent)

    def pytest_addoption(self, parser):
        group = parser.addgroup("general", "general options")
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
        group._addoption('--boxed',
                   action="store_true", dest="boxed", default=False,
                   help="box each test run in a separate process"), 
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
                   help="don't use assert reinterpretation and python traceback cutting. ")
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
        group.addoption('--hosts', dest="hosts", default=None, metavar="host1,host2,...", 
                   help="comma-separated list of host specs to send tests to.")
        group._addoption('--exec',
                   action="store", dest="executable", default=None,
                   help="python executable to run the tests with.")
        #group._addoption('-w', '--startserver',
        #           action="store_true", dest="startserver", default=False,
        #           help="starts local web server for displaying test progress.", 
        #           ),
        #group._addoption('-r', '--runbrowser',
        #           action="store_true", dest="runbrowser", default=False,
        #           help="run browser (implies --startserver)."
        #           ),
        #group._addoption('--rest',
        #           action='store_true', dest="restreport", default=False,
        #           help="restructured text output reporting."),

    def pytest_configure(self, config):
        self.setsession(config)

    def setsession(self, config):
        val = config.getvalue
        if val("collectonly"):
            from py.__.test.session import Session
            config.setsessionclass(Session)
        elif val("looponfailing"):
            from py.__.test.looponfail.remote import LooponfailingSession
            config.setsessionclass(LooponfailingSession)
        elif val("numprocesses") or val("dist") or val("executable"):
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
    assert x('--exec=x') == 'DSession'
    assert x('-f', '--exec=x') == 'LooponfailingSession'
    assert x('--dist', '--exec=x', '--collectonly') == 'Session'
