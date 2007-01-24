"""
module to access local filesystem pathes
(mostly filename manipulations but also file operations)
"""
import os, sys, stat

import py
#__________________________________________________________
#
# Local Path Posix Mixin
#__________________________________________________________

from py.__.path.local.common import Stat 

class PosixStat(Stat):
    def owner(self):
        entry = self.path._callex(py.std.pwd.getpwuid, self.uid)
        return entry[0]
    owner = property(owner, None, None, "owner of path") 

    def group(self):
        """ return group name of file. """
        entry = self.path._callex(py.std.grp.getgrgid, self.gid)
        return entry[0]
    group = property(group) 

class PosixMixin(object):
    def _makestat(self, statresult): 
        return PosixStat(self, statresult) 

    def _deprecated(self, name): 
        py.std.warnings.warn("'path.%s()' is deprecated, use "
                             "'path.stat().%s' instead." % (name,name),
                             DeprecationWarning, stacklevel=3)
    
    # an instance needs to be a local path instance
    def owner(self):
        """ return owner name of file. """
        self._deprecated('owner')
        return self.stat().owner 

    def group(self):
        """ return group name of file. """
        self._deprecated('group')
        return self.stat().group 

    def mode(self):
        """ return permission mode of the path object """
        self._deprecated('mode')
        return self.stat().mode

    def chmod(self, mode, rec=0):
        """ change permissions to the given mode. If mode is an
            integer it directly encodes the os-specific modes.
            if rec is True perform recursively.

            (xxx if mode is a string then it specifies access rights
            in '/bin/chmod' style, e.g. a+r).
        """
        if not isinstance(mode, int):
            raise TypeError("mode %r must be an integer" % (mode,))
        if rec:
            for x in self.visit(rec=rec):
                self._callex(os.chmod, str(x), mode)
        self._callex(os.chmod, str(self), mode)

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
                    self._callex(os.chown, str(x), uid, gid)
        self._callex(os.chown, str(self), uid, gid)

    def readlink(self):
        """ return value of a symbolic link. """
        return self._callex(os.readlink, self.strpath)

    def mklinkto(self, oldname):
        """ posix style hard link to another name. """
        self._callex(os.link, str(oldname), str(self))

    def mksymlinkto(self, value, absolute=1):
        """ create a symbolic link with the given value (pointing to another name). """
        if absolute:
            self._callex(os.symlink, str(value), self.strpath)
        else:
            base = self.common(value)
            # with posix local paths '/' is always a common base
            relsource = self.__class__(value).relto(base)
            reldest = self.relto(base)
            n = reldest.count(self.sep)
            target = self.sep.join(('..', )*n + (relsource, ))
            self._callex(os.symlink, target, self.strpath)


    def remove(self, rec=1):
        """ remove a file or directory (or a directory tree if rec=1).  """
        if self.check(dir=1, link=0):
            if rec:
                self._callex(py.std.shutil.rmtree, self.strpath)
            else:
                self._callex(os.rmdir, self.strpath)
        else:
            self._callex(os.remove, self.strpath)


def getuserid(user):
    import pwd
    if isinstance(user, int):
        return user
    entry = pwd.getpwnam(user)
    return entry[2]

def getgroupid(group):
    import grp
    if isinstance(group, int):
        return group
    entry = grp.getgrnam(group)
    return entry[2]
