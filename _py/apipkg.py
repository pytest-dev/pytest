"""
apipkg: control the exported namespace of a python package.

see http://pypi.python.org/pypi/apipkg

(c) holger krekel, 2009 - MIT license
"""
import os, sys
from types import ModuleType

__version__ = "1.0b1"

def initpkg(pkgname, exportdefs):
    """ initialize given package from the export definitions. """
    pkgmodule = sys.modules[pkgname]
    mod = ApiModule(pkgname, exportdefs)
    for name, value in mod.__dict__.items():
         if name[:2] != "__" or name == "__all__":
            setattr(pkgmodule, name, value)

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
        if parent:
            fullname = parent.__fullname__ + "." + name
            setattr(parent, name, self)
        else:
            fullname = name
        self.__fullname__ = fullname
        for name, importspec in importspec.items():
            if isinstance(importspec, dict):
                apimod = ApiModule(name, importspec, parent=self)
                sys.modules[apimod.__fullname__] = apimod
            else:
                if not importspec.count(":") == 1:
                    raise ValueError("invalid importspec %r" % (importspec,))
                if name == '__doc__':
                    self.__doc__ = importobj(importspec)
                else:
                    self.__map__[name] = importspec

    def __repr__(self):
        return '<ApiModule %r>' % (self.__fullname__,)

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
