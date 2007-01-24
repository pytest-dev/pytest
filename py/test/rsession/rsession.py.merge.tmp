
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
from py.__.test.rsession.hostmanage import HostInfo, HostOptions, HostManager

from py.__.test.rsession.local import local_loop, plain_runner, apigen_runner,\
    box_runner
from py.__.test.rsession.reporter import LocalReporter, RemoteReporter

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
        """ This initialises so called `reporter` class, which will
        handle all event presenting to user. Does not get called
        if main received custom reporter
        """
        startserverflag = self.config.option.startserver
        restflag = self.config.option.restreport
        
        if startserverflag and reporter is None:
            from py.__.test.rsession.web import start_server, exported_methods
            if self.config.option.runbrowser:
                from socket import INADDR_ANY
                port = INADDR_ANY   # pick a random port when starting browser
            else:
                port = 8000         # stick to a fixed port otherwise
            
            reporter = exported_methods.report
            httpd = start_server(server_address = ('', port))
            port = httpd.server_port
            if self.config.option.runbrowser:
                import webbrowser, thread
                # webbrowser.open() may block until the browser finishes or not
                url = "http://localhost:%d" % (port,)
                thread.start_new_thread(webbrowser.open, (url,))
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
        """ Kill web server
        """
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
    """ Parse sshadresses of hosts to have distinct hostname/hostdir
    """
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
        args = self.config.args

        sshhosts, remotepython, rsync_roots = self.read_distributed_config()
        reporter, startserverflag = self.init_reporter(reporter,
            sshhosts, RemoteReporter)
        reporter, checkfun = self.wrap_reporter(reporter)

        reporter(report.TestStarted(sshhosts))

        pkgdir = self.getpkgdir(args[0])
        done_dict = {}
        hostopts = HostOptions(rsync_roots=rsync_roots,
                               remote_python=remotepython,
                            optimise_localhost=self.optimise_localhost)
        hostmanager = HostManager(sshhosts, self.config, pkgdir, hostopts)
        try:
            nodes = hostmanager.init_hosts(reporter, done_dict)
            reporter(report.RsyncFinished())
            try:
                self.dispatch_tests(nodes, args, pkgdir, reporter, checkfun, done_dict)
            except (KeyboardInterrupt, SystemExit):
                print >>sys.stderr, "C-c pressed waiting for gateways to teardown..."
                channels = [node.channel for node in nodes]
                hostmanager.kill_channels(channels)
                hostmanager.teardown_gateways(reporter, channels)
                print >>sys.stderr, "... Done"
                raise

            channels = [node.channel for node in nodes]
            hostmanager.teardown_hosts(reporter, channels, nodes, 
                exitfirst=self.config.option.exitfirst)
            reporter(report.Nodes(nodes))
            retval = reporter(report.TestFinished())
            self.kill_server(startserverflag)
            return retval
        except (KeyboardInterrupt, SystemExit):
            reporter(report.InterruptedExecution())
            self.kill_server(startserverflag)
            raise
        except:
            reporter(report.CrashedExecution())
            self.kill_server(startserverflag)
            raise

    def read_distributed_config(self):
        """ Read from conftest file the configuration of distributed testing
        """
        try:
            rsync_roots = self.config.getvalue("distrsync_roots")
        except:
            rsync_roots = None    # all files and directories in the pkgdir
        sshhosts = [HostInfo(i) for i in
                    self.config.getvalue("disthosts")]
        parse_directories(sshhosts)
        remotepython = self.config.getvalue("dist_remotepython")
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
        args = self.config.args  
        
        sshhosts = [HostInfo('localhost')] # this is just an info to reporter
        
        if not self.config.option.nomagic:
            py.magic.invoke(assertion=1)

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
            if (self.config.getvalue('dist_boxing') or self.config.option.boxing)\
                   and not self.config.option.nocapture:
                return box_runner
            return plain_runner

