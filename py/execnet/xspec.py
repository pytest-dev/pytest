
import py

class XSpec:
    """ Execution Specification: key1=value1//key2=value2 ... 
        * keys need to be unique within the specification scope 
        * neither key nor value are allowed to contain "//"
        * keys are not allowed to contain "=" 
        * keys are not allowed to start with underscore 
        * if no "=value" is given, assume a boolean True value 
    """
    def __init__(self, *strings):
        for string in strings:
            for keyvalue in string.split("//"):
                i = keyvalue.find("=")
                if i == -1:
                    setattr(self, keyvalue, True)
                else:
                    setattr(self, keyvalue[:i], keyvalue[i+1:])

    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError(name) 
        return None

    def _samefilesystem(self):
        return bool(self.popen and not self.path)

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
    gw.spec = spec 
    # XXX events
    if spec.chdir:
        gw.remote_exec("""
            import os
            path = %r 
            try:
                os.chdir(path)
            except OSError:
                os.mkdir(path)
                os.chdir(path)
        """ % spec.chdir).waitclose()
    return gw
