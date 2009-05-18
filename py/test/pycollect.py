"""
Python related collection nodes.  Here is an example of 
a tree of collectors and test items that this modules provides:: 

        Module                  # File
            Class 
                Instance   
                    Function  
                    Generator 
                        ... 
            Function 
            Generator 
                Function 

        DoctestFile              # File
            DoctestFileContent   # acts as Item 

""" 
import py
from py.__.test.collect import configproperty, warnoldcollect
pydir = py.path.local(py.__file__).dirpath()
from py.__.test import funcargs

class PyobjMixin(object):
    def obj(): 
        def fget(self):
            try: 
                return self._obj   
            except AttributeError: 
                self._obj = obj = self._getobj() 
                return obj 
        def fset(self, value): 
            self._obj = value 
        return property(fget, fset, None, "underlying python object") 
    obj = obj()

    def _getobj(self):
        return getattr(self.parent.obj, self.name)

    def _getparent(self, cls):
        current = self
        while current and not isinstance(current, cls):
            current = current.parent
        return current 

    def getmodpath(self, stopatmodule=True, includemodule=False):
        """ return python path relative to the containing module. """
        chain = self.listchain()
        chain.reverse()
        parts = []
        for node in chain:
            if isinstance(node, Instance):
                continue
            name = node.name 
            if isinstance(node, Module):
                assert name.endswith(".py")
                name = name[:-3]
                if stopatmodule:
                    if includemodule:
                        parts.append(name)
                    break
            parts.append(name)
        parts.reverse()
        s = ".".join(parts)
        return s.replace(".[", "[")

    def _getfslineno(self):
        try:
            return self._fslineno
        except AttributeError:
            pass
        obj = self.obj
        # xxx let decorators etc specify a sane ordering
        if hasattr(obj, 'place_as'):
            obj = obj.place_as

        self._fslineno = py.code.getfslineno(obj)
        return self._fslineno

    def reportinfo(self):
        fspath, lineno = self._getfslineno()
        modpath = self.getmodpath()
        return fspath, lineno, modpath 

class PyCollectorMixin(PyobjMixin, py.test.collect.Collector): 
    Class = configproperty('Class')
    Instance = configproperty('Instance')
    Function = configproperty('Function')
    Generator = configproperty('Generator')
    
    def funcnamefilter(self, name): 
        return name.startswith('test') 
    def classnamefilter(self, name): 
        return name.startswith('Test')

    def collect(self):
        l = self._deprecated_collect()
        if l is not None:
            return l
        name2items = self._buildname2items()
        colitems = name2items.values()
        colitems.sort()
        return colitems

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

    def _deprecated_join(self, name):
        if self.__class__.join != py.test.collect.Collector.join:
            warnoldcollect()
            return self.join(name)

    def makeitem(self, name, obj):
        res = self.config.hook.pytest_pycollect_obj(
            collector=self, name=name, obj=obj)
        if res:
            return res
        if (self.classnamefilter(name)) and \
            py.std.inspect.isclass(obj):
            res = self._deprecated_join(name)
            if res is not None:
                return res 
            return self.Class(name, parent=self)
        elif self.funcnamefilter(name) and callable(obj): 
            res = self._deprecated_join(name)
            if res is not None:
                return res 
            if obj.func_code.co_flags & 32: # generator function 
                # XXX deprecation warning 
                return self.Generator(name, parent=self)
            else: 
                return self._genfunctions(name, obj)

    def _genfunctions(self, name, funcobj):
        module = self._getparent(Module).obj
        # due to _buildname2items funcobj is the raw function, we need
        # to work to get at the class 
        clscol = self._getparent(Class)
        cls = clscol and clscol.obj or None
        metafunc = funcargs.Metafunc(funcobj, config=self.config, cls=cls, module=module)
        gentesthook = self.config.hook.pytest_generate_tests.clone(extralookup=module)
        gentesthook(metafunc=metafunc)
        if not metafunc._calls:
            return self.Function(name, parent=self)
        return funcargs.FunctionCollector(name=name, 
            parent=self, calls=metafunc._calls)
        
class Module(py.test.collect.File, PyCollectorMixin):
    def _getobj(self):
        return self._memoizedcall('_obj', self._importtestmodule)

    def _importtestmodule(self):
        # we assume we are only called once per module 
        mod = self.fspath.pyimport()
        #print "imported test module", mod
        self.config.pluginmanager.consider_module(mod)
        return mod

    def setup(self): 
        if getattr(self.obj, 'disabled', 0):
            py.test.skip("%r is disabled" %(self.obj,))
        if not self.config.option.nomagic:
            #print "*" * 20, "INVOKE assertion", self
            py.magic.invoke(assertion=1)
        mod = self.obj
        #self.config.pluginmanager.register(mod)
        if hasattr(mod, 'setup_module'): 
            self.obj.setup_module(mod)

    def teardown(self): 
        if hasattr(self.obj, 'teardown_module'): 
            self.obj.teardown_module(self.obj) 
        if not self.config.option.nomagic:
            #print "*" * 20, "revoke assertion", self
            py.magic.revoke(assertion=1)
        #self.config.pluginmanager.unregister(self.obj)

