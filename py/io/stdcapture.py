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

    def reset(self): 
        """ reset sys.stdout and sys.stderr

            returns a tuple of file objects (out, err) for the captured
            data
        """
        outfile, errfile = self.done()
        return outfile.read(), errfile.read()


class StdCaptureFD(Capture): 
    """ This class allows to capture writes to FD1 and FD2 
        and may connect a NULL file to FD0 (and prevent
        reads from sys.stdin)
    """
    def __init__(self, out=True, err=True, mixed=False, in_=True, patchsys=True): 
        if in_:
            self._oldin = (sys.stdin, os.dup(0))
            sys.stdin  = DontReadFromInput()
            fd = os.open(devnullpath, os.O_RDONLY)
            os.dup2(fd, 0)
            os.close(fd)
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

    def done(self):
        """ return (outfile, errfile) and stop capturing. """
        outfile = errfile = emptyfile
        if hasattr(self, 'out'): 
            outfile = self.out.done() 
        if hasattr(self, 'err'): 
            errfile = self.err.done() 
        if hasattr(self, '_oldin'):
            oldsys, oldfd = self._oldin 
            os.dup2(oldfd, 0)
            os.close(oldfd)
            sys.stdin = oldsys 
        return outfile, errfile 

class StdCapture(Capture):
    """ This class allows to capture writes to sys.stdout|stderr "in-memory"
        and will raise errors on tries to read from sys.stdin. It only
        modifies sys.stdout|stderr|stdin attributes and does not 
        touch underlying File Descriptors (use StdCaptureFD for that). 
    """
    def __init__(self, out=True, err=True, in_=True, mixed=False):
        self._out = out
        self._err = err 
        self._in = in_
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
        if in_:
            self.oldin  = sys.stdin
            sys.stdin  = self.newin  = DontReadFromInput()

    def reset(self):
        """ return captured output as strings and restore sys.stdout/err."""
        x, y = self.done() 
        return x.read(), y.read() 

    def done(self): 
        """ return (outfile, errfile) and stop capturing. """
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
        if self._in:
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

try:
    devnullpath = os.devnull
except AttributeError:
    if os.name == 'nt':
        devnullpath = 'NUL'
    else:
        devnullpath = '/dev/null'

emptyfile = StringIO()

