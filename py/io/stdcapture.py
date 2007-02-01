import os
import sys
import py
try: from cStringIO import StringIO
except ImportError: from StringIO import StringIO

class Capture(object):
    def call(cls, func, *args, **kwargs): 
        """ return a (res, out, err) tuple where
            out and err represent the output/error output
            during function execution. 
            call the given function with args/kwargs
            and capture output/error during its execution. 
        """ 
        so = cls()
        try: 
            res = func(*args, **kwargs)
        finally: 
            out, err = so.reset()
        return res, out, err 
    call = classmethod(call) 

class StdCaptureFD(Capture): 
    """ capture Stdout and Stderr both on filedescriptor 
        and sys.stdout/stderr level. 
    """
    def __init__(self, out=True, err=True, patchsys=True): 
        if out: 
            self.out = py.io.FDCapture(1) 
            if patchsys: 
                self.out.setasfile('stdout')
        if err: 
            self.err = py.io.FDCapture(2) 
            if patchsys: 
                self.err.setasfile('stderr')

    def reset(self): 
        """ reset sys.stdout and sys.stderr

            returns a tuple of file objects (out, err) for the captured
            data
        """
        out = err = ""
        if hasattr(self, 'out'): 
            outfile = self.out.done() 
            out = outfile.read()
        if hasattr(self, 'err'): 
            errfile = self.err.done() 
            err = errfile.read()
        return out, err 

class StdCapture(Capture):
    """ capture sys.stdout/sys.stderr (but not system level fd 1 and 2).

    This class allows to capture writes to sys.stdout|stderr "in-memory"
    and will raise errors on tries to read from sys.stdin. 
    """
    def __init__(self):
        self.oldin  = sys.stdin
        self.oldout = sys.stdout
        self.olderr = sys.stderr
        sys.stdin  = self.newin  = DontReadFromInput()
        sys.stdout = self.newout = StringIO()
        sys.stderr = self.newerr = StringIO()

    def reset(self):
        """ return captured output and restore sys.stdout/err."""
        x, y = self.done() 
        return x.read(), y.read() 

    def done(self): 
        o,e = sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = (
            self.oldin, self.oldout, self.olderr)
        del self.oldin, self.oldout, self.olderr
        o, e = self.newout, self.newerr 
        o.seek(0)
        e.seek(0)
        return o,e 

class DontReadFromInput:
    """Temporary stub class.  Ideally when stdin is accessed, the
    capturing should be turned off, with possibly all data captured
    so far sent to the screen.  This should be configurable, though,
    because in automated test runs it is better to crash than
    hang indefinitely.
    """
    def read(self, *args):
        raise IOError("reading from stdin while output is captured")
    readline = read
    readlines = read
    __iter__ = read
