
import os, sys
import py

class FDCapture: 
    """ Capture IO to/from a given os-level filedescriptor. """
    def __init__(self, targetfd, tmpfile=None): 
        self.targetfd = targetfd
        if tmpfile is None: 
            tmpfile = self.maketmpfile()
        self.tmpfile = tmpfile 
        self._savefd = os.dup(targetfd)
        os.dup2(self.tmpfile.fileno(), targetfd) 
        self._patched = []

    def setasfile(self, name, module=sys): 
        key = (module, name)
        self._patched.append((key, getattr(module, name)))
        setattr(module, name, self.tmpfile) 

    def unsetfiles(self): 
        while self._patched: 
            (module, name), value = self._patched.pop()
            setattr(module, name, value) 

    def done(self): 
        os.dup2(self._savefd, self.targetfd) 
        self.unsetfiles() 
        os.close(self._savefd) 
        self.tmpfile.seek(0)
        return self.tmpfile 

    def maketmpfile(self): 
        f = os.tmpfile()
        newf = py.io.dupfile(f) 
        f.close()
        return newf 

class OutErrCapture: 
    """ capture Stdout and Stderr both on filedescriptor 
        and sys.stdout/stderr level. 
    """
    def __init__(self, out=True, err=True, patchsys=True): 
        if out: 
            self.out = FDCapture(1) 
            if patchsys: 
                self.out.setasfile('stdout')
        if err: 
            self.err = FDCapture(2) 
            if patchsys: 
                self.err.setasfile('stderr')

    def reset(self): 
        out = err = ""
        if hasattr(self, 'out'): 
            outfile = self.out.done() 
            out = outfile.read()
        if hasattr(self, 'err'): 
            errfile = self.err.done() 
            err = errfile.read()
        return out, err 

def callcapture(func, *args, **kwargs): 
    """ call the given function with args/kwargs
        and return a (res, out, err) tuple where
        out and err represent the output/error output
        during function execution. 
    """ 
    so = OutErrCapture()
    try: 
        res = func(*args, **kwargs)
    finally: 
        out, err = so.reset()
    return res, out, err 

