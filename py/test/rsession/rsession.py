
""" Remote session base class
"""

import os
import py
import sys
import re
import time

from py.__.test.rsession import report
from py.__.test.rsession.master import \
     setup_slave, MasterNode, dispatch_loop, itemgen, randomgen
from py.__.test.rsession.hostmanage import init_hosts, teardown_hosts, HostInfo

from py.__.test.rsession.local import local_loop, plain_runner, apigen_runner,\
    box_runner, RunnerPolicy
from py.__.test.rsession.reporter import LocalReporter, RemoteReporter

class RemoteOptions(object):
    def __init__(self, d):
        self.d = d
    
    def __getattr__(self, attr):
        if attr == 'd':
            return self.__dict__['d']
        return self.d[attr]
    
    def __setitem__(self, item, val):
        self.d[item] = val

# XXX: Must be initialised somehow
remote_options = RemoteOptions({'we_are_remote':False})

class SessionOptions:
    defaults = {
        'max_tasks_per_node' : 15,
        'runner_policy' : 'plain_runner',
        'nice_level' : 0,
        'waittime' : 100.0,
        'import_pypy' : False,
    }
    
    config = None
    
    def getvalue(self, opt):
        try:
            return getattr(self.config.getvalue('SessionOptions'), opt)
        except (KeyError, AttributeError): 
            try:
                return self.defaults[opt]
            except KeyError:
                raise AttributeError("Option %s undeclared" % opt)
    
    def bind_config(self, config):
        self.config = config
        # copy to remote session options
        try:
            ses_opt = self.config.getvalue('SessionOptions').__dict__
        except KeyError:
            ses_opt = self.defaults
        for key in self.defaults:
            try:
                val = ses_opt[key]
            except KeyError:
                val = self.defaults[key]
            remote_options[key] = val
        # copy to remote all options
        for item, val in config.option.__dict__.items():
            remote_options[item] = val
    
    def __repr__(self):
        return "<SessionOptions %s>" % self.config
    
    def __getattr__(self, attr):
        if self.config is None:
            raise AttributeError("Need to set up config first")
        return self.getvalue(attr)

session_options = SessionOptions()

class AbstractSession(object):
    """
        An abstract session executes collectors/items through a runner. 

    """
    def __init__(self, config, optimise_localhost=True):
        self.config = config
        self.optimise_localhost = optimise_localhost
        
    def make_colitems(paths, baseon): 
        # we presume that from the base we can simply get to 
        # the target paths by joining the basenames 
        res = []
        for x in paths: 
            x = py.path.local(x)
            current = py.test.collect.Directory(baseon)  
            relparts = x.relto(baseon).split(x.sep) 
            assert relparts 
            for part in relparts: 
                next = current.join(part) 
                assert next is not None, (current, part) 
                current = next 
            res.append(current) 
        return res 
    make_colitems = staticmethod(make_colitems) 

    def getpkgdir(path):
        path = py.path.local(path)
        pkgpath = path.pypkgpath()
        if pkgpath is None:
            pkgpath = path
        return pkgpath
    getpkgdir = staticmethod(getpkgdir)

    def init_reporter(self, reporter, sshhosts, reporter_class, arg=""):
        startserverflag = self.config.option.startserver
        restflag = self.config.option.restreport
        
        if startserverflag and reporter is None:
            from py.__.test.rsession.web import start_server, exported_methods
            
            reporter = exported_methods.report
            start_server()
            if self.config.option.runbrowser:
                import webbrowser
                webbrowser.open("http://localhost:8000")
        elif reporter is None: 
            if restflag:
                from py.__.test.rsession.rest import RestReporter
                reporter_class = RestReporter
            if arg:
                reporter_instance = reporter_class(self.config, sshhosts, self.getpkgdir(arg))
            else:
                reporter_instance = reporter_class(self.config, sshhosts)
            reporter = reporter_instance.report
        else:
            startserverflag = False
        
        return reporter, startserverflag
    
    def reporterror(reporter, data):
            excinfo, item = data
            if excinfo is None:
                reporter(report.ItemStart(item))
            elif excinfo.type is py.test.Item.Skipped:
                reporter(report.SkippedTryiter(excinfo, item))
            else:
                reporter(report.FailedTryiter(excinfo, item))
    reporterror = staticmethod(reporterror)

    def kill_server(self, startserverflag):
        if startserverflag:
            from py.__.test.rsession.web import kill_server
            kill_server()

    def wrap_reporter(self, reporter):
        """ We wrap reporter around, which makes it possible to us to track
        number of failures
        """
        self.was_failure = False
        def new_reporter(event):
            if isinstance(event, report.ReceivedItemOutcome) and \
                   not event.outcome.passed and \
                   not event.outcome.skipped:
                self.was_failure = True
            return reporter(event)
        checkfun = lambda : self.config.option.exitfirst and \
                            self.was_failure
        # for tests
        self.checkfun = checkfun
        return new_reporter, checkfun

def parse_directories(sshhosts):
    directories = {}
    for host in sshhosts:
        m = re.match("^(.*?):(.*)$", host.hostname)
        if m:
            host.hostname = m.group(1)
            host.relpath = m.group(2) + "-" + host.hostname
        else:
            host.relpath = "pytestcache-%s" % host.hostname

