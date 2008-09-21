"""
    Test OutcomeExceptions and helpers for creating them. 
    py.test.skip|fail|raises helper implementations 

"""

import py
import sys

class OutcomeException(Exception): 
    """ OutcomeException and its subclass instances indicate and 
        contain info about test and collection outcomes. 
    """ 
    def __init__(self, msg=None, excinfo=None): 
        self.msg = msg 
        self.excinfo = excinfo

    def __repr__(self):
        if self.msg: 
            return repr(self.msg) 
        return "<%s instance>" %(self.__class__.__name__,)
    __str__ = __repr__

class Passed(OutcomeException): 
    pass

class Skipped(OutcomeException): 
    pass

class Failed(OutcomeException): 
    pass

class ExceptionFailure(Failed): 
    def __init__(self, expr, expected, msg=None, excinfo=None): 
        Failed.__init__(self, msg=msg, excinfo=excinfo) 
        self.expr = expr 
        self.expected = expected

class Exit(Exception):
    """ for immediate program exits without tracebacks and reporter/summary. """
    def __init__(self, msg="unknown reason"):
        self.msg = msg 
        Exception.__init__(self, msg)

# exposed helper methods 

def exit(msg): 
    """ exit testing process immediately. """ 
    __tracebackhide__ = True
    raise Exit(msg)

def skip(msg="", ifraises=None, ns=None):
    """ (conditionally) skip this test/module/conftest. 
       
    msg: use this message when skipping. 
    ifraises: 
        if "exec ifraises in {'py': py}" raises an exception 
        skip this test. 
    ns: use this namespace when executing ifraises
    """
    __tracebackhide__ = True
    if ifraises is not None:
        ifraises = py.code.Source(ifraises).compile()
        if ns is None:
            ns = {}
        try:
            exec ifraises in ns
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            if not msg:
                msg = repr(e)
        else:
            return    
    raise Skipped(msg=msg) 

def fail(msg="unknown failure"):
    """ fail with the given Message. """
    __tracebackhide__ = True
    raise Failed(msg=msg) 

def raises(ExpectedException, *args, **kwargs):
    """ raise AssertionError, if target code does not raise the expected
        exception.
    """
    __tracebackhide__ = True 
    assert args
    if isinstance(args[0], str):
        code, = args
        assert isinstance(code, str)
        frame = sys._getframe(1)
        loc = frame.f_locals.copy()
        loc.update(kwargs)
        #print "raises frame scope: %r" % frame.f_locals
        try:
            code = py.code.Source(code).compile()
            exec code in frame.f_globals, loc
            # XXX didn'T mean f_globals == f_locals something special?
            #     this is destroyed here ...
        except ExpectedException:
            return py.code.ExceptionInfo()
    else:
        func = args[0]
        assert callable
        try:
            func(*args[1:], **kwargs)
        except ExpectedException:
            return py.code.ExceptionInfo()
        k = ", ".join(["%s=%r" % x for x in kwargs.items()])
        if k:
            k = ', ' + k
        expr = '%s(%r%s)' %(func.__name__, args, k)
    raise ExceptionFailure(msg="DID NOT RAISE", 
                           expr=args, expected=ExpectedException) 

def deprecated_call(func, *args, **kwargs):
    """ assert that calling func(*args, **kwargs)
        triggers a DeprecationWarning. 
    """ 
    warningmodule = py.std.warnings
    l = []
    oldwarn_explicit = getattr(warningmodule, 'warn_explicit')
    def warn_explicit(*args, **kwargs): 
        l.append(args) 
        oldwarn_explicit(*args, **kwargs)
    oldwarn = getattr(warningmodule, 'warn')
    def warn(*args, **kwargs): 
        l.append(args) 
        oldwarn(*args, **kwargs)
        
    warningmodule.warn_explicit = warn_explicit
    warningmodule.warn = warn
    try:
        ret = func(*args, **kwargs)
    finally:
        warningmodule.warn_explicit = warn_explicit
        warningmodule.warn = warn
    if not l:
        #print warningmodule
        raise AssertionError("%r did not produce DeprecationWarning" %(func,))
    return ret


# exitcodes for the command line
EXIT_OK = 0
EXIT_TESTSFAILED = 1
EXIT_INTERRUPTED = 2
EXIT_INTERNALERROR = 3
EXIT_NOHOSTS = 4
