"""
module for win-specific local path stuff

(implementor needed :-)
"""

import os
import py
from py.__.path.local.common import Stat 

class WinMixin:
    def _makestat(self, statresult):
        return Stat(self, statresult)

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

    def remove(self, rec=1):
        """ remove a file or directory (or a directory tree if rec=1).  """
        if self.check(dir=1, link=0):
            if rec:
                # force remove of readonly files on windows 
                self.chmod(0700, rec=1)
                self._callex(py.std.shutil.rmtree, self.strpath)
            else:
                self._callex(os.rmdir, self.strpath)
        else:
            self.chmod(0700)
            self._callex(os.remove, self.strpath)
