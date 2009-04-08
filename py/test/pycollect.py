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
from py.__.code.source import findsource
pydir = py.path.local(py.__file__).dirpath()

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

    def getfslineno(self):
        try:
            return self._fslineno
        except AttributeError:
            pass
        obj = self.obj
        # let decorators etc specify a sane ordering
        if hasattr(obj, 'place_as'):
            obj = obj.place_as
        try:
            code = py.code.Code(obj)
        except TypeError:
            # fallback to 
            fn = (py.std.inspect.getsourcefile(obj) or
                  py.std.inspect.getfile(obj))
            fspath = fn and py.path.local(fn) or None
            if fspath:
                try:
                    _, lineno = findsource(obj)
                except IOError:
                    lineno = None
            else:
                lineno = None
        else:
            fspath = code.path
            lineno = code.firstlineno 
        self._fslineno = fspath, lineno
        return fspath, lineno

    def repr_metainfo(self):
        fspath, lineno = self.getfslineno()
        modpath = self.getmodpath()
        return self.ReprMetaInfo(
            fspath=fspath, 
            lineno=lineno,
            modpath=modpath,
        )


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
        res = self.config.api.pytest_pymodule_makeitem(
            modcol=self, name=name, obj=obj)
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
                return self.Generator(name, parent=self)
            else: 
                return self.Function(name, parent=self)

class Module(py.test.collect.File, PyCollectorMixin):
    def _getobj(self):
        return self._memoizedcall('_obj', self._importtestmodule)

    def _importtestmodule(self):
        # we assume we are only called once per module 
        mod = self.fspath.pyimport()
        #print "imported test module", mod
        self.config.pytestplugins.consider_module(mod)
        return mod

    def setup(self): 
        if getattr(self.obj, 'disabled', 0):
            py.test.skip("%r is disabled" %(self.obj,))
        if not self.config.option.nomagic:
            #print "*" * 20, "INVOKE assertion", self
            py.magic.invoke(assertion=1)
        mod = self.obj
        self.config.pytestplugins.register(mod)
        if hasattr(mod, 'setup_module'): 
            self.obj.setup_module(mod)

    def teardown(self): 
        if hasattr(self.obj, 'teardown_module'): 
            self.obj.teardown_module(self.obj) 
        if not self.config.option.nomagic:
            #print "*" * 20, "revoke assertion", self
            py.magic.revoke(assertion=1)
        self.config.pytestplugins.unregister(self.obj)

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
        return self.getfslineno()

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
        return self.getfslineno()

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
            return setup_func_or_method(self.obj) 

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
        # test generators are collectors yet participate in 
        # the test-item setup and teardown protocol. 
        # otherwise we could avoid global setupstate
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
    def __init__(self, name, parent=None, config=None, args=(), callobj=_dummy):
        super(Function, self).__init__(name, parent, config=config) 
        self._finalizers = []
        self._args = args
        self.funcargs = {}
        if callobj is not _dummy: 
            self._obj = callobj 

    def addfinalizer(self, func):
        self._finalizers.append(func)
        
    def teardown(self):
        finalizers = self._finalizers
        while finalizers:
            call = finalizers.pop()
            call()
        super(Function, self).teardown()

    def readkeywords(self):
        d = super(Function, self).readkeywords()
        d.update(self.obj.func_dict)
        return d

    def runtest(self):
        """ execute the given test function. """
        if not self._deprecated_testexecution():
            self.setupargs() # XXX move to setup() / consider funcargs plugin
            ret = self.config.api.pytest_pyfunc_call(
                pyfuncitem=self, args=self._args, kwargs=self.funcargs)

    def setupargs(self):
        if self._args:
            # generator case: we don't do anything then
            pass
        else:
            # standard Python Test function/method case  
            funcobj = self.obj 
            startindex = getattr(funcobj, 'im_self', None) and 1 or 0 
            argnames = py.std.inspect.getargs(self.obj.func_code)[0]
            for i, argname in py.builtin.enumerate(argnames):
                if i < startindex:
                    continue 
                try:
                    self.funcargs[argname] = self.lookup_onearg(argname)
                except LookupError, e:
                    numdefaults = len(funcobj.func_defaults or ()) 
                    if i + numdefaults >= len(argnames):
                        continue # continue # seems that our args have defaults 
                    else:
                        raise

    def lookup_onearg(self, argname):
        prefix = "pytest_funcarg__"
        #makerlist = self.config.pytestplugins.listattr(prefix + argname)
        value = self.config.pytestplugins.call_firstresult(prefix + argname, pyfuncitem=self)
        if value is not None:
            return value
        else:
            self._raisefuncargerror(argname, prefix)

    def _raisefuncargerror(self, argname, prefix="pytest_funcarg__"):
        metainfo = self.repr_metainfo()
        available = []
        plugins = self.config.pytestplugins._plugins.values()
        plugins.extend(self.config.pytestplugins.pyplugins._plugins)
        for plugin in plugins:
            for name in vars(plugin.__class__):
                if name.startswith(prefix):
                    name = name[len(prefix):]
                    if name not in available:
                        available.append(name) 
        msg = "funcargument %r not found for: %s" %(argname,metainfo.verboseline())
        msg += "\n available funcargs: %s" %(", ".join(available),)
        raise LookupError(msg)

    def __eq__(self, other):
        try:
            return (self.name == other.name and 
                    self._args == other._args and
                    self.parent == other.parent and
                    self.obj == other.obj)
        except AttributeError:
            pass
        return False
    def __ne__(self, other):
        return not self == other


# DEPRECATED
#from py.__.test.plugin.pytest_doctest import DoctestFile 
