""" Python test discovery, setup and run of test functions. """
import py
import inspect
import sys
import pytest
from py._code.code import TerminalRepr
from _pytest.monkeypatch import monkeypatch

import _pytest
cutdir = py.path.local(_pytest.__file__).dirpath()

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption('--funcargs',
               action="store_true", dest="showfuncargs", default=False,
               help="show available function arguments, sorted by plugin")
    parser.addini("python_files", type="args",
        default=('test_*.py', '*_test.py'),
        help="glob-style file patterns for Python test module discovery")
    parser.addini("python_classes", type="args", default=("Test",),
        help="prefixes for Python test class discovery")
    parser.addini("python_functions", type="args", default=("test",),
        help="prefixes for Python test function and method discovery")

def pytest_cmdline_main(config):
    if config.option.showfuncargs:
        showfuncargs(config)
        return 0


def pytest_generate_tests(metafunc):
    try:
        param = metafunc.function.parametrize
    except AttributeError:
        return
    for p in param:
        metafunc.parametrize(*p.args, **p.kwargs)

def pytest_configure(config):
    config.addinivalue_line("markers",
        "parametrize(argnames, argvalues): call a test function multiple "
        "times passing in multiple different argument value sets. Example: "
        "@parametrize('arg1', [1,2]) would lead to two calls of the decorated "
        "test function, one with arg1=1 and another with arg1=2."
    )


@pytest.mark.trylast
def pytest_namespace():
    raises.Exception = pytest.fail.Exception
    return {
        'raises' : raises,
        'collect': {
        'Module': Module, 'Class': Class, 'Instance': Instance,
        'Function': Function, 'Generator': Generator,
        '_fillfuncargs': fillfuncargs}
    }

def pytest_funcarg__pytestconfig(request):
    """ the pytest config object with access to command line opts."""
    return request.config

def pytest_pyfunc_call(__multicall__, pyfuncitem):
    if not __multicall__.execute():
        testfunction = pyfuncitem.obj
        if pyfuncitem._isyieldedfunction():
            testfunction(*pyfuncitem._args)
        else:
            funcargs = pyfuncitem.funcargs
            testfunction(**funcargs)

def pytest_collect_file(path, parent):
    ext = path.ext
    pb = path.purebasename
    if ext == ".py":
        if not parent.session.isinitpath(path):
            for pat in parent.config.getini('python_files'):
                if path.fnmatch(pat):
                    break
            else:
               return
        return parent.ihook.pytest_pycollect_makemodule(
            path=path, parent=parent)

def pytest_pycollect_makemodule(path, parent):
    return Module(path, parent)

def pytest_pycollect_makeitem(__multicall__, collector, name, obj):
    res = __multicall__.execute()
    if res is not None:
        return res
    if inspect.isclass(obj):
        #if hasattr(collector.obj, 'unittest'):
        #    return # we assume it's a mixin class for a TestCase derived one
        if collector.classnamefilter(name):
            if not hasinit(obj):
                Class = collector._getcustomclass("Class")
                return Class(name, parent=collector)
    elif collector.funcnamefilter(name) and hasattr(obj, '__call__'):
        if is_generator(obj):
            return Generator(name, parent=collector)
        else:
            return collector._genfunctions(name, obj)

def is_generator(func):
    try:
        return py.code.getrawcode(func).co_flags & 32 # generator function
    except AttributeError: # builtin functions have no bytecode
        # assume them to not be generators
        return False

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
        assert isinstance(self._fslineno[1], int), obj
        return self._fslineno

    def reportinfo(self):
        # XXX caching?
        obj = self.obj
        if hasattr(obj, 'compat_co_firstlineno'):
            # nose compatibility
            fspath = sys.modules[obj.__module__].__file__
            if fspath.endswith(".pyc"):
                fspath = fspath[:-1]
            #assert 0
            #fn = inspect.getsourcefile(obj) or inspect.getfile(obj)
            lineno = obj.compat_co_firstlineno
            modpath = obj.__module__
        else:
            fspath, lineno = self._getfslineno()
            modpath = self.getmodpath()
        assert isinstance(lineno, int)
        return fspath, lineno, modpath

