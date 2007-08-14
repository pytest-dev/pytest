"""
Collect test items at filesystem and python module levels. 

Collectors and test items form a tree.  The difference
between a collector and a test item as seen from the session 
is smalll.  Collectors usually return a list of child 
collectors/items whereas items usually return None 
indicating a successful test run.  

The is a schematic example of a tree of collectors and test items:: 

    Directory
        Module 
            Class 
                Instance   
                    Function  
                    Generator 
                        ... 
            Function 
            Generator 
                Function 
        Directory       
            ... 

""" 
from __future__ import generators 
import py
from py.__.test.outcome import Skipped

def configproperty(name):
    def fget(self):
        #print "retrieving %r property from %s" %(name, self.fspath)
        return self._config.getvalue(name, self.fspath) 
    return property(fget)

class Collector(object): 
    """ Collector instances are iteratively generated
        (through their run() and join() methods)
        and form a tree.  attributes::

        parent: attribute pointing to the parent collector
                (or None if it is the root collector)
        name:   basename of this collector object
    """
    def __init__(self, name, parent=None):
        self.name = name 
        self.parent = parent
        self._config = getattr(parent, '_config', py.test.config)
        self.fspath = getattr(parent, 'fspath', None) 

    Module = configproperty('Module')
    DoctestFile = configproperty('DoctestFile')
    Directory = configproperty('Directory')
    Class = configproperty('Class')
    Instance = configproperty('Instance')
    Function = configproperty('Function')
    Generator = configproperty('Generator')

    _stickyfailure = None

    def __repr__(self): 
        return "<%s %r>" %(self.__class__.__name__, self.name) 

    def __eq__(self, other): 
        # XXX a rather strict check for now to not confuse
        #     the SetupState.prepare() logic
        return self is other
    
    def __hash__(self):
        return hash((self.name, self.parent))
    
    def __ne__(self, other):
        return not self == other

    def __cmp__(self, other): 
        s1 = self._getsortvalue()
        s2 = other._getsortvalue()
        #print "cmp", s1, s2
        return cmp(s1, s2) 

   
    def run(self):
        """ returns a list of names available from this collector.
            You can return an empty list.  Callers of this method
            must take care to catch exceptions properly.  The session
            object guards its calls to ``colitem.run()`` in its
            ``session.runtraced(colitem)`` method, including
            catching of stdout.
        """
        raise NotImplementedError("abstract")

    def join(self, name):
        """  return a child item for the given name.  Usually the
             session feeds the join method with each name obtained
             from ``colitem.run()``.  If the return value is None
             it means the ``colitem`` was not able to resolve
             with the given name.
        """

    def obj(): 
        def fget(self):
            try: 
                return self._obj   
            except AttributeError: 
                self._obj = obj = self._getobj() 
                return obj 
        def fset(self, value): 
            self._obj = value 
        return property(fget, fset, None, "underlying object") 
    obj = obj()

    def _getobj(self):
        return getattr(self.parent.obj, self.name)

    def multijoin(self, namelist): 
        """ return a list of colitems for the given namelist. """ 
        return [self.join(name) for name in namelist]

    def _getpathlineno(self): 
        return self.fspath, py.std.sys.maxint 

    def setup(self): 
        pass 

    def teardown(self): 
        pass 

    def listchain(self): 
        """ return list of all parent collectors up to ourself. """ 
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
        if isinstance(namelist, str):
            namelist = namelist.split("/")
        cur = self
        for name in namelist:
            if name:
                next = cur.join(name)
                assert next is not None, (cur, name, namelist)
                cur = next
        return cur

    def _haskeyword(self, keyword): 
        return keyword in self.name

    def _getmodpath(self):
        """ return dotted module path (relative to the containing). """ 
        inmodule = False 
        newl = []
        for x in self.listchain(): 
            if not inmodule and not isinstance(x, Module): 
                continue
            if not inmodule:  
                inmodule = True
                continue
            if newl and x.name[:1] in '([': 
                newl[-1] += x.name 
            else: 
                newl.append(x.name) 
        return ".".join(newl) 

    def _skipbykeyword(self, keyword): 
        """ raise Skipped() exception if the given keyword 
            matches for this collector. 
        """
        if not keyword:
            return
        chain = self.listchain()
        for key in filter(None, keyword.split()): 
            eor = key[:1] == '-'
            if eor:
                key = key[1:]
            if not (eor ^ self._matchonekeyword(key, chain)):
                py.test.skip("test not selected by keyword %r" %(keyword,))

    def _matchonekeyword(self, key, chain): 
        for subitem in chain:
            if subitem._haskeyword(key): 
                return True 
        return False

    def _tryiter(self, yieldtype=None, reporterror=None, keyword=None):
        """ yield stop item instances from flattening the collector. 
            XXX deprecated: this way of iteration is not safe in all
            cases. 
        """ 
        if yieldtype is None: 
            yieldtype = py.test.collect.Item 
        if isinstance(self, yieldtype):
            try:
                self._skipbykeyword(keyword)
                yield self
            except Skipped:
                if reporterror is not None:
                    excinfo = py.code.ExceptionInfo()
                    reporterror((excinfo, self))
        else:
            if not isinstance(self, py.test.collect.Item):
                try:
                    if reporterror is not None:
                        reporterror((None, self))
                    for x in self.run(): 
                        for y in self.join(x)._tryiter(yieldtype, 
                                            reporterror, keyword): 
                            yield y
                except KeyboardInterrupt:
                    raise
                except: 
                    if reporterror is not None: 
                        excinfo = py.code.ExceptionInfo()
                        reporterror((excinfo, self)) 

    def _getsortvalue(self): 
        return self.name 

    _captured_out = _captured_err = None
    def startcapture(self): 
        return None # by default collectors don't capture output

    def finishcapture(self): 
        return None # by default collectors don't capture output

    def _getouterr(self): 
        return self._captured_out, self._captured_err

    def _get_collector_trail(self):
        """ Shortcut
        """
        return self._config.get_collector_trail(self)

