import sys

if sys.version_info >= (3, 0):
    exec ("print_ = print ; exec_=exec")
    import builtins
    import pickle

    # some backward compatibility helpers 
    _basestring = str 
    def _totext(obj, encoding):
        if isinstance(obj, bytes):
            obj = obj.decode(encoding)
        elif not isinstance(obj, str):
            obj = str(obj)
        return obj

    def _isbytes(x): 
        return isinstance(x, bytes)
    def _istext(x): 
        return isinstance(x, str)

    def execfile(fn, globs=None, locs=None):
        if globs is None:
            back = sys._getframe(1)
            globs = back.f_globals
            locs = back.f_locals
            del back
        elif locs is None:
            locs = globs
        fp = open(fn, "rb")
        try:
            source = fp.read()
        finally:
            fp.close()
        exec_(source, globs, locs)

    def callable(obj):
        return hasattr(obj, "__call__")

else:
    try:
        import cPickle as pickle
    except ImportError:
        import pickle 
    _totext = unicode 
    _basestring = basestring
    execfile = execfile
    callable = callable
    def _isbytes(x): 
        return isinstance(x, str)
    def _istext(x): 
        return isinstance(x, unicode)

    import __builtin__ as builtins
    def print_(*args, **kwargs):
        """ minimal backport of py3k print statement. """ 
        sep = ' '
        if 'sep' in kwargs:
            sep = kwargs.pop('sep')
        end = '\n'
        if 'end' in kwargs:
            end = kwargs.pop('end')
        file = 'file' in kwargs and kwargs.pop('file') or sys.stdout
        if kwargs:
            args = ", ".join([str(x) for x in kwargs])
            raise TypeError("invalid keyword arguments: %s" % args)
        at_start = True
        for x in args:
            if not at_start:
                file.write(sep)
            file.write(str(x))
            at_start = False
        file.write(end)

    def exec_(obj, globals=None, locals=None):
        """ minimal backport of py3k exec statement. """ 
        if globals is None: 
            frame = sys._getframe(1)
            globals = frame.f_globals 
            if locals is None:
                locals = frame.f_locals
        elif locals is None:
            locals = globals
        exec2(obj, globals, locals) 

if sys.version_info >= (3,0):
    exec ("""
def _reraise(cls, val, tb):
    assert hasattr(val, '__traceback__')
    raise val
""")
else:
    exec ("""
def _reraise(cls, val, tb):
    raise cls, val, tb
def exec2(obj, globals, locals):
    exec obj in globals, locals 
""")
