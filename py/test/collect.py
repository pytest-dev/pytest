"""
Collect test items at filesystem and python module levels. 

Collectors and test items form a tree.  The difference
between a collector and a test item as seen from the session 
is smalll.  Collectors usually return a list of child 
collectors/items whereas items usually return None 
indicating a successful test run.  

The is a schematic example of a tree of collectors and test items:: 

    Directory
        Directory 
            CustomCollector  # provided via conftest's 
                CustomItem   # provided via conftest's
                CustomItem   # provided via conftest's
        Directory       
            ... 

""" 
import py

def configproperty(name):
    def fget(self):
        #print "retrieving %r property from %s" %(name, self.fspath)
        return self._config.getvalue(name, self.fspath) 
    return property(fget)

class SetupState(object):
    """ shared state for setting up/tearing down test items or collectors. """
    def __init__(self):
        self.stack = []

    def teardown_all(self): 
        while self.stack: 
            col = self.stack.pop() 
            col.teardown() 

    def teardown_exact(self, item):
        if self.stack and self.stack[-1] == item:
            col = self.stack.pop()
            col.teardown()
     
    def prepare(self, colitem): 
        """ setup objects along the collector chain to the test-method
            Teardown any unneccessary previously setup objects."""

        needed_collectors = colitem.listchain() 
        while self.stack: 
            if self.stack == needed_collectors[:len(self.stack)]: 
                break 
            col = self.stack.pop() 
            col.teardown()
        for col in needed_collectors[len(self.stack):]: 
            #print "setting up", col
            col.setup() 
            self.stack.append(col) 

class ReprMetaInfo(object):
    def __init__(self, fspath=None, lineno=None, modpath=None):
        self.fspath = fspath
        self.lineno = lineno 
        self.modpath = modpath

    def verboseline(self, basedir=None):
        params = self.__dict__.copy()
        if self.fspath:
            if basedir is not None:
                params['fspath'] = getrelpath(basedir, self.fspath)
        if self.lineno is not None:
            params['lineno'] = self.lineno + 1

        if self.fspath and self.lineno and self.modpath:
            line = "%(fspath)s:%(lineno)s: %(modpath)s"
        elif self.fspath and self.modpath:
            line = "%(fspath)s: %(modpath)s"
        elif self.fspath and self.lineno:
            line = "%(fspath)s:%(lineno)s"
        else:
            line = "[nometainfo]"
        return line % params
        

