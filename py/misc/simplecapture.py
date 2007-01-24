"""

capture stdout/stderr

"""
import sys
try: from cStringIO import StringIO
except ImportError: from StringIO import StringIO

class SimpleOutErrCapture:
    """ capture sys.stdout/sys.stderr (but not system level fd 1 and 2).

    this captures only "In-Memory" and is currently intended to be
    used by the unittest package to capture print-statements in tests.
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

def callcapture(func, *args, **kwargs): 
    so = SimpleOutErrCapture()
    try: 
        res = func(*args, **kwargs)
    finally: 
        out, err = so.reset()
    return res, out, err 
