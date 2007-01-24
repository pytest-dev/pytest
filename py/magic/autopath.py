import os, sys
from py.path import local
from py.__.path.common import PathStr

def autopath(globs=None, basefile='__init__.py'):
    """ return the (local) path of the "current" file pointed to by globals
        or - if it is none - alternatively the callers frame globals.

        the path will always point to a .py file  or to None.
        the path will have the following payload:
        pkgdir   is the last parent directory path containing 'basefile'
                 starting backwards from the current file.
    """
    if globs is None:
        globs = sys._getframe(1).f_globals
    try:
        __file__ = globs['__file__']
    except KeyError:
        if not sys.argv[0]:
            raise ValueError, "cannot compute autopath in interactive mode"
        __file__ = os.path.abspath(sys.argv[0])

    custom__file__ = isinstance(__file__, PathStr)
    if custom__file__:
        ret = __file__.__path__
    else:
        ret = local(__file__)
        if ret.ext in ('.pyc', '.pyo'):
            ret = ret.new(ext='.py')
    current = pkgdir = ret.dirpath()
    while 1:
        if basefile in current:
            pkgdir = current
            current = current.dirpath()
            if pkgdir != current:
                continue
        elif not custom__file__ and str(current) not in sys.path:
            sys.path.insert(0, str(current))
        break
    ret.pkgdir = pkgdir
    return ret
