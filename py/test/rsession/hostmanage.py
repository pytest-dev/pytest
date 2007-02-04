import sys, os
import py
import time
import thread, threading 
from py.__.test.rsession.master import MasterNode
from py.__.test.rsession.slave import setup_slave

from py.__.test.rsession import repevent 

class HostInfo(object):
    """ Class trying to store all necessary attributes
    for host
    """
    _hostname2list = {}
    localdest = None
    
    def __init__(self, spec):
        parts = spec.split(':', 1)
        self.hostname = parts.pop(0)
        if parts:
            self.relpath = parts[0]
        else:
            self.relpath = "pytestcache-" + self.hostname 
        self.hostid = self._getuniqueid(self.hostname) 

    def _getuniqueid(self, hostname):
        l = self._hostname2list.setdefault(hostname, [])
        hostid = hostname + "_" * len(l)
        l.append(hostid)
        return hostid

    def initgateway(self, python="python"):
        assert not hasattr(self, 'gw')
        if self.hostname == "localhost": 
            gw = py.execnet.PopenGateway(python=python)
        else:
            gw = py.execnet.SshGateway(self.hostname, 
                                       remotepython=python)
        self.gw = gw
        channel = gw.remote_exec("""
            import os
            targetdir = %r
            if not os.path.isabs(targetdir):
                homedir = os.environ['HOME']
                targetdir = os.path.join(homedir, targetdir)
            if not os.path.exists(targetdir):
                os.makedirs(targetdir)
            channel.send(os.path.abspath(targetdir))
        """ % self.relpath)
        self.gw_remotepath = channel.receive()
        #print "initialized", gw, "with remotepath", self.gw_remotepath
        if self.hostname == "localhost":
            self.localdest = py.path.local(self.gw_remotepath)
            assert self.localdest.check(dir=1)

    def __str__(self):
        return "<HostInfo %s:%s>" % (self.hostname, self.relpath)

    def __hash__(self):
        return hash(self.hostid)

    def __eq__(self, other):
        return self.hostid == other.hostid

    def __ne__(self, other):
        return not self == other

class HostRSync(py.execnet.RSync):
    """ RSyncer that filters out common files 
    """
    def __init__(self, *args, **kwargs):
        self._synced = {}
        super(HostRSync, self).__init__(*args, **kwargs)

    def filter(self, path):
        path = py.path.local(path)
        if not path.ext in ('.pyc', '.pyo'):
            if not path.basename.endswith('~'): 
                if path.check(dotfile=0):
                    return True

    def add_target_host(self, host, destrelpath=None, finishedcallback=None):
        key = host.hostname, host.relpath 
        if key in self._synced:
            if finishedcallback:
                finishedcallback()
            return False 
        self._synced[key] = True
        # the follow attributes are set from host.initgateway()
        gw = host.gw
        remotepath = host.gw_remotepath
        if destrelpath is not None:
            remotepath = os.path.join(remotepath, destrelpath)
        super(HostRSync, self).add_target(gw, 
                                          remotepath, 
                                          finishedcallback)
        return True # added the target

class HostManager(object):
    def __init__(self, sshhosts, config):
        self.sshhosts = sshhosts
        self.config = config

    def prepare_gateways(self):
        dist_remotepython = self.config.getvalue("dist_remotepython")
        for host in self.sshhosts:
            host.initgateway(python=dist_remotepython)
            host.gw.host = host

    def init_rsync(self, reporter):
        # send each rsync root  
        roots = self.config.getvalue_pathlist("dist_rsync_roots")
        if roots is None:
            roots = [self.config.topdir]
        self.prepare_gateways()
        rsync = HostRSync()
        for root in roots: 
            destrelpath = root.relto(self.config.topdir)
            for host in self.sshhosts:
                reporter(repevent.HostRSyncing(host))
                def donecallback():
                    reporter(repevent.HostReady(host))
                rsync.add_target_host(host, destrelpath, 
                                      finishedcallback=donecallback)
            rsync.send(root)

    def init_hosts(self, reporter):
        # hosts ready
        self.init_rsync(reporter)
        return self.setup_nodes(reporter)

    def setup_nodes(self, reporter):
        nodes = []
        for host in self.sshhosts:
            if hasattr(host.gw, 'remote_exec'): # otherwise dummy for tests :/
                ch = setup_slave(host, self.config)
                nodes.append(MasterNode(ch, reporter))
        return nodes

    def teardown_hosts(self, reporter, channels, nodes,
                       waiter=lambda : time.sleep(.1), exitfirst=False):
        for channel in channels:
            channel.send(None)
    
        clean = exitfirst
        while not clean:
            clean = True
            for node in nodes:
                if node.pending:
                    clean = False
            waiter()
        self.teardown_gateways(reporter, channels)

    def kill_channels(self, channels):
        for channel in channels:
            channel.send(42)

    def teardown_gateways(self, reporter, channels):
        for channel in channels:
            try:
                repevent.wrapcall(reporter, channel.waitclose)
            except KeyboardInterrupt, SystemExit:
                raise
            except:
                pass
            channel.gateway.exit()
