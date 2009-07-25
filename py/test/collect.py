"""
base test collection objects.  
Collectors and test Items form a tree
that is usually built iteratively.  
""" 
import py
from py.__.test.outcome import Skipped

def configproperty(name):
    def fget(self):
        #print "retrieving %r property from %s" %(name, self.fspath)
        return self.config.getvalue(name, self.fspath) 
    return property(fget)

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
    def __init__(self, name, parent=None):
        self.name = name 
        self.parent = parent
        self.config = getattr(parent, 'config', None)
        self.fspath = getattr(parent, 'fspath', None) 

    # 
    # note to myself: Pickling is uh.
    # 
    def __getstate__(self):
        return (self.name, self.parent)
    def __setstate__(self, (name, parent)):
        try:
            colitems = parent._memocollect()
        except KeyboardInterrupt:
            raise
        except Exception:
            # seems our parent can't collect us 
            # so let's be somewhat operable 
            self.name = name 
            self.parent = parent 
            self.config = parent.config
            #self._obj = "could not unpickle" 
        else:
            for colitem in colitems:
                if colitem.name == name:
                    # we are a copy that will not be returned
                    # by our parent 
                    self.__dict__ = colitem.__dict__
                    break

    def __repr__(self): 
        if getattr(self.config.option, 'debug', False):
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
 
    def setup(self): 
        pass

    def teardown(self): 
        pass

    def _memoizedcall(self, attrname, function):
        exattrname = "_ex_" + attrname 
        failure = getattr(self, exattrname, None)
        if failure is not None:
            raise failure[0], failure[1], failure[2]
        if hasattr(self, attrname):
            return getattr(self, attrname)
        try:
            res = function()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            failure = py.std.sys.exc_info()
            setattr(self, exattrname, failure)
            raise
        setattr(self, attrname, res)
        return res 

    def listchain(self, rootfirst=False):
        """ return list of all parent collectors up to self, 
            starting form root of collection tree. """ 
        l = [self]
        while 1: 
            x = l[-1]
            if x.parent is not None: 
                l.append(x.parent) 
            else: 
                if not rootfirst:
                    l.reverse() 
                return l 

    def listnames(self): 
        return [x.name for x in self.listchain()]

    def getparent(self, cls):
        current = self
        while current and not isinstance(current, cls):
            current = current.parent
        return current 

    def _getitembynames(self, namelist):
        cur = self
        for name in namelist:
            if name:
                next = cur.collect_by_name(name)
                if next is None: 
                    existingnames = [x.name for x in self._memocollect()]
                    msg = ("Collector %r does not have name %r "
                           "existing names are: %s" %
                           (cur, name, existingnames))
                    raise AssertionError(msg) 
                cur = next
        return cur

    
    def _getfsnode(self, path):
        # this method is usually called from
        # config.getfsnode() which returns a colitem 
        # from filename arguments
        #
        # pytest's collector tree does not neccessarily 
        # follow the filesystem and we thus need to do 
        # some special matching code here because
        # _getitembynames() works by colitem names, not
        # basenames. 
        if path == self.fspath:
            return self 
        basenames = path.relto(self.fspath).split(path.sep)
        cur = self
        while basenames:
            basename = basenames.pop(0)
            assert basename
            fspath = cur.fspath.join(basename)
            colitems = cur._memocollect()
            l = []
            for colitem in colitems:
                if colitem.fspath == fspath or colitem.name == basename:
                    l.append(colitem)
            if not l:
                msg = ("Collector %r does not provide %r colitem "
                       "existing colitems are: %s" %
                       (cur, fspath, colitems))
                raise AssertionError(msg) 
            if basenames:
                if len(l) > 1:
                    msg = ("Collector %r has more than one %r colitem "
                           "existing colitems are: %s" %
                           (cur, fspath, colitems))
                    raise AssertionError(msg) 
                cur = l[0]
            else:
                if len(l) > 1:
                    cur = l
                else:
                    cur = l[0]
                break
        return cur 

    def readkeywords(self):
        return dict([(x, True) for x in self._keywords()])

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
        chain = [item.readkeywords() for item in chain if item._keywords()]
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

    def _prunetraceback(self, traceback):
        return traceback 

    def _totrail(self):
        """ provide a trail relative to the topdir, 
            which can be used to reconstruct the
            collector (possibly on a different host
            starting from a different topdir). 
        """ 
        chain = self.listchain()
        topdir = self.config.topdir 
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

    def _repr_failure_py(self, excinfo, outerr=None):
        assert outerr is None, "XXX deprecated"
        excinfo.traceback = self._prunetraceback(excinfo.traceback)
        # XXX temporary hack: getrepr() should not take a 'style' argument
        # at all; it should record all data in all cases, and the style
        # should be parametrized in toterminal().
        if self.config.option.tbstyle == "short":
            style = "short"
        else:
            style = "long"
        return excinfo.getrepr(funcargs=True, 
                               showlocals=self.config.option.showlocals,
                               style=style)

    repr_failure = _repr_failure_py
    shortfailurerepr = "F"

