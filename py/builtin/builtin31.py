import sys

if sys.version_info >= (3, 0):
    exec ("print_ = print ; exec_=exec")
    import builtins
    basestring = str 

else:
    basestring = basestring
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
        out = sep.join([str(x) for x in args]) + end
        file.write(out)

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
