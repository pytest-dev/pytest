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
    
    def __init__(self, spec, addrel=""):
        parts = spec.split(':', 1)
        self.hostname = parts.pop(0)
        self.relpath = parts and parts.pop(0) or ""
        if self.hostname == "localhost" and not self.relpath:
            self.inplacelocal = True
            addrel = "" # inplace localhosts cannot have additions
        else:
            self.inplacelocal = False 
            if not self.relpath:
                self.relpath = "pytestcache-%s" % self.hostname
        if addrel:
            self.relpath += "/" + addrel # XXX too os-dependent
        assert not parts
        assert self.inplacelocal or self.relpath
        self.hostid = self._getuniqueid(self.hostname) 

    def _getuniqueid(self, hostname):
        l = self._hostname2list.setdefault(hostname, [])
        hostid = hostname + "[%d]" % len(l)
        l.append(hostid)
        return hostid

    def initgateway(self, python="python"):
        if self.hostname == "localhost":
            self.gw = py.execnet.PopenGateway(python=python)
        else:
            self.gw = py.execnet.SshGateway(self.hostname, 
                                            remotepython=python)
        if self.inplacelocal:
            self.gw.remote_exec(py.code.Source(
                sethomedir, "sethomedir()"
            )).waitclose()
            self.gw_remotepath = None
        else:
            assert self.relpath
            channel = self.gw.remote_exec(py.code.Source(
                gethomedir,
                sethomedir, "sethomedir()", 
                getpath_relto_home, """
                channel.send(getpath_relto_home(%r))
            """ % self.relpath,
            ))
            self.gw_remotepath = channel.receive()

    def __str__(self):
        return "<HostInfo %s:%s>" % (self.hostname, self.relpath)
    __repr__ = __str__

    def __hash__(self):
        return hash(self.hostid)

    def __eq__(self, other):
        return self.hostid == other.hostid

    def __ne__(self, other):
        return not self.hostid == other.hostid

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
        if host.inplacelocal: 
            remotepath = self._sourcedir
            self._synced[key] = True
        elif destrelpath:
            remotepath = os.path.join(remotepath, destrelpath)
        synced = key in self._synced 
        reporter(repevent.HostRSyncing(host, py.path.local(self._sourcedir), 
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
        roots = self.config.getvalue_pathlist("dist_rsync_roots")
        addrel = ""
        if roots is None:
            roots = [self.config.topdir]
            addrel = self.config.topdir.basename 
        self._addrel = addrel
        self.roots = roots
        if hosts is None:
            hosts = self.config.getvalue("dist_hosts")
            hosts = [HostInfo(x, addrel) for x in hosts]
        self.hosts = hosts

    def prepare_gateways(self, reporter):
        python = self.config.getvalue("dist_remotepython")
        for host in self.hosts:
            host.initgateway(python=python)
            reporter(repevent.HostGatewayReady(host, self.roots))
            host.gw.host = host

    def init_rsync(self, reporter):
        ignores = self.config.getvalue_pathlist("dist_rsync_ignore")
        self.prepare_gateways(reporter)
        # send each rsync root
        for root in self.roots:
            rsync = HostRSync(root, ignores=ignores, 
                              verbose=self.config.option.verbose)
            if self._addrel: 
                destrelpath = ""
            else:
                destrelpath = root.basename
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
    return os.path.normpath(targetpath)

def sethomedir():
    import os
    homedir = os.environ.get('HOME', '')
    if not homedir:
        homedir = os.environ.get('HOMEPATH', '.')
    os.chdir(homedir)
