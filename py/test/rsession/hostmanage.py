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
        hostid = hostname + "[%d]" % len(l)
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
        channel = gw.remote_exec(py.code.Source(
            gethomedir, 
            getpath_relto_home, """
            import os
            os.chdir(gethomedir())
            newdir = getpath_relto_home(%r)
            # we intentionally don't ensure that 'newdir' exists 
            channel.send(newdir)
            """ % str(self.relpath)
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
    def __init__(self, *args, **kwargs):
        self._synced = {}
        ignores= None
        if 'ignores' in kwargs:
            ignores = kwargs.pop('ignores')
        self._ignores = ignores or []
        kwargs['delete'] = True
        super(HostRSync, self).__init__(**kwargs)

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

    def add_target_host(self, host, reporter=lambda x: None,
                        destrelpath=None, finishedcallback=None):
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
        return remotepath 

class HostManager(object):
    def __init__(self, config, hosts=None, optimise_localhost=False):
        self.optimise_localhost = optimise_localhost
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
        dist_remotepython = self.config.getvalue("dist_remotepython")
        for host in self.hosts:
            host.initgateway(python=dist_remotepython)
            reporter(repevent.HostGatewayReady(host, self.roots))
            host.gw.host = host

    def init_rsync(self, reporter):
        # send each rsync root
        ignores = self.config.getvalue_pathlist("dist_rsync_ignore")
        self.prepare_gateways(reporter)
        for root in self.roots:
            rsync = HostRSync(ignores=ignores, 
                              verbose=self.config.option.verbose)
            destrelpath = root.relto(self.config.topdir)
            to_send = False
            for host in self.hosts:
                if host.hostname != 'localhost' or not self.optimise_localhost:
                    def donecallback(host=host, root=root):
                        reporter(repevent.HostRSyncRootReady(host, root))
                    remotepath = rsync.add_target_host(
                        host, reporter, destrelpath, finishedcallback=
                        donecallback)
                    reporter(repevent.HostRSyncing(host, root, remotepath))
                    to_send = True
                else:
                    reporter(repevent.HostRSyncRootReady(host, root))
            if to_send:
                # don't send if we have no targets
                rsync.send(root)

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
            try:
                channel.send(None)
            except IOError:
                print "Sending error, channel IOError"
                print channel._getremoterror()
                # XXX: this should go as soon as we'll have proper detection
                #      of hanging nodes and such
                raise
    
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
            try:
                channel.send(42)
            except IOError:
                print "Sending error, channel IOError"
                print channel._getremoterror()

    def teardown_gateways(self, reporter, channels):
        for channel in channels:
            try:
                repevent.wrapcall(reporter, channel.waitclose)
            except KeyboardInterrupt, SystemExit:
                raise
            except:
                pass
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
