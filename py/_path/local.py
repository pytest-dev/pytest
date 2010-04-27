"""
local path implementation.
"""
import sys, os, stat, re, atexit
import py
from py._path import common

iswin32 = sys.platform == "win32" or (getattr(os, '_name', False) == 'nt')

class Stat(object):
    def __getattr__(self, name):
        return getattr(self._osstatresult, "st_" + name)

    def __init__(self, path, osstatresult): 
        self.path = path 
        self._osstatresult = osstatresult

    def owner(self):
        if iswin32:
            raise NotImplementedError("XXX win32")
        import pwd 
        entry = py.error.checked_call(pwd.getpwuid, self.uid)
        return entry[0]
    owner = property(owner, None, None, "owner of path") 

    def group(self):
        """ return group name of file. """
        if iswin32:
            raise NotImplementedError("XXX win32")
        import grp
        entry = py.error.checked_call(grp.getgrgid, self.gid)
        return entry[0]
    group = property(group) 

class PosixPath(common.PathBase):
    def chown(self, user, group, rec=0):
        """ change ownership to the given user and group.
            user and group may be specified by a number or
            by a name.  if rec is True change ownership
            recursively.
        """
        uid = getuserid(user)
        gid = getgroupid(group)
        if rec:
            for x in self.visit(rec=lambda x: x.check(link=0)): 
                if x.check(link=0):
                    py.error.checked_call(os.chown, str(x), uid, gid)
        py.error.checked_call(os.chown, str(self), uid, gid)

    def readlink(self):
        """ return value of a symbolic link. """
        return py.error.checked_call(os.readlink, self.strpath)

    def mklinkto(self, oldname):
        """ posix style hard link to another name. """
        py.error.checked_call(os.link, str(oldname), str(self))

    def mksymlinkto(self, value, absolute=1):
        """ create a symbolic link with the given value (pointing to another name). """
        if absolute:
            py.error.checked_call(os.symlink, str(value), self.strpath)
        else:
            base = self.common(value)
            # with posix local paths '/' is always a common base
            relsource = self.__class__(value).relto(base)
            reldest = self.relto(base)
            n = reldest.count(self.sep)
            target = self.sep.join(('..', )*n + (relsource, ))
            py.error.checked_call(os.symlink, target, self.strpath)

    def samefile(self, other):
        """ return True if other refers to the same stat object as self. """
        return py.error.checked_call(os.path.samefile, str(self), str(other))

def getuserid(user):
    import pwd
    if not isinstance(user, int):
        user = pwd.getpwnam(user)[2]
    return user

def getgroupid(group):
    import grp
    if not isinstance(group, int):
        group = grp.getgrnam(group)[2]
    return group

FSBase = not iswin32 and PosixPath or common.PathBase

