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
    python = "python" 
    def __init__(self, spec, defaultjoinpath="pyexecnetcache"):
        if spec == "popen" or spec.startswith("popen:"):
            parts = spec.split(":", 2)
            self.type = self.address = parts.pop(0)
            if parts:
                self.python = parts.pop(0)
            if parts:
                self.joinpath = parts.pop(0)
            else:
                self.joinpath = ""
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
        return "<GatewaySpec %s:%s>" % (self.address, self.joinpath)
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

class MultiChannel:
    def __init__(self, channels):
        self._channels = channels

    def send_each(self, item):
        for ch in self._channels:
            ch.send(item)

    def receive_each(self, withchannel=False):
        assert not hasattr(self, '_queue')
        l = []
        for ch in self._channels:
            obj = ch.receive()
            if withchannel:
                l.append((ch, obj))
            else:
                l.append(obj)
        return l 

    def make_receive_queue(self, endmarker=NO_ENDMARKER_WANTED):
        try:
            return self._queue
        except AttributeError:
            self._queue = py.std.Queue.Queue()
            for ch in self._channels:
                def putreceived(obj, channel=ch):
                    self._queue.put((channel, obj))
                if endmarker is NO_ENDMARKER_WANTED:
                    ch.setcallback(putreceived)
                else:
                    ch.setcallback(putreceived, endmarker=endmarker)
            return self._queue


    def waitclose(self):
        first = None
        for ch in self._channels:
            try:
                ch.waitclose()
            except ch.RemoteError:
                if first is None:
                    first = py.std.sys.exc_info()
        if first:
            raise first[0], first[1], first[2]

class MultiGateway:
    RemoteError = RemoteError
    def __init__(self, gateways):
        self.gateways = gateways
    def remote_exec(self, source):
        channels = []
        for gw in self.gateways:
            channels.append(gw.remote_exec(source))
        return MultiChannel(channels)
    def exit(self):
        for gw in self.gateways:
            gw.exit()

class GatewayManager:
    RemoteError = RemoteError

    def __init__(self, specs):
        self.specs = [GatewaySpec(spec) for spec in specs]
        self.gateways = []

    def trace(self, msg):
        py._com.pyplugins.notify("trace", "gatewaymanage", msg)

    def makegateways(self):
        assert not self.gateways
        for spec in self.specs:
            self.trace("makegateway %s" %(spec))
            self.gateways.append(spec.makegateway())

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
        return MultiGateway(gateways=l)

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
