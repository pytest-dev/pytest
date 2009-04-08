"""
    instantiating, managing and rsyncing to hosts

"""

import py
import sys, os
from py.__.execnet.channel import RemoteError

NO_ENDMARKER_WANTED = object()

class GatewayManager:
    RemoteError = RemoteError

    def __init__(self, specs, defaultchdir="pyexecnetcache"):
        self.gateways = []
        self.specs = []
        for spec in specs:
            if not isinstance(spec, py.execnet.XSpec):
                spec = py.execnet.XSpec(spec)
            if not spec.chdir and not spec.popen:
                spec.chdir = defaultchdir
            self.specs.append(spec)
        self.api = py._com.PluginAPI(py.execnet._API)

    def makegateways(self):
        assert not self.gateways
        for spec in self.specs:
            gw = py.execnet.makegateway(spec)
            self.gateways.append(gw)
            gw.id = "[%s]" % len(self.gateways)
            self.api.pyexecnet_gwmanage_newgateway(
                gateway=gw, platinfo=gw._rinfo())

    def getgateways(self, remote=True, inplacelocal=True):
        if not self.gateways and self.specs:
            self.makegateways()
        l = []
        for gw in self.gateways:
            if gw.spec._samefilesystem():
                if inplacelocal:
                    l.append(gw)
            else:
                if remote:
                    l.append(gw)
        return py.execnet.MultiGateway(gateways=l)

    def multi_exec(self, source, inplacelocal=True):
        """ remote execute code on all gateways. 
            @param inplacelocal=False: don't send code to inplacelocal hosts. 
        """
        multigw = self.getgateways(inplacelocal=inplacelocal)
        return multigw.remote_exec(source)

    def multi_chdir(self, basename, inplacelocal=True):
        """ perform a remote chdir to the given path, may be relative. 
            @param inplacelocal=False: don't send code to inplacelocal hosts. 
        """ 
        self.multi_exec("import os ; os.chdir(%r)" % basename, 
                        inplacelocal=inplacelocal).waitclose()

    def rsync(self, source, notify=None, verbose=False, ignores=None):
        """ perform rsync to all remote hosts. 
        """ 
        rsync = HostRSync(source, verbose=verbose, ignores=ignores)
        seen = {}
        for gateway in self.gateways:
            spec = gateway.spec
            if not spec._samefilesystem():
                if spec in seen:
                    continue 
                def finished():
                    if notify:
                        notify("rsyncrootready", spec, source)
                rsync.add_target_host(gateway, finished=finished)
                seen[spec] = gateway
        if seen:
            self.api.pyexecnet_gwmanage_rsyncstart(
                source=source, 
                gateways=seen.values(),
            )
            rsync.send()
            self.api.pyexecnet_gwmanage_rsyncfinish(
                source=source, 
                gateways=seen.values()
            )

    def exit(self):
        while self.gateways:
            gw = self.gateways.pop()
            gw.exit()

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

    def add_target_host(self, gateway, finished=None):
        remotepath = os.path.basename(self._sourcedir)
        super(HostRSync, self).add_target(gateway, remotepath, 
                                          finishedcallback=finished,
                                          delete=True,)

    def _report_send_file(self, gateway, modified_rel_path):
        if self._verbose:
            path = os.path.basename(self._sourcedir) + "/" + modified_rel_path
            remotepath = gateway.spec.chdir
            print '%s:%s <= %s' % (gateway.remoteaddress, remotepath, path)
