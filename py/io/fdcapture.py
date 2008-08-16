
import os
import sys
import py
import tempfile

class FDCapture: 
    """ Capture IO to/from a given os-level filedescriptor. """
    
    def __init__(self, targetfd, tmpfile=None): 
        self.targetfd = targetfd
        if tmpfile is None: 
            tmpfile = self.maketmpfile()
        self.tmpfile = tmpfile 
        self._savefd = os.dup(targetfd)
        os.dup2(self.tmpfile.fileno(), targetfd) 
        self._patched = []

    def setasfile(self, name, module=sys): 
        """ patch <module>.<name> to self.tmpfile
        """
        key = (module, name)
        self._patched.append((key, getattr(module, name)))
        setattr(module, name, self.tmpfile) 

    def unsetfiles(self): 
        """ unpatch all patched items
        """
        while self._patched: 
            (module, name), value = self._patched.pop()
            setattr(module, name, value) 

    def done(self): 
        """ unpatch and clean up, returns the self.tmpfile (file object)
        """
        os.dup2(self._savefd, self.targetfd) 
        self.unsetfiles() 
        os.close(self._savefd) 
        self.tmpfile.seek(0)
        return self.tmpfile 

    def maketmpfile(self): 
        """ create a temporary file
        """
        f = tempfile.TemporaryFile()
        newf = py.io.dupfile(f) 
        f.close()
        return newf 

    def writeorg(self, str):
        """ write a string to the original file descriptor
        """
        tempfp = tempfile.TemporaryFile()
        try:
            os.dup2(self._savefd, tempfp.fileno())
            tempfp.write(str)
        finally:
            tempfp.close()