class PyCollectorMixin(PyobjMixin, pytest.Collector):

    def funcnamefilter(self, name):
        for prefix in self.config.getini("python_functions"):
            if name.startswith(prefix):
                return True

    def classnamefilter(self, name):
        for prefix in self.config.getini("python_classes"):
            if name.startswith(prefix):
                return True

    def collect(self):
        # NB. we avoid random getattrs and peek in the __dict__ instead
        # (XXX originally introduced from a PyPy need, still true?)
        dicts = [getattr(self.obj, '__dict__', {})]
        for basecls in inspect.getmro(self.obj.__class__):
            dicts.append(basecls.__dict__)
        seen = {}
        l = []
        for dic in dicts:
            for name, obj in dic.items():
                if name in seen:
                    continue
                seen[name] = True
                if name[0] != "_":
                    res = self.makeitem(name, obj)
                    if res is None:
                        continue
                    if not isinstance(res, list):
                        res = [res]
                    l.extend(res)
        l.sort(key=lambda item: item.reportinfo()[:2])
        return l

    def makeitem(self, name, obj):
        return self.ihook.pytest_pycollect_makeitem(
            collector=self, name=name, obj=obj)

    def _genfunctions(self, name, funcobj):
        module = self.getparent(Module).obj
        clscol = self.getparent(Class)
        cls = clscol and clscol.obj or None
        transfer_markers(funcobj, cls, module)
        metafunc = Metafunc(funcobj, config=self.config,
            cls=cls, module=module)
        gentesthook = self.config.hook.pytest_generate_tests
        extra = [module]
        if cls is not None:
            extra.append(cls())
        plugins = self.getplugins() + extra
        gentesthook.pcall(plugins, metafunc=metafunc)
        Function = self._getcustomclass("Function")
        if not metafunc._calls:
            return Function(name, parent=self)
        l = []
        for callspec in metafunc._calls:
            subname = "%s[%s]" %(name, callspec.id)
            function = Function(name=subname, parent=self,
                callspec=callspec, callobj=funcobj, keywords={callspec.id:True})
            l.append(function)
        return l

def transfer_markers(funcobj, cls, mod):
    # XXX this should rather be code in the mark plugin or the mark
    # plugin should merge with the python plugin.
    for holder in (cls, mod):
        try:
            pytestmark = holder.pytestmark
        except AttributeError:
            continue
        if isinstance(pytestmark, list):
            for mark in pytestmark:
                mark(funcobj)
        else:
            pytestmark(funcobj)

class Module(pytest.File, PyCollectorMixin):
    def _getobj(self):
        return self._memoizedcall('_obj', self._importtestmodule)

    def _importtestmodule(self):
        # we assume we are only called once per module
        try:
            mod = self.fspath.pyimport(ensuresyspath=True)
        except SyntaxError:
            excinfo = py.code.ExceptionInfo()
            raise self.CollectError(excinfo.getrepr(style="short"))
        except self.fspath.ImportMismatchError:
            e = sys.exc_info()[1]
            raise self.CollectError(
                "import file mismatch:\n"
                "imported module %r has this __file__ attribute:\n"
                "  %s\n"
                "which is not the same as the test file we want to collect:\n"
                "  %s\n"
                "HINT: remove __pycache__ / .pyc files and/or use a "
                "unique basename for your test file modules"
                 % e.args
            )
        #print "imported test module", mod
        self.config.pluginmanager.consider_module(mod)
        return mod

    def setup(self):
        if hasattr(self.obj, 'setup_module'):
            #XXX: nose compat hack, move to nose plugin
            # if it takes a positional arg, its probably a pytest style one
            # so we pass the current module object
            if inspect.getargspec(self.obj.setup_module)[0]:
                self.obj.setup_module(self.obj)
            else:
                self.obj.setup_module()

    def teardown(self):
        if hasattr(self.obj, 'teardown_module'):
            #XXX: nose compat hack, move to nose plugin
            # if it takes a positional arg, its probably a py.test style one
            # so we pass the current module object
            if inspect.getargspec(self.obj.teardown_module)[0]:
                self.obj.teardown_module(self.obj)
            else:
                self.obj.teardown_module()

class Class(PyCollectorMixin, pytest.Collector):

    def collect(self):
        return [self._getcustomclass("Instance")(name="()", parent=self)]

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

class Instance(PyCollectorMixin, pytest.Collector):
    def _getobj(self):
        return self.parent.obj()

    def newinstance(self):
        self.obj = self._getobj()
        return self.obj

