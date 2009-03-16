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

class KeywordDecorator:
    """ decorator for setting function attributes. """
    def __init__(self, keywords, lastname=None):
        self._keywords = keywords
        self._lastname = lastname

    def __call__(self, func=None, **kwargs):
        if func is None:
            kw = self._keywords.copy()
            kw.update(kwargs)
            return KeywordDecorator(kw)
        elif not hasattr(func, 'func_dict'):
            kw = self._keywords.copy()
            name = self._lastname
            if name is None:
                name = "mark"
            kw[name] = func
            return KeywordDecorator(kw)
        func.func_dict.update(self._keywords)
        return func 

    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError(name)
        kw = self._keywords.copy()
        kw[name] = True
        return self.__class__(kw, lastname=name)

mark = KeywordDecorator({})

# exitcodes for the command line
EXIT_OK = 0
EXIT_TESTSFAILED = 1
EXIT_INTERRUPTED = 2
EXIT_INTERNALERROR = 3
EXIT_NOHOSTS = 4