class Node(object): 
    """ base class for Nodes in the collection tree.  
        Collector nodes have children and 
        Item nodes are terminal. 

        All nodes of the collection tree carry a _config 
        attribute for these reasons: 
        - to access custom Collection Nodes from a project 
          (defined in conftest's)
        - to pickle themselves relatively to the "topdir" 
        - configuration/options for setup/teardown 
          stdout/stderr capturing and execution of test items 
    """
    ReprMetaInfo = ReprMetaInfo
    # XXX we keep global SetupState here because 
    #     pycollect's Generators participate 
    #     in setup/teardown procedures during collect. 
    _setupstate = SetupState() 
    def __init__(self, name, parent=None, config=None):
        self.name = name 
        self.parent = parent
        if config is None:
            config = getattr(parent, '_config')
        self._config = config 
        self.fspath = getattr(parent, 'fspath', None) 

    # 
    # note to myself: Pickling is uh.
    # 
    def __getstate__(self):
        return (self.name, self.parent)
    def __setstate__(self, (name, parent)):
        newnode = parent.join(name)
        if newnode is None:
            raise AssertionError(self, name, parent, parent.__dict__)
        self.__dict__.update(newnode.__dict__)
        #self.__init__(name=name, parent=parent)

    def __repr__(self): 
        if self._config.option.debug:
            return "<%s %r %0x>" %(self.__class__.__name__, 
                getattr(self, 'name', None), id(self))
        else:
            return "<%s %r>" %(self.__class__.__name__, 
                getattr(self, 'name', None))

    # methods for ordering nodes

    def __eq__(self, other): 
        if not isinstance(other, Node):
            return False 
        return self.name == other.name and self.parent == other.parent 

    def __ne__(self, other):
        return not self == other
    
    def __hash__(self):
        return hash((self.name, self.parent))

    def __cmp__(self, other): 
        if not isinstance(other, Node):
            return -1
        s1 = self._getsortvalue()
        s2 = other._getsortvalue()
        return cmp(s1, s2) 
 
    def setup(self): 
        pass

    def teardown(self): 
        pass

    def listchain(self): 
        """ return list of all parent collectors up to self. """ 
        l = [self]
        while 1: 
            x = l[-1]
            if x.parent is not None: 
                l.append(x.parent) 
            else: 
                l.reverse() 
                return l 

    def listnames(self): 
        return [x.name for x in self.listchain()]

    def _getitembynames(self, namelist):
        cur = self
        for name in namelist:
            if name:
                next = cur.join(name)
                if next is None: 
                    existingnames = cur.listdir()
                    msg = ("Collector %r does not have name %r "
                           "existing names are: %s" %
                           (cur, name, existingnames))
                    raise AssertionError(msg) 
                cur = next
        return cur

    def _keywords(self):
        return [self.name]

    def _skipbykeyword(self, keywordexpr): 
        """ return True if they given keyword expression means to 
            skip this collector/item. 
        """
        if not keywordexpr:
            return
        chain = self.listchain()
        for key in filter(None, keywordexpr.split()):
            eor = key[:1] == '-'
            if eor:
                key = key[1:]
            if not (eor ^ self._matchonekeyword(key, chain)):
                return True

    def _matchonekeyword(self, key, chain):
        elems = key.split(".")
        # XXX O(n^2), anyone cares?
        chain = [item._keywords() for item in chain if item._keywords()]
        for start, _ in enumerate(chain):
            if start + len(elems) > len(chain):
                return False
            for num, elem in enumerate(elems):
                for keyword in chain[num + start]:
                    ok = False
                    if elem in keyword:
                        ok = True
                        break
                if not ok:
                    break
            if num == len(elems) - 1 and ok:
                return True
        return False

    def _getsortvalue(self): 
        return self.name 

    def _prunetraceback(self, traceback):
        return traceback 

    def _totrail(self):
        """ provide a trail relative to the topdir, 
            which can be used to reconstruct the
            collector (possibly on a different host
            starting from a different topdir). 
        """ 
        chain = self.listchain()
        topdir = self._config.topdir 
        relpath = chain[0].fspath.relto(topdir)
        if not relpath:
            if chain[0].fspath == topdir:
                relpath = "."
            else:
                raise ValueError("%r not relative to topdir %s" 
                         %(chain[0].fspath, topdir))
        return relpath, tuple([x.name for x in chain[1:]])

    def _fromtrail(trail, config):
        relpath, names = trail
        fspath = config.topdir.join(relpath)
        col = config.getfsnode(fspath)
        return col._getitembynames(names)
    _fromtrail = staticmethod(_fromtrail)

    def _repr_failure_py(self, excinfo, outerr):
        excinfo.traceback = self._prunetraceback(excinfo.traceback)
        repr = excinfo.getrepr(funcargs=True, 
                               showlocals=self._config.option.showlocals)
        for secname, content in zip(["out", "err"], outerr):
            if content:
                repr.addsection("Captured std%s" % secname, content.rstrip())
        return repr 

    repr_failure = _repr_failure_py

    shortfailurerepr = "F"

class Collector(Node):
    """ 
        Collector instances generate children through 
        their listdir() and join() methods and thus 
        form a tree.  attributes::

        parent: attribute pointing to the parent collector
                (or None if this is the root collector)
        name:   basename of this collector object
    """
    Directory = configproperty('Directory')
    Module = configproperty('Module')
    DoctestFile = configproperty('DoctestFile')

    def run(self):
        """ deprecated: use listdir(). """
        py.std.warnings.warn("deprecated: use listdir()", category=DeprecationWarning)
        return self.listdir()

    def multijoin(self, namelist): 
        """ return a list of colitems for the given namelist. """ 
        return [self.join(name) for name in namelist]

    def listdir(self):
        """ returns a list of names available from this collector.
            You can return an empty list.  Callers of this method
            must take care to catch exceptions properly.  
        """
        raise NotImplementedError("abstract")

    def join(self, name):
        """  return a child collector or item for the given name.  
             If the return value is None there is no such child. 
        """
        raise NotImplementedError("abstract")

    def repr_failure(self, excinfo, outerr):
        return self._repr_failure_py(excinfo, outerr)

