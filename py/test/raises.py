import sys
import py
from py.__.test.outcome import ExceptionFailure

def raises(ExpectedException, *args, **kwargs):
    """ raise AssertionError, if target code does not raise the expected
        exception.
    """
    assert args
    __tracebackhide__ = True 
    if isinstance(args[0], str):
        expr, = args
        assert isinstance(expr, str)
        frame = sys._getframe(1)
        loc = frame.f_locals.copy()
        loc.update(kwargs)
        #print "raises frame scope: %r" % frame.f_locals
        source = py.code.Source(expr)
        try:
            exec source.compile() in frame.f_globals, loc
            #del __traceback__
            # XXX didn'T mean f_globals == f_locals something special?
            #     this is destroyed here ...
        except ExpectedException:
            return py.code.ExceptionInfo()
    else:
        func = args[0]
        assert callable
        try:
            func(*args[1:], **kwargs)
            #del __traceback__
        except ExpectedException:
            return py.code.ExceptionInfo()
        k = ", ".join(["%s=%r" % x for x in kwargs.items()])
        if k:
            k = ', ' + k
        expr = '%s(%r%s)' %(func.__name__, args, k)
    raise ExceptionFailure(msg="DID NOT RAISE", 
                           expr=args, expected=ExpectedException) 