class RSession(AbstractSession):
    """ Remote version of session
    """
    def main(self, reporter=None):
        """ main loop for running tests. """
        args = self.config.remaining

        session_options.bind_config(self.config)
        sshhosts, remotepython, rsync_roots = self.read_distributed_config()
        reporter, startserverflag = self.init_reporter(reporter,
            sshhosts, RemoteReporter)
        reporter, checkfun = self.wrap_reporter(reporter)

        reporter(report.TestStarted(sshhosts))

        pkgdir = self.getpkgdir(args[0])
        done_dict = {}
        nodes = init_hosts(reporter, sshhosts, pkgdir,
            rsync_roots, remotepython, remote_options=remote_options.d,
            optimise_localhost=self.optimise_localhost, done_dict=done_dict)
        reporter(report.RsyncFinished())
        
        try:
            self.dispatch_tests(nodes, args, pkgdir, reporter, checkfun, done_dict)
        finally:
            teardown_hosts(reporter, [node.channel for node in nodes], nodes, 
                exitfirst=self.config.option.exitfirst)
        reporter(report.Nodes(nodes))
        retval = reporter(report.TestFinished())
        self.kill_server(startserverflag)
        return retval

    def read_distributed_config(self):
        try:
            rsync_roots = self.config.getvalue("distrsync_roots")
        except:
            rsync_roots = None    # all files and directories in the pkgdir
        sshhosts = [HostInfo(i) for i in
                    self.config.getvalue("disthosts")]
        parse_directories(sshhosts)
        try:
            remotepython = self.config.getvalue("dist_remotepython")
        except:
            remotepython = None
        return sshhosts, remotepython, rsync_roots

    def dispatch_tests(self, nodes, args, pkgdir, reporter, checkfun, done_dict):
        colitems = self.make_colitems(args, baseon=pkgdir.dirpath())
        keyword = self.config.option.keyword
        itemgenerator = itemgen(colitems, reporter, keyword, self.reporterror)
        
        all_tests = dispatch_loop(nodes, itemgenerator, checkfun)
        #if all_tests:
        #    todo = {}
        #    for key, value in all_tests.items():
        #        if key not in done_dict:
        #            todo[key] = True
        #    rg = randomgen(todo, done_dict)
        #    dispatch_loop(nodes, rg, lambda:False, max_tasks_per_node=1)


class LSession(AbstractSession):
    """ Local version of session
    """
    def main(self, reporter=None, runner=None):
        # check out if used options makes any sense
        args = self.config.remaining  
        
        sshhosts = [HostInfo('localhost')] # this is just an info to reporter
        
        if not self.config.option.nomagic:
            py.magic.invoke(assertion=1)

        session_options.bind_config(self.config)
        reporter, startserverflag = self.init_reporter(reporter, 
            sshhosts, LocalReporter, args[0])
        reporter, checkfun = self.wrap_reporter(reporter)
        
        reporter(report.TestStarted(sshhosts))
        pkgdir = self.getpkgdir(args[0])
        colitems = self.make_colitems(args, baseon=pkgdir.dirpath())
        reporter(report.RsyncFinished())

        if runner is None:
            runner = self.init_runner(pkgdir)

        keyword = self.config.option.keyword

        itemgenerator = itemgen(colitems, reporter, keyword, self.reporterror)
        local_loop(self, reporter, itemgenerator, checkfun, self.config, runner=runner)
        
        retval = reporter(report.TestFinished())
        self.kill_server(startserverflag)

        if not self.config.option.nomagic:
            py.magic.revoke(assertion=1)

        self.write_docs(pkgdir)
        return retval

    def write_docs(self, pkgdir):
        if self.config.option.apigen:
            from py.__.apigen.tracer.docstorage import DocStorageAccessor
            apigen = py.path.local(self.config.option.apigen).pyimport()
            print >>sys.stderr, 'building documentation'
            capture = py.io.OutErrCapture()
            try:
                try:
                    apigen.build(pkgdir, DocStorageAccessor(self.docstorage))
                except (ValueError, AttributeError):
                    #import traceback
                    #exc, e, tb = sys.exc_info()
                    #print '%s - %s' % (exc, e)
                    #print ''.join(traceback.format_tb(tb))
                    #del tb
                    #print '-' * 79
                    raise NotImplementedError("Provided script does not seem "
                                              "to contain build function")
            finally:
                capture.reset()

    def init_runner(self, pkgdir):
        if self.config.option.apigen:
            from py.__.apigen.tracer.tracer import Tracer, DocStorage
            module = py
            try:
                apigen = py.path.local(self.config.option.apigen).pyimport()
                items = apigen.get_documentable_items(pkgdir)
                if isinstance(items, dict):
                    self.docstorage = DocStorage().from_dict(items)
                else:
                    self.docstorage = DocStorage().from_pkg(items)
            except ImportError:
                raise ImportError("Provided script cannot be imported")
            except (ValueError, AttributeError):
                raise NotImplementedError("Provided script does not seem "
                                          "to contain get_documentable_items")
            self.tracer = Tracer(self.docstorage)
            return apigen_runner
        else:
            return RunnerPolicy[session_options.runner_policy]
