"""
package initialization.

You use the functionality of this package by putting

    from py.initpkg import initpkg
    initpkg(__name__, exportdefs={
        'name1.name2' : ('./path/to/file.py', 'name')
        ...
    })

into your package's __init__.py file.  This will
lead your package to only expose the names of all
your implementation files that you explicitely
specify.  In the above example 'name1' will
become a Module instance where 'name2' is
bound in its namespace to the 'name' object
in the relative './path/to/file.py' python module.
Note that you can also use a '.c' file in which
case it will be compiled via distutils-facilities
on the fly.

"""
from __future__ import generators
import sys
import os
assert sys.version_info >= (2,2,0), "py lib requires python 2.2 or higher"
from types import ModuleType

# ---------------------------------------------------
# Package Object
# ---------------------------------------------------

class Package(object):
    def __init__(self, name, exportdefs, metainfo):
        pkgmodule = sys.modules[name]
        assert pkgmodule.__name__ == name
        self.name = name
        self.exportdefs = exportdefs
        self.module = pkgmodule
        assert not hasattr(pkgmodule, '__pkg__'), \
                   "unsupported reinitialization of %r" % pkgmodule
        pkgmodule.__pkg__ = self

        # make available pkgname.__
        implname = name + '.' + '__'
        self.implmodule = ModuleType(implname)
        self.implmodule.__name__ = implname
        self.implmodule.__file__ = os.path.abspath(pkgmodule.__file__)
        self.implmodule.__path__ = [os.path.abspath(p)
                                    for p in pkgmodule.__path__]
        pkgmodule.__ = self.implmodule
        setmodule(implname, self.implmodule)
        # inhibit further direct filesystem imports through the package module
        del pkgmodule.__path__

        # set metainfo 
        for name, value in metainfo.items(): 
            setattr(self, name, value) 
        version = metainfo.get('version', None)
        if version:
            pkgmodule.__version__ = version

    def _resolve(self, extpyish):
        """ resolve a combined filesystem/python extpy-ish path. """
        fspath, modpath = extpyish
        if not fspath.endswith('.py'):
            import py
            e = py.path.local(self.implmodule.__file__)
            e = e.dirpath(fspath, abs=True)
            e = py.path.extpy(e, modpath)
            return e.resolve()
        assert fspath.startswith('./'), \
               "%r is not an implementation path (XXX)" % (extpyish,)
        implmodule = self._loadimpl(fspath[:-3])
        if not isinstance(modpath, str): # export the entire module
            return implmodule

        current = implmodule
        for x in modpath.split('.'):
            try: 
                current = getattr(current, x)
            except AttributeError: 
                raise AttributeError("resolving %r failed: %s" %(
                                     extpyish, x))

        return current

    def getimportname(self, path): 
        if not path.ext.startswith('.py'): 
            return None 
        import py
        base = py.path.local(self.implmodule.__file__).dirpath()
        if not path.relto(base): 
            return None 
        names = path.new(ext='').relto(base).split(path.sep) 
        dottedname = ".".join([self.implmodule.__name__] + names)
        return dottedname 

    def _loadimpl(self, relfile):
        """ load implementation for the given relfile. """
        parts = [x.strip() for x in relfile.split('/') if x and x!= '.']
        modpath = ".".join([self.implmodule.__name__] + parts)
        #print "trying import", modpath
        return __import__(modpath, None, None, ['__doc__'])

    def exportitems(self):
        return self.exportdefs.items()

    def getpath(self):
        from py.path import local
        base = local(self.implmodule.__file__).dirpath()
        assert base.check()
        return base

    def _iterfiles(self):
        from py.__.path.common import checker
        base = self.getpath()
        for x in base.visit(checker(file=1, notext='.pyc'),
                            rec=checker(dotfile=0)):
            yield x

    def shahexdigest(self, cache=[]):
        """ return sha hexdigest for files contained in package. """
        if cache:
            return cache[0]
        from sha import sha
        sum = sha()
        # XXX the checksum depends on the order in which visit() enumerates
        # the files, and it doesn't depend on the file names and paths
        for x in self._iterfiles():
            sum.update(x.read())
        cache.append(sum.hexdigest())
        return cache[0]

    def getzipdata(self):
        """ return string representing a zipfile containing the package. """
        import zipfile
        import py
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        base = py.__pkg__.getpath().dirpath()
        outf = StringIO()
        f = zipfile.ZipFile(outf, 'w', compression=zipfile.ZIP_DEFLATED)
        try:
            for x in self._iterfiles():
                f.write(str(x), x.relto(base))
        finally:
            f.close()
        return outf.getvalue()

    def getrev(self):
        import py
        p = py.path.svnwc(self.module.__file__).dirpath()
        try:
            return p.info().rev
        except (KeyboardInterrupt, MemoryError, SystemExit):
            raise
        except:
            return 'unknown'

