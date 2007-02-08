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
        self.relpath = parts and parts.pop(0) or ""
        if not self.relpath and self.hostname != "localhost":
            self.relpath = "pytestcache-%s" % self.hostname
        assert not parts
        self.hostid = self._getuniqueid(self.hostname) 

    def _getuniqueid(self, hostname):
        l = self._hostname2list.setdefault(hostname, [])
        hostid = hostname + "[%d]" % len(l)
        l.append(hostid)
        return hostid

    def initgateway(self, python="python", topdir=None):
        if self.hostname == "localhost":
            self.gw = py.execnet.PopenGateway(python=python)
        else:
            self.gw = py.execnet.SshGateway(self.hostname, 
                                            remotepython=python)
        relpath = self.relpath or topdir 
        assert relpath 
        channel = self.gw.remote_exec(py.code.Source(
            gethomedir, 
            getpath_relto_home, """
            import os
            os.chdir(gethomedir())
            path = %r
            if path:
                path = getpath_relto_home(path)
            channel.send(path)
            """ % str(relpath)
        ))
        self.gw_remotepath = channel.receive()

    def __str__(self):
        return "<HostInfo %s:%s>" % (self.hostname, self.relpath)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.hostid)

    def __eq__(self, other):
        return self.hostid == other.hostid

    def __ne__(self, other):
        return not self == other

class HostRSync(py.execnet.RSync):
    """ RSyncer that filters out common files 
    """
    def __init__(self, sourcedir, *args, **kwargs):
        self._synced = {}
        ignores= None
        if 'ignores' in kwargs:
            ignores = kwargs.pop('ignores')
        self._ignores = ignores or []
        super(HostRSync, self).__init__(sourcedir=sourcedir, **kwargs)

    def filter(self, path):
        path = py.path.local(path)
        if not path.ext in ('.pyc', '.pyo'):
            if not path.basename.endswith('~'): 
                if path.check(dotfile=0):
                    for x in self._ignores:
                        if path == x:
                            break
                    else:
                        return True

    def add_target_host(self, host, destrelpath="", reporter=lambda x: None):
        remotepath = host.gw_remotepath 
        key = host.hostname, host.relpath
        if destrelpath:
            remotepath = os.path.join(remotepath, destrelpath)
        if host.hostname == "localhost" and remotepath == self._sourcedir:
            self._synced[key] = True
        synced = key in self._synced 
        reporter(repevent.HostRSyncing(host, self._sourcedir, 
                                       remotepath, synced))
        def hostrsynced(host=host):
            reporter(repevent.HostRSyncRootReady(host, self._sourcedir))
        if key in self._synced:
            hostrsynced()
            return
        self._synced[key] = True
        super(HostRSync, self).add_target(host.gw, remotepath, 
                                          finishedcallback=hostrsynced,
                                          delete=True,
                                          )
        return remotepath 

class HostManager(object):
    def __init__(self, config, hosts=None):
        self.config = config
        if hosts is None:
            hosts = self.config.getvalue("dist_hosts")
            hosts = [HostInfo(x) for x in hosts]
        self.hosts = hosts
        roots = self.config.getvalue_pathlist("dist_rsync_roots")
        if roots is None:
            roots = [self.config.topdir]
        self.roots = roots

    def prepare_gateways(self, reporter):
        python = self.config.getvalue("dist_remotepython")
        for host in self.hosts:
            host.initgateway(python=python, topdir=self.config.topdir)
            reporter(repevent.HostGatewayReady(host, self.roots))
            host.gw.host = host

    def init_rsync(self, reporter):
        ignores = self.config.getvalue_pathlist("dist_rsync_ignore")
        self.prepare_gateways(reporter)
        # send each rsync root
        for root in self.roots:
            rsync = HostRSync(root, ignores=ignores, 
                              verbose=self.config.option.verbose)
            destrelpath = root.relto(self.config.topdir)
            for host in self.hosts:
                rsync.add_target_host(host, destrelpath, reporter)
            rsync.send(raises=False)

    def setup_hosts(self, reporter):
        self.init_rsync(reporter)
        nodes = []
        for host in self.hosts:
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
            #try:
            try:
                repevent.wrapcall(reporter, channel.waitclose, 1)
            except IOError: # timeout
                # force closing
                channel.close()
            channel.gateway.exit()

def gethomedir():
    import os
    homedir = os.environ.get('HOME', '')
    if not homedir:
        homedir = os.environ.get('HOMEPATH', '.')
    return os.path.abspath(homedir)

def getpath_relto_home(targetpath):
    import os
    if not os.path.isabs(targetpath):
        homedir = gethomedir()
        targetpath = os.path.join(homedir, targetpath)
    return targetpath
