"""
    instantiating, managing and rsyncing to test hosts
"""

import py
import sys, os
import execnet
from execnet.gateway_base import RemoteError

class GatewayManager:
    RemoteError = RemoteError
    def __init__(self, specs, hook, defaultchdir="pyexecnetcache"):
        self.specs = []
        self.hook = hook
        self.group = execnet.Group()
        for spec in specs:
            if not isinstance(spec, execnet.XSpec):
                spec = execnet.XSpec(spec)
            if not spec.chdir and not spec.popen:
                spec.chdir = defaultchdir
            self.specs.append(spec)

    def makegateways(self):
        assert not list(self.group)
        for spec in self.specs:
            gw = self.group.makegateway(spec)
            self.hook.pytest_gwmanage_newgateway(
                gateway=gw, platinfo=gw._rinfo())

    def rsync(self, source, notify=None, verbose=False, ignores=None):
        """ perform rsync to all remote hosts. 
        """ 
        rsync = HostRSync(source, verbose=verbose, ignores=ignores)
        seen = py.builtin.set()
        gateways = []
        for gateway in self.group:
            spec = gateway.spec
            if not spec._samefilesystem():
                if spec not in seen:
                    def finished():
                        if notify:
                            notify("rsyncrootready", spec, source)
                    rsync.add_target_host(gateway, finished=finished)
                    seen.add(spec)
                    gateways.append(gateway)
        if seen:
            self.hook.pytest_gwmanage_rsyncstart(
                source=source, 
                gateways=gateways, 
            )
            rsync.send()
            self.hook.pytest_gwmanage_rsyncfinish(
                source=source, 
                gateways=gateways, 
            )

    def exit(self):
        self.group.terminate()

class HostRSync(execnet.RSync):
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
            py.builtin.print_('%s:%s <= %s' %
                              (gateway.spec, remotepath, path))
