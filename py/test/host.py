
class InvalidHostSpec(ValueError):
    pass

def parsehostspec(spec):
    parts = spec.split(":", 2)
    if len(parts) < 2:
        raise InvalidHostSpec(spec)
    type = parts.pop(0)
    if type == 'ssh':
        sshaddress = parts.pop(0)
        basedir = parts and ":".join(parts) or ''
        return SpecSSH(sshaddress, basedir)
    elif type == 'socket':
        host = parts.pop(0)
        if not parts:
            raise InvalidHostSpec(spec)
        remainder = parts.pop(0)
        parts = remainder.split(":", 1)
        port = int(parts.pop(0))
        basedir = parts and ":".join(parts) or ''
        return SpecSocket(host, port, basedir)
    else:
        raise InvalidHostSpec(spec)

class SpecSSH(object):
    def __init__(self, sshaddress, basedir):
        self.sshaddress = sshaddress
        self.basedir = basedir
        self.host = sshaddress.split('@', 1)[-1]
       
class SpecSocket(object):
    def __init__(self, host, port, basedir):
        self.host = host
        self.port = port
        self.basedir = basedir 
     
