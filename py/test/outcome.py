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
    # XXX slighly hackish: on 3k we fake to live in the builtins 
    # in order to have Skipped exception printing shorter/nicer
    __module__ = 'builtins'

class Failed(OutcomeException): 
    pass

class ExceptionFailure(Failed): 
    def __init__(self, expr, expected, msg=None, excinfo=None): 
        Failed.__init__(self, msg=msg, excinfo=excinfo) 
        self.expr = expr 
        self.expected = expected

class Exit(KeyboardInterrupt):
    """ for immediate program exits without tracebacks and reporter/summary. """
    def __init__(self, msg="unknown reason"):
        self.msg = msg 
        KeyboardInterrupt.__init__(self, msg)

# exposed helper methods 

def exit(msg): 
    """ exit testing process immediately. """ 
    __tracebackhide__ = True
    raise Exit(msg)

def skip(msg=""):
    """ skip with the given message. """
    __tracebackhide__ = True
    raise Skipped(msg=msg) 

def importorskip(modname, minversion=None):
    """ return imported module or skip() """
    compile(modname, '', 'eval') # to catch syntaxerrors
    try:
        mod = __import__(modname)
    except ImportError:
        py.test.skip("could not import %r" %(modname,))
    if minversion is None:
        return mod
    verattr = getattr(mod, '__version__', None)
    if isinstance(minversion, str):
        minver = minversion.split(".")
    else:
        minver = list(minversion)
    if verattr is None or verattr.split(".") < minver:
        py.test.skip("module %r has __version__ %r, required is: %r" %(
                     modname, verattr, minversion))
    return mod

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
            py.builtin.exec_(code, frame.f_globals, loc)
            # XXX didn'T mean f_globals == f_locals something special?
            #     this is destroyed here ...
        except ExpectedException:
            return py.code.ExceptionInfo()
    else:
        func = args[0]
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


# exitcodes for the command line
EXIT_OK = 0
EXIT_TESTSFAILED = 1
EXIT_INTERRUPTED = 2
EXIT_INTERNALERROR = 3
EXIT_NOHOSTS = 4
