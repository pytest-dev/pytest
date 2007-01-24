import sys, os
import py
import time
import thread, threading 
from py.__.test.rsession.master import \
     setup_slave, MasterNode
from py.__.test.rsession import report 

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

class HostRSync(py.execnet.RSync):
    """ An rsync wrapper which filters out *~, .svn/ and *.pyc
    """
    def __init__(self, rsync_roots):
        py.execnet.RSync.__init__(self, delete=True)
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

class HostOptions(object):
    """ Dummy container for host options, not to keep that
    as different function parameters, mostly related to
    tests only
    """
    def __init__(self, rsync_roots=None, remote_python="python",
                 optimise_localhost=True, do_sync=True,
                 create_gateways=True):
        self.rsync_roots = rsync_roots
        self.remote_python = remote_python
        self.optimise_localhost = optimise_localhost
        self.do_sync = do_sync
        self.create_gateways = create_gateways

class HostManager(object):
    def __init__(self, sshhosts, config, pkgdir, options=HostOptions()):
        self.sshhosts = sshhosts
        self.pkgdir = pkgdir
        self.config = config
        self.options = options
        if not options.create_gateways:
            self.prepare_gateways = self.prepare_dummy_gateways
        assert pkgdir.join("__init__.py").check(), (
            "%s probably wrong" %(pkgdir,))

    def prepare_dummy_gateways(self):
        for host in self.sshhosts:
            gw = DummyGateway()
            host.gw = gw
            gw.host = host
        return self.sshhosts

    def prepare_ssh_gateway(self, host):
        if self.options.remote_python is None:
            gw = py.execnet.SshGateway(host.hostname)
        else:
            gw = py.execnet.SshGateway(host.hostname,
                                       remotepython=self.options.remote_python)
        return gw

    def prepare_popen_rsync_gateway(self, host):
        """ Popen gateway, but with forced rsync
        """
        from py.__.execnet.register import PopenCmdGateway
        gw = PopenCmdGateway("cd ~; python -u -c 'exec input()'")
        if not host.relpath.startswith("/"):
            host.relpath = os.environ['HOME'] + '/' + host.relpath
        return gw

    def prepare_popen_gateway(self, host):
        if self.options.remote_python is None:
            gw = py.execnet.PopenGateway()
        else:
            gw = py.execnet.PopenGateway(python=self.options.remote_python)
        host.relpath = str(self.pkgdir.dirpath())
        return gw

    def prepare_gateways(self):
        for host in self.sshhosts:
            if host.hostname == 'localhost':
                if not self.options.optimise_localhost:
                    gw = self.prepare_popen_rsync_gateway(host)
                else:
                    gw = self.prepare_popen_gateway(host)
            else:
                gw = self.prepare_ssh_gateway(host)
            host.gw = gw
            gw.host = host
        return self.sshhosts

    def need_rsync(self, rsynced, hostname, remoterootpath):
        if (hostname, remoterootpath) in rsynced:
            return False
        if hostname == 'localhost' and self.options.optimise_localhost:
            return False
        return True

    def init_hosts(self, reporter, done_dict={}):
        if done_dict is None:
            done_dict = {}

        hosts = self.prepare_gateways()
        
        # rsyncing
        rsynced = {}

        if self.options.do_sync:
            rsync = HostRSync(self.options.rsync_roots)
        for host in hosts:
            if not self.need_rsync(rsynced, host.hostname, host.relpath):
                reporter(report.HostReady(host))
                continue
            rsynced[(host.hostname, host.relpath)] = True
            def done(host=host):
                reporter(report.HostReady(host))
            reporter(report.HostRSyncing(host))
            if self.options.do_sync:
                rsync.add_target(host.gw, host.relpath, done)
        if not self.options.do_sync:
            return # for testing only
        rsync.send(self.pkgdir.dirpath())
        # hosts ready
        return self.setup_nodes(reporter, done_dict)

    def setup_nodes(self, reporter, done_dict):
        nodes = []
        for host in self.sshhosts:
            ch = setup_slave(host.gw, os.path.join(host.relpath,\
                         self.pkgdir.basename), self.config)
            nodes.append(MasterNode(ch, reporter, done_dict))
    
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
                report.wrapcall(reporter, channel.waitclose)
            except KeyboardInterrupt, SystemExit:
                raise
            except:
                pass
            channel.gateway.exit()
