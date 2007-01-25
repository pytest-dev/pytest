
import os, inspect, socket
import sys
from py.magic import autopath ; mypath = autopath()

import py

# the list of modules that must be send to the other side 
# for bootstrapping gateways
# XXX we want to have a cleaner bootstrap mechanism 
#     by making sure early that we have the py lib available
#     in a sufficient version 

startup_modules = [
    'py.__.thread.io', 
    'py.__.thread.pool', 
    'py.__.execnet.inputoutput', 
    'py.__.execnet.gateway', 
    'py.__.execnet.message', 
    'py.__.execnet.channel', 
]

def getsource(dottedname): 
    mod = __import__(dottedname, None, None, ['__doc__'])
    return inspect.getsource(mod) 
    
from py.__.execnet import inputoutput, gateway 

class InstallableGateway(gateway.Gateway):
    """ initialize gateways on both sides of a inputoutput object. """
    def __init__(self, io):
        self.remote_bootstrap_gateway(io)
        super(InstallableGateway, self).__init__(io=io, startcount=1)

    def remote_bootstrap_gateway(self, io, extra=''):
        """ return Gateway with a asynchronously remotely
            initialized counterpart Gateway (which may or may not succeed).
            Note that the other sides gateways starts enumerating
            its channels with even numbers while the sender
            gateway starts with odd numbers.  This allows to
            uniquely identify channels across both sides.
        """
        bootstrap = ["we_are_remote=True", extra]
        bootstrap += [getsource(x) for x in startup_modules]
        bootstrap += [io.server_stmt, "Gateway(io=io, startcount=2).join(joinexec=False)",]
        source = "\n".join(bootstrap)
        self._trace("sending gateway bootstrap code")
        io.write('%r\n' % source)

class PopenCmdGateway(InstallableGateway):
    def __init__(self, cmd):
        infile, outfile = os.popen2(cmd)
        io = inputoutput.Popen2IO(infile, outfile)
        super(PopenCmdGateway, self).__init__(io=io)
##        self._pidchannel = self.remote_exec("""
##            import os
##            channel.send(os.getpid())
##        """)

##    def exit(self):
##        try:
##            self._pidchannel.waitclose(timeout=0.5)
##            pid = self._pidchannel.receive()
##        except IOError:
##            self._trace("IOError: could not receive child PID:")
##            self._traceex(sys.exc_info())
##            pid = None
##        super(PopenCmdGateway, self).exit()
##        if pid is not None: 
##            self._trace("waiting for pid %s" % pid)
##            try:
##                os.waitpid(pid, 0)
##            except KeyboardInterrupt: 
##                if sys.platform != "win32": 
##                    os.kill(pid, 15) 
##                raise
##            except OSError, e:
##                self._trace("child process %s already dead? error:%s" %
##                           (pid, str(e)))

class PopenGateway(PopenCmdGateway):
    # use sysfind/sysexec/subprocess instead of os.popen?
    def __init__(self, python=sys.executable):
        cmd = '%s -u -c "exec input()"' % python
        super(PopenGateway, self).__init__(cmd)

    def remote_bootstrap_gateway(self, io, extra=''):
        # XXX the following hack helps us to import the same version
        #     of the py lib and other dependcies, but only works for 
        #     PopenGateways because we can assume to have access to 
        #     the same filesystem 
        #     --> we definitely need proper remote imports working
        #         across any kind of gateway!
        x = py.path.local(py.__file__).dirpath().dirpath()
        ppath = os.environ.get('PYTHONPATH', '')
        plist = [str(x)] + ppath.split(':')
        s = "\n".join([extra, 
            "import sys ; sys.path[:0] = %r" % (plist,), 
            "import os ; os.environ['PYTHONPATH'] = %r" % ppath, 
            # redirect file descriptors 0 and 1 to /dev/null, to avoid
            # complete confusion (this is independent from the sys.stdout
            # and sys.stderr redirection that gateway.remote_exec() can do)
            # note that we redirect fd 2 on win too, since for some reason that
            # blocks there, while it works (sending to stderr if possible else
            # ignoring) on *nix
            str(py.code.Source("""
                try:
                    devnull = os.devnull
                except AttributeError:
                    if os.name == 'nt':
                        devnull = 'NUL'
                    else:
                        devnull = '/dev/null'
                sys.stdin  = os.fdopen(os.dup(0), 'rb', 0)
                sys.stdout = os.fdopen(os.dup(1), 'wb', 0)
                if os.name == 'nt':
                    sys.stderr = os.fdopen(os.dup(2), 'wb', 0)
                fd = os.open(devnull, os.O_RDONLY)
                os.dup2(fd, 0)
                os.close(fd)
                fd = os.open(devnull, os.O_WRONLY)
                os.dup2(fd, 1)
                if os.name == 'nt':
                    os.dup2(fd, 2)
                os.close(fd)
            """)),
            ""
            ])
        super(PopenGateway, self).remote_bootstrap_gateway(io, s)

