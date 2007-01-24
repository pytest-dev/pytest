"""

"""

import py
import sys

log = py.log.get("dynpkg", 
                 info=py.log.STDOUT, 
                 debug=py.log.STDOUT,
                 command=None) # py.log.STDOUT)

from distutils import util

class DistPython: 
    def __init__(self, location=None, python=None): 
        if python is None:
            python = py.std.sys.executable
        self.python = python
        if location is None:
            location = py.path.local()
        self.location = location 
        self.plat_specifier = '.%s-%s' % (util.get_platform(), sys.version[0:3])

    def clean(self):
        out = self._exec("clean -a")
        #print out

    def build(self):
        out = self._exec("build")
        #print out

    def _exec(self, cmd):
        python = self.python 
        old = self.location.chdir()
        try:
            cmd = "%(python)s setup.py %(cmd)s" % locals()
            log.command(cmd)
            out = py.process.cmdexec(cmd)
        finally:
            old.chdir()
        return out 

    def get_package_path(self, pkgname):
        pkg = self._get_package_path(pkgname) 
        if pkg is None:
            #self.clean()
            self.build()
            pkg = self._get_package_path(pkgname)
        assert pkg is not None 
        return pkg 

    def _get_package_path(self, pkgname):
        major, minor = py.std.sys.version_info[:2]
        #assert major >=2 and minor in (3,4,5)
        suffix = "%s.%s" %(major, minor)
        location = self.location
        for base in [location.join('build', 'lib'),
                     location.join('build', 'lib'+ self.plat_specifier)]:
            if base.check(dir=1):
                for pkg in base.visit(lambda x: x.check(dir=1)):
                    if pkg.basename == pkgname:
                        # 
                        if pkg.dirpath().basename ==  'lib'+ self.plat_specifier or \
                           pkg.dirpath().basename == 'lib':
                            return pkg

def setpkg(finalpkgname, distdir):
    assert distdir.check(dir=1)
    dist = DistPython(distdir) 
    pkg = dist.get_package_path(finalpkgname) 
    assert pkg.check(dir=1)
    sys.path.insert(0, str(pkg.dirpath()))
    try:
        modname = pkg.purebasename
        if modname in sys.modules:
            log.debug("removing from sys.modules:", modname)
            del sys.modules[modname]
        sys.modules[modname] = mod = __import__(modname) 
    finally: 
        sys.path[0] # XXX
    log.info("module is at", mod.__file__) 
    return mod 
 