class FSCollector(Collector): 
    def __init__(self, fspath, parent=None): 
        fspath = py.path.local(fspath) 
        super(FSCollector, self).__init__(fspath.basename, parent) 
        self.fspath = fspath 

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

    def run(self):
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
                Directory = py.test.config.getvalue('Directory', p) 
                res = Directory(p, parent=self) 
            name2items[name] = res 
        return res

class PyCollectorMixin(Collector): 
    def funcnamefilter(self, name): 
        return name.startswith('test') 
    def classnamefilter(self, name): 
        return name.startswith('Test')

    def _buildname2items(self): 
        # NB. we avoid random getattrs and peek in the __dict__ instead
        d = {}
        dicts = [getattr(self.obj, '__dict__', {})]
        for basecls in py.std.inspect.getmro(self.obj.__class__):
            dicts.append(basecls.__dict__)
        seen = {}
        for dic in dicts:
            for name, obj in dic.items():
                if name in seen:
                    continue
                seen[name] = True
                res = self.makeitem(name, obj)
                if res is not None:
                    d[name] = res 
        return d

    def makeitem(self, name, obj, usefilters=True):
        if (not usefilters or self.classnamefilter(name)) and \
            py.std.inspect.isclass(obj):
            return self.Class(name, parent=self)
        elif (not usefilters or self.funcnamefilter(name)) and callable(obj): 
            if obj.func_code.co_flags & 32: # generator function 
                return self.Generator(name, parent=self)
            else: 
                return self.Function(name, parent=self)

    def _prepare(self): 
        if not hasattr(self, '_name2items'): 
            ex = getattr(self, '_name2items_exception', None)
            if ex is not None: 
                raise ex[0], ex[1], ex[2]
            try: 
                self._name2items = self._buildname2items()
            except (SystemExit, KeyboardInterrupt): 
                raise 
            except:
                self._name2items_exception = py.std.sys.exc_info()
                raise

    def run(self): 
        self._prepare()
        itemlist = self._name2items.values()
        itemlist.sort()
        return [x.name for x in itemlist]

    def join(self, name): 
        self._prepare()
        return self._name2items.get(name, None) 