def setmodule(modpath, module):
    #print "sys.modules[%r] = %r" % (modpath, module)
    sys.modules[modpath] = module

# ---------------------------------------------------
# Virtual Module Object
# ---------------------------------------------------

class Module(ModuleType):
    def __init__(self, pkg, name):
        self.__pkg__ = pkg
        self.__name__ = name
        self.__map__ = {}

    def __getattr__(self, name):
        if '*' in self.__map__: 
            extpy = self.__map__['*'][0], name 
            result = self.__pkg__._resolve(extpy) 
        else: 
            try:
                extpy = self.__map__[name]
            except KeyError:
                __tracebackhide__ = True
                raise AttributeError(name)
            else: 
                result = self.__pkg__._resolve(extpy) 
                del self.__map__[name]
        setattr(self, name, result)
        #self._fixinspection(result, name) 
        return result

    def _deprecated_fixinspection(self, result, name): 
        # modify some attrs to make a class appear at export level 
        if hasattr(result, '__module__'):
            if not result.__module__.startswith('py.__'):
                return   # don't change __module__ nor __name__ for classes
                         # that the py lib re-exports from somewhere else,
                         # e.g. py.builtin.BaseException
            try:
                setattr(result, '__module__', self.__name__)
            except (AttributeError, TypeError):
                pass
        if hasattr(result, '__bases__'):
            try:
                setattr(result, '__name__', name)
            except (AttributeError, TypeError):
                pass

    def __repr__(self):
        return '<Module %r>' % (self.__name__, )

    def getdict(self):
        # force all the content of the module to be loaded when __dict__ is read
        dictdescr = ModuleType.__dict__['__dict__']
        dict = dictdescr.__get__(self)
        if dict is not None:
            if '*' not in self.__map__: 
                for name in self.__map__.keys():
                    hasattr(self, name)   # force attribute to be loaded, ignore errors
                assert not self.__map__, "%r not empty" % self.__map__
            else: 
                fsname = self.__map__['*'][0] 
                dict.update(self.__pkg__._loadimpl(fsname[:-3]).__dict__)
        return dict

    __dict__ = property(getdict)
    del getdict

# ---------------------------------------------------
# Bootstrap Virtual Module Hierarchy
# ---------------------------------------------------

def initpkg(pkgname, exportdefs, **kw):
    #print "initializing package", pkgname
    # bootstrap Package object
    pkg = Package(pkgname, exportdefs, kw)
    seen = { pkgname : pkg.module }
    deferred_imports = []

    for pypath, extpy in pkg.exportitems():
        pyparts = pypath.split('.')
        modparts = pyparts[:]
        if extpy[1] != '*': 
            lastmodpart = modparts.pop()
        else: 
            lastmodpart = '*'
        current = pkgname

        # ensure modules
        for name in modparts:
            previous = current
            current += '.' + name
            if current not in seen:
                seen[current] = mod = Module(pkg, current)
                setattr(seen[previous], name, mod)
                setmodule(current, mod)

        mod = seen[current]
        if not hasattr(mod, '__map__'):
            assert mod is pkg.module, \
                   "only root modules are allowed to be non-lazy. "
            deferred_imports.append((mod, pyparts[-1], extpy))
        else:
            if extpy[1] == '__doc__':
                mod.__doc__ = pkg._resolve(extpy)
            else:
                mod.__map__[lastmodpart] = extpy 

    for mod, pypart, extpy in deferred_imports: 
        setattr(mod, pypart, pkg._resolve(extpy))

