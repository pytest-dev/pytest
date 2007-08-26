"""

svn-Command based Implementation of a Subversion WorkingCopy Path.

  SvnWCCommandPath  is the main class.

  SvnWC is an alias to this class.

"""

import os, sys, time, re, calendar
import py
from py.__.path import common
from py.__.path.svn import cache
from py.__.path.svn import svncommon

DEBUG = 0

rex_blame = re.compile(r'\s*(\d+)\s*(\S+) (.*)')

class SvnWCCommandPath(common.FSPathBase):
    """ path implementation offering access/modification to svn working copies.
        It has methods similar to the functions in os.path and similar to the
        commands of the svn client.
    """
    sep = os.sep

    def __new__(cls, wcpath=None):
        self = object.__new__(cls)
        if isinstance(wcpath, cls):
            if wcpath.__class__ == cls:
                return wcpath
            wcpath = wcpath.localpath
        if svncommon._check_for_bad_chars(str(wcpath),
                                          svncommon.ALLOWED_CHARS):
            raise ValueError("bad char in wcpath %s" % (wcpath, ))
        self.localpath = py.path.local(wcpath)
        return self

    strpath = property(lambda x: str(x.localpath), None, None, "string path")

    def __eq__(self, other):
        return self.localpath == getattr(other, 'localpath', None)

    def _geturl(self):
        if getattr(self, '_url', None) is None:
            info = self.info()
            self._url = info.url #SvnPath(info.url, info.rev)
        assert isinstance(self._url, str)
        return self._url

    url = property(_geturl, None, None, "url of this WC item")

    def _escape(self, cmd):
        return svncommon._escape_helper(cmd)

    def dump(self, obj):
        """ pickle object into path location"""
        return self.localpath.dump(obj)

    def svnurl(self):
        """ return current SvnPath for this WC-item. """
        info = self.info()
        return py.path.svnurl(info.url)


    def __repr__(self):
        return "svnwc(%r)" % (self.strpath) # , self._url)

    def __str__(self):
        return str(self.localpath)

    def _svn(self, cmd, *args):
        l = ['svn %s' % cmd]
        args = [self._escape(item) for item in args]
        l.extend(args)
        l.append('"%s"' % self._escape(self.strpath))
        # try fixing the locale because we can't otherwise parse
        string = svncommon.fixlocale() + " ".join(l)
        if DEBUG:
            print "execing", string
        try:
            try:
                key = 'LC_MESSAGES'
                hold = os.environ.get(key)
                os.environ[key] = 'C'
                out = py.process.cmdexec(string)
            finally:
                if hold:
                    os.environ[key] = hold
                else:
                    del os.environ[key]
        except py.process.cmdexec.Error, e:
            strerr = e.err.lower()
            if strerr.find('file not found') != -1: 
                raise py.error.ENOENT(self) 
            if (strerr.find('file exists') != -1 or 
                strerr.find('file already exists') != -1 or
                strerr.find("can't create directory") != -1):
                raise py.error.EEXIST(self)
            raise
        return out

    def switch(self, url): 
        """ switch to given URL. """
        self._svn('switch', url)

    def checkout(self, url=None, rev=None):
        """ checkout from url to local wcpath. """
        args = []
        if url is None:
            url = self.url
        if rev is None or rev == -1:
            if (py.std.sys.platform != 'win32' and
                    svncommon._getsvnversion() == '1.3'):
                url += "@HEAD" 
        else:
            if svncommon._getsvnversion() == '1.3':
                url += "@%d" % rev
            else:
                args.append('-r', str(rev))
        self._svn('co', url, *args)

    def update(self, rev = 'HEAD'):
        """ update working copy item to given revision. (None -> HEAD). """
        self._svn('up -r %s' % rev)

    def write(self, content, mode='wb'):
        """ write content into local filesystem wc. """
        self.localpath.write(content, mode)

    def dirpath(self, *args):
        """ return the directory Path of the current Path. """
        return self.__class__(self.localpath.dirpath(*args))

    def _ensuredirs(self):
        parent = self.dirpath()
        if parent.check(dir=0):
            parent._ensuredirs()
        if self.check(dir=0):
            self.mkdir()
        return self

    def ensure(self, *args, **kwargs):
        """ ensure that an args-joined path exists (by default as
            a file). if you specify a keyword argument 'directory=True'
            then the path is forced  to be a directory path.
        """
        try:
            p = self.join(*args)
            if p.check():
                if p.check(versioned=False):
                    p.add()
                return p 
            if kwargs.get('dir', 0):
                return p._ensuredirs()
            parent = p.dirpath()
            parent._ensuredirs()
            p.write("")
            p.add()
            return p
        except:
            error_enhance(sys.exc_info())

    def mkdir(self, *args):
        """ create & return the directory joined with args. """
        if args:
            return self.join(*args).mkdir()
        else:
            self._svn('mkdir')
            return self

    def add(self):
        """ add ourself to svn """
        self._svn('add')

    def remove(self, rec=1, force=1):
        """ remove a file or a directory tree. 'rec'ursive is
            ignored and considered always true (because of
            underlying svn semantics.
        """
        assert rec, "svn cannot remove non-recursively"
        if not self.check(versioned=True):
            # not added to svn (anymore?), just remove
            py.path.local(self).remove()
            return
        flags = []
        if force:
            flags.append('--force')
        self._svn('remove', *flags)

    def copy(self, target):
        """ copy path to target."""
        py.process.cmdexec("svn copy %s %s" %(str(self), str(target)))

    def rename(self, target):
        """ rename this path to target. """
        py.process.cmdexec("svn move --force %s %s" %(str(self), str(target)))

    _rex_status = re.compile(r'\s+(\d+|-)\s+(\S+)\s+(\S+)\s+(.*)')

    def lock(self):
        """ set a lock (exclusive) on the resource """
        out = self._svn('lock').strip()
        if not out:
            # warning or error, raise exception
            raise Exception(out[4:])
    
    def unlock(self):
        """ unset a previously set lock """
        out = self._svn('unlock').strip()
        if out.startswith('svn:'):
            # warning or error, raise exception
            raise Exception(out[4:])

    def cleanup(self):
        """ remove any locks from the resource """
        # XXX should be fixed properly!!!
        try:
            self.unlock()
        except:
            pass

    def status(self, updates=0, rec=0, externals=0):
        """ return (collective) Status object for this file. """
        # http://svnbook.red-bean.com/book.html#svn-ch-3-sect-4.3.1
        #             2201     2192        jum   test
        # XXX
        if externals:
            raise ValueError("XXX cannot perform status() "
                             "on external items yet")
        else:
            #1.2 supports: externals = '--ignore-externals'
            externals = ''
        if rec:
            rec= ''
        else:
            rec = '--non-recursive'

        # XXX does not work on all subversion versions
        #if not externals: 
        #    externals = '--ignore-externals' 

        if updates:
            updates = '-u'
        else:
            updates = ''

        update_rev = None

        out = self._svn('status -v %s %s %s' % (updates, rec, externals))
        rootstatus = WCStatus(self)
        for line in out.split('\n'):
            if not line.strip():
                continue
            #print "processing %r" % line
            flags, rest = line[:8], line[8:]
            # first column
            c0,c1,c2,c3,c4,c5,x6,c7 = flags
            #if '*' in line:
            #    print "flags", repr(flags), "rest", repr(rest)

            if c0 in '?XI':
                fn = line.split(None, 1)[1]
                if c0 == '?':
                    wcpath = self.join(fn, abs=1)
                    rootstatus.unknown.append(wcpath)
                elif c0 == 'X':
                    wcpath = self.__class__(self.localpath.join(fn, abs=1))
                    rootstatus.external.append(wcpath)
                elif c0 == 'I':
                    wcpath = self.join(fn, abs=1)
                    rootstatus.ignored.append(wcpath)

                continue

            #elif c0 in '~!' or c4 == 'S':
            #    raise NotImplementedError("received flag %r" % c0)

            m = self._rex_status.match(rest)
            if not m:
                if c7 == '*':
                    fn = rest.strip()
                    wcpath = self.join(fn, abs=1)
                    rootstatus.update_available.append(wcpath)
                    continue
                if line.lower().find('against revision:')!=-1:
                    update_rev = int(rest.split(':')[1].strip())
                    continue
                # keep trying
                raise ValueError, "could not parse line %r" % line
            else:
                rev, modrev, author, fn = m.groups()
            wcpath = self.join(fn, abs=1)
            #assert wcpath.check()
            if c0 == 'M':
                assert wcpath.check(file=1), "didn't expect a directory with changed content here"
                rootstatus.modified.append(wcpath)
            elif c0 == 'A' or c3 == '+' :
                rootstatus.added.append(wcpath)
            elif c0 == 'D':
                rootstatus.deleted.append(wcpath)
            elif c0 == 'C':
                rootstatus.conflict.append(wcpath)
            elif c0 == '~':
                rootstatus.kindmismatch.append(wcpath)
            elif c0 == '!':
                rootstatus.incomplete.append(wcpath)
            elif not c0.strip():
                rootstatus.unchanged.append(wcpath)
            else:
                raise NotImplementedError("received flag %r" % c0)

            if c1 == 'M':
                rootstatus.prop_modified.append(wcpath)
            # XXX do we cover all client versions here?
            if c2 == 'L' or c5 == 'K':
                rootstatus.locked.append(wcpath)
            if c7 == '*':
                rootstatus.update_available.append(wcpath)

            if wcpath == self:
                rootstatus.rev = rev
                rootstatus.modrev = modrev
                rootstatus.author = author
                if update_rev:
                    rootstatus.update_rev = update_rev
                continue
        return rootstatus

    def diff(self, rev=None):
        """ return a diff of the current path against revision rev (defaulting
            to the last one).
        """
        if rev is None:
            out = self._svn('diff')
        else:
            out = self._svn('diff -r %d' % rev)
        return out

    def blame(self):
        """ return a list of tuples of three elements:
(revision, commiter, line)"""
        out = self._svn('blame')
        result = []
        blamelines = out.splitlines()
        reallines = py.path.svnurl(self.url).readlines()
        for i, (blameline, line) in py.builtin.enumerate(
                zip(blamelines, reallines)):
            m = rex_blame.match(blameline)
            if not m:
                raise ValueError("output line %r of svn blame does not match "
                                 "expected format" % (line, ))
            rev, name, _ = m.groups()
            result.append((int(rev), name, line))
        return result

    _rex_commit = re.compile(r'.*Committed revision (\d+)\.$', re.DOTALL)
    def commit(self, msg='', rec=1):
        """ commit with support for non-recursive commits """
        from py.__.path.svn import cache
        # XXX i guess escaping should be done better here?!?
        cmd = 'commit -m "%s" --force-log' % (msg.replace('"', '\\"'),)
        if not rec:
            cmd += ' -N'
        out = self._svn(cmd)
        try:
            del cache.info[self]
        except KeyError:
            pass
        if out: 
            m = self._rex_commit.match(out)
            return int(m.group(1))

    def propset(self, name, value, *args):
        """ set property name to value on this path. """
        d = py.path.local.mkdtemp() 
        try: 
            p = d.join('value') 
            p.write(value) 
            self._svn('propset', name, '--file', str(p), *args)
        finally: 
            d.remove() 

    def propget(self, name):
        """ get property name on this path. """
        res = self._svn('propget', name)
        return res[:-1] # strip trailing newline

    def propdel(self, name):
        """ delete property name on this path. """
        res = self._svn('propdel', name)
        return res[:-1] # strip trailing newline

    def proplist(self, rec=0):
        """ return a mapping of property names to property values.
If rec is True, then return a dictionary mapping sub-paths to such mappings.
"""
        if rec:
            res = self._svn('proplist -R')
            return make_recursive_propdict(self, res)
        else:
            res = self._svn('proplist')
            lines = res.split('\n')
            lines = map(str.strip, lines[1:])
            return svncommon.PropListDict(self, lines)

    def revert(self, rec=0):
        """ revert the local changes of this path. if rec is True, do so
recursively. """
        if rec:
            result = self._svn('revert -R')
        else:
            result = self._svn('revert')
        return result

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
        if kw:
            localpath = self.localpath.new(**kw)
        else:
            localpath = self.localpath
        return self.__class__(localpath)

    def join(self, *args, **kwargs):
        """ return a new Path (with the same revision) which is composed
            of the self Path followed by 'args' path components.
        """
        if not args:
            return self
        localpath = self.localpath.join(*args, **kwargs)
        return self.__class__(localpath)

    def info(self, usecache=1):
        """ return an Info structure with svn-provided information. """
        info = usecache and cache.info.get(self)
        if not info:
            try:
                output = self._svn('info')
            except py.process.cmdexec.Error, e:
                if e.err.find('Path is not a working copy directory') != -1:
                    raise py.error.ENOENT(self, e.err)
                raise
            # XXX SVN 1.3 has output on stderr instead of stdout (while it does
            # return 0!), so a bit nasty, but we assume no output is output
            # to stderr...
            if (output.strip() == '' or 
                    output.lower().find('not a versioned resource') != -1):
                raise py.error.ENOENT(self, output)
            info = InfoSvnWCCommand(output)

            # Can't reliably compare on Windows without access to win32api
            if py.std.sys.platform != 'win32': 
                if info.path != self.localpath: 
                    raise py.error.ENOENT(self, "not a versioned resource:" + 
                            " %s != %s" % (info.path, self.localpath)) 
            cache.info[self] = info
        self.rev = info.rev
        return info

    def listdir(self, fil=None, sort=None):
        """ return a sequence of Paths.

        listdir will return either a tuple or a list of paths
        depending on implementation choices.
        """
        if isinstance(fil, str):
            fil = common.fnmatch(fil)
        # XXX unify argument naming with LocalPath.listdir
        def notsvn(path):
            return path.basename != '.svn' 

        paths = []
        for localpath in self.localpath.listdir(notsvn):
            p = self.__class__(localpath)
            paths.append(p)

        if fil or sort:
            paths = filter(fil, paths)
            paths = isinstance(paths, list) and paths or list(paths)
            if callable(sort):
                paths.sort(sort)
            elif sort:
                paths.sort()
        return paths

    def open(self, mode='r'):
        """ return an opened file with the given mode. """
        return open(self.strpath, mode)

    def _getbyspec(self, spec):
        return self.localpath._getbyspec(spec)

    class Checkers(py.path.local.Checkers):
        def __init__(self, path):
            self.svnwcpath = path
            self.path = path.localpath
        def versioned(self):
            try:
                s = self.svnwcpath.info()
            except (py.error.ENOENT, py.error.EEXIST): 
                return False 
            except py.process.cmdexec.Error, e:
                if e.err.find('is not a working copy')!=-1:
                    return False
                raise
            else:
                return True 

    def log(self, rev_start=None, rev_end=1, verbose=False):
        """ return a list of LogEntry instances for this path.
rev_start is the starting revision (defaulting to the first one).
rev_end is the last revision (defaulting to HEAD).
if verbose is True, then the LogEntry instances also know which files changed.
"""
        from py.__.path.svn.urlcommand import _Head, LogEntry
        assert self.check()   # make it simpler for the pipe
        rev_start = rev_start is None and _Head or rev_start
        rev_end = rev_end is None and _Head or rev_end

        if rev_start is _Head and rev_end == 1:
                rev_opt = ""
        else:
            rev_opt = "-r %s:%s" % (rev_start, rev_end)
        verbose_opt = verbose and "-v" or ""
        s = svncommon.fixlocale()
        # some blather on stderr
        stdin, stdout, stderr  = os.popen3(s + 'svn log --xml %s %s "%s"' % (
                                           rev_opt, verbose_opt,
                                           self.strpath))
        from xml.dom import minidom
        from xml.parsers.expat import ExpatError
        try:
            tree = minidom.parse(stdout)
        except ExpatError:
            # XXX not entirely sure about this exception... shouldn't it be
            # some py.error.* something?
            raise ValueError('no such revision')
        result = []
        for logentry in filter(None, tree.firstChild.childNodes):
            if logentry.nodeType == logentry.ELEMENT_NODE:
                result.append(LogEntry(logentry))
        return result

    def size(self):
        """ Return the size of the file content of the Path. """
        return self.info().size

    def mtime(self):
        """ Return the last modification time of the file. """
        return self.info().mtime

    def __hash__(self):
        return hash((self.strpath, self.__class__))


