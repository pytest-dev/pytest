
""" This is an implementation of an execnet protocol on top
of a transport layer provided by the greensock2 interface.

It has the same semantics, but does not use threads at all
(which makes it suitable for specific enviroments, like pypy-c).

There are some features lacking, most notable:
- callback support for channels
- socket gateway
- bootstrapping (there is assumption of pylib being available
  on remote side, which is not always true)
"""

import sys, os, py, inspect
from py.__.net import greensock2
from py.__.net.msgstruct import message, decodemessage

MSG_REMOTE_EXEC = 'r'
MSG_OBJECT      = 'o'
MSG_ERROR       = 'e'
MSG_CHAN_CLOSE  = 'c'
MSG_FATAL       = 'f'
MSG_CHANNEL  = 'n'

class Gateway(object):

    def __init__(self, input, output, is_remote=False):
        self.input  = input
        self.output = output
        self.nextchannum = int(is_remote)
        self.receivers = {}
        self.greenlet = greensock2.autogreenlet(self.serve_forever, is_remote)

    def remote_exec(self, remote_source):
        remote_source = py.code.Source(remote_source)
        chan = self.newchannel()
        msg = message(MSG_REMOTE_EXEC, chan.n, str(remote_source))
        self.output.sendall(msg)
        return chan

    def newchannel(self):
        n = self.nextchannum
        self.nextchannum += 2
        return self.make_channel(n)

    def make_channel(self, n):
        giver, accepter = greensock2.meetingpoint()
        assert n not in self.receivers
        self.receivers[n] = giver
        return Channel(self, n, accepter)

    def serve_forever(self, is_remote=False):
        try:
            buffer = ""
            while 1:
                msg, buffer = decodemessage(buffer)
                if msg is None:
                    buffer += self.input.recv(16384)
                else:
                    handler = HANDLERS[msg[0]]
                    handler(self, *msg[1:])
        except greensock2.greenlet.GreenletExit:
            raise
        except:
            if is_remote:
                msg = message(MSG_FATAL, format_error(*sys.exc_info()))
                self.output.sendall(msg)
            else:
                raise

    def msg_remote_exec(self, n, source):
        def do_execute(channel):
            try:
                d = {'channel': channel}
                exec source in d
            except:
                channel.report_error(*sys.exc_info())
            else:
                channel.close()
        greensock2.autogreenlet(do_execute, self.make_channel(n))

    def msg_object(self, n, objrepr):
        obj = eval(objrepr)
        if n in self.receivers:
            self.receivers[n].give_queued(obj)

    def msg_error(self, n, s):
        if n in self.receivers:
            self.receivers[n].give_queued(RemoteError(s))
            self.receivers[n].close()
            del self.receivers[n]

    def msg_chan_close(self, n):
        if n in self.receivers:
            self.receivers[n].close()
            del self.receivers[n]

    def msg_channel(self, n, m):
        if n in self.receivers:
            self.receivers[n].give_queued(self.make_channel(m))

    def msg_fatal(self, s):
        raise RemoteError(s)

HANDLERS = {
    MSG_REMOTE_EXEC: Gateway.msg_remote_exec,
    MSG_OBJECT:      Gateway.msg_object,
    MSG_ERROR:       Gateway.msg_error,
    MSG_CHAN_CLOSE:  Gateway.msg_chan_close,
    MSG_CHANNEL:     Gateway.msg_channel,
    MSG_FATAL:       Gateway.msg_fatal,
    }


class Channel(object):

    def __init__(self, gw, n, accepter):
        self.gw = gw
        self.n = n
        self.accepter = accepter

    def send(self, obj):
        if isinstance(obj, Channel):
            assert obj.gw is self.gw
            msg = message(MSG_CHANNEL, self.n, obj.n)
        else:
            msg = message(MSG_OBJECT, self.n, repr(obj))
        self.gw.output.sendall(msg)

    def receive(self):
        obj = self.accepter.accept()
        if isinstance(obj, RemoteError):
            raise obj
        else:
            return obj

    def close(self):
        try:
            self.gw.output.sendall(message(MSG_CHAN_CLOSE, self.n))
        except OSError:
            pass

    def report_error(self, exc_type, exc_value, exc_traceback=None):
        s = format_error(exc_type, exc_value, exc_traceback)
        try:
            self.gw.output.sendall(message(MSG_ERROR, self.n, s))
        except OSError:
            pass


class RemoteError(Exception):
    pass

def format_error(exc_type, exc_value, exc_traceback=None):
    import traceback, StringIO
    s = StringIO.StringIO()
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=s)
    return s.getvalue()


class PopenCmdGateway(Gateway):
    action = "exec input()"

    def __init__(self, cmdline):
        from py.__.net.pipe.fd import FDInput, FDOutput
        child_in, child_out = os.popen2(cmdline, 't', 0)
        fdin  = FDInput(child_out.fileno(), child_out.close)
        fdout = FDOutput(child_in.fileno(), child_in.close)
        fdout.sendall(self.get_bootstrap_code())
        super(PopenCmdGateway, self).__init__(input = fdin, output = fdout)

    def get_bootstrap_code():
        # XXX assumes that the py lib is installed on the remote side
        src = []
        src.append('from py.__.net import greenexecnet')
        src.append('greenexecnet.PopenCmdGateway.run_server()')
        src.append('')
        return '%r\n' % ('\n'.join(src),)
    get_bootstrap_code = staticmethod(get_bootstrap_code)

    def run_server():
        from py.__.net.pipe.fd import FDInput, FDOutput
        gw = Gateway(input = FDInput(os.dup(0)),
                     output = FDOutput(os.dup(1)),
                     is_remote = True)
        # for now, ignore normal I/O
        fd = os.open('/dev/null', os.O_RDWR)
        os.dup2(fd, 0)
        os.dup2(fd, 1)
        os.close(fd)
        greensock2._suspend_forever()
    run_server = staticmethod(run_server)

class PopenGateway(PopenCmdGateway):
    def __init__(self, python=sys.executable):
        cmdline = '"%s" -u -c "%s"' % (python, self.action)
        super(PopenGateway, self).__init__(cmdline)

class SshGateway(PopenCmdGateway):
    def __init__(self, sshaddress, remotepython='python', identity=None):
        self.sshaddress = sshaddress
        remotecmd = '%s -u -c "%s"' % (remotepython, self.action)
        cmdline = [sshaddress, remotecmd]
        # XXX Unix style quoting
        for i in range(len(cmdline)):
            cmdline[i] = "'" + cmdline[i].replace("'", "'\\''") + "'"
        cmd = 'ssh -C'
        if identity is not None: 
            cmd += ' -i %s' % (identity,)
        cmdline.insert(0, cmd) 
        super(SshGateway, self).__init__(' '.join(cmdline))


##f = open('LOG', 'a')
##import os; print >> f, '[%d] READY' % (os.getpid(),)
##f.close()
