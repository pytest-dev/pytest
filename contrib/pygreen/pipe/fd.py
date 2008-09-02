import os
from pygreen import greensock2


class FDInput(object):

    def __init__(self, read_fd, close=True):
        self.read_fd = read_fd
        self._close = close     # a flag or a callback

    def shutdown_rd(self):
        fd = self.read_fd
        if fd is not None:
            self.read_fd = None
            close = self._close
            if close:
                self._close = False
                if close == True:
                    os.close(fd)
                else:
                    close()

    __del__ = shutdown_rd

    def wait_input(self):
        greensock2.wait_input(self.read_fd)

    def recv(self, bufsize):
##        f = open('LOG', 'a')
##        import os; print >> f, '[%d] RECV' % (os.getpid(),)
##        f.close()
        res = greensock2.read(self.read_fd, bufsize)
##        f = open('LOG', 'a')
##        import os; print >> f, '[%d] RECV %r' % (os.getpid(), res)
##        f.close()
        return res

    def recvall(self, bufsize):
        return greensock2.readall(self.read_fd, bufsize)


class FDOutput(object):

    def __init__(self, write_fd, close=True):
        self.write_fd = write_fd
        self._close = close     # a flag or a callback

    def shutdown_wr(self):
        fd = self.write_fd
        if fd is not None:
            self.write_fd = None
            close = self._close
            if close:
                self._close = False
                if close == True:
                    os.close(fd)
                else:
                    close()

    __del__ = shutdown_wr

    def wait_output(self):
        greensock2.wait_output(self.write_fd)

    def sendall(self, buffer):
##        f = open('LOG', 'a')
##        import os; print >> f, '[%d] %r' % (os.getpid(), buffer)
##        f.close()
        greensock2.writeall(self.write_fd, buffer)
