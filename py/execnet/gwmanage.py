"""
    instantiating, managing and rsyncing to hosts

Host specification strings and implied gateways:

    socket:hostname:port:path SocketGateway
    popen[-executable][:path]          PopenGateway
    [ssh:]spec:path           SshGateway
    * [SshGateway]

on hostspec.makeconnection() a Host object
will be created which has an instantiated gateway. 
the remote side will be chdir()ed to the specified path. 
if no path was specified, do no chdir() at all. 


"""
import py
import sys, os
from py.__.test.dsession.masterslave import MasterNode
from py.__.test import event
from py.__.execnet.channel import RemoteError

NO_ENDMARKER_WANTED = object()

class GatewaySpec(object):
    python = None
    def __init__(self, spec, defaultjoinpath="pyexecnetcache"):
        self._spec = spec
        if spec == "popen" or spec.startswith("popen:"):
            parts = spec.split(":", 2)
            self.type = self.address = parts.pop(0)
            if parts:
                python = parts.pop(0)
                # XXX XXX XXX do better GWSPEC that can deal
                # with "C:" 
                if py.std.sys.platform == "win32" and len(python) == 1:
                    python = "%s:%s" %(python, parts.pop(0))
                self.python = python
            if parts:
                self.joinpath = parts.pop(0)
            else:
                self.joinpath = ""
            if not self.python:
                self.python = py.std.sys.executable

        elif spec.startswith("socket:"):
            parts = spec[7:].split(":", 2)
            self.address = parts.pop(0)
            if parts:
                port = int(parts.pop(0))
                self.address = self.address, port
            self.joinpath = parts and parts.pop(0) or ""
            self.type = "socket"
        else:
            if spec.startswith("ssh:"):
                spec = spec[4:]
            parts = spec.split(":", 2)
            self.address = parts.pop(0)
            self.python = parts and parts.pop(0) or "python"
            self.joinpath = parts and parts.pop(0) or ""
            self.type = "ssh"
        if not self.joinpath and not self.inplacelocal():
            self.joinpath = defaultjoinpath

    def inplacelocal(self):
        return bool(self.type == "popen" and not self.joinpath)

    def __str__(self):
        return "<GatewaySpec %s>" % self._spec
    __repr__ = __str__

    def makegateway(self, waitclose=True):
        if self.type == "popen":
            gw = py.execnet.PopenGateway(python=self.python)
        elif self.type == "socket":
            gw = py.execnet.SocketGateway(*self.address)
        elif self.type == "ssh":
            gw = py.execnet.SshGateway(self.address, remotepython=self.python)
        if self.joinpath:
            channel = gw.remote_exec("""
                import os 
                path = %r
                try:
                    os.chdir(path)
                except OSError:
                    os.mkdir(path)
                    os.chdir(path)
            """ % self.joinpath)
            if waitclose:
                channel.waitclose()
        else:
            if waitclose:
                gw.remote_exec("").waitclose()
        gw.spec = self
        return gw 

class GatewayManager:
    RemoteError = RemoteError

    def __init__(self, specs):
        self.specs = [GatewaySpec(spec) for spec in specs]
        self.gateways = []

    def trace(self, msg):
        self.notify("trace", "gatewaymanage", msg)

    def notify(self, eventname, *args, **kwargs):
        py._com.pyplugins.notify(eventname, *args, **kwargs)

    def makegateways(self):
        assert not self.gateways
        for spec in self.specs:
            gw = spec.makegateway()
            self.gateways.append(gw)
            gw.id = "[%s]" % len(self.gateways)
            self.notify("gwmanage_newgateway", gw)

    def getgateways(self, remote=True, inplacelocal=True):
        if not self.gateways and self.specs:
            self.makegateways()
        l = []
        for gw in self.gateways:
            if gw.spec.inplacelocal():
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
        added = False
        for gateway in self.gateways:
            spec = gateway.spec
            if not spec.inplacelocal():
                self.trace("add_target_host %r" %(gateway,))
                def finished():
                    if notify:
                        notify("rsyncrootready", spec, source)
                rsync.add_target_host(gateway, finished=finished)
                added = True
        if added:
            self.trace("rsyncing %r" % source)
            rsync.send()
            self.trace("rsyncing %r finished" % source)
        else:
            self.trace("rsync: nothing to do.")

    def exit(self):
        while self.gateways:
            gw = self.gateways.pop()
            self.trace("exiting gateway %s" % gw)
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
            remotepath = gateway.spec.joinpath
            print '%s:%s <= %s' % (gateway.remoteaddress, remotepath, path)
