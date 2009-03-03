import py
import sys, os
from py.__.test.dsession.masterslave import MasterNode
from py.__.execnet.gwmanage import GatewayManager
from py.__.test import event

def getconfighosts(config):
    if config.option.numprocesses:
        hosts = ['localhost'] * config.option.numprocesses
    else:
        hosts = config.getvalue("dist_hosts")
        assert hosts is not None
    return hosts
    
class HostManager(object):
    def __init__(self, config, hosts=None):
        self.config = config 
        roots = self.config.getvalue_pathlist("rsyncroots")
        if not roots:
            roots = self.config.getvalue_pathlist("dist_rsync_roots")
        self.roots = roots
        if hosts is None:
            hosts = getconfighosts(self.config)
        self.gwmanager = GatewayManager(hosts)

    def makegateways(self):
        old = self.config.topdir.chdir()  
        try:
            self.gwmanager.makegateways()
        finally:
            old.chdir()

    def rsync_roots(self):
        """ make sure that all remote gateways
            have the same set of roots in their
            current directory. 
        """
        # we change to the topdir sot that 
        # PopenGateways will have their cwd 
        # such that unpickling configs will 
        # pick it up as the right topdir 
        # (for other gateways this chdir is irrelevant)
        self.makegateways()
        options = {
            'ignores': self.config.getvalue_pathlist("dist_rsync_ignore"),
            'verbose': self.config.option.verbose
        }
        if self.roots:
            # send each rsync root
            for root in self.roots:
                self.gwmanager.rsync(root, **options)
        else: 
            # we transfer our topdir as the root 
            # but need to be careful regarding 
            self.gwmanager.rsync(self.config.topdir, **options)
            self.gwmanager.multi_chdir(self.config.topdir.basename, inplacelocal=False)
        self.config.bus.notify("rsyncfinished", event.RsyncFinished())

    def setup_hosts(self, putevent):
        self.rsync_roots()
        nice = self.config.getvalue("dist_nicelevel")
        if nice != 0:
            self.gwmanager.multi_exec("""
                import os
                if hasattr(os, 'nice'): 
                    os.nice(%r)
            """ % nice).wait()
            
        for host, gateway in self.gwmanager.spec2gateway.items():
            host.node = MasterNode(host, 
                                   gateway,
                                   self.config, 
                                   putevent)

    def teardown_hosts(self):
        self.gwmanager.exit()