class FSCollector(Collector): 
    def __init__(self, fspath, parent=None, config=None): 
        fspath = py.path.local(fspath) 
        super(FSCollector, self).__init__(fspath.basename, parent, config=config) 
        self.fspath = fspath 

    def __getstate__(self):
        if self.parent is None:
            # the root node needs to pickle more context info 
            topdir = self._config.topdir
            relpath = self.fspath.relto(topdir)
            if not relpath:
                if self.fspath == topdir:
                    relpath = "."
                else:
                    raise ValueError("%r not relative to topdir %s" 
                            %(self.fspath, topdir))
            return (self.name, self._config, relpath)
        else:
            return (self.name, self.parent)

    def __setstate__(self, picklestate):
        if len(picklestate) == 3:
            # root node
            name, config, relpath = picklestate
            if not config._initialized:
                raise ValueError("incomplete unpickling of "
                  "config object, need call to _initafterpickle()?")
            fspath = config.topdir.join(relpath)
            fsnode = config.getfsnode(fspath)
            self.__dict__.update(fsnode.__dict__)
        else:
            name, parent = picklestate
            self.__init__(parent.fspath.join(name), parent=parent)


class Directory(FSCollector): 
    def filefilter(self, path): 
        if path.check(file=1):
            b = path.purebasename 
            ext = path.ext
            return (b.startswith('test_') or 
                    b.endswith('_test')) and ext in ('.txt', '.py')
    
    def recfilter(self, path): 
        if path.check(dir=1, dotfile=0):
            return path.basename not in ('CVS', '_darcs', '{arch}')

    def listdir(self):
        files = []
        dirs = []
        for p in self.fspath.listdir():
            if self.filefilter(p):
                files.append(p.basename)
            elif self.recfilter(p):
                dirs.append(p.basename) 
        files.sort()
        dirs.sort()
        return files + dirs

    def join(self, name):
        name2items = self.__dict__.setdefault('_name2items', {})
        try:
            res = name2items[name]
        except KeyError:
            p = self.fspath.join(name)
            res = None
            if p.check(file=1): 
                if p.ext == '.py':
                    res = self.Module(p, parent=self) 
                elif p.ext == '.txt':
                    res = self.DoctestFile(p, parent=self)
            elif p.check(dir=1): 
                # not use self.Directory here as 
                # dir/conftest.py shall be able to 
                # define Directory(dir) already 
                Directory = self._config.getvalue('Directory', p) 
                res = Directory(p, parent=self) 
            name2items[name] = res 
        return res

from py.__.test.runner import basic_run_report, forked_run_report
class Item(Node): 
    """ a basic test item. """
    def _getrunner(self):
        if self._config.option.boxed:
            return forked_run_report
        return basic_run_report

    def repr_metainfo(self):
        try:
            return self.ReprMetaInfo(self.fspath, modpath=self.__class__.__name__)
        except AttributeError:
            code = py.code.Code(self.execute)
            return self.ReprMetaInfo(code.path, code.firstlineno)
      
    def execute(self):
        """ execute this test item."""
        
        
def getrelpath(curdir, dest): 
    try:
        base = curdir.common(dest)
        if not base:  # can be the case on windows
            return dest
        curdir2base = curdir.relto(base)
        reldest = dest.relto(base)
        if curdir2base:
            n = curdir2base.count(curdir.sep) + 1
        else:
            n = 0
        l = ['..'] * n
        if reldest:
            l.append(reldest)     
        target = dest.sep.join(l)
        return target 
    except AttributeError:
        return dest
