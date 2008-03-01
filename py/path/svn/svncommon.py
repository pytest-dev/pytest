"""
module with a base subversion path object.
"""
import os, sys, time, re, string
import py
from py.__.path import common

ALLOWED_CHARS = "_ -/\\=$.~+" #add characters as necessary when tested
if sys.platform == "win32":
    ALLOWED_CHARS += ":"
ALLOWED_CHARS_HOST = ALLOWED_CHARS + '@:'
    
def _getsvnversion(ver=[]):
    try:
        return ver[0]
    except IndexError:
        v = py.process.cmdexec("svn -q --version")
        v.strip()
        v = '.'.join(v.split('.')[:2])
        ver.append(v)
        return v

def _escape_helper(text):
    text = str(text)
    if py.std.sys.platform != 'win32':
        text = str(text).replace('$', '\\$')
    return text

def _check_for_bad_chars(text, allowed_chars=ALLOWED_CHARS):
    for c in str(text):
        if c.isalnum():
            continue
        if c in allowed_chars:
            continue
        return True
    return False

#_______________________________________________________________

class SvnPathBase(common.FSPathBase):
    """ Base implementation for SvnPath implementations. """
    sep = '/'

    def _geturl(self):
        return self.strpath
    url = property(_geturl, None, None, "url of this svn-path.")

    def __str__(self):
        """ return a string representation (including rev-number) """
        return self.strpath

    def __hash__(self):
        return hash(self.strpath)

    def new(self, **kw):
        """ create a modified version of this path. A 'rev' argument
            indicates a new revision.
            the following keyword arguments modify various path parts:

              http://host.com/repo/path/file.ext
              |-----------------------|          dirname
                                        |------| basename
                                        |--|     purebasename
                                            |--| ext
        """
        obj = object.__new__(self.__class__)
        obj.rev = kw.get('rev', self.rev)
        obj.auth = kw.get('auth', self.auth)
        dirname, basename, purebasename, ext = self._getbyspec(
             "dirname,basename,purebasename,ext")
        if 'basename' in kw:
            if 'purebasename' in kw or 'ext' in kw:
                raise ValueError("invalid specification %r" % kw)
        else:
            pb = kw.setdefault('purebasename', purebasename)
            ext = kw.setdefault('ext', ext)
            if ext and not ext.startswith('.'):
                ext = '.' + ext
            kw['basename'] = pb + ext

        kw.setdefault('dirname', dirname)
        kw.setdefault('sep', self.sep)
        if kw['basename']:
            obj.strpath = "%(dirname)s%(sep)s%(basename)s" % kw
        else:
            obj.strpath = "%(dirname)s" % kw
        return obj

    def _getbyspec(self, spec):
        """ get specified parts of the path.  'arg' is a string
            with comma separated path parts. The parts are returned
            in exactly the order of the specification.

            you may specify the following parts:

            http://host.com/repo/path/file.ext
            |-----------------------|          dirname
                                      |------| basename
                                      |--|     purebasename
                                          |--| ext
        """
        res = []
        parts = self.strpath.split(self.sep)
        for name in spec.split(','):
            name = name.strip()
            if name == 'dirname':
                res.append(self.sep.join(parts[:-1]))
            elif name == 'basename':
                res.append(parts[-1])
            else:
                basename = parts[-1]
                i = basename.rfind('.')
                if i == -1:
                    purebasename, ext = basename, ''
                else:
                    purebasename, ext = basename[:i], basename[i:]
                if name == 'purebasename':
                    res.append(purebasename)
                elif name == 'ext':
                    res.append(ext)
                else:
                    raise NameError, "Don't know part %r" % name
        return res

    def __eq__(self, other):
        """ return true if path and rev attributes each match """
        return (str(self) == str(other) and
               (self.rev == other.rev or self.rev == other.rev))

    def __ne__(self, other):
        return not self == other

    def join(self, *args):
        """ return a new Path (with the same revision) which is composed
            of the self Path followed by 'args' path components.
        """
        if not args:
            return self

        args = tuple([arg.strip(self.sep) for arg in args])
        parts = (self.strpath, ) + args
        newpath = self.__class__(self.sep.join(parts), self.rev, self.auth)
        return newpath

    def propget(self, name):
        """ return the content of the given property. """
        value = self._propget(name)
        return value

    def proplist(self):
        """ list all property names. """
        content = self._proplist()
        return content

    def listdir(self, fil=None, sort=None):
        """ list directory contents, possibly filter by the given fil func
            and possibly sorted.
        """
        if isinstance(fil, str):
            fil = common.fnmatch(fil)
        nameinfo_seq = self._listdir_nameinfo()
        if len(nameinfo_seq) == 1:
            name, info = nameinfo_seq[0]
            if name == self.basename and info.kind == 'file':
                #if not self.check(dir=1):
                raise py.error.ENOTDIR(self)
        paths = self._make_path_tuple(nameinfo_seq)

        if fil or sort:
            paths = filter(fil, paths)
            paths = isinstance(paths, list) and paths or list(paths)
            if callable(sort):
                paths.sort(sort)
            elif sort:
                paths.sort()
        return paths

    def info(self):
        """ return an Info structure with svn-provided information. """
        parent = self.dirpath()
        nameinfo_seq = parent._listdir_nameinfo()
        bn = self.basename
        for name, info in nameinfo_seq:
            if name == bn:
                return info
        raise py.error.ENOENT(self)

    def size(self):
        """ Return the size of the file content of the Path. """
        return self.info().size

    def mtime(self):
        """ Return the last modification time of the file. """
        return self.info().mtime

    # shared help methods

    def _escape(self, cmd):
        return _escape_helper(cmd)

    def _make_path_tuple(self, nameinfo_seq):
        """ return a tuple of paths from a nameinfo-tuple sequence.
        """
        #assert self.rev is not None, "revision of %s should not be None here" % self
        res = []
        for name, info in nameinfo_seq:
            child = self.join(name)
            res.append(child)
        return tuple(res)


    def _childmaxrev(self):
        """ return maximum revision number of childs (or self.rev if no childs) """
        rev = self.rev
        for name, info in self._listdir_nameinfo():
            rev = max(rev, info.created_rev)
        return rev

    #def _getlatestrevision(self):
    #    """ return latest repo-revision for this path. """
    #    url = self.strpath
    #    path = self.__class__(url, None)
    #
    #    # we need a long walk to find the root-repo and revision
    #    while 1:
    #        try:
    #            rev = max(rev, path._childmaxrev())
    #            previous = path
    #            path = path.dirpath()
    #        except (IOError, process.cmdexec.Error):
    #            break
    #    if rev is None:
    #        raise IOError, "could not determine newest repo revision for %s" % self
    #    return rev

    class Checkers(common.FSCheckers):
        def dir(self):
            try:
                return self.path.info().kind == 'dir'
            except py.error.Error:
                return self._listdirworks()

        def _listdirworks(self):
            try:
                self.path.listdir()
            except py.error.ENOENT:
                return False
            else:
                return True

        def file(self):
            try:
                return self.path.info().kind == 'file'
            except py.error.ENOENT:
                return False

        def exists(self):
            try:
                return self.path.info()
            except py.error.ENOENT:
                return self._listdirworks()

