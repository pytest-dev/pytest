import py

class Stat(object):
    def __init__(self, path, osstatresult): 
        self.path = path 
        self._osstatresult = osstatresult

    for name in ('atime blksize blocks ctime dev gid ' 
                 'ino mode mtime nlink rdev size uid'.split()):
        
        code = """if 1:
            def fget(self):
                return getattr(self._osstatresult, "st_%(name)s", None)
            %(name)s = property(fget)
            def fget_deprecated(self):
                py.std.warnings.warn("statresult.st_%(name)s is deprecated, use "
                                     "statresult.%(name)s instead.", 
                                     DeprecationWarning, stacklevel=2)
                return getattr(self._osstatresult, "st_%(name)s", None)
            st_%(name)s = property(fget_deprecated)
""" % locals()
        exec code
    del fget 
    del fget_deprecated