class FunctionMixin(PyobjMixin):
    """ mixin for the code common to Function and Generator.
    """
    def setup(self):
        """ perform setup for this test function. """
        if hasattr(self, '_preservedparent'):
            obj = self._preservedparent
        elif isinstance(self.parent, Instance):
            obj = self.parent.newinstance()
            self.obj = self._getobj()
        else:
            obj = self.parent.obj
        if inspect.ismethod(self.obj):
            name = 'setup_method'
        else:
            name = 'setup_function'
        setup_func_or_method = getattr(obj, name, None)
        if setup_func_or_method is not None:
            setup_func_or_method(self.obj)

    def teardown(self):
        """ perform teardown for this test function. """
        if inspect.ismethod(self.obj):
            name = 'teardown_method'
        else:
            name = 'teardown_function'
        obj = self.parent.obj
        teardown_func_or_meth = getattr(obj, name, None)
        if teardown_func_or_meth is not None:
            teardown_func_or_meth(self.obj)

    def _prunetraceback(self, excinfo):
        if hasattr(self, '_obj') and not self.config.option.fulltrace:
            code = py.code.Code(self.obj)
            path, firstlineno = code.path, code.firstlineno
            traceback = excinfo.traceback
            ntraceback = traceback.cut(path=path, firstlineno=firstlineno)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(path=path)
                if ntraceback == traceback:
                    ntraceback = ntraceback.cut(excludepath=cutdir)
            excinfo.traceback = ntraceback.filter()

    def _repr_failure_py(self, excinfo, style="long"):
        if excinfo.errisinstance(FuncargRequest.LookupError):
            fspath, lineno, msg = self.reportinfo()
            lines, _ = inspect.getsourcelines(self.obj)
            for i, line in enumerate(lines):
                if line.strip().startswith('def'):
                    return FuncargLookupErrorRepr(fspath, lineno,
            lines[:i+1], str(excinfo.value))
        if excinfo.errisinstance(pytest.fail.Exception):
            if not excinfo.value.pytrace:
                return str(excinfo.value)
        return super(FunctionMixin, self)._repr_failure_py(excinfo,
            style=style)

    def repr_failure(self, excinfo, outerr=None):
        assert outerr is None, "XXX outerr usage is deprecated"
        return self._repr_failure_py(excinfo,
            style=self.config.option.tbstyle)

class FuncargLookupErrorRepr(TerminalRepr):
    def __init__(self, filename, firstlineno, deflines, errorstring):
        self.deflines = deflines
        self.errorstring = errorstring
        self.filename = filename
        self.firstlineno = firstlineno

    def toterminal(self, tw):
        tw.line()
        for line in self.deflines:
            tw.line("    " + line.strip())
        for line in self.errorstring.split("\n"):
            tw.line("        " + line.strip(), red=True)
        tw.line()
        tw.line("%s:%d" % (self.filename, self.firstlineno+1))


class Generator(FunctionMixin, PyCollectorMixin, pytest.Collector):
    def collect(self):
        # test generators are seen as collectors but they also
        # invoke setup/teardown on popular request
        # (induced by the common "test_*" naming shared with normal tests)
        self.session._setupstate.prepare(self)
        # see FunctionMixin.setup and test_setupstate_is_preserved_134
        self._preservedparent = self.parent.obj
        l = []
        seen = {}
        for i, x in enumerate(self.obj()):
            name, call, args = self.getcallargs(x)
            if not py.builtin.callable(call):
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
        if isinstance(obj[0], py.builtin._basestring):
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
class Function(FunctionMixin, pytest.Item):
    """ a Function Item is responsible for setting up
        and executing a Python callable test object.
    """
    _genid = None
    def __init__(self, name, parent=None, args=None, config=None,
                 callspec=None, callobj=_dummy, keywords=None, session=None):
        super(Function, self).__init__(name, parent,
            config=config, session=session)
        self._args = args
        if self._isyieldedfunction():
            assert not callspec, (
                "yielded functions (deprecated) cannot have funcargs")
        else:
            if callspec is not None:
                self.callspec = callspec
                self.funcargs = callspec.funcargs or {}
                self._genid = callspec.id
                if hasattr(callspec, "param"):
                    self._requestparam = callspec.param
            else:
                self.funcargs = {}
        if callobj is not _dummy:
            self._obj = callobj
        self.function = getattr(self.obj, 'im_func', self.obj)
        self.keywords.update(py.builtin._getfuncdict(self.obj) or {})
        if keywords:
            self.keywords.update(keywords)

    def _getobj(self):
        name = self.name
        i = name.find("[") # parametrization
        if i != -1:
            name = name[:i]
        return getattr(self.parent.obj, name)

    def _isyieldedfunction(self):
        return self._args is not None

    def runtest(self):
        """ execute the underlying test function. """
        self.ihook.pytest_pyfunc_call(pyfuncitem=self)

    def setup(self):
        super(Function, self).setup()
        if hasattr(self, 'funcargs'):
            fillfuncargs(self)

    def __eq__(self, other):
        try:
            return (self.name == other.name and
                    self._args == other._args and
                    self.parent == other.parent and
                    self.obj == other.obj and
                    getattr(self, '_genid', None) ==
                    getattr(other, '_genid', None)
            )
        except AttributeError:
            pass
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.parent, self.name))

