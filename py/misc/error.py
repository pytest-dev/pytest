
import py
import errno

class Error(EnvironmentError):
    __module__ = 'py.error'

    def __repr__(self):
        return "%s.%s %r: %s " %(self.__class__.__module__,
                               self.__class__.__name__,
                               self.__class__.__doc__,
                               " ".join(map(str, self.args)),
                               #repr(self.args)
                                )

    def __str__(self):
        return "[%s]: %s" %(self.__class__.__doc__,
                          " ".join(map(str, self.args)),
                          )

_winerrnomap = {
    2: errno.ENOENT, 
    3: errno.ENOENT, 
    17: errno.EEXIST,
    22: errno.ENOTDIR,
    267: errno.ENOTDIR,
    5: errno.EACCES,  # anything better?
}
# note: 'py.std' may not be imported yet at all, because 
# the 'error' module in this file is imported very early.
# This is dependent on dict order.

ModuleType = type(py)

class py_error(ModuleType):
    """ py.error lazily provides higher level Exception classes
        for each possible POSIX errno (as defined per
        the 'errno' module.  All such Exceptions derive
        from py.error.Error, which itself is a subclass
        of EnvironmentError.
    """
    Error = Error

    def _getwinerrnoclass(cls, eno): 
        return cls._geterrnoclass(_winerrnomap[eno]) 
    _getwinerrnoclass = classmethod(_getwinerrnoclass) 

    def _geterrnoclass(eno, _errno2class = {}):
        try:
            return _errno2class[eno]
        except KeyError:
            clsname = py.std.errno.errorcode.get(eno, "UnknownErrno%d" %(eno,))
            cls = type(Error)(clsname, (Error,),
                    {'__module__':'py.error',
                     '__doc__': py.std.os.strerror(eno)})
            _errno2class[eno] = cls
            return cls
    _geterrnoclass = staticmethod(_geterrnoclass)

    def __getattr__(self, name):
        eno = getattr(py.std.errno, name)
        cls = self._geterrnoclass(eno)
        setattr(self, name, cls)
        return cls

    def getdict(self, done=[]):
        try:
            return done[0]
        except IndexError:
            for name in py.std.errno.errorcode.values():
                hasattr(self, name)   # force attribute to be loaded, ignore errors
            dictdescr = ModuleType.__dict__['__dict__']
            done.append(dictdescr.__get__(self))
            return done[0]

    __dict__ = property(getdict)
    del getdict

error = py_error('py.error', py_error.__doc__)
