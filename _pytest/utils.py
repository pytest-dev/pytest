import py
import sys
import types
import _pytest
import inspect
import functools

# used to work around a python2 exception info leak

exc_clear = getattr(sys, 'exc_clear', lambda: None)


NoneType = type(None)

isfunction = inspect.isfunction
isclass = inspect.isclass
callable = py.builtin.callable

NOTSET = object()

if hasattr(inspect, 'signature'):
    def _format_args(func):
        return str(inspect.signature(func))
else:
    def _format_args(func):
        return inspect.formatargspec(*inspect.getargspec(func))


if  sys.version_info[:2] == (2, 6):
    def isclass(object):
        """ Return true if the object is a class. Overrides inspect.isclass for
        python 2.6 because it will return True for objects which always return
        something on __getattr__ calls (see #1035).
        Backport of https://hg.python.org/cpython/rev/35bf8f7a8edc
        """
        return isinstance(object, (type, types.ClassType))


def is_generator(func):
    try:
        return _pytest._code.getrawcode(func).co_flags & 32 # generator function
    except AttributeError: # builtin functions have no bytecode
        # assume them to not be generators
        return False


def getimfunc(func):
    try:
        return func.__func__
    except AttributeError:
        try:
            return func.im_func
        except AttributeError:
            return func

def safe_getattr(object, name, default):
    """ Like getattr but return default upon any Exception.

    Attribute access can potentially fail for 'evil' Python objects.
    See issue214
    """
    try:
        return getattr(object, name, default)
    except Exception:
        return default



def num_mock_patch_args(function):
    """ return number of arguments used up by mock arguments (if any) """
    patchings = getattr(function, "patchings", None)
    if not patchings:
        return 0
    mock = sys.modules.get("mock", sys.modules.get("unittest.mock", None))
    if mock is not None:
        return len([p for p in patchings
                        if not p.attribute_name and p.new is mock.DEFAULT])
    return len(patchings)

def getfuncargnames(function, startindex=None):
    # XXX merge with main.py's varnames
    #assert not isclass(function)
    realfunction = function
    while hasattr(realfunction, "__wrapped__"):
        realfunction = realfunction.__wrapped__
    if startindex is None:
        startindex = inspect.ismethod(function) and 1 or 0
    if realfunction != function:
        startindex += num_mock_patch_args(function)
        function = realfunction
    if isinstance(function, functools.partial):
        argnames = inspect.getargs(_pytest._code.getrawcode(function.func))[0]
        partial = function
        argnames = argnames[len(partial.args):]
        if partial.keywords:
            for kw in partial.keywords:
                argnames.remove(kw)
    else:
        argnames = inspect.getargs(_pytest._code.getrawcode(function))[0]
    defaults = getattr(function, 'func_defaults',
                       getattr(function, '__defaults__', None)) or ()
    numdefaults = len(defaults)
    if numdefaults:
        return tuple(argnames[startindex:-numdefaults])
    return tuple(argnames[startindex:])


def getfslineno(obj):
    # xxx let decorators etc specify a sane ordering
    obj = get_real_func(obj)
    if hasattr(obj, 'place_as'):
        obj = obj.place_as
    fslineno = _pytest._code.getfslineno(obj)
    assert isinstance(fslineno[1], int), obj
    return fslineno


def get_real_func(obj):
    """ gets the real function object of the (possibly) wrapped object by
    functools.wraps or functools.partial.
    """
    while hasattr(obj, "__wrapped__"):
        obj = obj.__wrapped__
    if isinstance(obj, functools.partial):
        obj = obj.func
    return obj