def hasinit(obj):
    init = getattr(obj, '__init__', None)
    if init:
        if init != object.__init__:
            return True


def getfuncargnames(function, startindex=None):
    # XXX merge with main.py's varnames
    argnames = py.std.inspect.getargs(py.code.getrawcode(function))[0]
    if startindex is None:
        startindex = py.std.inspect.ismethod(function) and 1 or 0
    defaults = getattr(function, 'func_defaults',
                       getattr(function, '__defaults__', None)) or ()
    numdefaults = len(defaults)
    if numdefaults:
        return argnames[startindex:-numdefaults]
    return argnames[startindex:]

def fillfuncargs(function):
    """ fill missing funcargs. """
    request = FuncargRequest(pyfuncitem=function)
    request._fillfuncargs()

_notexists = object()

class CallSpec2(object):
    def __init__(self, metafunc):
        self.metafunc = metafunc
        self.funcargs = {}
        self._idlist = []
        self.params = {}
        self._globalid = _notexists
        self._globalid_args = set()
        self._globalparam = _notexists

    def copy(self, metafunc):
        cs = CallSpec2(self.metafunc)
        cs.funcargs.update(self.funcargs)
        cs.params.update(self.params)
        cs._idlist = list(self._idlist)
        cs._globalid = self._globalid
        cs._globalid_args = self._globalid_args
        cs._globalparam = self._globalparam
        return cs

    def _checkargnotcontained(self, arg):
        if arg in self.params or arg in self.funcargs:
            raise ValueError("duplicate %r" %(arg,))

    def getparam(self, name):
        try:
            return self.params[name]
        except KeyError:
            if self._globalparam is _notexists:
                raise ValueError(name)
            return self._globalparam

    @property
    def id(self):
        return "-".join(map(str, filter(None, self._idlist)))

    def setmulti(self, valtype, argnames, valset, id):
        for arg,val in zip(argnames, valset):
            self._checkargnotcontained(arg)
            getattr(self, valtype)[arg] = val
        self._idlist.append(id)

    def setall(self, funcargs, id, param):
        for x in funcargs:
            self._checkargnotcontained(x)
        self.funcargs.update(funcargs)
        if id is not _notexists:
            self._idlist.append(id)
        if param is not _notexists:
            assert self._globalparam is _notexists
            self._globalparam = param