class WCStatus:
    attrnames = ('modified','added', 'conflict', 'unchanged', 'external',
                'deleted', 'prop_modified', 'unknown', 'update_available',
                'incomplete', 'kindmismatch', 'ignored', 'locked'
                )

    def __init__(self, wcpath, rev=None, modrev=None, author=None):
        self.wcpath = wcpath
        self.rev = rev
        self.modrev = modrev
        self.author = author

        for name in self.attrnames:
            setattr(self, name, [])

    def allpath(self, sort=True, **kw):
        d = {}
        for name in self.attrnames:
            if name not in kw or kw[name]:
                for path in getattr(self, name):
                    d[path] = 1
        l = d.keys()
        if sort:
            l.sort()
        return l

class InfoSvnWCCommand:
    def __init__(self, output):
        # Path: test
        # URL: http://codespeak.net/svn/std.path/trunk/dist/std.path/test
        # Repository UUID: fd0d7bf2-dfb6-0310-8d31-b7ecfe96aada
        # Revision: 2151
        # Node Kind: directory
        # Schedule: normal
        # Last Changed Author: hpk
        # Last Changed Rev: 2100
        # Last Changed Date: 2003-10-27 20:43:14 +0100 (Mon, 27 Oct 2003)
        # Properties Last Updated: 2003-11-03 14:47:48 +0100 (Mon, 03 Nov 2003)

        d = {}
        for line in output.split('\n'):
            if not line.strip():
                continue
            key, value = line.split(':', 1)
            key = key.lower().replace(' ', '')
            value = value.strip()
            d[key] = value
        try:
            self.url = d['url']
        except KeyError:
            raise  ValueError, "Not a versioned resource"
            #raise ValueError, "Not a versioned resource %r" % path
        self.kind = d['nodekind'] == 'directory' and 'dir' or d['nodekind']
        self.rev = int(d['revision'])
        self.path = py.path.local(d['path'])
        self.size = self.path.size()
        if 'lastchangedrev' in d:
            self.created_rev = int(d['lastchangedrev'])
        if 'lastchangedauthor' in d:
            self.last_author = d['lastchangedauthor']
        if 'lastchangeddate' in d:
            self.mtime = parse_wcinfotime(d['lastchangeddate'])
            self.time = self.mtime * 1000000

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

