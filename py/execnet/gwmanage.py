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


class GatewaySpec(object):
    type = "ssh"
    def __init__(self, spec, defaultjoinpath="pyexecnetcache"):
        if spec == "popen" or spec.startswith("popen:"):
            self.address = "popen"
            self.joinpath = spec[len(self.address)+1:]
            self.type = "popen"
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
            parts = spec.split(":", 1)
            self.address = parts.pop(0)
            self.joinpath = parts and parts.pop(0) or ""
        if not self.joinpath and not self.inplacelocal():
            self.joinpath = defaultjoinpath

    def inplacelocal(self):
        return bool(self.type == "popen" and not self.joinpath)

    def __str__(self):
        return "<GatewaySpec %s:%s>" % (self.address, self.joinpath)
    __repr__ = __str__

    def makegateway(self, python=None, waitclose=True):
        if self.type == "popen":
            gw = py.execnet.PopenGateway(python=python)
        elif self.type == "socket":
            gw = py.execnet.SocketGateway(*self.address)
        elif self.type == "ssh":
            gw = py.execnet.SshGateway(self.address, remotepython=python)
        if self.joinpath:
            channel = gw.remote_exec("import os ; os.chdir(channel.receive())")
            channel.send(self.joinpath)
            if waitclose:
                channel.waitclose()
        else:
            if waitclose:
                gw.remote_exec("").waitclose()
        gw.spec = self
        return gw 

class MultiChannel:
    def __init__(self, channels):
        self._channels = channels

    def receive(self):
        values = []
        for ch in self._channels:
            values.append(ch.receive())
        return values

    def wait(self):
        for ch in self._channels:
            ch.waitclose()

class GatewayManager:
    def __init__(self, specs):
        self.spec2gateway = {}
        for spec in specs:
            self.spec2gateway[GatewaySpec(spec)] = None

    def trace(self, msg):
        py._com.pyplugins.notify("trace_gatewaymanage", msg)
        #print "trace", msg

    def makegateways(self):
        for spec, value in self.spec2gateway.items():
            assert value is None
            self.trace("makegateway %s" %(spec))
            self.spec2gateway[spec] = spec.makegateway()

    def multi_exec(self, source, inplacelocal=True):
        source = py.code.Source(source)
        channels = []
        for spec, gw in self.spec2gateway.items():
            if inplacelocal or not spec.inplacelocal():
                channels.append(gw.remote_exec(source))
        return MultiChannel(channels)

    def multi_chdir(self, basename, inplacelocal=True):
        self.multi_exec("import os ; os.chdir(%r)" % basename, 
                        inplacelocal=inplacelocal).wait()

    def rsync(self, source, notify=None, verbose=False, ignores=None):
        rsync = HostRSync(source, verbose=verbose, ignores=ignores)
        added = False
        for spec, gateway in self.spec2gateway.items():
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
        while self.spec2gateway:
            spec, gw = self.spec2gateway.popitem()
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