class Metafunc:
    def __init__(self, function, config=None, cls=None, module=None):
        self.config = config
        self.module = module
        self.function = function
        self.funcargnames = getfuncargnames(function,
                                            startindex=int(cls is not None))
        self.cls = cls
        self.module = module
        self._calls = []
        self._ids = py.builtin.set()

    def parametrize(self, argnames, argvalues, indirect=False, ids=None):
        """ Add new invocations to the underlying test function using the list
        of argvalues for the given argnames.  Parametrization is performed
        during the collection phase.  If you need to setup expensive resources
        you may pass indirect=True and implement a funcarg factory which can
        perform the expensive setup just before a test is actually run.

        :arg argnames: an argument name or a list of argument names

        :arg argvalues: a list of values for the argname or a list of tuples of
            values for the list of argument names.

        :arg indirect: if True each argvalue corresponding to an argument will
            be passed as request.param to its respective funcarg factory so
            that it can perform more expensive setups during the setup phase of
            a test rather than at collection time.

        :arg ids: list of string ids each corresponding to the argvalues so
            that they are part of the test id. If no ids are provided they will
            be generated automatically from the argvalues.
        """
        if not isinstance(argnames, (tuple, list)):
            argnames = (argnames,)
            argvalues = [(val,) for val in argvalues]
        if not indirect:
            #XXX should we also check for the opposite case?
            for arg in argnames:
                if arg not in self.funcargnames:
                    raise ValueError("%r has no argument %r" %(self.function, arg))
        valtype = indirect and "params" or "funcargs"
        if not ids:
            idmaker = IDMaker()
            ids = list(map(idmaker, argvalues))
        newcalls = []
        for callspec in self._calls or [CallSpec2(self)]:
            for i, valset in enumerate(argvalues):
                assert len(valset) == len(argnames)
                newcallspec = callspec.copy(self)
                newcallspec.setmulti(valtype, argnames, valset, ids[i])
                newcalls.append(newcallspec)
        self._calls = newcalls

    def addcall(self, funcargs=None, id=_notexists, param=_notexists):
        """ (deprecated, use parametrize) Add a new call to the underlying
        test function during the collection phase of a test run.  Note that
        request.addcall() is called during the test collection phase prior and
        independently to actual test execution.  You should only use addcall()
        if you need to specify multiple arguments of a test function.

        :arg funcargs: argument keyword dictionary used when invoking
            the test function.

        :arg id: used for reporting and identification purposes.  If you
            don't supply an `id` an automatic unique id will be generated.

        :arg param: a parameter which will be exposed to a later funcarg factory
            invocation through the ``request.param`` attribute.
        """
        assert funcargs is None or isinstance(funcargs, dict)
        if funcargs is not None:
            for name in funcargs:
                if name not in self.funcargnames:
                    pytest.fail("funcarg %r not used in this function." % name)
        else:
            funcargs = {}
        if id is None:
            raise ValueError("id=None not allowed")
        if id is _notexists:
            id = len(self._calls)
        id = str(id)
        if id in self._ids:
            raise ValueError("duplicate id %r" % id)
        self._ids.add(id)

        cs = CallSpec2(self)
        cs.setall(funcargs, id, param)
        self._calls.append(cs)

class IDMaker:
    def __init__(self):
        self.counter = 0
    def __call__(self, valset):
        l = []
        for val in valset:
            if not isinstance(val, (int, str)):
                val = "."+str(self.counter)
            self.counter += 1
            l.append(str(val))
        return "-".join(l)

