import py
defaultconftestpath = py.magic.autopath().dirpath('defaultconftest.py')

class Conftest(object):
    """ the single place for accessing values and interacting 
        towards conftest modules from py.test objects. 

        Note that triggering Conftest instances to import 
        conftest.py files may result in added cmdline options. 
        XXX
    """ 
    def __init__(self, path=None, onimport=None):
        self._path2confmods = {}
        self._onimport = onimport
        if path is not None:
            self.setinitial([path])

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
        for arg in args + [current]:
            anchor = current.join(arg, abs=1)
            if anchor.check(): # we found some file object 
                self._path2confmods[None] = self.getconftestmodules(anchor)
                break
        else:
            assert 0, "no root of filesystem?"

    def getconftestmodules(self, path):
        """ return a list of imported conftest modules for the given path.  """ 
        try:
            clist = self._path2confmods[path]
        except KeyError:
            if path is None:
                raise ValueError("missing default conftest.")
            dp = path.dirpath()
            if dp == path: 
                return [self.importconftest(defaultconftestpath)]
            clist = self.getconftestmodules(dp)
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
        raise KeyError, name

    def importconftest(self, conftestpath):
        # Using caching here looks redundant since ultimately
        # sys.modules caches already 
        assert conftestpath.check(), conftestpath
        if not conftestpath.dirpath('__init__.py').check(file=1): 
            # HACK: we don't want any "globally" imported conftest.py, 
            #       prone to conflicts and subtle problems 
            modname = str(conftestpath).replace('.', conftestpath.sep)
            mod = conftestpath.pyimport(modname=modname)
        else:
            mod = conftestpath.pyimport()
        if self._onimport:
            self._onimport(mod)
        return mod
