"""
"""
import os, sys
import py

class Checkers:
    _depend_on_existence = 'exists', 'link', 'dir', 'file'

    def __init__(self, path):
        self.path = path

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

    def exists(self):
        raise NotImplementedError

    def basename(self, arg):
        return self.path.basename == arg

    def basestarts(self, arg):
        return self.path.basename.startswith(arg)

    def relto(self, arg):
        return self.path.relto(arg)

    def fnmatch(self, arg):
        return FNMatcher(arg)(self.path)

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
                raise TypeError(
                    "no %r checker available for %r" % (name, self.path))
            try:
                if py.code.getrawcode(meth).co_argcount > 1:
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

class NeverRaised(Exception): 
    pass

class PathBase(object):
    """ shared implementation for filesystem path objects."""
    Checkers = Checkers

    def __div__(self, other):
        return self.join(str(other))
    __truediv__ = __div__ # py3k

    def basename(self):
        """ basename part of path. """
        return self._getbyspec('basename')[0]
    basename = property(basename, None, None, basename.__doc__)

    def purebasename(self):
        """ pure base name of the path."""
        return self._getbyspec('purebasename')[0]
    purebasename = property(purebasename, None, None, purebasename.__doc__)

    def ext(self):
        """ extension of the path (including the '.')."""
        return self._getbyspec('ext')[0]
    ext = property(ext, None, None, ext.__doc__)

    def dirpath(self, *args, **kwargs):
        """ return the directory Path of the current Path joined
            with any given path arguments.
        """
        return self.new(basename='').join(*args, **kwargs)

    def read(self, mode='r'):
        """ read and return a bytestring from reading the path. """
        if sys.version_info < (2,3):
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
        """ (deprecated) return object unpickled from self.read() """
        f = self.open('rb')
        try:
            return py.error.checked_call(py.std.pickle.load, f)
        finally:
            f.close()

    def move(self, target):
        """ move this path to target. """
        if target.relto(self):
            raise py.error.EINVAL(target, 
                "cannot move path into a subdirectory of itself")
        try:
            self.rename(target)
        except py.error.EXDEV:  # invalid cross-device link
            self.copy(target)
            self.remove()

    def __repr__(self):
        """ return a string representation of this path. """
        return repr(str(self))

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
        if not kw:
            kw = {'exists' : 1}
        return self.Checkers(self)._evaluate(kw)

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
        if sys.platform == "win32" or getattr(os, '_name', None) == 'nt':
            if os.path.normcase(strself).startswith(
               os.path.normcase(strrelpath)):
                return strself[len(strrelpath):]        
        elif strself.startswith(strrelpath):
            return strself[len(strrelpath):]
        return ""

    def bestrelpath(self, dest): 
        """ return a string which is a relative path from self 
            to dest such that self.join(bestrelpath) == dest and 
            if not such path can be determined return dest. 
        """ 
        try:
            base = self.common(dest)
            if not base:  # can be the case on windows
                return str(dest)
            self2base = self.relto(base)
            reldest = dest.relto(base)
            if self2base:
                n = self2base.count(self.sep) + 1
            else:
                n = 0
            l = ['..'] * n
            if reldest:
                l.append(reldest)     
            target = dest.sep.join(l)
            return target 
        except AttributeError:
            return str(dest)


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

    def __lt__(self, other):
        try:
            return self.strpath < other.strpath 
        except AttributeError:
            return str(self) < str(other)

    def visit(self, fil=None, rec=None, ignore=NeverRaised):
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
            fil = FNMatcher(fil)
        if rec: 
            if isinstance(rec, str):
                rec = fnmatch(fil)
            elif not hasattr(rec, '__call__'):
                rec = None
        try:
            entries = self.listdir()
        except ignore:
            return
        dirs = [p for p in entries 
                    if p.check(dir=1) and (rec is None or rec(p))]
        for subdir in dirs:
            for p in subdir.visit(fil=fil, rec=rec, ignore=ignore):
                yield p
        for p in entries:
            if fil is None or fil(p):
                yield p

    def _sortlist(self, res, sort):
        if sort:
            if hasattr(sort, '__call__'):
                res.sort(sort)
            else:
                res.sort()

    def samefile(self, other):
        """ return True if other refers to the same stat object as self. """
        return self.strpath == str(other)

class FNMatcher:
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

