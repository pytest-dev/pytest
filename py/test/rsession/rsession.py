
""" Remote session base class
"""

import os
import py
import sys
import re
import time

from py.__.test import repevent
from py.__.test.rsession.master import MasterNode, dispatch_loop
from py.__.test.rsession.hostmanage import HostInfo, HostManager
from py.__.test.rsession.local import local_loop, plain_runner, apigen_runner,\
    box_runner
from py.__.test.reporter import LocalReporter, RemoteReporter, TestReporter
from py.__.test.session import AbstractSession, itemgen
from py.__.test.outcome import Skipped, Failed
    
class RSession(AbstractSession):
    """ Remote version of session
    """
    reporterclass = RemoteReporter
    
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

        reporter(repevent.TestStarted(hm.hosts, self.config,
                                      hm.roots))
        self.reporter = reporter

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
        itemgenerator = itemgen(self, colitems, reporter, keyword)
        all_tests = dispatch_loop(nodes, itemgenerator, checkfun)
