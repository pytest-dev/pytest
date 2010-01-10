"""
apipkg: control the exported namespace of a python package.

see http://pypi.python.org/pypi/apipkg

(c) holger krekel, 2009 - MIT license
"""
import sys
from types import ModuleType

__version__ = "1.0b4"

def initpkg(pkgname, exportdefs):
    """ initialize given package from the export definitions. """
    mod = ApiModule(pkgname, exportdefs, implprefix=pkgname)
    oldmod = sys.modules[pkgname]
    mod.__file__ = getattr(oldmod, '__file__', None)
    mod.__version__ = getattr(oldmod, '__version__', None)
    mod.__path__ = getattr(oldmod, '__path__', None)
    mod.__loader__ = getattr(oldmod, '__loader__', None)
    sys.modules[pkgname]  = mod

def importobj(modpath, attrname):
    module = __import__(modpath, None, None, ['__doc__'])
    return getattr(module, attrname)

class ApiModule(ModuleType):
    def __init__(self, name, importspec, implprefix=None):
        self.__name__ = name
        self.__all__ = [x for x in importspec if x != '__onfirstaccess__']
        self.__map__ = {}
        self.__implprefix__ = implprefix or name
        for name, importspec in importspec.items():
            if isinstance(importspec, dict):
                subname = '%s.%s'%(self.__name__, name)
                apimod = ApiModule(subname, importspec, implprefix)
                sys.modules[subname] = apimod
                setattr(self, name, apimod)
            else:
                modpath, attrname = importspec.split(':')
                if modpath[0] == '.':
                    modpath = implprefix + modpath
                if name == '__doc__':
                    self.__doc__ = importobj(modpath, attrname)
                else:
                    self.__map__[name] = (modpath, attrname)

    def __repr__(self):
        l = []
        if hasattr(self, '__version__'):
            l.append("version=" + repr(self.__version__))
        if hasattr(self, '__file__'):
            l.append('from ' + repr(self.__file__))
        if l:
            return '<ApiModule %r %s>' % (self.__name__, " ".join(l))
        return '<ApiModule %r>' % (self.__name__,)

    def __makeattr(self, name):
        """lazily compute value for name or raise AttributeError if unknown."""
        target = None
        if '__onfirstaccess__' in self.__map__:
            target = self.__map__.pop('__onfirstaccess__')
            importobj(*target)()
        try:
            modpath, attrname = self.__map__[name]
        except KeyError:
            if target is not None and name != '__onfirstaccess__':
                # retry, onfirstaccess might have set attrs
                return getattr(self, name)
            raise AttributeError(name)
        else:
            result = importobj(modpath, attrname)
            setattr(self, name, result)
            del self.__map__[name]
            return result

    __getattr__ = __makeattr

    def __dict__(self):
        # force all the content of the module to be loaded when __dict__ is read
        dictdescr = ModuleType.__dict__['__dict__']
        dict = dictdescr.__get__(self)
        if dict is not None:
            hasattr(self, 'some')
            for name in self.__all__:
                try:
                    self.__makeattr(name)
                except AttributeError:
                    pass
        return dict
    __dict__ = property(__dict__)