class Class(PyCollectorMixin, py.test.collect.Collector): 

    def collect(self):
        l = self._deprecated_collect()
        if l is not None:
            return l
        return [self.Instance(name="()", parent=self)]

    def setup(self): 
        if getattr(self.obj, 'disabled', 0):
            py.test.skip("%r is disabled" %(self.obj,))
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
        return self._getfslineno()

class Instance(PyCollectorMixin, py.test.collect.Collector): 
    def _getobj(self): 
        return self.parent.obj()  
    def Function(self): 
        return getattr(self.obj, 'Function', 
                       PyCollectorMixin.Function.__get__(self)) # XXX for python 2.2
    def _keywords(self):
        return []
    Function = property(Function)

    #def __repr__(self):
    #    return "<%s of '%s'>" %(self.__class__.__name__, 
    #                         self.parent.obj.__name__)

    def newinstance(self):  
        self.obj = self._getobj()
        return self.obj

class FunctionMixin(PyobjMixin):
    """ mixin for the code common to Function and Generator.
    """

    def _getsortvalue(self):  
        return self._getfslineno()

    def setup(self): 
        """ perform setup for this test function. """
        if hasattr(self.obj, 'im_self'):
            name = 'setup_method' 
        else: 
            name = 'setup_function' 
        if isinstance(self.parent, Instance):
            obj = self.parent.newinstance()
            self.obj = self._getobj()
        else:
            obj = self.parent.obj 
        setup_func_or_method = getattr(obj, name, None)
        if setup_func_or_method is not None: 
            setup_func_or_method(self.obj) 

    def teardown(self): 
        """ perform teardown for this test function. """
        if hasattr(self.obj, 'im_self'):
            name = 'teardown_method' 
        else: 
            name = 'teardown_function' 
        obj = self.parent.obj 
        teardown_func_or_meth = getattr(obj, name, None)
        if teardown_func_or_meth is not None: 
            teardown_func_or_meth(self.obj) 

    def _prunetraceback(self, traceback):
        if hasattr(self, '_obj') and not self.config.option.fulltrace: 
            code = py.code.Code(self.obj) 
            path, firstlineno = code.path, code.firstlineno 
            ntraceback = traceback.cut(path=path, firstlineno=firstlineno)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(path=path)
                if ntraceback == traceback:
                    ntraceback = ntraceback.cut(excludepath=pydir)
            traceback = ntraceback.filter()
        return traceback 

    def repr_failure(self, excinfo, outerr):
        return self._repr_failure_py(excinfo, outerr)

    shortfailurerepr = "F"

class Generator(FunctionMixin, PyCollectorMixin, py.test.collect.Collector): 
    def collect(self):
        # test generators are seen as collectors but they also 
        # invoke setup/teardown on popular request 
        # (induced by the common "test_*" naming shared with normal tests)
        self.config._setupstate.prepare(self) 
        l = []
        seen = {}
        for i, x in py.builtin.enumerate(self.obj()): 
            name, call, args = self.getcallargs(x)
            if not callable(call): 
                raise TypeError("%r yielded non callable test %r" %(self.obj, call,))
            if name is None:
                name = "[%d]" % i
            else:
                name = "['%s']" % name
            if name in seen:
                raise ValueError("%r generated tests with non-unique name %r" %(self, name))
            seen[name] = True
            l.append(self.Function(name, self, args=args, callobj=call))
        return l
        
    def getcallargs(self, obj):
        if not isinstance(obj, (tuple, list)):
            obj = (obj,)
        # explict naming
        if isinstance(obj[0], basestring):
            name = obj[0]
            obj = obj[1:]
        else:
            name = None
        call, args = obj[0], obj[1:]
        return name, call, args 
    

#
#  Test Items 
#
_dummy = object()
class Function(FunctionMixin, py.test.collect.Item): 
    """ a Function Item is responsible for setting up  
        and executing a Python callable test object.
    """
    def __init__(self, name, parent=None, config=None, args=(), 
                 callspec=None, callobj=_dummy):
        super(Function, self).__init__(name, parent, config=config) 
        self._args = args 
        if args:
            assert not callspec, "yielded functions (deprecated) cannot have funcargs" 
        else:
            self.funcargs = callspec and callspec.funcargs or {}
            if hasattr(callspec, "param"):
                self._requestparam = callspec.param
        if callobj is not _dummy: 
            self._obj = callobj 

    #def addfinalizer(self, func):
    #    self.config._setupstate.ddfinalizer(func, colitem=self)
        
    def readkeywords(self):
        d = super(Function, self).readkeywords()
        d.update(self.obj.func_dict)
        return d

    def runtest(self):
        """ execute the given test function. """
        kwargs = getattr(self, 'funcargs', {})
        self.config.hook.pytest_pyfunc_call(
            pyfuncitem=self, args=self._args, kwargs=kwargs)

    def setup(self):
        super(Function, self).setup()
        if hasattr(self, 'funcargs'): 
            funcargs.fillfuncargs(self)

    def __eq__(self, other):
        try:
            return (self.name == other.name and 
                    self._args == other._args and
                    self.parent == other.parent and
                    self.obj == other.obj and 
                    getattr(self, '_requestparam', None) == 
                    getattr(other, '_requestparam', None) 
            )
        except AttributeError:
            pass
        return False

    def __ne__(self, other):
        return not self == other

