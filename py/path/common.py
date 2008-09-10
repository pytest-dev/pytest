"""
module with base functionality for std.path package

"""
from __future__ import generators
import os, sys
import py
from py.__.misc.warn import APIWARN

def checktype(pathinstance, kw):
    names = ('local', 'svnwc', 'svnurl', 'py', )
    for name,value in kw.items():
        if name in names:
            cls = getattr(py.path, name)
            if bool(isinstance(pathinstance, cls)) ^ bool(value):
                return False
            del kw[name]
    return True

class checker:
    """ deprecated: return checker callable checking for the given 
        kwargs-specified specification. 
    """
    def __init__(self, **kwargs):
        APIWARN("0.9.0", 
            "py.path.checker is deprecated, construct "
            "calls to pathobj.check() instead", 
        )
        self.kwargs = kwargs
    def __call__(self, p):
        return p.check(**self.kwargs)

class Checkers:
    _depend_on_existence = 'exists', 'link'

    def __init__(self, path):
        self.path = path

    def exists(self):
        raise NotImplementedError

    def basename(self, arg):
        return self.path.basename == arg

    def basestarts(self, arg):
        return self.path.basename.startswith(arg)

    def relto(self, arg):
        return self.path.relto(arg)

    def fnmatch(self, arg):
        return fnmatch(arg)(self.path)

    def endswith(self, arg):
        return str(self.path).endswith(arg)

    def _evaluate(self, kw):
        for name, value in kw.items():
            invert = False
            meth = None
            try:
                meth = getattr(self, name)
            except AttributeError:
                if name[:3] == 'not':
                    invert = True
                    try:
                        meth = getattr(self, name[3:])
                    except AttributeError:
                        pass
            if meth is None:
                raise TypeError, "no %r checker available for %r" % (name, self.path)
            try:
                if meth.im_func.func_code.co_argcount > 1:
                    if (not meth(value)) ^ invert:
                        return False
                else:
                    if bool(value) ^ bool(meth()) ^ invert:
                        return False
            except (py.error.ENOENT, py.error.ENOTDIR):
                for name in self._depend_on_existence:
                    if name in kw:
                        if kw.get(name):
                            return False
                    name = 'not' + name
                    if name in kw:
                        if not kw.get(name):
                            return False
        return True

class _dummyclass: 
    pass