class Collector(Node):
    """ 
        Collector instances create children through collect()
        and thus iteratively build a tree.  attributes::

        parent: attribute pointing to the parent collector
                (or None if this is the root collector)
        name:   basename of this collector object
    """
    Directory = configproperty('Directory')
    Module = configproperty('Module')

    def collect(self):
        """ returns a list of children (items and collectors) 
            for this collection node. 
        """
        raise NotImplementedError("abstract")

    def collect_by_name(self, name):
        """ return a child matching the given name, else None. """
        for colitem in self._memocollect():
            if colitem.name == name:
                return colitem

    def repr_failure(self, excinfo, outerr=None):
        """ represent a failure. """
        assert outerr is None, "XXX deprecated"
        return self._repr_failure_py(excinfo)

    def _memocollect(self):
        """ internal helper method to cache results of calling collect(). """
        return self._memoizedcall('_collected', self.collect)

    # **********************************************************************
    # DEPRECATED METHODS 
    # **********************************************************************
    
    def _deprecated_collect(self):
        # avoid recursion:
        # collect -> _deprecated_collect -> custom run() ->
        # super().run() -> collect
        attrname = '_depcollectentered'
        if hasattr(self, attrname):
            return
        setattr(self, attrname, True)
        method = getattr(self.__class__, 'run', None)
        if method is not None and method != Collector.run:
            warnoldcollect(function=method)
            names = self.run()
            return filter(None, [self.join(name) for name in names])

    def run(self):
        """ DEPRECATED: returns a list of names available from this collector.
            You can return an empty list.  Callers of this method
            must take care to catch exceptions properly.  
        """
        return [colitem.name for colitem in self._memocollect()]

    def join(self, name): 
        """  DEPRECATED: return a child collector or item for the given name.  
             If the return value is None there is no such child. 
        """
        return self.collect_by_name(name)

class FSCollector(Collector): 
    def __init__(self, fspath, parent=None):
        fspath = py.path.local(fspath) 
        super(FSCollector, self).__init__(fspath.basename, parent)
        self.fspath = fspath 

    def __getstate__(self):
        if self.parent is None:
            # the root node needs to pickle more context info 
            topdir = self.config.topdir
            relpath = self.fspath.relto(topdir)
            if not relpath:
                if self.fspath == topdir:
                    relpath = "."
                else:
                    raise ValueError("%r not relative to topdir %s" 
                            %(self.fspath, topdir))
            return (self.name, self.config, relpath)
        else:
            return (self.name, self.parent)

    def __setstate__(self, picklestate):
        if len(picklestate) == 3:
            # root node
            name, config, relpath = picklestate
            fspath = config.topdir.join(relpath)
            fsnode = config.getfsnode(fspath)
            self.__dict__.update(fsnode.__dict__)
        else:
            name, parent = picklestate
            self.__init__(parent.fspath.join(name), parent=parent)

class File(FSCollector):
    """ base class for collecting tests from a file. """

class Directory(FSCollector): 
    def recfilter(self, path): 
        if path.check(dir=1, dotfile=0):
            return path.basename not in ('CVS', '_darcs', '{arch}')

    def collect(self):
        l = self._deprecated_collect() 
        if l is not None:
            return l 
        l = []
        for path in self.fspath.listdir(sort=True): 
            res = self.consider(path)
            if res is not None:
                if isinstance(res, (list, tuple)):
                    l.extend(res)
                else:
                    l.append(res)
        return l

    def _ignore(self, path):
        ignore_paths = self.config.getconftest_pathlist("collect_ignore", path=path)
        return ignore_paths and path in ignore_paths 

    def consider(self, path):
        if self._ignore(path):
            return
        if path.check(file=1):
            res = self.consider_file(path)
        elif path.check(dir=1):
            res = self.consider_dir(path)
        else:
            res = None            
        if isinstance(res, list):
            # throw out identical results
            l = []
            for x in res:
                if x not in l:
                    assert x.parent == self, "wrong collection tree construction"
                    l.append(x)
            res = l 
        return res

    def consider_file(self, path):
        return self.config.hook.pytest_collect_file(path=path, parent=self)

    def consider_dir(self, path, usefilters=None):
        if usefilters is not None:
            py.log._apiwarn("0.99", "usefilters argument not needed")
        return self.config.hook.pytest_collect_directory(
            path=path, parent=self)

class Item(Node): 
    """ a basic test item. """
    def _deprecated_testexecution(self):
        if self.__class__.run != Item.run:
            warnoldtestrun(function=self.run)
        elif self.__class__.execute != Item.execute:
            warnoldtestrun(function=self.execute)
        else:
            return False
        self.run()
        return True

    def run(self):
        """ deprecated, here because subclasses might call it. """
        return self.execute(self.obj)

    def execute(self, obj):
        """ deprecated, here because subclasses might call it. """
        return obj()

    def reportinfo(self):
        return self.fspath, None, ""
        
def warnoldcollect(function=None):
    py.log._apiwarn("1.0", 
        "implement collector.collect() instead of "
        "collector.run() and collector.join()",
        stacklevel=2, function=function)

def warnoldtestrun(function=None):
    py.log._apiwarn("1.0", 
        "implement item.runtest() instead of "
        "item.run() and item.execute()",
        stacklevel=2, function=function)
