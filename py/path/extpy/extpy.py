"""
A path to python objects located in filesystems.

Note: this is still experimental and may be removed
      for the first stable release!
"""
from __future__ import generators
import py
from py.__.path import common
import sys
import inspect
moduletype = type(py)

class Extpy(common.PathBase):
    """ path object for addressing python objects. """
    sep = '.'
    def __new__(cls, root, modpath=''):
        if not isinstance(modpath, str):
            raise TypeError("second 'modpath' argument must be a dotted name.")
        if isinstance(root, str):
            root = py.path.local(root)

        self = object.__new__(cls)
        if isinstance(root, Extpy): 
            # we don't want it nested, do we? 
            assert not modpath 
            root = root.root 
        self.modpath = modpath
        self.root = root
        return self

    def __hash__(self):
        return hash((self.root, self.modpath))

    def __repr__(self):
        return 'extpy(%r, %r)' % (self.root, self.modpath)

    def __str__(self):
        return "%s%s.%s" %(self.root, self.root.sep, self.modpath) 

    def join(self, *args):
        for arg in args:
            if not isinstance(arg, str):
                raise TypeError, "non-strings not allowed in %r" % args
        modpath = [x.strip('.') for x in ((self.modpath,)+args) if x]
        modpath = self.sep.join(modpath)
        return self.__class__(self.root, modpath)

    def relto(self, other):
        if self.root != other.root: 
            return '' 
        return super(Extpy, self).relto(other) 

    def dirpath(self, *args):
        modpath = self.modpath.split(self.sep) [:-1]
        modpath = self.sep.join(modpath+list(args))
        return self.__class__(self.root, modpath)

    def new(self, **kw):
        """ create a modified version of this path.
            the following keyword arguments modify various path parts:
            modpath    substitute module path
        """
        cls = self.__class__
        if 'modpath' in kw:
            return cls(self.root, kw['modpath'])
        if 'basename' in kw:
            i = self.modpath.rfind('.')
            if i != -1:
                return cls(self.root, self.modpath[i+1:] + kw['basename'])
            else:
                return cls(self.root, kw['basename'])
        return cls(self.root, self.modpath)

    def _getbyspec(self, spec):
        l = []
        modparts = self.modpath.split(self.sep)
        for name in spec.split(','):
            if name == 'basename':
                l.append(modparts[-1])
        return l

    def resolve(self):
        """return the python object, obtained from traversing from
           the root along the modpath.
        """
        rest = filter(None, self.modpath.split('.'))
        target = self.getpymodule()
        for name in rest:
            try:
                target = getattr(target, name)
            except AttributeError:
                raise py.error.ENOENT(target, name)
        return target

    def getpymodule(self):
        if hasattr(self.root, 'resolve'):
            return self.root.resolve()
        else:
            return self.root.getpymodule()

    def listobj(self, fil=None, **kw):
        l = []
        for x in self.listdir(fil, **kw):
            l.append(x.resolve())
        return l

    def listdir(self, fil=None, sort=True, **kw):
        if kw:
            if fil is None:
                fil = lambda x: x.check(**kw) 
            else:
                raise TypeError, "cannot take filter and keyword arguments"
        elif isinstance(fil, str):
            fil = common.fnmatch(fil)
        obj = self.resolve()
        l = []
        #print "listdir on", self
        if not hasattr(obj, '__dict__'):
            raise py.error.ENOTDIR(self, "does not have a __dict__ attribute")
        for name in dir(obj):
            sub = self.join(name)
            if not fil or fil(sub):
                l.append(sub)

        #print "listdir(%r) -> %r" %(self, l)
        #print "listdir on", repr(self)
        return l

    def getfilelineno(self, scrapinit=0):
        x = obj = self.resolve()
        if inspect.ismodule(obj):
            return obj.__file__, 0
        if inspect.ismethod(obj):
            obj = obj.im_func
        if inspect.isfunction(obj):
            obj = obj.func_code
        if inspect.iscode(obj):
            return py.path.local(obj.co_filename), obj.co_firstlineno - 1
        else:
            source, lineno = inspect.findsource(obj)
            return x.getfile(), lineno - 1

    def visit(self, fil=None, rec=None, ignore=None, seen=None):
        def myrec(p, seen={id(self): True}):
            if id(p) in seen:
                return False
            seen[id(p)] = True
            if self.samefile(p):
                return True

        for x in super(Extpy, self).visit(fil=fil, rec=rec, ignore=ignore):
            yield x
        return

        if seen is None:
            seen = {id(self): True}

        if isinstance(fil, str):
            fil = common.fnmatch(fil)
        if isinstance(rec, str):
            rec = common.fnmatch(fil)

        if ignore:
            try:
                l = self.listdir()
            except ignore:
                return
        else:
            l = self.listdir()
        reclist = []
        for p in l:
            if fil is None or fil(p):
                yield p
            if id(p) not in seen:
                try:
                    obj = p.resolve()
                    if inspect.isclass(obj) or inspect.ismodule(obj):
                        reclist.append(p)
                finally:
                    seen[id(p)] = p
        for p in reclist:
            for i in p.visit(fil, rec, seen):
                yield i

    def samefile(self, other):
        otherobj = other.resolve()
        try:
            x = inspect.getfile(otherobj)
        except TypeError:
            return False
        if x.endswith('.pyc'):
            x = x[:-1]
        if str(self.root) == x:
            return True

    def read(self, mode='ignored'):
        """ return a bytestring from looking at our underlying object. 
        
        mode parmeter exists for consistency, but is ignored."""
        return str(self.resolve())

    class Checkers(common.Checkers):
        _depend_on_existence = (common.Checkers._depend_on_existence +
                                ('func', 'class_', 'exists', 'dir'))

        def _obj(self):
            self._obj = self.path.resolve()
            return self._obj

        def exists(self):
            obj = self._obj()
            return True

        def func(self):
            ob = self._obj()
            return inspect.isfunction(ob) or inspect.ismethod(ob)

        def class_(self):
            ob = self._obj()
            return inspect.isclass(ob)

        def isinstance(self, args):
            return isinstance(self._obj(), args)

        def dir(self):
            obj = self._obj()
            return inspect.isclass(obj) or inspect.ismodule(obj)

        def file(self):
            return not self.dir()

        def genfunc(self):
            try:
                return self._obj().func_code.co_flags & 32
            except AttributeError:
                return False
