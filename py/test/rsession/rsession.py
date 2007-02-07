
""" Remote session base class
"""

import os
import py
import sys
import re
import time

from py.__.test.rsession import repevent
from py.__.test.rsession.master import MasterNode, dispatch_loop, itemgen
from py.__.test.rsession.hostmanage import HostInfo, HostManager
from py.__.test.rsession.local import local_loop, plain_runner, apigen_runner,\
    box_runner
from py.__.test.rsession.reporter import LocalReporter, RemoteReporter
from py.__.test.session import Session
from py.__.test.outcome import Skipped, Failed

class AbstractSession(Session): 
    """
        An abstract session executes collectors/items through a runner. 

    """
    def fixoptions(self):
        option = self.config.option 
        if option.runbrowser and not option.startserver:
            #print "--runbrowser implies --startserver"
            option.startserver = True
        if self.config.getvalue("dist_boxed"):
            option.boxed = True
        super(AbstractSession, self).fixoptions()

    def init_reporter(self, reporter, hosts, reporter_class, arg=""):
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
                reporter_instance = reporter_class(self.config, hosts)
            else:
                reporter_instance = reporter_class(self.config, hosts)
            reporter = reporter_instance.report
        else:
            startserverflag = False
        
        return reporter, startserverflag
    
    def reporterror(reporter, data):
        excinfo, item = data
        if excinfo is None:
            reporter(repevent.ItemStart(item))
        elif excinfo.type is Skipped:
            reporter(repevent.SkippedTryiter(excinfo, item))
        else:
            reporter(repevent.FailedTryiter(excinfo, item))
    reporterror = staticmethod(reporterror)

    def kill_server(self, startserverflag):
        """ Kill web server
        """
        if startserverflag:
            from py.__.test.rsession.web import kill_server
            kill_server()

    def wrap_reporter(self, reporter):
        """ We wrap reporter around, which makes it possible to us to track
        existance of failures
        """
        self.was_failure = False
        def new_reporter(event):
            if isinstance(event, repevent.ReceivedItemOutcome) and \
                   not event.outcome.passed and \
                   not event.outcome.skipped:
                self.was_failure = True
            return reporter(event)
        checkfun = lambda : self.config.option.exitfirst and \
                            self.was_failure
        # for tests
        self.checkfun = checkfun
        return new_reporter, checkfun

class RSession(AbstractSession):
    """ Remote version of session
    """
    def fixoptions(self):
        super(RSession, self).fixoptions()
        option = self.config.option 
        if option.nocapture:
            print "Cannot use nocapture with distributed testing"
            sys.exit(1)
        config = self.config
        try:
            config.getvalue('dist_hosts')
        except KeyError:
            print "For running ad-hoc distributed tests you need to specify"
            print "dist_hosts in a local conftest.py file, for example:"
            print "for example:"
            print
            print "  dist_hosts = ['localhost'] * 4 # for 3 processors"
            print "  dist_hosts = ['you@remote.com', '...'] # for testing on ssh accounts"
            print "   # with your remote ssh accounts"
            print 
            print "see also: http://codespeak.net/py/current/doc/test.html#automated-distributed-testing"
            raise SystemExit
    
    def main(self, reporter=None):
        """ main loop for running tests. """
        args = self.config.args

        hm = HostManager(self.config)
        reporter, startserverflag = self.init_reporter(reporter,
            hm.hosts, RemoteReporter)
        reporter, checkfun = self.wrap_reporter(reporter)

        reporter(repevent.TestStarted(hm.hosts, self.config.topdir,
                                      hm.roots))

        try:
            nodes = hm.setup_hosts(reporter)
            reporter(repevent.RsyncFinished())
            try:
                self.dispatch_tests(nodes, reporter, checkfun)
            except (KeyboardInterrupt, SystemExit):
                print >>sys.stderr, "C-c pressed waiting for gateways to teardown..."
                channels = [node.channel for node in nodes]
                hm.kill_channels(channels)
                hm.teardown_gateways(reporter, channels)
                print >>sys.stderr, "... Done"
                raise

            channels = [node.channel for node in nodes]
            hm.teardown_hosts(reporter, channels, nodes, 
                              exitfirst=self.config.option.exitfirst)
            reporter(repevent.Nodes(nodes))
            retval = reporter(repevent.TestFinished())
            self.kill_server(startserverflag)
            return retval
        except (KeyboardInterrupt, SystemExit):
            reporter(repevent.InterruptedExecution())
            self.kill_server(startserverflag)
            raise
        except:
            reporter(repevent.CrashedExecution())
            self.kill_server(startserverflag)
            raise

    def dispatch_tests(self, nodes, reporter, checkfun):
        colitems = self.config.getcolitems()
        keyword = self.config.option.keyword
        itemgenerator = itemgen(colitems, reporter, keyword, self.reporterror)
        
        all_tests = dispatch_loop(nodes, itemgenerator, checkfun)

class LSession(AbstractSession):
    """ Local version of session
    """
    def main(self, reporter=None, runner=None):
        # check out if used options makes any sense
        args = self.config.args  
       
        hm = HostManager(self.config, hosts=[HostInfo('localhost')])
        hosts = hm.hosts
        if not self.config.option.nomagic:
            py.magic.invoke(assertion=1)

        reporter, startserverflag = self.init_reporter(reporter, 
            hosts, LocalReporter, args[0])
        reporter, checkfun = self.wrap_reporter(reporter)
        
        reporter(repevent.TestStarted(hosts, self.config.topdir, []))
        colitems = self.config.getcolitems()
        reporter(repevent.RsyncFinished())

        if runner is None:
            runner = self.init_runner()

        keyword = self.config.option.keyword

        itemgenerator = itemgen(colitems, reporter, keyword, self.reporterror)
        local_loop(self, reporter, itemgenerator, checkfun, self.config, runner=runner)
        
        retval = reporter(repevent.TestFinished())
        self.kill_server(startserverflag)

        if not self.config.option.nomagic:
            py.magic.revoke(assertion=1)

        self.write_docs()
        return retval

    def write_docs(self):
        if self.config.option.apigen:
            from py.__.apigen.tracer.docstorage import DocStorageAccessor
            apigen = py.path.local(self.config.option.apigen).pyimport()
            if not hasattr(apigen, 'build'):
                raise NotImplementedError("%s does not contain 'build' "
                                          "function" %(apigen,))
            print >>sys.stderr, 'building documentation'
            capture = py.io.StdCaptureFD()
            try:
                pkgdir = py.path.local(self.config.args[0]).pypkgpath()
                apigen.build(pkgdir,
                             DocStorageAccessor(self.docstorage),
                             capture)
            finally:
                capture.reset()
            print >>sys.stderr, '\ndone'

    def init_runner(self):
        if self.config.option.apigen:
            from py.__.apigen.tracer.tracer import Tracer, DocStorage
            pkgdir = py.path.local(self.config.args[0]).pypkgpath()
            apigen = py.path.local(self.config.option.apigen).pyimport()
            if not hasattr(apigen, 'get_documentable_items'):
                raise NotImplementedError("Provided script does not seem "
                                          "to contain get_documentable_items")
            pkgname, items = apigen.get_documentable_items(pkgdir)
            self.docstorage = DocStorage().from_dict(items,
                                                     module_name=pkgname)
            self.tracer = Tracer(self.docstorage)
            return apigen_runner
        elif self.config.option.boxed:
            return box_runner
        else:
            return plain_runner

