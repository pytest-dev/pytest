"""
test collection nodes, forming a tree, Items are leafs.
""" 
import py

def configproperty(name):
    def fget(self):
        #print "retrieving %r property from %s" %(name, self.fspath)
        return self.config._getcollectclass(name, self.fspath)
    return property(fget)

class HookProxy:
    def __init__(self, node):
        self.node = node
    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError(name)
        hookmethod = getattr(self.node.config.hook, name)
        def call_matching_hooks(**kwargs):
            plugins = self.node.config._getmatchingplugins(self.node.fspath)
            return hookmethod.pcall(plugins, **kwargs)
        return call_matching_hooks

class Node(object): 
    """ base class for all Nodes in the collection tree.  
        Collector subclasses have children, Items are terminal nodes. 
    """
    def __init__(self, name, parent=None, config=None):
        self.name = name 
        self.parent = parent
        self.config = config or parent.config
        self.fspath = getattr(parent, 'fspath', None) 
        self.ihook = HookProxy(self)

    def _reraiseunpicklingproblem(self):
        if hasattr(self, '_unpickle_exc'):
            py.builtin._reraise(*self._unpickle_exc)
            
    # 
    # note to myself: Pickling is uh.
    # 
    def __getstate__(self):
        return (self.name, self.parent)
    def __setstate__(self, nameparent):
        name, parent = nameparent
        try:
            colitems = parent._memocollect()
            for colitem in colitems:
                if colitem.name == name:
                    # we are a copy that will not be returned
                    # by our parent 
                    self.__dict__ = colitem.__dict__
                    break
            else:
                raise ValueError("item %r not found in parent collection %r" %(
                    name, [x.name for x in colitems]))
        except KeyboardInterrupt:
            raise
        except Exception:
            # our parent can't collect us but we want unpickling to
            # otherwise continue - self._reraiseunpicklingproblem() will
            # reraise the problem 
            self._unpickle_exc = py.std.sys.exc_info()
            self.name = name 
            self.parent = parent 
            self.config = parent.config

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
            py.builtin._reraise(failure[0], failure[1], failure[2])
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

    def listchain(self):
        """ return list of all parent collectors up to self, 
            starting from root of collection tree. """ 
        l = [self]
        while 1: 
            x = l[0]
            if x.parent is not None and x.parent.parent is not None:
                l.insert(0, x.parent)
            else: 
                return l 

    def listnames(self): 
        return [x.name for x in self.listchain()]

    def getparent(self, cls):
        current = self
        while current and not isinstance(current, cls):
            current = current.parent
        return current 
    
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

    def _repr_failure_py(self, excinfo):
        excinfo.traceback = self._prunetraceback(excinfo.traceback)
        # XXX should excinfo.getrepr record all data and toterminal()
        # process it? 
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
            return [x for x in [self.join(name) for name in names] if x]

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

    def _prunetraceback(self, traceback):
        if hasattr(self, 'fspath'):
            path = self.fspath 
            ntraceback = traceback.cut(path=self.fspath)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(excludepath=py._pydir)
            traceback = ntraceback.filter()
        return traceback 

class FSCollector(Collector): 
    def __init__(self, fspath, parent=None, config=None):
        fspath = py.path.local(fspath) 
        super(FSCollector, self).__init__(fspath.basename, parent, config=config)
        self.fspath = fspath 

    def __getstate__(self):
        # RootCollector.getbynames() inserts a directory which we need
        # to throw out here for proper re-instantiation
        if isinstance(self.parent.parent, RootCollector):
            assert self.parent.fspath == self.parent.parent.fspath, self.parent
            return (self.name, self.parent.parent) # shortcut
        return super(Collector, self).__getstate__()

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

    def consider(self, path):
        if self.ihook.pytest_ignore_collect(path=path, config=self.config):
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
                    assert x.parent == self, (x.parent, self)
                    assert x.fspath == path, (x.fspath, path)
                    l.append(x)
            res = l 
        return res

    def consider_file(self, path):
        return self.ihook.pytest_collect_file(path=path, parent=self)

    def consider_dir(self, path, usefilters=None):
        if usefilters is not None:
            py.log._apiwarn("0.99", "usefilters argument not needed")
        return self.ihook.pytest_collect_directory(path=path, parent=self)

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


    
class RootCollector(Directory):
    def __init__(self, config):
        Directory.__init__(self, config.topdir, parent=None, config=config)
        self.name = None

    def __repr__(self):
        return "<RootCollector fspath=%r>" %(self.fspath,)
        
    def getbynames(self, names):
        current = self.consider(self.config.topdir)
        while names:
            name = names.pop(0)
            if name == ".": # special "identity" name
                continue 
            l = []
            for x in current._memocollect():
                if x.name == name:
                    l.append(x)
                elif x.fspath == current.fspath.join(name):
                    l.append(x)
                elif x.name == "()":
                    names.insert(0, name)
                    l.append(x)
                    break
            if not l:
                raise ValueError("no node named %r below %r" %(name, current))
            current = l[0]
        return current

    def totrail(self, node):
        chain = node.listchain()
        names = [self._getrelpath(chain[0].fspath)] 
        names += [x.name for x in chain[1:]]
        return names

    def fromtrail(self, trail):
        return self.config._rootcol.getbynames(trail)

    def _getrelpath(self, fspath):
        topdir = self.config.topdir
        relpath = fspath.relto(topdir)
        if not relpath:
            if fspath == topdir:
                relpath = "."
            else:
                raise ValueError("%r not relative to topdir %s" 
                        %(self.fspath, topdir))
        return relpath

    def __getstate__(self):
        return self.config

    def __setstate__(self, config):
        self.__init__(config)
