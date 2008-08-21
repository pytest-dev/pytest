"""
  InputOutput Classes used for connecting gateways
  across process or computer barriers.
"""

import socket, os, sys, thread

class SocketIO:
    server_stmt = """
io = SocketIO(clientsock)
import sys
#try:
#    sys.stdout = sys.stderr = open('/tmp/execnet-socket-debug.log', 'a', 0)
#except (IOError, OSError):
#    sys.stdout = sys.stderr = open('/dev/null', 'w')
#print '='*60
"""

    error = (socket.error, EOFError)
    def __init__(self, sock):
        self.sock = sock
        try:
            sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_IP, socket.IP_TOS, 0x10)  # IPTOS_LOWDELAY
        except socket.error, e:
            print "WARNING: Cannot set socket option:", str(e)
        self.readable = self.writeable = True

    def read(self, numbytes):
        "Read exactly 'bytes' bytes from the socket."
        buf = ""
        while len(buf) < numbytes:
            t = self.sock.recv(numbytes - len(buf))
            #print 'recv -->', len(t)
            if not t:
                raise EOFError
            buf += t
        return buf

    def write(self, data):
        """write out all bytes to the socket. """
        self.sock.sendall(data)

    def close_read(self):
        if self.readable:
            try:
                self.sock.shutdown(0)
            except socket.error:
                pass
            self.readable = None
    def close_write(self):
        if self.writeable:
            try:
                self.sock.shutdown(1)
            except socket.error:
                pass
            self.writeable = None

class Popen2IO:
    server_stmt = """
import os, sys, StringIO
io = Popen2IO(sys.stdout, sys.stdin)
sys.stdout = sys.stderr = StringIO.StringIO() 
#try:
#    sys.stdout = sys.stderr = open('/tmp/execnet-popen-debug.log', 'a', 0)
#except (IOError, OSError):
#    sys.stdout = sys.stderr = open('/dev/null', 'w')
#print '='*60
"""
    error = (IOError, OSError, EOFError)

    def __init__(self, infile, outfile):
        self.outfile, self.infile = infile, outfile
        if sys.platform == "win32":
            import msvcrt
            msvcrt.setmode(infile.fileno(), os.O_BINARY)
            msvcrt.setmode(outfile.fileno(), os.O_BINARY)

        self.readable = self.writeable = True
        self.lock = thread.allocate_lock()

    def read(self, numbytes):
        """Read exactly 'bytes' bytes from the pipe. """
        #import sys
        #print >> sys.stderr, "reading..."
        s = self.infile.read(numbytes)
        #print >> sys.stderr, "read: %r" % s
        if len(s) < numbytes:
            raise EOFError
        return s

    def write(self, data):
        """write out all bytes to the pipe. """
        #import sys
        #print >> sys.stderr, "writing: %r" % data
        self.outfile.write(data)
        self.outfile.flush()

    def close_read(self):
        if self.readable:
            self.infile.close()
            self.readable = None
    def close_write(self):
        self.lock.acquire()
        try:
            if self.writeable:
                self.outfile.close()
                self.writeable = None
        finally:
            self.lock.release()