class PathBase(object):
    """ shared implementation for filesystem path objects."""
    Checkers = Checkers

    def check(self, **kw):
        """ check a path for existence, or query its properties

            without arguments, this returns True if the path exists (on the
            filesystem), False if not

            with (keyword only) arguments, the object compares the value
            of the argument with the value of a property with the same name
            (if it has one, else it raises a TypeError)

            when for example the keyword argument 'ext' is '.py', this will
            return True if self.ext == '.py', False otherwise
        """
        if kw:
            kw = kw.copy()
            if not checktype(self, kw):
                return False
        else:
            kw = {'exists' : 1}
        return self.Checkers(self)._evaluate(kw)

    def __iter__(self):
        for i in self.listdir():
            yield i

    def __contains__(self, other):
        if isinstance(other, str):
            return self.join(other).check()
        else:
            if other.dirpath() != self:
                return False
            p = self.join(other.basename)
            return p.check()

    def basename(self):
        return self._getbyspec('basename')[0]
    basename = property(basename, None, None, 'basename part of path')

    def relto(self, relpath):
        """ return a string which is the relative part of the path
        to the given 'relpath'. 
        """
        if not isinstance(relpath, (str, PathBase)): 
            raise TypeError("%r: not a string or path object" %(relpath,))
        strrelpath = str(relpath)
        if strrelpath and strrelpath[-1] != self.sep:
            strrelpath += self.sep
        #assert strrelpath[-1] == self.sep
        #assert strrelpath[-2] != self.sep
        strself = str(self)
        if sys.platform == "win32":
            if os.path.normcase(strself).startswith(
               os.path.normcase(strrelpath)):
                return strself[len(strrelpath):]        
        elif strself.startswith(strrelpath):
            return strself[len(strrelpath):]
        return ""

    def parts(self, reverse=False):
        """ return a root-first list of all ancestor directories
            plus the path itself.
        """
        current = self
        l = [self]
        while 1:
            last = current
            current = current.dirpath()
            if last == current:
                break
            l.insert(0, current)
        if reverse:
            l.reverse()
        return l

    def common(self, other):
        """ return the common part shared with the other path
            or None if there is no common part.
        """
        last = None
        for x, y in zip(self.parts(), other.parts()):
            if x != y:
                return last
            last = x
        return last

    def __add__(self, other):
        """ return new path object with 'other' added to the basename"""
        return self.new(basename=self.basename+str(other))

    def __cmp__(self, other):
        """ return sort value (-1, 0, +1). """
        try:
            return cmp(self.strpath, other.strpath)
        except AttributeError:
            return cmp(str(self), str(other)) # self.path, other.path)

    def __repr__(self):
        """ return a string representation of this path. """
        return repr(str(self))

    def visit(self, fil=None, rec=None, ignore=_dummyclass):
        """ yields all paths below the current one

            fil is a filter (glob pattern or callable), if not matching the
            path will not be yielded, defaulting to None (everything is
            returned)

            rec is a filter (glob pattern or callable) that controls whether
            a node is descended, defaulting to None

            ignore is an Exception class that is ignoredwhen calling dirlist()
            on any of the paths (by default, all exceptions are reported)
        """
        if isinstance(fil, str):
            fil = fnmatch(fil)
        if rec: 
            if isinstance(rec, str):
                rec = fnmatch(fil)
            elif not callable(rec): 
                rec = lambda x: True 
        reclist = [self]
        while reclist: 
            current = reclist.pop(0)
            try:
                dirlist = current.listdir() 
            except ignore:
                return
            for p in dirlist:
                if fil is None or fil(p):
                    yield p
                if p.check(dir=1) and (rec is None or rec(p)):
                    reclist.append(p)

    def _callex(self, func, *args):
        """ call a function and raise errno-exception if applicable. """
        __tracebackhide__ = True
        try:
            return func(*args)
        except py.error.Error: 
            raise
        except EnvironmentError, e:
            if not hasattr(e, 'errno'):
                raise
            __tracebackhide__ = False
            cls, value, tb = sys.exc_info()
            errno = e.errno 
            try:
                if not isinstance(e, WindowsError): 
                    raise NameError
            except NameError: 
                # we are not on Windows, or we got a proper OSError
                cls = py.error._geterrnoclass(errno)
            else: 
                try: 
                    cls = py.error._getwinerrnoclass(errno)
                except KeyError:    
                    raise cls, value, tb
            value = cls("%s%r" % (func.__name__, args))
            __tracebackhide__ = True
            raise cls, value

    def _gethashinstance(self, hashtype):
        if hashtype == "md5": 
            return py.std.md5.md5()
        elif hashtype == "sha": 
            return py.std.sha.sha()
        else:
            raise ValueError("unknown hash type: %r" %(hashtype,))


class fnmatch:
    def __init__(self, pattern):
        self.pattern = pattern
    def __call__(self, path):
        """return true if the basename/fullname matches the glob-'pattern'.

        *       matches everything
        ?       matches any single character
        [seq]   matches any character in seq
        [!seq]  matches any char not in seq

        if the pattern contains a path-separator then the full path
        is used for pattern matching and a '*' is prepended to the
        pattern.

        if the pattern doesn't contain a path-separator the pattern
        is only matched against the basename.
        """
        pattern = self.pattern
        if pattern.find(path.sep) == -1:
            name = path.basename
        else:
            name = str(path) # path.strpath # XXX svn?
            pattern = '*' + path.sep + pattern
        from fnmatch import fnmatch
        return fnmatch(name, pattern)


class FSCheckers(Checkers):
    _depend_on_existence = Checkers._depend_on_existence+('dir', 'file')

    def dir(self):
        raise NotImplementedError

    def file(self):
        raise NotImplementedError

    def dotfile(self):
        return self.path.basename.startswith('.')

    def ext(self, arg):
        if not arg.startswith('.'):
            arg = '.' + arg
        return self.path.ext == arg

