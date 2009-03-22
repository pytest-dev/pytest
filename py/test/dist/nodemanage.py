import py
import sys, os
from py.__.test.dist.txnode import TXNode
from py.__.execnet.gwmanage import GatewayManager

    
class NodeManager(object):
    def __init__(self, config, specs=None):
        self.config = config 
        if specs is None:
            specs = self.config.getxspecs()
        self.roots = self.config.getrsyncdirs()
        self.gwmanager = GatewayManager(specs)
        self.nodes = []
        self._nodesready = py.std.threading.Event()

    def trace(self, msg):
        self.config.bus.notify("trace", "nodemanage", msg)

    def config_getignores(self):
        return self.config.getconftest_pathlist("rsyncignore")

    def rsync_roots(self):
        """ make sure that all remote gateways
            have the same set of roots in their
            current directory. 
        """
        self.makegateways()
        options = {
            'ignores': self.config_getignores(), 
            'verbose': self.config.option.verbose,
        }
        if self.roots:
            # send each rsync root
            for root in self.roots:
                self.gwmanager.rsync(root, **options)
        else: 
            XXX # do we want to care for situations without explicit rsyncdirs? 
            # we transfer our topdir as the root
            self.gwmanager.rsync(self.config.topdir, **options)
            # and cd into it 
            self.gwmanager.multi_chdir(self.config.topdir.basename, inplacelocal=False)

    def makegateways(self):
        # we change to the topdir sot that 
        # PopenGateways will have their cwd 
        # such that unpickling configs will 
        # pick it up as the right topdir 
        # (for other gateways this chdir is irrelevant)
        self.trace("making gateways")
        old = self.config.topdir.chdir()  
        try:
            self.gwmanager.makegateways()
        finally:
            old.chdir()

    def setup_nodes(self, putevent):
        self.rsync_roots()
        self.trace("setting up nodes")
        for gateway in self.gwmanager.gateways:
            node = TXNode(gateway, self.config, putevent, slaveready=self._slaveready)
            gateway.node = node  # to keep node alive 
            self.trace("started node %r" % node)

    def _slaveready(self, node):
        #assert node.gateway == node.gateway
        #assert node.gateway.node == node
        self.nodes.append(node)
        self.trace("%s slave node ready %r" % (node.gateway.id, node))
        if len(self.nodes) == len(self.gwmanager.gateways):
            self._nodesready.set()
   
    def wait_nodesready(self, timeout=None):
        self._nodesready.wait(timeout)
        if not self._nodesready.isSet():
            raise IOError("nodes did not get ready for %r secs" % timeout)

    def teardown_nodes(self):
        # XXX do teardown nodes? 
        self.gwmanager.exit()