def parse_apr_time(timestr):
    i = timestr.rfind('.')
    if i == -1:
        raise ValueError, "could not parse %s" % timestr
    timestr = timestr[:i]
    parsedtime = time.strptime(timestr, "%Y-%m-%dT%H:%M:%S")
    return time.mktime(parsedtime)

class PropListDict(dict):
    """ a Dictionary which fetches values (InfoSvnCommand instances) lazily"""
    def __init__(self, path, keynames):
        dict.__init__(self, [(x, None) for x in keynames])
        self.path = path

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        if value is None:
            value = self.path.propget(key)
            dict.__setitem__(self, key, value)
        return value

def fixlocale():
    if sys.platform != 'win32':
        return 'LC_ALL=C '
    return ''

# some nasty chunk of code to solve path and url conversion and quoting issues
ILLEGAL_CHARS = '* | \ / : < > ? \t \n \x0b \x0c \r'.split(' ')
if os.sep in ILLEGAL_CHARS:
    ILLEGAL_CHARS.remove(os.sep)
ISWINDOWS = sys.platform == 'win32'
_reg_allow_disk = re.compile(r'^([a-z]\:\\)?[^:]+$', re.I)
def _check_path(path):
    illegal = ILLEGAL_CHARS[:]
    sp = path.strpath
    if ISWINDOWS:
        illegal.remove(':')
        if not _reg_allow_disk.match(sp):
            raise ValueError('path may not contain a colon (:)')
    for char in sp:
        if char not in string.printable or char in illegal:
            raise ValueError('illegal character %r in path' % (char,))

def path_to_fspath(path, addat=True):
    _check_path(path)
    sp = path.strpath
    if addat and path.rev != -1:
        sp = '%s@%s' % (sp, path.rev)
    elif addat:
        sp = '%s@HEAD' % (sp,)
    return sp
    
def url_from_path(path):
    fspath = path_to_fspath(path, False)
    quote = py.std.urllib.quote
    if ISWINDOWS:
        match = _reg_allow_disk.match(fspath)
        fspath = fspath.replace('\\', '/')
        if match.group(1):
            fspath = '/%s%s' % (match.group(1).replace('\\', '/'),
                                quote(fspath[len(match.group(1)):]))
        else:
            fspath = quote(fspath)
    else:
        fspath = quote(fspath)
    if path.rev != -1:
        fspath = '%s@%s' % (fspath, path.rev)
    else:
        fspath = '%s@HEAD' % (fspath,)
    return 'file://%s' % (fspath,)

class SvnAuth(object):
    """ container for auth information for Subversion """
    def __init__(self, username, password, cache_auth=True, interactive=True):
        self.username = username
        self.password = password
        self.cache_auth = cache_auth
        self.interactive = interactive

    def makecmdoptions(self):
        uname = self.username.replace('"', '\\"')
        passwd = self.password.replace('"', '\\"')
        ret = []
        if uname:
            ret.append('--username="%s"' % (uname,))
        if passwd:
            ret.append('--password="%s"' % (passwd,))
        if not self.cache_auth:
            ret.append('--no-auth-cache')
        if not self.interactive:
            ret.append('--non-interactive')
        return ' '.join(ret)

    def __str__(self):
        return "<SvnAuth username=%s ...>" %(self.username,)
