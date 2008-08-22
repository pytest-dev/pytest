import py
import sys, os
from py.__.test.dsession.masterslave import MasterNode
from py.__.test import event

class Host(object):
    """ Host location representation for distributed testing. """ 
    _hostname2list = {}
    
    def __init__(self, spec, addrel="", python=None):
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
        self.python = python 

    def __getstate__(self):
        return (self.hostname, self.relpath, self.hostid)
       
    def __setstate__(self, repr):
        self.hostname, self.relpath, self.hostid = repr

    def _getuniqueid(self, hostname):
        l = self._hostname2list.setdefault(hostname, [])
        hostid = hostname + "-%d" % len(l)
        l.append(hostid)
        return hostid

    def initgateway(self):
        python = self.python or "python"
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
        return "<Host id=%s %s:%s>" % (self.hostid, self.hostname, self.relpath)
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

    def add_target_host(self, host, destrelpath="", notify=None):
        remotepath = host.gw_remotepath 
        key = host.hostname, host.relpath
        if host.inplacelocal: 
            remotepath = self._sourcedir
            self._synced[key] = True
        elif destrelpath:
            remotepath = os.path.join(remotepath, destrelpath)
        synced = key in self._synced 
        if notify: 
            notify(
                event.HostRSyncing(host, py.path.local(self._sourcedir), 
                                      remotepath, synced))
        def hostrsynced(host=host):
            if notify: 
                notify(
                    event.HostRSyncRootReady(host, self._sourcedir))
        if key in self._synced:
            hostrsynced()
            return
        self._synced[key] = True
        super(HostRSync, self).add_target(host.gw, remotepath, 
                                          finishedcallback=hostrsynced,
                                          delete=True,
                                          )
        return remotepath 

def gethosts(config, addrel):
    if config.option.numprocesses:
        hosts = ['localhost'] * config.option.numprocesses
    else:
        hosts = config.getvalue("dist_hosts")
    python = config.option.executable or "python"
    hosts = [Host(x, addrel, python=python) for x in hosts]
    return hosts
    
class HostManager(object):
    def __init__(self, session, hosts=None):
        self.session = session 
        roots = self.session.config.getvalue_pathlist("dist_rsync_roots")
        addrel = ""
        if roots is None:
            roots = [self.session.config.topdir]
            addrel = self.session.config.topdir.basename 
        self._addrel = addrel
        self.roots = roots
        if hosts is None:
            hosts = gethosts(self.session.config, addrel)
        self.hosts = hosts

    def prepare_gateways(self):
        for host in self.hosts:
            host.initgateway()
            self.session.bus.notify(event.HostGatewayReady(host, self.roots))

    def init_rsync(self):
        self.prepare_gateways()
        # send each rsync root
        ignores = self.session.config.getvalue_pathlist("dist_rsync_ignore")
        for root in self.roots:
            rsync = HostRSync(root, ignores=ignores, 
                              verbose=self.session.config.option.verbose)
            if self._addrel: 
                destrelpath = ""
            else:
                destrelpath = root.basename
            for host in self.hosts:
                rsync.add_target_host(host, destrelpath)
            rsync.send(raises=False)
        self.session.bus.notify(event.RsyncFinished())

    def setup_hosts(self, notify=None):
        if notify is None:
            notify = self.session.bus.notify
        self.init_rsync()
        for host in self.hosts:
            host.node = MasterNode(host, 
                                   self.session.config, 
                                   notify)

#
# helpers 
#
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

def makehostup(host=None):
    if host is None:
        host = Host("localhost")
    platinfo = {}
    for name in 'platform', 'executable', 'version_info':
        platinfo["sys."+name] = getattr(sys, name)
    return event.HostUp(host, platinfo)
