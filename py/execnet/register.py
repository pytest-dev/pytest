
import os, inspect, socket
import sys
from py.magic import autopath ; mypath = autopath()
from py.__.misc.warn import APIWARN

import py
if sys.platform == "win32":
    win32 = True
    import msvcrt
else:
    win32 = False

# the list of modules that must be send to the other side 
# for bootstrapping gateways
# XXX we'd like to have a leaner and meaner bootstrap mechanism 

startup_modules = [
    'py.__.thread.io', 
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
        self._remote_bootstrap_gateway(io)
        super(InstallableGateway, self).__init__(io=io, _startcount=1) 
        # XXX we dissallow execution form the other side
        self._initreceive(requestqueue=False) 

    def _remote_bootstrap_gateway(self, io, extra=''):
        """ return Gateway with a asynchronously remotely
            initialized counterpart Gateway (which may or may not succeed).
            Note that the other sides gateways starts enumerating
            its channels with even numbers while the sender
            gateway starts with odd numbers.  This allows to
            uniquely identify channels across both sides.
        """
        bootstrap = [extra]
        bootstrap += [getsource(x) for x in startup_modules]
        bootstrap += [io.server_stmt, 
                      "Gateway(io=io, _startcount=2)._servemain()", 
                     ]
        source = "\n".join(bootstrap)
        self._trace("sending gateway bootstrap code")
        io.write('%r\n' % source)

class PopenCmdGateway(InstallableGateway):
    def __init__(self, cmd):
        infile, outfile = os.popen2(cmd)
        self._cmd = cmd
        io = inputoutput.Popen2IO(infile, outfile)
        super(PopenCmdGateway, self).__init__(io=io)


class PopenGateway(PopenCmdGateway):
    """ This Gateway provides interaction with a newly started
        python subprocess. 
    """
    def __init__(self, python=sys.executable):
        """ instantiate a gateway to a subprocess 
            started with the given 'python' executable. 
        """
        cmd = '%s -u -c "exec input()"' % python
        super(PopenGateway, self).__init__(cmd)

    def _remote_bootstrap_gateway(self, io, extra=''):
        # have the subprocess use the same PYTHONPATH and py lib 
        x = py.path.local(py.__file__).dirpath().dirpath()
        ppath = os.environ.get('PYTHONPATH', '')
        plist = [str(x)] + ppath.split(':')
        s = "\n".join([extra, 
            "import sys ; sys.path[:0] = %r" % (plist,), 
            "import os ; os.environ['PYTHONPATH'] = %r" % ppath, 
            str(py.code.Source(stdouterrin_setnull)), 
            "stdouterrin_setnull()", 
            ""
            ])
        super(PopenGateway, self)._remote_bootstrap_gateway(io, s)

class SocketGateway(InstallableGateway):
    """ This Gateway provides interaction with a remote process
        by connecting to a specified socket.  On the remote
        side you need to manually start a small script 
        (py/execnet/script/socketserver.py) that accepts
        SocketGateway connections. 
    """
    def __init__(self, host, port):
        """ instantiate a gateway to a process accessed
            via a host/port specified socket. 
        """
        self.host = host = str(host)
        self.port = port = int(port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        io = inputoutput.SocketIO(sock)
        super(SocketGateway, self).__init__(io=io)
        self.remoteaddress = '%s:%d' % (self.host, self.port)

    def new_remote(cls, gateway, hostport=None): 
        """ return a new (connected) socket gateway, instatiated
            indirectly through the given 'gateway'. 
        """ 
        if hostport is None: 
            host, port = ('', 0)  # XXX works on all platforms? 
        else:   
            host, port = hostport 
        socketserverbootstrap = py.code.Source(
            mypath.dirpath('script', 'socketserver.py').read('rU'), """
            import socket
            sock = bind_and_listen((%r, %r)) 
            port = sock.getsockname()
            channel.send(port) 
            startserver(sock)
            """ % (host, port)
        ) 
        # execute the above socketserverbootstrap on the other side
        channel = gateway.remote_exec(socketserverbootstrap)
        (realhost, realport) = channel.receive()
        #gateway._trace("new_remote received" 
        #               "port=%r, hostname = %r" %(realport, hostname))
        return py.execnet.SocketGateway(host, realport) 
    new_remote = classmethod(new_remote)

    
class SshGateway(PopenCmdGateway):
    """ This Gateway provides interaction with a remote Python process,
        established via the 'ssh' command line binary.  
        The remote side needs to have a Python interpreter executable. 
    """
    def __init__(self, sshaddress, remotepython='python', 
        identity=None, ssh_config=None): 
        """ instantiate a remote ssh process with the 
            given 'sshaddress' and remotepython version.
            you may specify an ssh_config file. 
            DEPRECATED: you may specify an 'identity' filepath. 
        """
        self.remoteaddress = sshaddress
        remotecmd = '%s -u -c "exec input()"' % (remotepython,)
        cmdline = [sshaddress, remotecmd]
        # XXX Unix style quoting
        for i in range(len(cmdline)):
            cmdline[i] = "'" + cmdline[i].replace("'", "'\\''") + "'"
        cmd = 'ssh -C'
        if identity is not None: 
            APIWARN("1.0", "pass in 'ssh_config' file instead of identity")
            cmd += ' -i %s' % (identity,)
        if ssh_config is not None:
            cmd += ' -F %s' % (ssh_config)
        cmdline.insert(0, cmd) 
        cmd = ' '.join(cmdline)
        super(SshGateway, self).__init__(cmd)
       
    def _remote_bootstrap_gateway(self, io, s=""): 
        extra = "\n".join([
            str(py.code.Source(stdouterrin_setnull)), 
            "stdouterrin_setnull()",
            s, 
        ])
        super(SshGateway, self)._remote_bootstrap_gateway(io, extra)


def stdouterrin_setnull():
    """ redirect file descriptors 0 and 1 (and possibly 2) to /dev/null. 
        note that this function may run remotely without py lib support. 
    """
    # complete confusion (this is independent from the sys.stdout
    # and sys.stderr redirection that gateway.remote_exec() can do)
    # note that we redirect fd 2 on win too, since for some reason that
    # blocks there, while it works (sending to stderr if possible else
    # ignoring) on *nix
    import sys, os
    try:
        devnull = os.devnull
    except AttributeError:
        if os.name == 'nt':
            devnull = 'NUL'
        else:
            devnull = '/dev/null'
    # stdin
    sys.stdin  = os.fdopen(os.dup(0), 'rb', 0)
    fd = os.open(devnull, os.O_RDONLY)
    os.dup2(fd, 0)
    os.close(fd)

    # stdout
    sys.stdout = os.fdopen(os.dup(1), 'wb', 0)
    fd = os.open(devnull, os.O_WRONLY)
    os.dup2(fd, 1)

    # stderr for win32
    if os.name == 'nt':
        sys.stderr = os.fdopen(os.dup(2), 'wb', 0)
        os.dup2(fd, 2)
    os.close(fd)
