"""
(c) 2008-2009, holger krekel 
"""
import py

class XSpec:
    """ Execution Specification: key1=value1//key2=value2 ... 
        * keys need to be unique within the specification scope 
        * neither key nor value are allowed to contain "//"
        * keys are not allowed to contain "=" 
        * keys are not allowed to start with underscore 
        * if no "=value" is given, assume a boolean True value 
    """
    # XXX allow customization, for only allow specific key names
    popen = ssh = socket = python = chdir = nice = None

    def __init__(self, string):
        self._spec = string
        for keyvalue in string.split("//"):
            i = keyvalue.find("=")
            if i == -1:
                key, value = keyvalue, True
            else:
                key, value = keyvalue[:i], keyvalue[i+1:]
            if key[0] == "_":
                raise AttributeError("%r not a valid XSpec key" % key)
            if key in self.__dict__:
                raise ValueError("duplicate key: %r in %r" %(key, string))
            setattr(self, key, value)

    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError(name)
        return None

    def __repr__(self):
        return "<XSpec %r>" %(self._spec,)
    def __str__(self):
        return self._spec 

    def __hash__(self):
        return hash(self._spec)
    def __eq__(self, other):
        return self._spec == getattr(other, '_spec', None)
    def __ne__(self, other):
        return self._spec != getattr(other, '_spec', None)

    def _samefilesystem(self):
        return bool(self.popen and not self.chdir)

def makegateway(spec):
    if not isinstance(spec, XSpec):
        spec = XSpec(spec)
    if spec.popen:
        gw = py.execnet.PopenGateway(python=spec.python)
    elif spec.ssh:
        gw = py.execnet.SshGateway(spec.ssh, remotepython=spec.python)
    elif spec.socket:
        assert not spec.python, "socket: specifying python executables not supported"
        hostport = spec.socket.split(":")
        gw = py.execnet.SocketGateway(*hostport)
    else:
        raise ValueError("no gateway type found for %r" % (spec._spec,))
    gw.spec = spec 
    if spec.chdir or spec.nice:
        channel = gw.remote_exec("""
            import os
            path, nice = channel.receive()
            if path:
                if not os.path.exists(path):
                    os.mkdir(path)
                os.chdir(path)
            if nice and hasattr(os, 'nice'):
                os.nice(nice)
        """)
        nice = spec.nice and int(spec.nice) or 0
        channel.send((spec.chdir, nice))
        channel.waitclose()
    return gw
