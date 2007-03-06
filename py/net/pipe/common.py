import greensock2
from pypeers.tool import log


class BufferedInput(object):
    in_buf = ''

    def recv(self, bufsize):
        self.wait_input()
        buf = self.in_buf[:bufsize]
        self.in_buf = self.in_buf[bufsize:]
        return buf

    def recvall(self, bufsize):
        result = []
        while bufsize > 0:
            buf = self.recv(bufsize)
            result.append(buf)
            bufsize -= len(buf)
        return ''.join(result)

# ____________________________________________________________

def forwardpipe(s1, s2):
    try:
        while 1:
            s2.wait_output()
            buffer = s1.recv(32768)
            log('[%r -> %r] %r', s1, s2, buffer)
            s2.sendall(buffer)
            del buffer
    finally:
        s2.shutdown_wr()
        s1.shutdown_rd()

def linkpipes(s1, s2):
    greensock2.autogreenlet(forwardpipe, s1, s2)
    greensock2.autogreenlet(forwardpipe, s2, s1)