class Module(FSCollector, PyCollectorMixin):
    def run(self):
        if getattr(self.obj, 'disabled', 0):
            return []
        return super(Module, self).run()

    def join(self, name):
        res = super(Module, self).join(name)
        if res is None:
            attr = getattr(self.obj, name, None)
            if attr is not None:
                res = self.makeitem(name, attr, usefilters=False)
        return res
    
    def startcapture(self): 
        self._config._startcapture(self, path=self.fspath)

    def finishcapture(self): 
        self._config._finishcapture(self)

    def __repr__(self): 
        return "<%s %r>" % (self.__class__.__name__, self.name)

    def obj(self): 
        try: 
            return self._obj    
        except AttributeError:
            failure = getattr(self, '_stickyfailure', None)
            if failure is not None: 
                raise failure[0], failure[1], failure[2]
            try: 
                self._obj = obj = self.fspath.pyimport() 
            except KeyboardInterrupt: 
                raise
            except: 
                self._stickyfailure = py.std.sys.exc_info()
                raise 
            return obj 
    obj = property(obj, None, None, "module object")

    def setup(self): 
        if hasattr(self.obj, 'setup_module'): 
            self.obj.setup_module(self.obj) 

    def teardown(self): 
        if hasattr(self.obj, 'teardown_module'): 
            self.obj.teardown_module(self.obj) 


class Class(PyCollectorMixin, Collector): 

    def run(self): 
        if getattr(self.obj, 'disabled', 0):
            return []
        return ["()"]

    def join(self, name):
        assert name == '()'
        return self.Instance(name, self)

    def setup(self): 
        setup_class = getattr(self.obj, 'setup_class', None)
        if setup_class is not None: 
            setup_class = getattr(setup_class, 'im_func', setup_class) 
            setup_class(self.obj) 

    def teardown(self): 
        teardown_class = getattr(self.obj, 'teardown_class', None) 
        if teardown_class is not None: 
            teardown_class = getattr(teardown_class, 'im_func', teardown_class) 
            teardown_class(self.obj) 

    def _getsortvalue(self):
        # try to locate the class in the source - not nice, but probably
        # the most useful "solution" that we have
        try:
            file = (py.std.inspect.getsourcefile(self.obj) or
                    py.std.inspect.getfile(self.obj))
            if not file:
                raise IOError
            lines, lineno = py.std.inspect.findsource(self.obj)
            return py.path.local(file), lineno
        except IOError:
            pass
        # fall back...
        for x in self._tryiter((py.test.collect.Generator, py.test.collect.Item)):
            return x._getsortvalue()

class Instance(PyCollectorMixin, Collector): 
    def _getobj(self): 
        return self.parent.obj()  
    def Function(self): 
        return getattr(self.obj, 'Function', 
                       Collector.Function.__get__(self)) # XXX for python 2.2 
    Function = property(Function)


class FunctionMixin(object):
    """ mixin for the code common to Function and Generator.
    """
    def _getpathlineno(self):
        code = py.code.Code(self.obj) 
        return code.path, code.firstlineno 

    def _getsortvalue(self):  
        return self._getpathlineno() 

    def setup(self): 
        """ perform setup for this test function. """
        if getattr(self.obj, 'im_self', None): 
            name = 'setup_method' 
        else: 
            name = 'setup_function' 
        obj = self.parent.obj 
        meth = getattr(obj, name, None)
        if meth is not None: 
            return meth(self.obj) 

    def teardown(self): 
        """ perform teardown for this test function. """
        if getattr(self.obj, 'im_self', None): 
            name = 'teardown_method' 
        else: 
            name = 'teardown_function' 
        obj = self.parent.obj 
        meth = getattr(obj, name, None)
        if meth is not None: 
            return meth(self.obj) 

class Generator(FunctionMixin, PyCollectorMixin, Collector): 
    def run(self): 
        self._prepare()
        itemlist = self._name2items
        return [itemlist["[%d]" % num].name for num in xrange(len(itemlist))]
    
    def _buildname2items(self): 
        d = {} 
        # slightly hackish to invoke setup-states on
        # collection ...
        self.Function._state.prepare(self)
        for i, x in py.builtin.enumerate(self.obj()): 
            call, args = self.getcallargs(x)
            if not callable(call): 
                raise TypeError("yielded test %r not callable" %(call,))
            name = "[%d]" % i
            d[name] = self.Function(name, self, args, obj=call, sort_value = i)
        return d
        
    def getcallargs(self, obj):
        if isinstance(obj, (tuple, list)):
            call, args = obj[0], obj[1:]
        else:
            call, args = obj, ()
        return call, args 

class DoctestFile(PyCollectorMixin, FSCollector): 
    def run(self):
        return [self.fspath.basename]

    def join(self, name):
        from py.__.test.doctest import DoctestText
        if name == self.fspath.basename: 
            item = DoctestText(self.fspath.basename, parent=self)
            item._content = self.fspath.read()
            return item