class FSPathBase(PathBase):
    """ shared implementation for filesystem path objects."""
    Checkers = FSCheckers

    def __div__(self, other):
        return self.join(str(other))

    def dirpath(self, *args, **kwargs):
        """ return the directory Path of the current Path joined
            with any given path arguments.
        """
        return self.new(basename='').join(*args, **kwargs)

    def ext(self):
        """ extension of the path (including the '.')."""
        return self._getbyspec('ext')[0]
    ext = property(ext, None, None, 'extension part of path')

    def purebasename(self):
        """ pure base name of the path."""
        return self._getbyspec('purebasename')[0]
    purebasename = property(purebasename, None, None, 'basename without extension')

    def read(self, mode='rb'):
        """ read and return a bytestring from reading the path. """
        if py.std.sys.version_info < (2,3):
            for x in 'u', 'U':
                if x in mode:
                    mode = mode.replace(x, '')
        f = self.open(mode)
        try:
            return f.read()
        finally:
            f.close()

    def readlines(self, cr=1):
        """ read and return a list of lines from the path. if cr is False, the
newline will be removed from the end of each line. """
        if not cr:
            content = self.read('rU')
            return content.split('\n')
        else:
            f = self.open('rU')
            try:
                return f.readlines()
            finally:
                f.close()

    def load(self):
        """ return object unpickled from self.read() """
        f = self.open('rb')
        try:
            from cPickle import load
            return self._callex(load, f)
        finally:
            f.close()

    def move(self, target):
        """ move this path to target. """
        if target.relto(self):
            raise py.error.EINVAL(target, "cannot move path into a subdirectory of itself")
        try:
            self.rename(target)
        except py.error.EXDEV:  # invalid cross-device link
            self.copy(target)
            self.remove()

    def _getpymodule(self):
        """resolve this path to a module python object. """
        modname = str(self)
        modname = modname.replace('.', self.sep)
        try:
            return sys.modules[modname]
        except KeyError:
            co = self._getpycodeobj()
            mod = py.std.new.module(modname)
            mod.__file__ = PathStr(self)
            if self.basename == '__init__.py':
                mod.__path__ = [str(self.dirpath())]
            sys.modules[modname] = mod
            try: 
                exec co in mod.__dict__
            except: 
                del sys.modules[modname] 
                raise 
            return mod

    def _getpycodeobj(self):
        """ read the path and compile it to a py.code.Code object. """
        s = self.read('rU')
        # XXX str(self) should show up somewhere in the code's filename
        return py.code.compile(s)

class PathStr(str):
    def __init__(self, path):
        global old_import_hook
        self.__path__ = path
        if old_import_hook is None:
            import __builtin__
            old_import_hook = __builtin__.__import__
            __builtin__.__import__ = custom_import_hook

def relativeimport(p, name, parent=None):
    names = name.split('.')
    last_list = [False] * (len(names)-1) + [True]
    modules = []
    for name, is_last in zip(names, last_list):
        if hasattr(parent, name):
            # shortcut if there is already the correct name
            # in the parent package
            submodule = getattr(parent, name)
        else:
            if is_last and p.new(basename=name+'.py').check():
                p = p.new(basename=name+'.py')
            else:
                p = p.new(basename=name).join('__init__.py')
                if not p.check():
                    return None   # not found
            submodule = p._getpymodule()
            if parent is not None:
                setattr(parent, name, submodule)
        modules.append(submodule)
        parent = submodule
    return modules   # success


old_import_hook = None

def custom_import_hook(name, glob=None, loc=None, fromlist=None, extra=None, level=None):
    __tracebackhide__ = False 
    __file__ = glob and glob.get('__file__')
    if isinstance(__file__, PathStr):
        # try to perform a relative import
        # for cooperation with py.magic.autopath, first look in the pkgdir
        modules = None
        if hasattr(__file__.__path__, 'pkgdir'):
            modules = relativeimport(__file__.__path__.pkgdir, name)
        if not modules:
            modules = relativeimport(__file__.__path__, name)
        if modules:
            if fromlist:
                submodule = modules[-1]  # innermost submodule
                # try to import submodules named in the 'fromlist' if the
                # 'submodule' is a package
                p = submodule.__file__.__path__
                if p.check(basename='__init__.py'):
                    for name in fromlist:
                        relativeimport(p, name, parent=submodule)
                        # failures are fine
                return submodule
            else:
                return modules[0]   # outermost package
    # fall-back
    __tracebackhide__ = True 
    try:
        return old_import_hook(name, glob, loc, fromlist, level)
    except TypeError:
        return old_import_hook(name, glob, loc, fromlist)
        