class LocalPath(FSBase):
    """ object oriented interface to os.path and other local filesystem 
        related information. 
    """
    sep = os.sep
    class Checkers(common.Checkers):
        def _stat(self):
            try:
                return self._statcache
            except AttributeError:
                try:
                    self._statcache = self.path.stat()
                except py.error.ELOOP:
                    self._statcache = self.path.lstat()
                return self._statcache

        def dir(self):
            return stat.S_ISDIR(self._stat().mode)

        def file(self):
            return stat.S_ISREG(self._stat().mode)

        def exists(self):
            return self._stat()

        def link(self):
            st = self.path.lstat()
            return stat.S_ISLNK(st.mode)

    def __new__(cls, path=None):
        """ Initialize and return a local Path instance.

        Path can be relative to the current directory.
        If it is None then the current working directory is taken.
        Note that Path instances always carry an absolute path.
        Note also that passing in a local path object will simply return
        the exact same path object. Use new() to get a new copy.
        """
        if isinstance(path, common.PathBase):
            if path.__class__ == cls:
                return path
            path = path.strpath
        # initialize the path
        self = object.__new__(cls)
        if not path:
            self.strpath = os.getcwd()
        elif isinstance(path, py.builtin._basestring):
            self.strpath = os.path.abspath(os.path.normpath(str(path)))
        else:
            raise ValueError("can only pass None, Path instances "
                             "or non-empty strings to LocalPath")
        assert isinstance(self.strpath, str)
        return self

    def __hash__(self):
        return hash(self.strpath)

    def __eq__(self, other):
        s1 = str(self)
        s2 = str(other)
        if iswin32: 
            s1 = s1.lower()
            s2 = s2.lower()
        return s1 == s2

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return str(self) < str(other)

    def remove(self, rec=1):
        """ remove a file or directory (or a directory tree if rec=1).  """
        if self.check(dir=1, link=0):
            if rec:
                # force remove of readonly files on windows 
                if iswin32: 
                    self.chmod(448, rec=1) # octcal 0700
                py.error.checked_call(py.std.shutil.rmtree, self.strpath)
            else:
                py.error.checked_call(os.rmdir, self.strpath)
        else:
            if iswin32: 
                self.chmod(448) # octcal 0700
            py.error.checked_call(os.remove, self.strpath)

    def computehash(self, hashtype="md5", chunksize=524288):
        """ return hexdigest of hashvalue for this file. """
        try:
            try:
                import hashlib as mod
            except ImportError:
                if hashtype == "sha1":
                    hashtype = "sha"
                mod = __import__(hashtype)
            hash = getattr(mod, hashtype)()
        except (AttributeError, ImportError):
            raise ValueError("Don't know how to compute %r hash" %(hashtype,))
        f = self.open('rb')
        try:
            while 1:
                buf = f.read(chunksize)
                if not buf:
                    return hash.hexdigest()
                hash.update(buf) 
        finally:
            f.close()

    def new(self, **kw):
        """ create a modified version of this path.
            the following keyword arguments modify various path parts:

              a:/some/path/to/a/file.ext
              ||                            drive
                |-------------|             dirname
                                |------|    basename
                                |--|        purebasename
                                    |--|    ext
        """
        obj = object.__new__(self.__class__)
        drive, dirname, basename, purebasename,ext = self._getbyspec(
             "drive,dirname,basename,purebasename,ext")
        if 'basename' in kw:
            if 'purebasename' in kw or 'ext' in kw:
                raise ValueError("invalid specification %r" % kw)
        else:
            pb = kw.setdefault('purebasename', purebasename)
            try:
                ext = kw['ext']
            except KeyError:
                pass
            else:
                if ext and not ext.startswith('.'):
                    ext = '.' + ext
            kw['basename'] = pb + ext

        kw.setdefault('drive', drive)
        kw.setdefault('dirname', dirname)
        kw.setdefault('sep', self.sep)
        obj.strpath = os.path.normpath(
            "%(drive)s%(dirname)s%(sep)s%(basename)s" % kw)
        return obj
    
    def _getbyspec(self, spec):
        """ return a sequence of specified path parts.  'spec' is
            a comma separated string containing path part names.
            according to the following convention:
            a:/some/path/to/a/file.ext
            ||                            drive
              |-------------|             dirname
                              |------|    basename
                              |--|        purebasename
                                  |--|    ext
        """
        res = []
        parts = self.strpath.split(self.sep)

        args = filter(None, spec.split(',') )
        append = res.append
        for name in args:
            if name == 'drive':
                append(parts[0])
            elif name == 'dirname':
                append(self.sep.join(['']+parts[1:-1]))
            else:
                basename = parts[-1]
                if name == 'basename':
                    append(basename)
                else:
                    i = basename.rfind('.')
                    if i == -1:
                        purebasename, ext = basename, ''
                    else:
                        purebasename, ext = basename[:i], basename[i:]
                    if name == 'purebasename':
                        append(purebasename)
                    elif name == 'ext':
                        append(ext)
                    else:
                        raise ValueError("invalid part specification %r" % name)
        return res

    def join(self, *args, **kwargs):
        """ return a new path by appending all 'args' as path
        components.  if abs=1 is used restart from root if any
        of the args is an absolute path.
        """
        if not args:
            return self
        strpath = self.strpath
        sep = self.sep
        strargs = [str(x) for x in args]
        if kwargs.get('abs', 0):
            for i in range(len(strargs)-1, -1, -1):
                if os.path.isabs(strargs[i]):
                    strpath = strargs[i]
                    strargs = strargs[i+1:]
                    break
        for arg in strargs:
            arg = arg.strip(sep)
            if iswin32:
                # allow unix style paths even on windows.
                arg = arg.strip('/')
                arg = arg.replace('/', sep)
            if arg:
                if not strpath.endswith(sep):
                    strpath += sep
                strpath += arg
        obj = self.new()
        obj.strpath = os.path.normpath(strpath)
        return obj

    def open(self, mode='r'):
        """ return an opened file with the given mode. """
        return py.error.checked_call(open, self.strpath, mode)

    def listdir(self, fil=None, sort=None):
        """ list directory contents, possibly filter by the given fil func
            and possibly sorted.
        """
        if isinstance(fil, str):
            fil = common.FNMatcher(fil)
        res = []
        for name in py.error.checked_call(os.listdir, self.strpath):
            childurl = self.join(name)
            if fil is None or fil(childurl):
                res.append(childurl)
        self._sortlist(res, sort)
        return res 

    def size(self):
        """ return size of the underlying file object """
        return self.stat().size

    def mtime(self):
        """ return last modification time of the path. """
        return self.stat().mtime

    def copy(self, target, archive=False):
        """ copy path to target."""
        assert not archive, "XXX archive-mode not supported"
        if self.check(file=1):
            if target.check(dir=1):
                target = target.join(self.basename)
            assert self!=target
            copychunked(self, target)
        else:
            def rec(p):
                return p.check(link=0)
            for x in self.visit(rec=rec):
                relpath = x.relto(self)
                newx = target.join(relpath)
                newx.dirpath().ensure(dir=1)
                if x.check(link=1):
                    newx.mksymlinkto(x.readlink())
                elif x.check(file=1):
                    copychunked(x, newx)
                elif x.check(dir=1):
                    newx.ensure(dir=1)

    def rename(self, target):
        """ rename this path to target. """
        return py.error.checked_call(os.rename, str(self), str(target))

    def dump(self, obj, bin=1):
        """ pickle object into path location"""
        f = self.open('wb')
        try:
            py.error.checked_call(py.std.pickle.dump, obj, f, bin)
        finally:
            f.close()

    def mkdir(self, *args):
        """ create & return the directory joined with args. """
        p = self.join(*args)
        py.error.checked_call(os.mkdir, str(p))
        return p

    def write(self, data, mode='w'):
        """ write data into path. """
        if 'b' in mode:
            if not py.builtin._isbytes(data):
                raise ValueError("can only process bytes")
        else:
            if not py.builtin._istext(data):
                if not py.builtin._isbytes(data):
                    data = str(data)
                else:
                    data = py.builtin._totext(data, sys.getdefaultencoding())
        f = self.open(mode)
        try:
            f.write(data)
        finally:
            f.close()

    def _ensuredirs(self):
        parent = self.dirpath()
        if parent == self:
            return self
        if parent.check(dir=0):
            parent._ensuredirs()
        if self.check(dir=0):
            try:
                self.mkdir()
            except py.error.EEXIST:
                # race condition: file/dir created by another thread/process.
                # complain if it is not a dir
                if self.check(dir=0):
                    raise
        return self

    def ensure(self, *args, **kwargs):
        """ ensure that an args-joined path exists (by default as
            a file). if you specify a keyword argument 'dir=True'
            then the path is forced to be a directory path.
        """
        p = self.join(*args)
        if kwargs.get('dir', 0):
            return p._ensuredirs()
        else:
            p.dirpath()._ensuredirs()
            if not p.check(file=1):
                p.open('w').close()
            return p

    def stat(self):
        """ Return an os.stat() tuple. """
        return Stat(self, py.error.checked_call(os.stat, self.strpath))

    def lstat(self):
        """ Return an os.lstat() tuple. """
        return Stat(self, py.error.checked_call(os.lstat, self.strpath))

    def setmtime(self, mtime=None):
        """ set modification time for the given path.  if 'mtime' is None
        (the default) then the file's mtime is set to current time.

        Note that the resolution for 'mtime' is platform dependent.
        """
        if mtime is None:
            return py.error.checked_call(os.utime, self.strpath, mtime)
        try:
            return py.error.checked_call(os.utime, self.strpath, (-1, mtime))
        except py.error.EINVAL:
            return py.error.checked_call(os.utime, self.strpath, (self.atime(), mtime))

    def chdir(self):
        """ change directory to self and return old current directory """
        old = self.__class__()
        py.error.checked_call(os.chdir, self.strpath)
        return old

    def realpath(self):
        """ return a new path which contains no symbolic links."""
        return self.__class__(os.path.realpath(self.strpath))

    def atime(self):
        """ return last access time of the path. """
        return self.stat().atime

    def __repr__(self):
        return 'local(%r)' % self.strpath

    def __str__(self):
        """ return string representation of the Path. """
        return self.strpath

    def pypkgpath(self, pkgname=None):
        """ return the path's package path by looking for the given
            pkgname.  If pkgname is None then look for the last
            directory upwards which still contains an __init__.py
            and whose basename is python-importable.
            Return None if a pkgpath can not be determined.
        """
        pkgpath = None
        for parent in self.parts(reverse=True):
            if pkgname is None:
                if parent.check(file=1):
                    continue
                if not isimportable(parent.basename):
                    break
                if parent.join('__init__.py').check():
                    pkgpath = parent
                    continue
                return pkgpath
            else:
                if parent.basename == pkgname:
                    return parent
        return pkgpath

    def _prependsyspath(self, path):
        s = str(path)
        if s != sys.path[0]:
            #print "prepending to sys.path", s
            sys.path.insert(0, s)

    def chmod(self, mode, rec=0):
        """ change permissions to the given mode. If mode is an
            integer it directly encodes the os-specific modes.
            if rec is True perform recursively.
        """
        if not isinstance(mode, int):
            raise TypeError("mode %r must be an integer" % (mode,))
        if rec:
            for x in self.visit(rec=rec):
                py.error.checked_call(os.chmod, str(x), mode)
        py.error.checked_call(os.chmod, str(self), mode)

    def pyimport(self, modname=None, ensuresyspath=True):
        """ return path as an imported python module.
            if modname is None, look for the containing package
            and construct an according module name.
            The module will be put/looked up in sys.modules.
        """
        if not self.check():
            raise py.error.ENOENT(self)
        #print "trying to import", self
        pkgpath = None
        if modname is None:
            pkgpath = self.pypkgpath()
            if pkgpath is not None:
                if ensuresyspath:
                    self._prependsyspath(pkgpath.dirpath())
                pkg = __import__(pkgpath.basename, None, None, [])
                names = self.new(ext='').relto(pkgpath.dirpath())
                names = names.split(self.sep)
                modname = ".".join(names)
            else:
                # no package scope, still make it possible
                if ensuresyspath:
                    self._prependsyspath(self.dirpath())
                modname = self.purebasename
            mod = __import__(modname, None, None, ['__doc__'])
            modfile = mod.__file__
            if modfile[-4:] in ('.pyc', '.pyo'):
                modfile = modfile[:-1]
            elif modfile.endswith('$py.class'):
                modfile = modfile[:-9] + '.py'
            if not self.samefile(modfile):
                raise EnvironmentError("mismatch:\n"
                "imported module %r\n"
                "does not stem from %r\n" 
                "maybe __init__.py files are missing?" % (mod, str(self)))
            return mod
        else:
            try:
                return sys.modules[modname]
            except KeyError:
                # we have a custom modname, do a pseudo-import
                mod = py.std.types.ModuleType(modname)
                mod.__file__ = str(self)
                sys.modules[modname] = mod
                try:
                    py.builtin.execfile(str(self), mod.__dict__)
                except:
                    del sys.modules[modname]
                    raise
                return mod

    def sysexec(self, *argv, **popen_opts):
        """ return stdout text from executing a system child process,
            where the 'self' path points to executable. 
            The process is directly invoked and not through a system shell. 
        """
        from subprocess import Popen, PIPE
        argv = map(str, argv)
        popen_opts['stdout'] = popen_opts['stderr'] = PIPE
        proc = Popen([str(self)] + list(argv), **popen_opts)
        stdout, stderr = proc.communicate()
        ret = proc.wait()
        if py.builtin._isbytes(stdout):
            stdout = py.builtin._totext(stdout, sys.getdefaultencoding())
        if ret != 0:
            if py.builtin._isbytes(stderr):
                stderr = py.builtin._totext(stderr, sys.getdefaultencoding())
            raise py.process.cmdexec.Error(ret, ret, str(self),
                                           stdout, stderr,)
        return stdout

    def sysfind(cls, name, checker=None):
        """ return a path object found by looking at the systems
            underlying PATH specification. If the checker is not None
            it will be invoked to filter matching paths.  If a binary
            cannot be found, None is returned
            Note: This is probably not working on plain win32 systems
            but may work on cygwin.
        """
        if os.path.isabs(name):
            p = py.path.local(name)
            if p.check(file=1):
                return p
        else:
            if iswin32:
                paths = py.std.os.environ['Path'].split(';')
                if '' not in paths and '.' not in paths:
                    paths.append('.')
                try:
                    systemroot = os.environ['SYSTEMROOT']
                except KeyError:
                    pass
                else:
                    paths = [re.sub('%SystemRoot%', systemroot, path)
                             for path in paths]
                tryadd = '', '.exe', '.com', '.bat' # XXX add more?
            else:
                paths = py.std.os.environ['PATH'].split(':')
                tryadd = ('',)

            for x in paths:
                for addext in tryadd:
                    p = py.path.local(x).join(name, abs=True) + addext
                    try:
                        if p.check(file=1):
                            if checker:
                                if not checker(p):
                                    continue
                            return p
                    except py.error.EACCES:
                        pass
        return None
    sysfind = classmethod(sysfind)

    def _gethomedir(cls):
        try:
            x = os.environ['HOME']
        except KeyError:
            x = os.environ['HOMEPATH']
        return cls(x)
    _gethomedir = classmethod(_gethomedir)

    #"""
    #special class constructors for local filesystem paths
    #"""
    def get_temproot(cls):
        """ return the system's temporary directory
            (where tempfiles are usually created in)
        """
        return py.path.local(py.std.tempfile.gettempdir())
    get_temproot = classmethod(get_temproot)

    def mkdtemp(cls):
        """ return a Path object pointing to a fresh new temporary directory
            (which we created ourself).
        """
        import tempfile
        tries = 10
        for i in range(tries):
            dname = tempfile.mktemp()
            dpath = cls(tempfile.mktemp())
            try:
                dpath.mkdir()
            except (py.error.EEXIST, py.error.EPERM, py.error.EACCES):
                continue
            return dpath
        raise py.error.ENOENT(dpath, "could not create tempdir, %d tries" % tries)
    mkdtemp = classmethod(mkdtemp)

    def make_numbered_dir(cls, prefix='session-', rootdir=None, keep=3,
                          lock_timeout = 172800):   # two days
        """ return unique directory with a number greater than the current
            maximum one.  The number is assumed to start directly after prefix.
            if keep is true directories with a number less than (maxnum-keep)
            will be removed.
        """
        if rootdir is None:
            rootdir = cls.get_temproot()

        def parse_num(path):
            """ parse the number out of a path (if it matches the prefix) """
            bn = path.basename
            if bn.startswith(prefix):
                try:
                    return int(bn[len(prefix):])
                except ValueError:
                    pass

        # compute the maximum number currently in use with the
        # prefix
        lastmax = None
        while True:
            maxnum = -1
            for path in rootdir.listdir():
                num = parse_num(path)
                if num is not None:
                    maxnum = max(maxnum, num)

            # make the new directory
            try:
                udir = rootdir.mkdir(prefix + str(maxnum+1))
            except py.error.EEXIST:
                # race condition: another thread/process created the dir
                # in the meantime.  Try counting again
                if lastmax == maxnum:
                    raise
                lastmax = maxnum
                continue
            break

        # put a .lock file in the new directory that will be removed at
        # process exit
        if lock_timeout:
            lockfile = udir.join('.lock')
            mypid = os.getpid()
            if hasattr(lockfile, 'mksymlinkto'):
                lockfile.mksymlinkto(str(mypid))
            else:
                lockfile.write(str(mypid))
            def try_remove_lockfile():
                # in a fork() situation, only the last process should
                # remove the .lock, otherwise the other processes run the
                # risk of seeing their temporary dir disappear.  For now
                # we remove the .lock in the parent only (i.e. we assume
                # that the children finish before the parent).
                if os.getpid() != mypid:
                    return
                try:
                    lockfile.remove()
                except py.error.Error:
                    pass
            atexit.register(try_remove_lockfile)

        # prune old directories
        if keep:
            for path in rootdir.listdir():
                num = parse_num(path)
                if num is not None and num <= (maxnum - keep):
                    lf = path.join('.lock')
                    try:
                        t1 = lf.lstat().mtime
                        t2 = lockfile.lstat().mtime
                        if not lock_timeout or abs(t2-t1) < lock_timeout:
                            continue   # skip directories still locked
                    except py.error.Error:
                        pass   # assume that it means that there is no 'lf'
                    try:
                        path.remove(rec=1)
                    except KeyboardInterrupt:
                        raise
                    except: # this might be py.error.Error, WindowsError ...
                        pass
        
        # make link...
        try:
            username = os.environ['USER']           #linux, et al
        except KeyError:
            try:
                username = os.environ['USERNAME']   #windows
            except KeyError:
                username = 'current'

        src  = str(udir)
        dest = src[:src.rfind('-')] + '-' + username
        try:
            os.unlink(dest)
        except OSError:
            pass
        try:
            os.symlink(src, dest)
        except (OSError, AttributeError): # AttributeError on win32
            pass

        return udir
    make_numbered_dir = classmethod(make_numbered_dir)