def parse_wcinfotime(timestr):
    """ Returns seconds since epoch, UTC. """
    # example: 2003-10-27 20:43:14 +0100 (Mon, 27 Oct 2003)
    m = re.match(r'(\d+-\d+-\d+ \d+:\d+:\d+) ([+-]\d+) .*', timestr)
    if not m:
        raise ValueError, "timestring %r does not match" % timestr
    timestr, timezone = m.groups()
    # do not handle timezone specially, return value should be UTC
    parsedtime = time.strptime(timestr, "%Y-%m-%d %H:%M:%S")
    return calendar.timegm(parsedtime)

def make_recursive_propdict(wcroot,
                            output,
                            rex = re.compile("Properties on '(.*)':")):
    """ Return a dictionary of path->PropListDict mappings. """
    lines = filter(None, output.split('\n'))
    pdict = {}
    while lines:
        line = lines.pop(0)
        m = rex.match(line)
        if not m:
            raise ValueError, "could not parse propget-line: %r" % line
        path = m.groups()[0]
        wcpath = wcroot.join(path, abs=1)
        propnames = []
        while lines and lines[0].startswith('  '):
            propname = lines.pop(0).strip()
            propnames.append(propname)
        assert propnames, "must have found properties!"
        pdict[wcpath] = svncommon.PropListDict(wcpath, propnames)
    return pdict

def error_enhance((cls, error, tb)):
    raise cls, error, tb

