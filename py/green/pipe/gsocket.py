from py.__.green import greensock2
import socket, errno, os

error = socket.error


class _delegate(object):
    def __init__(self, methname):
        self.methname = methname
    def __get__(self, obj, typ=None):
        result = getattr(obj._s, self.methname)
        setattr(obj, self.methname, result)
        return result


class GreenSocket(object):

    def __init__(self, family = socket.AF_INET,
                       type   = socket.SOCK_STREAM,
                       proto  = 0):
        self._s = socket.socket(family, type, proto)
        self._s.setblocking(False)

    def fromsocket(cls, s):
        if isinstance(s, GreenSocket):
            s = s._s
        result = GreenSocket.__new__(cls)
        result._s = s
        s.setblocking(False)
        return result
    fromsocket = classmethod(fromsocket)

    def accept(self):
        while 1:
            try:
                s, addr = self._s.accept()
                break
            except error, e:
                if e.args[0] not in (errno.EAGAIN, errno.EWOULDBLOCK):
                    raise
            self.wait_input()
        return self.fromsocket(s), addr

    bind   = _delegate("bind")
    close  = _delegate("close")

    def connect(self, addr):
        err = self.connect_ex(addr)
        if err:
            raise error(err, os.strerror(err))

    def connect_ex(self, addr):
        err = self._s.connect_ex(addr)
        if err == errno.EINPROGRESS:
            greensock2.wait_output(self._s)
            err = self._s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        return err

    #XXX dup
    fileno      = _delegate("fileno")
    getpeername = _delegate("getpeername")
    getsockname = _delegate("getsockname")
    getsockopt  = _delegate("getsockopt")
    listen      = _delegate("listen")

    def makefile(self, mode='r', bufsize=-1):
        # hack, but reusing the internal socket._fileobject should just work
        return socket._fileobject(self, mode, bufsize)

    def recv(self, bufsize):
        return greensock2.recv(self._s, bufsize)

    def recvall(self, bufsize):
        return greensock2.recvall(self._s, bufsize)

    def recvfrom(self, bufsize):
        self.wait_input()
        buf, addr = self._s.recvfrom(bufsize)
        if not buf:
            raise ConnexionClosed("inbound connexion closed")
        return buf, addr

    def send(self, data):
        self.wait_output()
        return self._s.send(data)

    def sendto(self, data, addr):
        self.wait_output()
        return self._s.sendto(data, addr)

    def sendall(self, data):
        greensock2.sendall(self._s, data)

    setsockopt = _delegate("setsockopt")
    shutdown   = _delegate("shutdown")

    def shutdown_rd(self):
        try:
            self._s.shutdown(socket.SHUT_RD)
        except error:
            pass

    def shutdown_wr(self):
        try:
            self._s.shutdown(socket.SHUT_WR)
        except error:
            pass

    def wait_input(self):
        greensock2.wait_input(self._s)

    def wait_output(self):
        greensock2.wait_output(self._s)
