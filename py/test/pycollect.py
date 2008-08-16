"""
Python related collection nodes.  Here is an example of 
a tree of collectors and test items that this modules provides:: 

        Module                  # FSCollector
            Class 
                Instance   
                    Function  
                    Generator 
                        ... 
            Function 
            Generator 
                Function 

        DoctestFile              # FSCollector 
            DoctestFileContent   # acts as Item 

""" 
import py
from py.__.test.collect import Collector, FSCollector, Item, configproperty

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

    def getmodpath(self, stopatmodule=True):
        """ return python path relative to the containing module. """
        chain = self.listchain()
        chain.reverse()
        parts = []
        for node in chain:
            if isinstance(node, Instance):
                continue
            if stopatmodule and isinstance(node, Module):
                break
            parts.append(node.name)
        parts.reverse()
        s = ".".join(parts)
        return s.replace(".[", "[")

    def getfslineno(self):
        try:
            return self._fslineno
        except AttributeError:
            pass
        try:
            code = py.code.Code(self.obj)
        except TypeError:
            # fallback to 
            fn = (py.std.inspect.getsourcefile(self.obj) or
                  py.std.inspect.getfile(self.obj))
            fspath = fn and py.path.local(fn) or None
            if fspath:
                try:
                    lines, lineno = py.std.inspect.findsource(self.obj)
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


class PyCollectorMixin(PyobjMixin, Collector): 
    Class = configproperty('Class')
    Instance = configproperty('Instance')
    Function = configproperty('Function')
    Generator = configproperty('Generator')
    
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

    def listdir(self): 
        self._prepare()
        itemlist = self._name2items.values()
        itemlist.sort()
        return [x.name for x in itemlist]

    def join(self, name): 
        self._prepare()
        return self._name2items.get(name, None) 

class Module(FSCollector, PyCollectorMixin):
    _stickyfailure = None

    def listdir(self):
        if getattr(self.obj, 'disabled', 0):
            return []
        return super(Module, self).listdir()

    def join(self, name):
        res = super(Module, self).join(name)
        if res is None:
            attr = getattr(self.obj, name, None)
            if attr is not None:
                res = self.makeitem(name, attr, usefilters=False)
        return res
    
    def _getobj(self):
        failure = self._stickyfailure
        if failure is not None: 
            raise failure[0], failure[1], failure[2]
        try: 
            self._obj = obj = self.fspath.pyimport() 
        except KeyboardInterrupt: 
            raise
        except:
            self._stickyfailure = py.std.sys.exc_info()
            raise 
        return self._obj 

    def setup(self): 
        if not self._config.option.nomagic:
            #print "*" * 20, "INVOKE assertion", self
            py.magic.invoke(assertion=1)
        if hasattr(self.obj, 'setup_module'): 
            self.obj.setup_module(self.obj) 

    def teardown(self): 
        if hasattr(self.obj, 'teardown_module'): 
            self.obj.teardown_module(self.obj) 
        if not self._config.option.nomagic:
            #print "*" * 20, "revoke assertion", self
            py.magic.revoke(assertion=1)

class Class(PyCollectorMixin, Collector): 

    def listdir(self): 
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
        return self.getfslineno()


class Instance(PyCollectorMixin, Collector): 
    def _getobj(self): 
        return self.parent.obj()  
    def Function(self): 
        return getattr(self.obj, 'Function', 
                       PyCollectorMixin.Function.__get__(self)) # XXX for python 2.2
    def _keywords(self):
        return []
    Function = property(Function)

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
        if not self._config.option.fulltrace: 
            code = py.code.Code(self.obj) 
            path, firstlineno = code.path, code.firstlineno 
            ntraceback = traceback.cut(path=path, firstlineno=firstlineno)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(path=path)
            traceback = ntraceback.filter()
        return traceback 

    def repr_failure(self, excinfo, outerr):
        return self._repr_failure_py(excinfo, outerr)

    shortfailurerepr = "F"

class Generator(FunctionMixin, PyCollectorMixin, Collector): 
    def listdir(self): 
        self._prepare()
        itemlist = self._name2items
        return [itemlist["[%d]" % num].name for num in xrange(len(itemlist))]
    
    def _buildname2items(self):
        d = {} 
        # XXX test generators are collectors yet participate in 
        # the test-item setup and teardown protocol 
        # if not for this we could probably avoid global setupstate
        self._setupstate.prepare(self) 
        for i, x in py.builtin.enumerate(self.obj()): 
            call, args = self.getcallargs(x)
            if not callable(call): 
                raise TypeError("%r yielded non callable test %r" %(self.obj, call,))
            name = "[%d]" % i  
            d[name] = self.Function(name, self, args=args, callobj=call)
        return d
        
    def getcallargs(self, obj):
        if isinstance(obj, (tuple, list)):
            call, args = obj[0], obj[1:]
        else:
            call, args = obj, ()
        return call, args 

#
#  Test Items 
#
_dummy = object()
class Function(FunctionMixin, Item): 
    """ a Function Item is responsible for setting up  
        and executing a Python callable test object.
    """
    def __init__(self, name, parent=None, config=None, args=(), callobj=_dummy):
        super(Function, self).__init__(name, parent, config=config) 
        self._args = args
        if callobj is not _dummy: 
            self._obj = callobj 

    def execute(self):
        """ execute the given test function. """
        self.obj(*self._args)

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

    def __repr__(self):
        return "<Function %r at %0x>"%(self.name, id(self))

class DoctestFile(FSCollector): 
    def listdir(self):
        return [self.fspath.basename]

    def join(self, name):
        if name == self.fspath.basename: 
            return DoctestFileContent(name, self)

from py.__.code.excinfo import Repr, ReprFileLocation

class ReprFailDoctest(Repr):
    def __init__(self, reprlocation, lines):
        self.reprlocation = reprlocation
        self.lines = lines
    def toterminal(self, tw):
        for line in self.lines:
            tw.line(line)
        self.reprlocation.toterminal(tw)
             
class DoctestFileContent(Item):
    def repr_failure(self, excinfo, outerr):
        if excinfo.errisinstance(py.compat.doctest.DocTestFailure):
            doctestfailure = excinfo.value
            example = doctestfailure.example
            test = doctestfailure.test
            filename = test.filename 
            lineno = example.lineno + 1
            message = excinfo.type.__name__
            reprlocation = ReprFileLocation(filename, lineno, message)
            checker = py.compat.doctest.OutputChecker() 
            REPORT_UDIFF = py.compat.doctest.REPORT_UDIFF
            filelines = py.path.local(filename).readlines(cr=0)
            i = max(0, lineno - 10)
            lines = []
            for line in filelines[i:lineno]:
                lines.append("%03d %s" % (i+1, line))
                i += 1
            lines += checker.output_difference(example, 
                    doctestfailure.got, REPORT_UDIFF).split("\n")
            return ReprFailDoctest(reprlocation, lines)
        #elif excinfo.errisinstance(py.compat.doctest.UnexpectedException):
        else: 
            return super(DoctestFileContent, self).repr_failure(excinfo, outerr)
            
    def execute(self):
        failed, tot = py.compat.doctest.testfile(
            str(self.fspath), module_relative=False, 
            raise_on_error=True, verbose=0)