class FuncargRequest:
    """ A request for function arguments from a test function.

        Note that there is an optional ``param`` attribute in case
        there was an invocation to metafunc.addcall(param=...).
        If no such call was done in a ``pytest_generate_tests``
        hook, the attribute will not be present.
    """
    _argprefix = "pytest_funcarg__"
    _argname = None

    class LookupError(LookupError):
        """ error on performing funcarg request. """

    def __init__(self, pyfuncitem):
        self._pyfuncitem = pyfuncitem
        if hasattr(pyfuncitem, '_requestparam'):
            self.param = pyfuncitem._requestparam
        extra = [obj for obj in (self.module, self.instance) if obj]
        self._plugins = pyfuncitem.getplugins() + extra
        self._funcargs  = self._pyfuncitem.funcargs.copy()
        self._name2factory = {}
        self._currentarg = None

    @property
    def function(self):
        """ function object of the test invocation. """
        return self._pyfuncitem.obj

    @property
    def keywords(self):
        """ keywords of the test function item.

        .. versionadded:: 2.0
        """
        return self._pyfuncitem.keywords

    @property
    def module(self):
        """ module where the test function was collected. """
        return self._pyfuncitem.getparent(pytest.Module).obj

    @property
    def cls(self):
        """ class (can be None) where the test function was collected. """
        clscol = self._pyfuncitem.getparent(pytest.Class)
        if clscol:
            return clscol.obj
    @property
    def instance(self):
        """ instance (can be None) on which test function was collected. """
        return py.builtin._getimself(self.function)

    @property
    def config(self):
        """ the pytest config object associated with this request. """
        return self._pyfuncitem.config

    @property
    def fspath(self):
        """ the file system path of the test module which collected this test. """
        return self._pyfuncitem.fspath

    def _fillfuncargs(self):
        argnames = getfuncargnames(self.function)
        if argnames:
            assert not getattr(self._pyfuncitem, '_args', None), (
                "yielded functions cannot have funcargs")
        for argname in argnames:
            if argname not in self._pyfuncitem.funcargs:
                self._pyfuncitem.funcargs[argname] = self.getfuncargvalue(argname)


    def applymarker(self, marker):
        """ Apply a marker to a single test function invocation.
        This method is useful if you don't want to have a keyword/marker
        on all function invocations.

        :arg marker: a :py:class:`_pytest.mark.MarkDecorator` object
            created by a call to ``py.test.mark.NAME(...)``.
        """
        if not isinstance(marker, py.test.mark.XYZ.__class__):
            raise ValueError("%r is not a py.test.mark.* object")
        self._pyfuncitem.keywords[marker.markname] = marker

    def cached_setup(self, setup, teardown=None, scope="module", extrakey=None):
        """ Return a testing resource managed by ``setup`` &
        ``teardown`` calls.  ``scope`` and ``extrakey`` determine when the
        ``teardown`` function will be called so that subsequent calls to
        ``setup`` would recreate the resource.

        :arg teardown: function receiving a previously setup resource.
        :arg setup: a no-argument function creating a resource.
        :arg scope: a string value out of ``function``, ``class``, ``module``
            or ``session`` indicating the caching lifecycle of the resource.
        :arg extrakey: added to internal caching key of (funcargname, scope).
        """
        if not hasattr(self.config, '_setupcache'):
            self.config._setupcache = {} # XXX weakref?
        cachekey = (self._currentarg, self._getscopeitem(scope), extrakey)
        cache = self.config._setupcache
        try:
            val = cache[cachekey]
        except KeyError:
            val = setup()
            cache[cachekey] = val
            if teardown is not None:
                def finalizer():
                    del cache[cachekey]
                    teardown(val)
                self._addfinalizer(finalizer, scope=scope)
        return val

    def getfuncargvalue(self, argname):
        """ Retrieve a function argument by name for this test
        function invocation.  This allows one function argument factory
        to call another function argument factory.  If there are two
        funcarg factories for the same test function argument the first
        factory may use ``getfuncargvalue`` to call the second one and
        do something additional with the resource.
        """
        try:
            return self._funcargs[argname]
        except KeyError:
            pass
        if argname not in self._name2factory:
            self._name2factory[argname] = self.config.pluginmanager.listattr(
                    plugins=self._plugins,
                    attrname=self._argprefix + str(argname)
            )
        #else: we are called recursively
        if not self._name2factory[argname]:
            self._raiselookupfailed(argname)
        funcargfactory = self._name2factory[argname].pop()
        oldarg = self._currentarg
        mp = monkeypatch()
        mp.setattr(self, '_currentarg', argname)
        try:
            param = self._pyfuncitem.callspec.getparam(argname)
        except (AttributeError, ValueError):
            pass
        else:
            mp.setattr(self, 'param', param, raising=False)
        try:
            self._funcargs[argname] = res = funcargfactory(request=self)
        finally:
            mp.undo()
        return res

    def _getscopeitem(self, scope):
        if scope == "function":
            return self._pyfuncitem
        elif scope == "session":
            return None
        elif scope == "class":
            x = self._pyfuncitem.getparent(pytest.Class)
            if x is not None:
                return x
            scope = "module"
        if scope == "module":
            return self._pyfuncitem.getparent(pytest.Module)
        raise ValueError("unknown finalization scope %r" %(scope,))

    def addfinalizer(self, finalizer):
        """add finalizer function to be called after test function
        finished execution. """
        self._addfinalizer(finalizer, scope="function")

    def _addfinalizer(self, finalizer, scope):
        colitem = self._getscopeitem(scope)
        self._pyfuncitem.session._setupstate.addfinalizer(
            finalizer=finalizer, colitem=colitem)

    def __repr__(self):
        return "<FuncargRequest for %r>" %(self._pyfuncitem)

    def _raiselookupfailed(self, argname):
        available = []
        for plugin in self._plugins:
            for name in vars(plugin):
                if name.startswith(self._argprefix):
                    name = name[len(self._argprefix):]
                    if name not in available:
                        available.append(name)
        fspath, lineno, msg = self._pyfuncitem.reportinfo()
        msg = "LookupError: no factory found for function argument %r" % (argname,)
        msg += "\n available funcargs: %s" %(", ".join(available),)
        msg += "\n use 'py.test --funcargs [testpath]' for help on them."
        raise self.LookupError(msg)

