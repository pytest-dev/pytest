
import os, sys

class FDCapture: 
    def __init__(self, targetfd, sysattr=None): 
        self.targetfd = targetfd
        self.tmpfile = self.maketmpfile()
        self._savefd = os.dup(targetfd)
        os.dup2(self.tmpfile.fileno(), targetfd) 
        if sysattr is not None: 
            self._reset = (lambda oldval=getattr(sys, sysattr): 
                               setattr(sys, sysattr, oldval))
            setattr(sys, sysattr, self.tmpfile) 

    def done(self): 
        os.dup2(self._savefd, self.targetfd) 
        if hasattr(self, '_reset'): 
            self._reset() 
            del self._reset 
        os.close(self._savefd) 
        f = self.tmpfile
        f.seek(0)
        del self._savefd 
        del self.tmpfile 
        return f 

    def maketmpfile(self): 
        f = os.tmpfile()
        fd = f.fileno()
        newfd = os.dup(fd) 
        newf = os.fdopen(newfd, 'w+b', 0)
        f.close()
        return newf 

class Capture: 
    def __init__(self): 
        self._out = FDCapture(1, 'stdout') 
        self._oldsysout = sys.stdout 
        sys.stdout = self._out.tmpfile

        self._err = FDCapture(2, 'stderr') 
        self._olderrout = sys.stderr 
        sys.stderr = self._err.tmpfile

    def reset(self): 
        outfile = self._out.done() 
        errfile = self._err.done() 
        return outfile.read(), errfile.read() 

