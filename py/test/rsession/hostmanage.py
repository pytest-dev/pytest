import sys, os
import py
import time
import thread, threading 
from py.__.test.rsession.master import \
     setup_slave, MasterNode
from py.__.test.rsession import report 
from py.__.test.rsession.rsync import RSync

class HostInfo(object):
    """ Class trying to store all necessary attributes
    for host
    """
    host_ids = {}
    
    def __init__(self, hostname, relpath=None):
        self.hostid = self._getuniqueid(hostname)
        self.hostname = hostname
        self.relpath = relpath

    def _getuniqueid(cls, hostname):
        if not hostname in cls.host_ids:
            cls.host_ids[hostname] = 0
            return hostname
        retval = hostname + '_' + str(cls.host_ids[hostname])
        cls.host_ids[hostname] += 1
        return retval
    _getuniqueid = classmethod(_getuniqueid)

    def __str__(self):
        return "<HostInfo %s>" % (self.hostname,)

    def __hash__(self):
        return hash(self.hostid)

    def __eq__(self, other):
        return self.hostid == other.hostid

    def __ne__(self, other):
        return not self == other

class HostRSync(RSync):
    """ An rsync wrapper which filters out *~, .svn/ and *.pyc
    """
    def __init__(self, rsync_roots):
        RSync.__init__(self, delete=True)
        self.rsync_roots = rsync_roots

    def filter(self, path):
        if path.endswith('.pyc') or path.endswith('~'):
            return False
        dir, base = os.path.split(path)
        if base == '.svn':
            return False
        if self.rsync_roots is None or dir != self.sourcedir:
            return True
        else:
            return base in self.rsync_roots

class DummyGateway(object):
    pass

def prepare_gateway(sshosts, optimise_localhost, 
    remote_python, pkgdir, real_create=True):
    hosts = []
    for host in sshosts:
        if host.hostname != 'localhost' or not optimise_localhost:
            if real_create:
                # for tests we want to use somtehing different
                if host.hostname == 'localhost' and optimise_localhost is False:
                    from py.__.execnet.register import PopenCmdGateway
                    gw = PopenCmdGateway("cd ~; python -u -c 'exec input()'")
                    if not host.relpath.startswith("/"):
                        host.relpath = os.environ['HOME'] + '/' + host.relpath
                else:
                    if remote_python is None:
                        gw = py.execnet.SshGateway(host.hostname)
                    else:
                        gw = py.execnet.SshGateway(host.hostname,
                                                   remotepython=remote_python)
            else:
                gw = DummyGateway()
        else:
            if remote_python is None:
                gw = py.execnet.PopenGateway()
            else:
                gw = py.execnet.PopenGateway(remotepython=remote_python)
            host.relpath = str(pkgdir.dirpath())
        host.gw = gw
        gw.host = host
    return sshosts

def init_hosts(reporter, sshhosts, pkgdir, rsync_roots=None,
               remote_python=None, \
               remote_options={}, optimise_localhost=True,\
               do_sync=True, done_dict=None):
    if done_dict is None:
        done_dict = {}
    assert pkgdir.join("__init__.py").check(), (
            "%s probably wrong" %(pkgdir,))

    exc_info = [None]
    hosts = prepare_gateway(sshhosts, optimise_localhost,
        remote_python, pkgdir, real_create=do_sync)
    
    # rsyncing
    rsynced = {}

    if do_sync:
        rsync = HostRSync(rsync_roots)
    for host in hosts:
    #for num, host, gw, remoterootpath in hosts:
        remoterootpath = host.relpath
        if (host.hostname, remoterootpath) in rsynced or\
           (host.hostname == 'localhost' and optimise_localhost):
            reporter(report.HostReady(host))
            continue
        rsynced[(host.hostname, host.relpath)] = True
        def done(host=host):
            reporter(report.HostReady(host))
        reporter(report.HostRSyncing(host))
        if do_sync:
            rsync.add_target(host.gw, remoterootpath, done)
    if not do_sync:
        return # for testing only
    rsync.send(pkgdir.dirpath())

    # hosts ready
    return setup_nodes(hosts, pkgdir, remote_options, reporter, done_dict)

def setup_nodes(hosts, pkgdir, remote_options, reporter, done_dict):
    nodes = []
    for host in hosts:
        ch = setup_slave(host.gw, os.path.join(host.relpath,\
                         pkgdir.basename), remote_options)
        nodes.append(MasterNode(ch, reporter, done_dict))
    
    return nodes

def teardown_hosts(reporter, channels, nodes, waiter=lambda : time.sleep(.1),
        exitfirst=False):
    for channel in channels:
        channel.send(None)
    
    from py.__.test.rsession.rsession import session_options

    clean = exitfirst
    while not clean:
        clean = True
        for node in nodes:
            if node.pending:
                clean = False
        waiter()
        

    for channel in channels:
        try:
            report.wrapcall(reporter, channel.waitclose, int(session_options.waittime))
        except KeyboardInterrupt, SystemExit:
            raise
        except:
            pass
        channel.gateway.exit()
