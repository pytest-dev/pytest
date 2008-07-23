import py
import sys, os, re
from distutils import sysconfig
from distutils import core 

winextensions = 1
if sys.platform == 'win32':
    try:
        import _winreg, win32gui, win32con
    except ImportError:
        winextensions = 0

class Params: 
    """ a crazy hack to convince distutils to please 
        install all of our files inside the package. 
    """
    _sitepackages = py.path.local(sysconfig.get_python_lib()) 
    def __init__(self, pkgmod): 
        name = pkgmod.__name__ 
        self._pkgdir = py.path.local(pkgmod.__file__).dirpath()
        self._rootdir = self._pkgdir.dirpath()
        self._pkgtarget = self._sitepackages.join(name) 
        self._datadict = {}
        self.packages = []
        self.scripts = []
        self.hacktree() 
        self.data_files = self._datadict.items() 
        self.data_files.sort() 
        self.packages.sort()
        self.scripts.sort()

    def hacktree(self): 
        for p in self._pkgdir.visit(None, lambda x: x.basename != '.svn'): 
            if p.check(file=1): 
                if p.ext in ('.pyc', '.pyo'): 
                    continue
                if p.dirpath().basename == 'bin': 
                    self.scripts.append(p.relto(self._rootdir))
                    self.adddatafile(p)
                elif p.ext == '.py': 
                    self.addpythonfile(p) 
                else: 
                    self.adddatafile(p)
            #else: 
            #    if not p.listdir(): 
            #        self.adddatafile(p.ensure('dummy'))

    def adddatafile(self, p): 
        if p.ext in ('.pyc', 'pyo'): 
            return
        target = self._pkgtarget.join(p.dirpath().relto(self._pkgdir))
        l = self._datadict.setdefault(str(target), [])
        l.append(p.relto(self._rootdir))

    def addpythonfile(self, p): 
        parts = p.parts() 
        for above in p.parts(reverse=True)[1:]: 
            if self._pkgdir.relto(above): 
                dottedname = p.dirpath().relto(self._rootdir).replace(p.sep, '.')
                if dottedname not in self.packages: 
                    self.packages.append(dottedname) 
                break 
            if not above.join('__init__.py').check(): 
                self.adddatafile(p)
                #print "warning, added data file", p
                break 

#if sys.platform != 'win32': 
#    scripts.remove('py/bin/pytest.cmd') 
#else: 
#    scripts.remove('py/bin/py.test') 
#

### helpers: 
def checknonsvndir(p): 
    if p.basename != '.svn' and p.check(dir=1): 
        return True

def dump(params): 
    print "packages"
    for x in params.packages: 
        print "package ", x
    print 
    print "scripts"
    for x in params.scripts: 
        print "script  ", x
    print 

    print "data files"
    for x in params.data_files: 
        print "data file   ", x
    print 

def addbindir2path():
    if sys.platform != 'win32' or not winextensions:
        return
    
    # Add py/bin to PATH environment variable
    bindir = os.path.join(sysconfig.get_python_lib(), "py", "bin", "win32")
    
    # check for the user path
    ureg = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)
    ukey = r"Environment"
    
    # not every user has his own path on windows
    try:
        upath = get_registry_value(ureg, ukey, "PATH")
    except WindowsError:
        upath=""
    # if bindir allready in userpath -> do nothing
    if bindir in upath: 
        return
    
    reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
    key = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    path = get_registry_value(reg, key, "Path")
    # if bindir allready in systempath -> do nothing
    if bindir in path:
        return 
    path += ";" + bindir
    print "Setting PATH to:", path
    
    pathset=False
    try:
        set_registry_value(reg, key, "PATH", path)
        pathset=True
    except WindowsError:
        print "cannot set systempath, falling back to userpath"
        pass
    
    if not pathset:
        try:
            if len(upath)>0: #if no user path present
                upath += ";" 
            upath+=bindir
            set_registry_value(ureg, ukey, "Path", upath)
            pathset=True
        except WindowsError:
            print "cannot set userpath, please add %s to your path" % (bindir,)
            return
            
    #print "Current PATH is:", get_registry_value(reg, key, "Path")

    # Propagate changes throughout the system
    win32gui.SendMessageTimeout(win32con.HWND_BROADCAST,
        win32con.WM_SETTINGCHANGE, 0, "Environment",
        win32con.SMTO_ABORTIFHUNG, 5000)

    # Propagate changes to current command prompt
    os.system("set PATH=%s" % path)
    
def get_registry_value(reg, key, value_name):
    k = _winreg.OpenKey(reg, key)
    value = _winreg.QueryValueEx(k, value_name)[0]
    _winreg.CloseKey(k)
    return value
  
def set_registry_value(reg, key, value_name, value):
    k = _winreg.OpenKey(reg, key, 0, _winreg.KEY_WRITE)
    value_type = _winreg.REG_SZ
    # if we handle the Path value, then set its type to REG_EXPAND_SZ
    # so that things like %SystemRoot% get automatically expanded by the
    # command prompt
    if value_name == "Path":
        value_type = _winreg.REG_EXPAND_SZ
    _winreg.SetValueEx(k, value_name, 0, value_type, value)
    _winreg.CloseKey(k)

### end helpers

def setup(pkg, **kw): 
    """ invoke distutils on a given package. 
    """
    if 'install' in sys.argv[1:]:
        print "precompiling greenlet module" 
        try:
            x = py.magic.greenlet()
        except (RuntimeError, ImportError):
            print "could not precompile greenlet module, skipping"

    params = Params(pkg)
    #dump(params)
    source = getattr(pkg, '__pkg__', pkg)
    namelist = list(core.setup_keywords)
    namelist.extend(['packages', 'scripts', 'data_files'])
    for name in namelist: 
        for ns in (source, params): 
            if hasattr(ns, name): 
                kw[name] = getattr(ns, name) 
                break 

    #script_args = sys.argv[1:]
    #if 'install' in script_args: 
    #    script_args = ['--quiet'] + script_args 
    #    #print "installing", py 
    #py.std.pprint.pprint(kw)
    core.setup(**kw)
    if 'install' in sys.argv[1:]:
        addbindir2path()
        x = params._rootdir.join('build')
        if x.check(): 
            print "removing", x
            x.remove()
