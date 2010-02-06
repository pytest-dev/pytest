import py

class Conftest(object):
    """ the single place for accessing values and interacting 
        towards conftest modules from py.test objects. 

        (deprecated)
        Note that triggering Conftest instances to import 
        conftest.py files may result in added cmdline options. 
    """ 
    def __init__(self, onimport=None, confcutdir=None):
        self._path2confmods = {}
        self._onimport = onimport
        self._conftestpath2mod = {}
        self._confcutdir = confcutdir

    def setinitial(self, args):
        """ try to find a first anchor path for looking up global values
            from conftests. This function is usually called _before_  
            argument parsing.  conftest files may add command line options
            and we thus have no completely safe way of determining
            which parts of the arguments are actually related to options
            and which are file system paths.  We just try here to get 
            bootstrapped ... 
        """
        current = py.path.local()
        opt = '--confcutdir'
        for i in range(len(args)):
            opt1 = str(args[i])
            if opt1.startswith(opt):
                if opt1 == opt:
                    if len(args) > i:
                        p = current.join(args[i+1], abs=True)
                elif opt1.startswith(opt + "="):
                    p = current.join(opt1[len(opt)+1:], abs=1)
                self._confcutdir = p 
                break
        for arg in args + [current]:
            anchor = current.join(arg, abs=1)
            if anchor.check(): # we found some file object 
                self._path2confmods[None] = self.getconftestmodules(anchor)
                # let's also consider test* dirs 
                if anchor.check(dir=1):
                    for x in anchor.listdir(lambda x: x.check(dir=1, dotfile=0)):
                        self.getconftestmodules(x)
                break
        else:
            assert 0, "no root of filesystem?"

    def getconftestmodules(self, path):
        """ return a list of imported conftest modules for the given path.  """ 
        try:
            clist = self._path2confmods[path]
        except KeyError:
            if path is None:
                raise ValueError("missing default confest.")
            dp = path.dirpath()
            if dp == path:
                clist = []
            else:
                cutdir = self._confcutdir
                clist = self.getconftestmodules(dp)
                if cutdir and path != cutdir and not path.relto(cutdir):
                    pass
                else:
                    conftestpath = path.join("conftest.py")
                    if conftestpath.check(file=1):
                        clist.append(self.importconftest(conftestpath))
            self._path2confmods[path] = clist
        # be defensive: avoid changes from caller side to
        # affect us by always returning a copy of the actual list 
        return clist[:]

    def rget(self, name, path=None):
        mod, value = self.rget_with_confmod(name, path)
        return value

    def rget_with_confmod(self, name, path=None):
        modules = self.getconftestmodules(path)
        modules.reverse()
        for mod in modules:
            try:
                return mod, getattr(mod, name)
            except AttributeError:
                continue
        raise KeyError(name)

    def importconftest(self, conftestpath):
        assert conftestpath.check(), conftestpath
        try:
            return self._conftestpath2mod[conftestpath]
        except KeyError:
            if not conftestpath.dirpath('__init__.py').check(file=1): 
                # HACK: we don't want any "globally" imported conftest.py, 
                #       prone to conflicts and subtle problems 
                modname = str(conftestpath).replace('.', conftestpath.sep)
                mod = conftestpath.pyimport(modname=modname)
            else:
                mod = conftestpath.pyimport()
            self._conftestpath2mod[conftestpath] = mod
            dirpath = conftestpath.dirpath()
            if dirpath in self._path2confmods:
                for path, mods in self._path2confmods.items():
                    if path and path.relto(dirpath) or path == dirpath:
                        assert mod not in mods
                        mods.append(mod)
            self._postimport(mod)
            return mod

    def _postimport(self, mod):
        if self._onimport:
            self._onimport(mod)
        return mod