def showfuncargs(config):
    from _pytest.main import wrap_session
    return wrap_session(config, _showfuncargs_main)

def _showfuncargs_main(config, session):
    session.perform_collect()
    if session.items:
        plugins = session.items[0].getplugins()
    else:
        plugins = session.getplugins()
    curdir = py.path.local()
    tw = py.io.TerminalWriter()
    verbose = config.getvalue("verbose")
    for plugin in plugins:
        available = []
        for name, factory in vars(plugin).items():
            if name.startswith(FuncargRequest._argprefix):
                name = name[len(FuncargRequest._argprefix):]
                if name not in available:
                    available.append([name, factory])
        if available:
            pluginname = plugin.__name__
            for name, factory in available:
                loc = getlocation(factory, curdir)
                if verbose:
                    funcargspec = "%s -- %s" %(name, loc,)
                else:
                    funcargspec = name
                tw.line(funcargspec, green=True)
                doc = factory.__doc__ or ""
                if doc:
                    for line in doc.split("\n"):
                        tw.line("    " + line.strip())
                else:
                    tw.line("    %s: no docstring available" %(loc,),
                        red=True)

def getlocation(function, curdir):
    import inspect
    fn = py.path.local(inspect.getfile(function))
    lineno = py.builtin._getcode(function).co_firstlineno
    if fn.relto(curdir):
        fn = fn.relto(curdir)
    return "%s:%d" %(fn, lineno+1)

# builtin pytest.raises helper

def raises(ExpectedException, *args, **kwargs):
    """ assert that a code block/function call raises @ExpectedException
    and raise a failure exception otherwise.

    If using Python 2.5 or above, you may use this function as a
    context manager::

        >>> with raises(ZeroDivisionError):
        ...    1/0

    Or you can specify a callable by passing a to-be-called lambda::

        >>> raises(ZeroDivisionError, lambda: 1/0)
        <ExceptionInfo ...>

    or you can specify an arbitrary callable with arguments::

        >>> def f(x): return 1/x
        ...
        >>> raises(ZeroDivisionError, f, 0)
        <ExceptionInfo ...>
        >>> raises(ZeroDivisionError, f, x=0)
        <ExceptionInfo ...>

    A third possibility is to use a string to be executed::

        >>> raises(ZeroDivisionError, "f(0)")
        <ExceptionInfo ...>
    """
    __tracebackhide__ = True

    if not args:
        return RaisesContext(ExpectedException)
    elif isinstance(args[0], str):
        code, = args
        assert isinstance(code, str)
        frame = sys._getframe(1)
        loc = frame.f_locals.copy()
        loc.update(kwargs)
        #print "raises frame scope: %r" % frame.f_locals
        try:
            code = py.code.Source(code).compile()
            py.builtin.exec_(code, frame.f_globals, loc)
            # XXX didn'T mean f_globals == f_locals something special?
            #     this is destroyed here ...
        except ExpectedException:
            return py.code.ExceptionInfo()
    else:
        func = args[0]
        try:
            func(*args[1:], **kwargs)
        except ExpectedException:
            return py.code.ExceptionInfo()
        k = ", ".join(["%s=%r" % x for x in kwargs.items()])
        if k:
            k = ', ' + k
        expr = '%s(%r%s)' %(getattr(func, '__name__', func), args, k)
    pytest.fail("DID NOT RAISE")

class RaisesContext(object):
    def __init__(self, ExpectedException):
        self.ExpectedException = ExpectedException
        self.excinfo = None

    def __enter__(self):
        self.excinfo = object.__new__(py.code.ExceptionInfo)
        return self.excinfo

    def __exit__(self, *tp):
        __tracebackhide__ = True
        if tp[0] is None:
            pytest.fail("DID NOT RAISE")
        self.excinfo.__init__(tp)
        return issubclass(self.excinfo.type, self.ExpectedException)

