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
        """ reset sys.stdout/stderr and return captured output as strings. """
        if hasattr(self, '_suspended'):
            outfile = self._kwargs['out']
            errfile = self._kwargs['err']
            del self._kwargs
        else:
            outfile, errfile = self.done() 
        out, err = "", ""
        if outfile:
            out = outfile.read()
            outfile.close()
        if errfile and errfile != outfile:
            err = errfile.read()
            errfile.close()
        return out, err

    def suspend(self):
        """ return current snapshot captures, memorize tempfiles. """
        assert not hasattr(self, '_suspended')
        self._suspended = True
        outerr = self.readouterr()
        outfile, errfile = self.done()
        self._kwargs['out'] = outfile
        self._kwargs['err'] = errfile
        return outerr

    def resume(self):
        """ resume capturing with original temp files. """
        assert self._suspended
        self._initialize(**self._kwargs)
        del self._suspended


class StdCaptureFD(Capture): 
    """ This class allows to capture writes to FD1 and FD2 
        and may connect a NULL file to FD0 (and prevent
        reads from sys.stdin)
    """
    def __init__(self, out=True, err=True, 
                 mixed=False, in_=True, patchsys=True): 
        self._kwargs = locals().copy()
        del self._kwargs['self']
        self._initialize(**self._kwargs)

    def _initialize(self, out=True, err=True, 
                    mixed=False, in_=True, patchsys=True): 
        if in_:
            self._oldin = (sys.stdin, os.dup(0))
            sys.stdin  = DontReadFromInput()
            fd = os.open(devnullpath, os.O_RDONLY)
            os.dup2(fd, 0)
            os.close(fd)
        if out: 
            tmpfile = None
            if hasattr(out, 'write'):
                tmpfile = out
            self.out = py.io.FDCapture(1, tmpfile=tmpfile)
            if patchsys: 
                self.out.setasfile('stdout')
        if err: 
            if mixed and out:
                tmpfile = self.out.tmpfile 
            elif hasattr(err, 'write'):
                tmpfile = err
            else:
                tmpfile = None
            self.err = py.io.FDCapture(2, tmpfile=tmpfile) 
            if patchsys: 
                self.err.setasfile('stderr')

    def done(self):
        """ return (outfile, errfile) and stop capturing. """
        if hasattr(self, 'out'): 
            outfile = self.out.done() 
        else:
            outfile = None
        if hasattr(self, 'err'): 
            errfile = self.err.done() 
        else:
            errfile = None 
        if hasattr(self, '_oldin'):
            oldsys, oldfd = self._oldin 
            os.dup2(oldfd, 0)
            os.close(oldfd)
            sys.stdin = oldsys 
        return outfile, errfile 

    def readouterr(self):
        """ return snapshot value of stdout/stderr capturings. """
        l = []
        for name in ('out', 'err'):
            res = ""
            if hasattr(self, name):
                f = getattr(self, name).tmpfile
                f.seek(0)
                res = f.read()
                f.truncate(0)
                f.seek(0)
            l.append(res)
        return l 

class StdCapture(Capture):
    """ This class allows to capture writes to sys.stdout|stderr "in-memory"
        and will raise errors on tries to read from sys.stdin. It only
        modifies sys.stdout|stderr|stdin attributes and does not 
        touch underlying File Descriptors (use StdCaptureFD for that). 
    """
    def __init__(self, out=True, err=True, in_=True, mixed=False):
        self._kwargs = locals().copy()
        del self._kwargs['self']
        self._initialize(**self._kwargs)

    def _initialize(self, out, err, in_, mixed):
        self._out = out
        self._err = err 
        self._in = in_
        if out: 
            self._oldout = sys.stdout
            if not hasattr(out, 'write'):
                out = StringIO()
            sys.stdout = self.out = out
        if err: 
            self._olderr = sys.stderr
            if out and mixed: 
                err = self.out 
            elif not hasattr(err, 'write'):
                err = StringIO()
            sys.stderr = self.err = err
        if in_:
            self._oldin  = sys.stdin
            sys.stdin  = self.newin  = DontReadFromInput()

    def done(self): 
        """ return (outfile, errfile) and stop capturing. """
        o,e = sys.stdout, sys.stderr
        if self._out: 
            try:
                sys.stdout = self._oldout 
            except AttributeError:
                raise IOError("stdout capturing already reset")
            del self._oldout
            outfile = self.out
            outfile.seek(0)
        else:
            outfile = None
        if self._err: 
            try:
                sys.stderr = self._olderr 
            except AttributeError:
                raise IOError("stderr capturing already reset")
            del self._olderr 
            errfile = self.err 
            errfile.seek(0)
        else:
            errfile = None
        if self._in:
            sys.stdin = self._oldin 
        return outfile, errfile

    def readouterr(self):
        """ return snapshot value of stdout/stderr capturings. """
        out = err = ""
        if self._out:
            out = sys.stdout.getvalue()
            sys.stdout.truncate(0)
        if self._err:
            err = sys.stderr.getvalue()
            sys.stderr.truncate(0)
        return out, err 

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
   
    def fileno(self):
        raise ValueError("redirected Stdin is pseudofile, has no fileno()") 
    def isatty(self):
        return False

try:
    devnullpath = os.devnull
except AttributeError:
    if os.name == 'nt':
        devnullpath = 'NUL'
    else:
        devnullpath = '/dev/null'


