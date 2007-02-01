import os
import sys
import py
try: from cStringIO import StringIO
except ImportError: from StringIO import StringIO

emptyfile = StringIO()

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
    def __init__(self, out=True, err=True, mixed=False, patchsys=True): 
        if out: 
            self.out = py.io.FDCapture(1) 
            if patchsys: 
                self.out.setasfile('stdout')
        if err: 
            if mixed and out:
                tmpfile = self.out.tmpfile 
            else:
                tmpfile = None    
            self.err = py.io.FDCapture(2, tmpfile=tmpfile) 
            if patchsys: 
                self.err.setasfile('stderr')

    def reset(self): 
        """ reset sys.stdout and sys.stderr

            returns a tuple of file objects (out, err) for the captured
            data
        """
        outfile = errfile = emptyfile
        if hasattr(self, 'out'): 
            outfile = self.out.done() 
        if hasattr(self, 'err'): 
            errfile = self.err.done() 
        return outfile.read(), errfile.read()

class StdCapture(Capture):
    """ capture sys.stdout/sys.stderr (but not system level fd 1 and 2).

    This class allows to capture writes to sys.stdout|stderr "in-memory"
    and will raise errors on tries to read from sys.stdin. 
    """
    def __init__(self, out=True, err=True, mixed=False):
        self._out = out
        self._err = err 
        if out: 
            self.oldout = sys.stdout
            sys.stdout = self.newout = StringIO()
        if err: 
            self.olderr = sys.stderr
            if out and mixed: 
                newerr = self.newout 
            else:
                newerr = StringIO()
            sys.stderr = self.newerr = newerr
        self.oldin  = sys.stdin
        sys.stdin  = self.newin  = DontReadFromInput()

    def reset(self):
        """ return captured output and restore sys.stdout/err."""
        x, y = self.done() 
        return x.read(), y.read() 

    def done(self): 
        o,e = sys.stdout, sys.stderr
        outfile = errfile = emptyfile
        if self._out: 
            try:
                sys.stdout = self.oldout 
            except AttributeError:
                raise IOError("stdout capturing already reset")
            del self.oldout
            outfile = self.newout
            outfile.seek(0)
        if self._err: 
            try:
                sys.stderr = self.olderr 
            except AttributeError:
                raise IOError("stderr capturing already reset")
            del self.olderr 
            errfile = self.newerr 
            errfile.seek(0)
        sys.stdin = self.oldin 
        return outfile, errfile

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
