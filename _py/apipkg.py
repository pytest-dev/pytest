"""
apipkg: control the exported namespace of a python package.

see http://pypi.python.org/pypi/apipkg

(c) holger krekel, 2009 - MIT license
"""
import sys
from types import ModuleType

__version__ = "1.0b2"

def initpkg(pkgname, exportdefs):
    """ initialize given package from the export definitions.
        replace it in sys.modules
    """
    mod = ApiModule(pkgname, exportdefs)
    oldmod = sys.modules[pkgname]
    mod.__file__ = getattr(oldmod, '__file__', None)
    mod.__version__ = getattr(oldmod, '__version__', None)
    mod.__path__ = getattr(oldmod, '__path__', None)
    sys.modules[pkgname]  = mod

def importobj(importspec):
    """ return object specified by importspec."""
    modpath, attrname = importspec.split(":")
    module = __import__(modpath, None, None, ['__doc__'])
    return getattr(module, attrname)

class ApiModule(ModuleType):
    def __init__(self, name, importspec, parent=None):
        self.__name__ = name
        self.__all__ = list(importspec)
        self.__map__ = {}
        for name, importspec in importspec.items():
            if isinstance(importspec, dict):
                package = '%s.%s'%(self.__name__, name)
                apimod = ApiModule(package, importspec, parent=self)
                sys.modules[package] = apimod
                setattr(self, name, apimod)
            else:
                if not importspec.count(":") == 1:
                    raise ValueError("invalid importspec %r" % (importspec,))
                if name == '__doc__':
                    self.__doc__ = importobj(importspec)
                else:
                    if importspec[0] == '.':
                        importspec = self.__name__ + importspec
                    self.__map__[name] = importspec

    def __repr__(self):
        return '<ApiModule %r>' % (self.__name__,)

    def __getattr__(self, name):
        try:
            importspec = self.__map__.pop(name)
        except KeyError:
            raise AttributeError(name)
        else:
            result = importobj(importspec)
            setattr(self, name, result)
            return result

    def __dict__(self):
        # force all the content of the module to be loaded when __dict__ is read
        dictdescr = ModuleType.__dict__['__dict__']
        dict = dictdescr.__get__(self)
        if dict is not None:
            for name in self.__all__:
                hasattr(self, name)  # force attribute load, ignore errors
        return dict
    __dict__ = property(__dict__)