class SocketGateway(InstallableGateway):
    def __init__(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host = str(host)
        self.port = port = int(port)
        sock.connect((host, port))
        io = inputoutput.SocketIO(sock)
        InstallableGateway.__init__(self, io=io)

    def _getremoteaddress(self):
        return '%s:%d' % (self.host, self.port)

    def remote_install(cls, gateway, hostport=None): 
        """ return a connected socket gateway through the
            given gateway. 
        """ 
        if hostport is None: 
            host, port = ('', 0) 
        else:   
            host, port = hostport 
        socketserverbootstrap = py.code.Source(
            mypath.dirpath('script', 'socketserver.py').read('rU'),
            """
            import socket
            sock = bind_and_listen((%r, %r)) 
            hostname = socket.gethostname() 
            channel.send((hostname, sock.getsockname()))
            startserver(sock)
        """ % (host, port)) 
        # execute the above socketserverbootstrap on the other side
        channel = gateway.remote_exec(socketserverbootstrap)
        hostname, (realhost, realport) = channel.receive() 
        if not hostname:
            hostname = realhost
        #gateway._trace("remote_install received" 
        #              "port=%r, hostname = %r" %(realport, hostname))
        return py.execnet.SocketGateway(hostname, realport) 
    remote_install = classmethod(remote_install)
    
class SshGateway(PopenCmdGateway):
    def __init__(self, sshaddress, remotepython='python', identity=None): 
        self.sshaddress = sshaddress
        remotecmd = '%s -u -c "exec input()"' % (remotepython,)
        cmdline = [sshaddress, remotecmd]
        # XXX Unix style quoting
        for i in range(len(cmdline)):
            cmdline[i] = "'" + cmdline[i].replace("'", "'\\''") + "'"
        cmd = 'ssh -C'
        if identity is not None: 
            cmd += ' -i %s' % (identity,)
        cmdline.insert(0, cmd) 
        super(SshGateway, self).__init__(' '.join(cmdline))

    def _getremoteaddress(self):
        return self.sshaddress

class ExecGateway(PopenGateway):
    def remote_exec_sync_stdcapture(self, lines, callback):
        # hack: turn the content of the cell into
        #
        # if 1:
        #    line1
        #    line2
        #    ...
        #
        lines = ['   ' + line for line in lines]
        lines.insert(0, 'if 1:')
        lines.append('')
        sourcecode = '\n'.join(lines)
        try:
            callbacks = self.callbacks
        except AttributeError:
            callbacks = self.callbacks = {}
        answerid = id(callback)
        self.callbacks[answerid] = callback

        self.exec_remote('''
            import sys, StringIO
            try:
                execns
            except:
                execns = {}
            oldout, olderr = sys.stdout, sys.stderr
            try:
                buffer = StringIO.StringIO()
                sys.stdout = sys.stderr = buffer
                try:
                    exec compile(%(sourcecode)r, 'single') in execns
                except:
                    import traceback
                    traceback.print_exc()
            finally:
                sys.stdout=oldout
                sys.stderr=olderr
            # fiddle us (the caller) into executing the callback on remote answers
            gateway.exec_remote(
                "gateway.invoke_callback(%(answerid)r, %%r)" %% buffer.getvalue())
        ''' % locals())

    def invoke_callback(self, answerid, value):
        callback = self.callbacks[answerid]
        del self.callbacks[answerid]
        callback(value)
