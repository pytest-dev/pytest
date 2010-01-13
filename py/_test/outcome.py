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
    """ exit testing process as if KeyboardInterrupt was triggered. """ 
    __tracebackhide__ = True
    raise Exit(msg)

def skip(msg=""):
    """ skip an executing test with the given message.  Note: it's usually
    better use the py.test.mark.skipif marker to declare a test to be
    skipped under certain conditions like mismatching platforms or 
    dependencies.  See the pytest_skipping plugin for details. 
    """
    __tracebackhide__ = True
    raise Skipped(msg=msg) 

def fail(msg=""):
    """ explicitely fail this executing test with the given Message. """
    __tracebackhide__ = True
    raise Failed(msg=msg) 

def raises(ExpectedException, *args, **kwargs):
    """ if args[0] is callable: raise AssertionError if calling it with 
        the remaining arguments does not raise the expected exception.  
        if args[0] is a string: raise AssertionError if executing the
        the string in the calling scope does not raise expected exception. 
        for examples:
        x = 5
        raises(TypeError, lambda x: x + 'hello', x=x)
        raises(TypeError, "x + 'hello'")
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

def importorskip(modname, minversion=None):
    """ return imported module if it has a higher __version__ than the 
    optionally specified 'minversion' - otherwise call py.test.skip() 
    with a message detailing the mismatch. 
    """
    compile(modname, '', 'eval') # to catch syntaxerrors
    try:
        mod = __import__(modname, None, None, ['__doc__'])
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



# exitcodes for the command line
EXIT_OK = 0
EXIT_TESTSFAILED = 1
EXIT_INTERRUPTED = 2
EXIT_INTERNALERROR = 3
EXIT_NOHOSTS = 4