def copychunked(src, dest):
    chunksize = 524288 # half a meg of bytes
    fsrc = src.open('rb')
    try:
        fdest = dest.open('wb')
        try:
            while 1:
                buf = fsrc.read(chunksize)
                if not buf:
                    break
                fdest.write(buf)
        finally:
            fdest.close()
    finally:
        fsrc.close()

def autopath(globs=None):
    """ (deprecated) return the (local) path of the "current" file pointed to by globals or - if it is none - alternatively the callers frame globals.

        the path will always point to a .py file  or to None.
        the path will have the following payload:
        pkgdir   is the last parent directory path containing __init__.py 
    """
    py.log._apiwarn("1.1", "py.magic.autopath deprecated, "
        "use py.path.local(__file__) and maybe pypkgpath/pyimport().")
    if globs is None:
        globs = sys._getframe(1).f_globals
    try:
        __file__ = globs['__file__']
    except KeyError:
        if not sys.argv[0]:
            raise ValueError("cannot compute autopath in interactive mode")
        __file__ = os.path.abspath(sys.argv[0])

    ret = py.path.local(__file__)
    if ret.ext in ('.pyc', '.pyo'):
        ret = ret.new(ext='.py')
    current = pkgdir = ret.dirpath()
    while 1:
        if current.join('__init__.py').check():
            pkgdir = current
            current = current.dirpath()
            if pkgdir != current:
                continue
        elif str(current) not in sys.path:
            sys.path.insert(0, str(current))
        break
    ret.pkgdir = pkgdir
    return ret


def isimportable(name):
    if name:
        if not (name[0].isalpha() or name[0] == '_'):
            return False
        name= name.replace("_", '')
        return not name or name.isalnum()
