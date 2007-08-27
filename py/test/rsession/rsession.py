
""" Remote session base class
"""

import os
import py
import sys
import re
import time

from py.__.test import repevent
from py.__.test.rsession.master import MasterNode, dispatch_loop, itemgen
from py.__.test.rsession.hostmanage import HostInfo, HostManager
from py.__.test.rsession.local import local_loop, plain_runner, apigen_runner,\
    box_runner
from py.__.test.reporter import LocalReporter, RemoteReporter, TestReporter
from py.__.test.session import AbstractSession
from py.__.test.outcome import Skipped, Failed
    
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
        config = self.config
        hm = HostManager(config)
        reporter, checkfun = self.init_reporter(reporter, config, hm.hosts)

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
            return retval
        except (KeyboardInterrupt, SystemExit):
            reporter(repevent.InterruptedExecution())
            raise
        except:
            reporter(repevent.CrashedExecution())
            raise

    def dispatch_tests(self, nodes, reporter, checkfun):
        colitems = self.config.getcolitems()
        keyword = self.config.option.keyword
        itemgenerator = itemgen(colitems, reporter, keyword)
        all_tests = dispatch_loop(nodes, itemgenerator, checkfun)

class LSession(AbstractSession):
    """ Local version of session
    """
    def main(self, reporter=None, runner=None):
        # check out if used options makes any sense
        config = self.config
        hm = HostManager(config, hosts=[HostInfo('localhost')])
        hosts = hm.hosts
        if not self.config.option.nomagic:
            py.magic.invoke(assertion=1)

        reporter, checkfun = self.init_reporter(reporter, config, hosts)
        
        reporter(repevent.TestStarted(hosts, self.config.topdir, []))
        colitems = self.config.getcolitems()
        reporter(repevent.RsyncFinished())

        if runner is None:
            runner = self.init_runner()

        keyword = self.config.option.keyword

        itemgenerator = itemgen(colitems, reporter, keyword)
        local_loop(self, reporter, itemgenerator, checkfun, self.config, runner=runner)
        
        retval = reporter(repevent.TestFinished())

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

