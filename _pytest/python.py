""" Python test discovery, setup and run of test functions. """
import py
import inspect
import sys
import pytest
from _pytest.main import getfslineno
from _pytest.monkeypatch import monkeypatch
from py._code.code import TerminalRepr

import _pytest
cutdir = py.path.local(_pytest.__file__).dirpath()

class FixtureFunctionMarker:
    def __init__(self, scope, params):
        self.scope = scope
        self.params = params
    def __call__(self, function):
        function._pytestfixturefunction = self
        return function

class SetupMarker:
    def __init__(self, scope):
        self.scope = scope
    def __call__(self, function):
        function._pytestsetup = self
        return function

# XXX a test fails when scope="function" how it should be, investigate
def fixture(scope=None, params=None):
    """ return a decorator to mark a fixture factory function.

    The name of the fixture function can be referenced in a test context
    to cause activation ahead of running tests.  Test modules or classes
    can use the pytest.mark.needsfixtures(fixturename) marker to specify
    needed fixtures.  Test functions can use fixture names as input arguments
    in which case the object returned from the fixture function will be
    injected.

    :arg scope: the scope for which this fixture is shared, one of
                "function", "class", "module", "session". Defaults to "function".
    :arg params: an optional list of parameters which will cause multiple
                invocations of the fixture functions and their dependent
                tests.
    """
    return FixtureFunctionMarker(scope, params)

def setup(scope="function"):
    """ return a decorator to mark a function as providing a fixture for
    a testcontext.  A fixture function is executed for each scope and may
    receive funcargs which allows it to initialise and provide implicit
    test state.  A fixture function may receive the "testcontext" object
    and register a finalizer via "testcontext.addfinalizer(finalizer)"
    which will be called when the last test in the testcontext has
    executed.

    :arg scope: the scope for which the setup function will be active, one
                of "function", "class", "module", "session".
                Defaults to "function".
    """
    return SetupMarker(scope)

def cached_property(f):
    """returns a cached property that is calculated by function f.
    taken from http://code.activestate.com/recipes/576563-cached-property/"""
    def get(self):
        try:
            return self._property_cache[f]
        except AttributeError:
            self._property_cache = {}
            x = self._property_cache[f] = f(self)
            return x
        except KeyError:
            x = self._property_cache[f] = f(self)
            return x
    return property(get)

def pyobj_property(name):
    def get(self):
        node = self.getparent(getattr(pytest, name))
        if node is not None:
            return node.obj
    doc = "python %s object this node was collected from (can be None)." % (
          name.lower(),)
    return property(get, None, None, doc)


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

def pytest_sessionstart(session):
    session.funcargmanager = FuncargManager(session)

@pytest.mark.trylast
def pytest_namespace():
    raises.Exception = pytest.fail.Exception
    return {
        'fixture': fixture,
        'setup': setup,
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
            try:
                funcargnames = pyfuncitem.funcargnames
            except AttributeError:
                funcargs = pyfuncitem.funcargs
            else:
                funcargs = {}
                for name in funcargnames:
                    funcargs[name] = pyfuncitem.funcargs[name]
            testfunction(**funcargs)

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

class PyobjContext(object):
    module = pyobj_property("Module")
    cls = pyobj_property("Class")
    instance = pyobj_property("Instance")

class PyobjMixin(PyobjContext):
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
        return getfslineno(self.obj)

    def reportinfo(self):
        # XXX caching?
        obj = self.obj
        if hasattr(obj, 'compat_co_firstlineno'):
            # nose compatibility
            fspath = sys.modules[obj.__module__].__file__
            if fspath.endswith(".pyc"):
                fspath = fspath[:-1]
            lineno = obj.compat_co_firstlineno
            modpath = obj.__module__
        else:
            fspath, lineno = getfslineno(obj)
            modpath = self.getmodpath()
        assert isinstance(lineno, int)
        return fspath, lineno, modpath

class PyCollector(PyobjMixin, pytest.Collector):

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
        metafunc = Metafunc(funcobj, parentnode=self, config=self.config,
            cls=cls, module=module)
        gentesthook = self.config.hook.pytest_generate_tests
        extra = [module]
        if cls is not None:
            extra.append(cls())
        plugins = self.getplugins() + extra
        gentesthook.pcall(plugins, metafunc=metafunc)
        Function = self._getcustomclass("Function")
        l = []
        if not metafunc._calls:
            l.append(Function(name, parent=self))
        for callspec in metafunc._calls:
            subname = "%s[%s]" %(name, callspec.id)
            function = Function(name=subname, parent=self,
                callspec=callspec, callobj=funcobj,
                keywords={callspec.id:True})
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

class Module(pytest.File, PyCollector):
    """ Collector for test classes and functions. """
    def _getobj(self):
        return self._memoizedcall('_obj', self._importtestmodule)

    def collect(self):
        self.session.funcargmanager._parsefactories(self.obj, self.nodeid)
        return super(Module, self).collect()

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
        setup_module = xunitsetup(self.obj, "setup_module")
        if setup_module is not None:
            #XXX: nose compat hack, move to nose plugin
            # if it takes a positional arg, its probably a pytest style one
            # so we pass the current module object
            if inspect.getargspec(setup_module)[0]:
                setup_module(self.obj)
            else:
                setup_module()

    def teardown(self):
        teardown_module = xunitsetup(self.obj, 'teardown_module')
        if teardown_module is not None:
            #XXX: nose compat hack, move to nose plugin
            # if it takes a positional arg, its probably a py.test style one
            # so we pass the current module object
            if inspect.getargspec(teardown_module)[0]:
                teardown_module(self.obj)
            else:
                teardown_module()

class Class(PyCollector):
    """ Collector for test methods. """
    def collect(self):
        return [self._getcustomclass("Instance")(name="()", parent=self)]

    def setup(self):
        setup_class = xunitsetup(self.obj, 'setup_class')
        if setup_class is not None:
            setup_class = getattr(setup_class, 'im_func', setup_class)
            setup_class = getattr(setup_class, '__func__', setup_class)
            setup_class(self.obj)

    def teardown(self):
        teardown_class = xunitsetup(self.obj, 'teardown_class')
        if teardown_class is not None:
            teardown_class = getattr(teardown_class, 'im_func', teardown_class)
            teardown_class = getattr(teardown_class, '__func__', teardown_class)
            teardown_class(self.obj)

class Instance(PyCollector):
    def _getobj(self):
        obj = self.parent.obj()
        return obj

    def collect(self):
        self.session.funcargmanager._parsefactories(self.obj, self.nodeid)
        return super(Instance, self).collect()

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
        setup_func_or_method = xunitsetup(obj, name)
        if setup_func_or_method is not None:
            setup_func_or_method(self.obj)

    def teardown(self):
        """ perform teardown for this test function. """
        if inspect.ismethod(self.obj):
            name = 'teardown_method'
        else:
            name = 'teardown_function'
        obj = self.parent.obj
        teardown_func_or_meth = xunitsetup(obj, name)
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
        if excinfo.errisinstance(pytest.fail.Exception):
            if not excinfo.value.pytrace:
                return str(excinfo.value)
        return super(FunctionMixin, self)._repr_failure_py(excinfo,
            style=style)

    def repr_failure(self, excinfo, outerr=None):
        assert outerr is None, "XXX outerr usage is deprecated"
        return self._repr_failure_py(excinfo,
            style=self.config.option.tbstyle)


class Generator(FunctionMixin, PyCollector):
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


def hasinit(obj):
    init = getattr(obj, '__init__', None)
    if init:
        if init != object.__init__:
            return True



def fillfuncargs(function):
    """ fill missing funcargs for a test function. """
    if getattr(function, "_args", None) is None:  # not a yielded function
        try:
            request = function._request
        except AttributeError:
            request = function._request = FuncargRequest(function)
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
        self._arg2scopenum = {}  # used for sorting parametrized resources

    def copy(self, metafunc):
        cs = CallSpec2(self.metafunc)
        cs.funcargs.update(self.funcargs)
        cs.params.update(self.params)
        cs._arg2scopenum.update(self._arg2scopenum)
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

    def setmulti(self, valtype, argnames, valset, id, scopenum=0):
        for arg,val in zip(argnames, valset):
            self._checkargnotcontained(arg)
            getattr(self, valtype)[arg] = val
            # we want self.params to be always set because of
            # parametrize_sorted() which groups tests by params/scope
            if valtype == "funcargs":
                self.params[arg] = id
            self._arg2scopenum[arg] = scopenum
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
    def __init__(self, function, config=None, cls=None, module=None,
                 parentnode=None):
        self.config = config
        self.module = module
        self.function = function
        self.parentnode = parentnode
        self.parentid = getattr(parentnode, "nodeid", "")
        argnames = getfuncargnames(function, startindex=int(cls is not None))
        if parentnode is not None:
            fm = parentnode.session.funcargmanager
            self.funcargnames, self._arg2facdeflist = fm.getallfuncargnames(
                argnames, parentnode)
        else:
            self.funcargnames = argnames
        self.cls = cls
        self.module = module
        self._calls = []
        self._ids = py.builtin.set()
        self._arg2scopenum = {}

    def parametrize(self, argnames, argvalues, indirect=False, ids=None,
        scope="function"):
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
        if scope is None:
            scope = "function"
        scopenum = scopes.index(scope)
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
                #print ("setmulti %r id %r" % (argnames, ids[i]))
                newcallspec.setmulti(valtype, argnames, valset, ids[i],
                                     scopenum)
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
    argprefix = session.funcargmanager._argprefix
    for plugin in plugins:
        available = []
        for name, factory in vars(plugin).items():
            if name.startswith(argprefix):
                name = name[len(argprefix):]
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
    if ExpectedException is AssertionError:
        # we want to catch a AssertionError
        # replace our subclass with the builtin one
        # see https://bitbucket.org/hpk42/pytest/issue/176/pytestraises
        from _pytest.assertion.util import BuiltinAssertionError as ExpectedException

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

#
#  the basic py.test Function item
#
_dummy = object()
class Function(FunctionMixin, pytest.Item):
    """ a Function Item is responsible for setting up and executing a
    Python test function.
    """
    _genid = None
    def __init__(self, name, parent=None, args=None, config=None,
                 callspec=None, callobj=_dummy, keywords=None, session=None):
        super(Function, self).__init__(name, parent, config=config,
                                       session=session)
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
                    self.param = callspec.param
            else:
                self.funcargs = {}
            self._request = req = FuncargRequest(self)
            #req._discoverfactories()
        if callobj is not _dummy:
            self.obj = callobj
        startindex = int(self.cls is not None)
        self.funcargnames = getfuncargnames(self.obj, startindex=startindex)
        for name, val in (py.builtin._getfuncdict(self.obj) or {}).items():
            setattr(self.markers, name, val)
        if keywords:
            for name, val in keywords.items():
                setattr(self.markers, name, val)

    @property
    def function(self):
        "underlying python 'function' object"
        return getattr(self.obj, 'im_func', self.obj)

    def _getobj(self):
        name = self.name
        i = name.find("[") # parametrization
        if i != -1:
            name = name[:i]
        return getattr(self.parent.obj, name)

    @property
    def _pyfuncitem(self):
        "(compatonly) for code expecting pytest-2.2 style request objects"
        return self

    def _isyieldedfunction(self):
        return getattr(self, "_args", None) is not None

    def runtest(self):
        """ execute the underlying test function. """
        self.ihook.pytest_pyfunc_call(pyfuncitem=self)

    def setup(self):
        super(Function, self).setup()
        if hasattr(self, "_request"):
            self._request._callsetup()
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

scope2props = dict(session=())
scope2props["module"] = ("fspath", "module")
scope2props["class"] = scope2props["module"] + ("cls",)
scope2props["instance"] = scope2props["class"] + ("instance", )
scope2props["function"] = scope2props["instance"] + ("function", "keywords")

def scopeproperty(name=None, doc=None):
    def decoratescope(func):
        scopename = name or func.__name__
        def provide(self):
            if func.__name__ in scope2props[self.scope]:
                return func(self)
            raise AttributeError("%s not available in %s-scoped context" % (
                scopename, self.scope))
        return property(provide, None, None, func.__doc__)
    return decoratescope


class FuncargRequest:
    """ A request for function arguments from a test or setup function.

    A request object gives access to attributes of the requesting
    test context.  It has an optional ``param`` attribute in case
    of parametrization.
    """

    def __init__(self, pyfuncitem):
        self._pyfuncitem = pyfuncitem
        if hasattr(pyfuncitem, '_requestparam'):
            self.param = pyfuncitem._requestparam
        #: Scope string, one of "function", "cls", "module", "session"
        self.scope = "function"
        self.getparent = pyfuncitem.getparent
        self._funcargs  = self._pyfuncitem.funcargs.copy()
        self._name2factory = {}
        self.funcargmanager = pyfuncitem.session.funcargmanager
        self._currentarg = None
        self.parentid = pyfuncitem.parent.nodeid
        self.funcargnames, self._arg2facdeflist_ = \
            self.funcargmanager.getallfuncargnames(
                getfuncargnames(self.function), # XXX _pyfuncitem...
                pyfuncitem.parent)
        self._factorystack = []

    @property
    def node(self):
        """ underlying collection node (depends on request scope)"""
        return self._getscopeitem(self.scope)

    def _getfaclist(self, argname):
        facdeflist = self._name2factory.get(argname, None)
        getfactb = None
        function = None
        if facdeflist is None:
            if self._factorystack:
                function = self._factorystack[-1].func
                getfactb = lambda: self._factorystack[:-1]
            else:
                function = self.function
            facdeflist = self.funcargmanager.getfactorylist(
                            argname, self.parentid)
            self._name2factory[argname] = facdeflist
        if not facdeflist:
            self.funcargmanager._raiselookupfailed(argname, function,
                                                   self.parentid, getfactb)
        return facdeflist

    @property
    def config(self):
        """ the pytest config object associated with this request. """
        return self._pyfuncitem.config


    @scopeproperty()
    def function(self):
        """ test function object if the request has a per-function scope. """
        return self._pyfuncitem.obj

    @scopeproperty("class")
    def cls(self):
        """ class (can be None) where the test function was collected. """
        clscol = self._pyfuncitem.getparent(pytest.Class)
        if clscol:
            return clscol.obj

    @property
    def instance(self):
        """ instance (can be None) on which test function was collected. """
        # unittest support hack, see _pytest.unittest.TestCaseFunction
        try:
            return self._pyfuncitem._testcase
        except AttributeError:
            return py.builtin._getimself(self.function)

    @scopeproperty()
    def module(self):
        """ python module object where the test function was collected. """
        return self._pyfuncitem.getparent(pytest.Module).obj

    @scopeproperty()
    def fspath(self):
        """ the file system path of the test module which collected this test. """
        return self._pyfuncitem.fspath

    @property
    def keywords(self):
        """ (deprecated, use node.markers class) dictionary of markers. """
        return self._pyfuncitem.keywords

    @property
    def session(self):
        """ pytest session object. """
        return self._pyfuncitem.session

    def addfinalizer(self, finalizer):
        """add finalizer/teardown function to be called after the
        last test within the requesting test context finished
        execution. """
        self._addfinalizer(finalizer, scope=self.scope)

    def _addfinalizer(self, finalizer, scope):
        if scope != "function" and hasattr(self, "param"):
            # parametrized resources are sorted by param
            # so we rather store finalizers per (argname, param)
            colitem = (self._currentarg, self.param)
        else:
            colitem = self._getscopeitem(scope)
        self._pyfuncitem.session._setupstate.addfinalizer(
            finalizer=finalizer, colitem=colitem)

    def applymarker(self, marker):
        """ Apply a marker to a single test function invocation.
        This method is useful if you don't want to have a keyword/marker
        on all function invocations.

        :arg marker: a :py:class:`_pytest.mark.MarkDecorator` object
            created by a call to ``py.test.mark.NAME(...)``.
        """
        self.node.applymarker(marker)

    def raiseerror(self, msg):
        """ raise a FuncargLookupError with the given message. """
        raise self.funcargmanager.FuncargLookupError(self.function, msg)


    def _fillfuncargs(self):
        item = self._pyfuncitem
        funcargnames = getattr(item, "funcargnames", self.funcargnames)
        for argname in funcargnames:
            if argname not in item.funcargs:
                item.funcargs[argname] = self.getfuncargvalue(argname)

    def _callsetup(self):
        self.funcargmanager.ensure_setupcalls(self)

    def cached_setup(self, setup, teardown=None, scope="module", extrakey=None):
        """ (deprecated) Return a testing resource managed by ``setup`` &
        ``teardown`` calls.  ``scope`` and ``extrakey`` determine when the
        ``teardown`` function will be called so that subsequent calls to
        ``setup`` would recreate the resource.  With pytest-2.3 you
        do not need ``cached_setup()`` as you can directly declare a scope
        on a funcarg factory and register a finalizer through
        ``request.addfinalizer()``.

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
            __tracebackhide__ = True
            if scopemismatch(self.scope, scope):
                raise ScopeMismatchError("You tried to access a %r scoped "
                    "resource with a %r scoped request object" %(
                    (scope, self.scope)))
            __tracebackhide__ = False
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

        **Note**, however, that starting with pytest-2.3 it is usually
        easier and better to directly use the needed funcarg in the
        factory function signature.  This will also work seemlessly
        with parametrization and the new resource setup optimizations.
        """
        try:
            return self._funcargs[argname]
        except KeyError:
            pass
        try:
            factorydeflist = self._getfaclist(argname)
        except FuncargLookupError:
            if argname == "request":
                return self
            raise
        factorydef = factorydeflist.pop()
        self._factorystack.append(factorydef)
        try:
            return self._getfuncargvalue(factorydef)
        finally:
            self._factorystack.pop()

    def _getfuncargvalue(self, factorydef):
        # collect funcargs from the factory
        newnames = factorydef.funcargnames
        argname = factorydef.argname
        factory_kwargs = {}
        def fillfactoryargs():
            for newname in newnames:
                val = self.getfuncargvalue(newname)
                factory_kwargs[newname] = val

        node = self._pyfuncitem
        mp = monkeypatch()
        mp.setattr(self, '_currentarg', argname)
        try:
            param = node.callspec.getparam(argname)
        except (AttributeError, ValueError):
            pass
        else:
            mp.setattr(self, 'param', param, raising=False)

        scope = factorydef.scope
        funcargfactory = factorydef.func
        if scope is not None:
            __tracebackhide__ = True
            if scopemismatch(self.scope, scope):
                # try to report something helpful
                lines = self._factorytraceback()
                raise ScopeMismatchError("You tried to access the %r scoped "
                    "funcarg %r with a %r scoped request object, "
                    "involved factories\n%s" %(
                    (scope, argname, self.scope, "\n".join(lines))))
            __tracebackhide__ = False
            mp.setattr(self, "scope", scope)
            kwargs = {}
            if hasattr(self, "param"):
                kwargs["extrakey"] = param
            fillfactoryargs()
            val = self.cached_setup(lambda: funcargfactory(**factory_kwargs),
                                    scope=scope, **kwargs)
        else:
            fillfactoryargs()
            val = funcargfactory(**factory_kwargs)
        mp.undo()
        self._funcargs[argname] = val
        return val

    def _factorytraceback(self):
        lines = []
        for factorydef in self._factorystack:
            factory = factorydef.func
            fs, lineno = getfslineno(factory)
            p = self._pyfuncitem.session.fspath.bestrelpath(fs)
            args = inspect.formatargspec(*inspect.getargspec(factory))
            lines.append("%s:%d:  def %s%s" %(
                p, lineno, factory.__name__, args))
        return lines


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

    def __repr__(self):
        return "<FuncargRequest for %r>" %(self._pyfuncitem)

class ScopeMismatchError(Exception):
    """ A funcarg factory tries to access a funcargvalue/factory
    which has a lower scope (e.g. a Session one calls a function one)
    """

scopes = "session module class function".split()
def scopemismatch(currentscope, newscope):
    return scopes.index(newscope) > scopes.index(currentscope)

def slice_kwargs(names, kwargs):
    new_kwargs = {}
    for name in names:
        new_kwargs[name] = kwargs[name]
    return new_kwargs

class FuncargLookupError(LookupError):
    """ could not find a factory. """
    def __init__(self, function, msg, factblines=None):
        self.function = function
        self.msg = msg
        self.factblines = factblines

class FuncargLookupErrorRepr(TerminalRepr):
    def __init__(self, filename, firstlineno, deflines, errorstring, factblines):
        self.deflines = deflines
        self.errorstring = errorstring
        self.filename = filename
        self.firstlineno = firstlineno
        self.factblines = factblines

    def toterminal(self, tw):
        tw.line()
        if self.factblines:
            tw.line('    dependency of:')
            for factorydef in self.factblines:
                tw.line('        %s in %s' % (
                    factorydef.argname,
                    factorydef.baseid,
                ))
            tw.line()
        for line in self.deflines:
            tw.line("    " + line.strip())
        for line in self.errorstring.split("\n"):
            tw.line("        " + line.strip(), red=True)
        tw.line()
        tw.line("%s:%d" % (self.filename, self.firstlineno+1))

class FuncargManager:
    _argprefix = "pytest_funcarg__"
    FuncargLookupError = FuncargLookupError
    FuncargLookupErrorRepr = FuncargLookupErrorRepr

    def __init__(self, session):
        self.session = session
        self.config = session.config
        self.arg2facspec = {}
        self._seenplugins = set()
        self._holderobjseen = set()
        self.setuplist = []
        self._arg2finish = {}
        session.config.pluginmanager.register(self, "funcmanage")

    ### XXX this hook should be called for historic events like pytest_configure
    ### so that we don't have to do the below pytest_configure hook
    def pytest_plugin_registered(self, plugin):
        if plugin in self._seenplugins:
            return
        #print "plugin_registered", plugin
        nodeid = ""
        try:
            p = py.path.local(plugin.__file__)
        except AttributeError:
            pass
        else:
            if p.basename.startswith("conftest.py"):
                nodeid = p.dirpath().relto(self.session.fspath)
        self._parsefactories(plugin, nodeid)
        self._seenplugins.add(plugin)

    @pytest.mark.tryfirst
    def pytest_configure(self, config):
        plugins = config.pluginmanager.getplugins()
        for plugin in plugins:
            self.pytest_plugin_registered(plugin)

    def getallfuncargnames(self, funcargnames, parentnode):
        # collect the closure of all funcargs, starting with
        # funcargnames as the initial set
        # we populate and return a arg2facdeflist mapping
        # so that the caller can reuse it and does not have to re-discover
        # factories again for each funcargname
        parentid = parentnode.nodeid
        funcargnames = list(funcargnames)
        _, setupargs = self.getsetuplist(parentnode)
        def merge(otherlist):
            for arg in otherlist:
                if arg not in funcargnames:
                    funcargnames.append(arg)
        merge(setupargs)
        arg2facdeflist = {}
        lastlen = -1
        while lastlen != len(funcargnames):
            lastlen = len(funcargnames)
            for argname in list(funcargnames):
                if argname in arg2facdeflist:
                    continue
                facdeflist = self.getfactorylist(argname, parentid)
                arg2facdeflist[argname] = facdeflist
                if facdeflist is not None:
                    for facdef in facdeflist:
                        merge(facdef.funcargnames)
        return funcargnames, arg2facdeflist

    def pytest_generate_tests(self, metafunc):
        for argname in metafunc.funcargnames:
            faclist = metafunc._arg2facdeflist[argname]
            if faclist is None:
                continue # will raise FuncargLookupError at setup time
            for facdef in faclist:
                if facdef.params is not None:
                    metafunc.parametrize(argname, facdef.params, indirect=True,
                                         scope=facdef.scope)

    def pytest_collection_modifyitems(self, items):
        # separate parametrized setups
        items[:] = parametrize_sorted(items, set(), {}, 0)

    def pytest_runtest_teardown(self, item, nextitem):
        try:
            cs1 = item.callspec
        except AttributeError:
            return
        for name in cs1.params:
            try:
                if name in nextitem.callspec.params and \
                    cs1.params[name] == nextitem.callspec.params[name]:
                    continue
            except AttributeError:
                pass
            key = (name, cs1.params[name])
            item.session._setupstate._callfinalizers(key)
            l = self._arg2finish.get(name)
            if l is not None:
                for fin in l:
                    fin()

    def _parsefactories(self, holderobj, nodeid, unittest=False):
        if holderobj in self._holderobjseen:
            return
        #print "parsefactories", holderobj
        self._holderobjseen.add(holderobj)
        for name in dir(holderobj):
            #print "check", holderobj, name
            obj = getattr(holderobj, name)
            if not callable(obj):
                continue
            # resource factories either have a pytest_funcarg__ prefix
            # or are "funcarg" marked
            marker = getattr(obj, "_pytestfixturefunction", None)
            if marker is not None:
                if not isinstance(marker, FixtureFunctionMarker):
                    # magic globals  with __getattr__
                    # give us something thats wrong for that case
                    continue
                assert not name.startswith(self._argprefix)
                argname = name
                scope = marker.scope
                params = marker.params
            elif name.startswith(self._argprefix):
                argname = name[len(self._argprefix):]
                scope = None
                params = None
            else:
                # no funcargs. check if we have a setup function.
                setup = getattr(obj, "_pytestsetup", None)
                if setup is not None:
                    scope = setup.scope
                    sf = SetupCall(self, nodeid, obj, scope, unittest)
                    self.setuplist.append(sf)
                continue
            faclist = self.arg2facspec.setdefault(argname, [])
            factorydef = FactoryDef(self, nodeid, argname, obj, scope, params)
            faclist.append(factorydef)
            ### check scope/params mismatch?

    def getsetuplist(self, node):
        nodeid = node.nodeid
        l = []
        allargnames = []
        for setupcall in self.setuplist:
            if nodeid.startswith(setupcall.baseid):
                l.append(setupcall)
                for arg in setupcall.funcargnames:
                    if arg not in allargnames:
                        allargnames.append(arg)
        l.sort(key=lambda x: x.scopenum)
        return l, allargnames


    def getfactorylist(self, argname, nodeid):
        try:
            factorydeflist = self.arg2facspec[argname]
        except KeyError:
            return None
        else:
            return self._matchfactories(factorydeflist, nodeid)

    def _matchfactories(self, factorydeflist, nodeid):
        l = []
        for factorydef in factorydeflist:
            #print "check", basepath, nodeid
            if nodeid.startswith(factorydef.baseid):
                l.append(factorydef)
        return l

    def _raiselookupfailed(self, argname, function, nodeid, getfactb=None):
        available = []
        for name, facdef in self.arg2facspec.items():
            faclist = self._matchfactories(facdef, nodeid)
            if faclist:
                available.append(name)
        msg = "LookupError: no factory found for argument %r" % (argname,)
        msg += "\n available funcargs: %s" %(", ".join(available),)
        msg += "\n use 'py.test --funcargs [testpath]' for help on them."
        lines = getfactb and getfactb() or []
        raise FuncargLookupError(function, msg, lines)

    def ensure_setupcalls(self, request):
        setuplist, allnames = self.getsetuplist(request._pyfuncitem)
        for setupcall in setuplist:
            if setupcall.active:
                continue
            request._factorystack.append(setupcall)
            mp = monkeypatch()
            try:
                mp.setattr(request, "scope", setupcall.scope)
                kwargs = {}
                for name in setupcall.funcargnames:
                    kwargs[name] = request.getfuncargvalue(name)
                scope = setupcall.scope or "function"
                scol = setupcall.scopeitem = request._getscopeitem(scope)
                self.session._setupstate.addfinalizer(setupcall.finish, scol)
                for argname in setupcall.funcargnames: # XXX all deps?
                    self.addargfinalizer(setupcall.finish, argname)
                req = kwargs.get("request", None)
                if req is not None:
                    mp.setattr(req, "addfinalizer", setupcall.addfinalizer)
                # for unittest-setup methods we need to provide
                # the correct instance
                posargs = ()
                if setupcall.unittest:
                    posargs = (request.instance,)
                setupcall.execute(posargs, kwargs)
            finally:
                mp.undo()
                request._factorystack.remove(setupcall)

    def addargfinalizer(self, finalizer, argname):
        l = self._arg2finish.setdefault(argname, [])
        l.append(finalizer)

    def removefinalizer(self, finalizer):
        for l in self._arg2finish.values():
            try:
                l.remove(finalizer)
            except ValueError:
                pass


class SetupCall:
    """ a container/helper for managing calls to setup functions. """
    def __init__(self, funcargmanager, baseid, func, scope, unittest):
        self.funcargmanager = funcargmanager
        self.baseid = baseid
        self.func = func
        startindex = unittest and 1 or None
        self.funcargnames = getfuncargnames(func, startindex=startindex)
        self.scope = scope
        self.scopenum = scopes.index(scope)
        self.active = False
        self.unittest= unittest
        self._finalizer = []

    def execute(self, posargs, kwargs):
        assert not self.active
        self.active = True
        self.func(*posargs, **kwargs)

    def addfinalizer(self, finalizer):
        assert self.active
        self._finalizer.append(finalizer)

    def finish(self):
        while self._finalizer:
            func = self._finalizer.pop()
            func()
        # check neccesity of next commented call
        self.funcargmanager.removefinalizer(self.finish)
        self.active = False

class FactoryDef:
    """ A container for a factory definition. """
    def __init__(self, funcargmanager, baseid, argname, func, scope, params):
        self.funcargmanager = funcargmanager
        self.baseid = baseid
        self.func = func
        self.argname = argname
        self.scope = scope
        self.params = params
        self.funcargnames = getfuncargnames(func)

def getfuncargnames(function, startindex=None):
    # XXX merge with main.py's varnames
    if inspect.isclass(function):
        function = function.__init__
        startindex = 1
    elif startindex is None:
        startindex = inspect.ismethod(function) and 1 or 0
    argnames = inspect.getargs(py.code.getrawcode(function))[0]
    defaults = getattr(function, 'func_defaults',
                       getattr(function, '__defaults__', None)) or ()
    numdefaults = len(defaults)
    if numdefaults:
        return argnames[startindex:-numdefaults]
    return argnames[startindex:]

# algorithm for sorting on a per-parametrized resource setup basis

def parametrize_sorted(items, ignore, cache, scopenum):
    if scopenum >= 3:
        return items
    newitems = []
    olditems = []
    slicing_argparam = None
    for item in items:
        argparamlist = getfuncargparams(item, ignore, scopenum, cache)
        if slicing_argparam is None and argparamlist:
            slicing_argparam = argparamlist[0]
            slicing_index = len(olditems)
        if slicing_argparam in argparamlist:
            newitems.append(item)
        else:
            olditems.append(item)
    if newitems:
        newignore = ignore.copy()
        newignore.add(slicing_argparam)
        newitems = parametrize_sorted(newitems + olditems[slicing_index:],
                                      newignore, cache, scopenum)
        old1 = parametrize_sorted(olditems[:slicing_index], newignore,
                                  cache, scopenum+1)
        return old1 + newitems
    else:
        olditems = parametrize_sorted(olditems, ignore, cache, scopenum+1)
    return olditems + newitems

def getfuncargparams(item, ignore, scopenum, cache):
    """ return list of (arg,param) tuple, sorted by broader scope first. """
    assert scopenum < 3  # function
    try:
        cs = item.callspec
    except AttributeError:
        return []
    if scopenum == 0:
        argparams = [x for x in cs.params.items() if x not in ignore
                        and cs._arg2scopenum[x[0]] == scopenum]
    elif scopenum == 1:  # module
        argparams = []
        for argname, param in cs.params.items():
            if cs._arg2scopenum[argname] == scopenum:
                key = (argname, param, item.fspath)
                if key in ignore:
                    continue
                argparams.append(key)
    elif scopenum == 2:  # class
        argparams = []
        for argname, param in cs.params.items():
            if cs._arg2scopenum[argname] == scopenum:
                l = cache.setdefault(item.fspath, [])
                try:
                    i = l.index(item.cls)
                except ValueError:
                    i = len(l)
                    l.append(item.cls)
                key = (argname, param, item.fspath, i)
                if key in ignore:
                    continue
                argparams.append(key)
    #elif scopenum == 3:
    #    argparams = []
    #    for argname, param in cs.params.items():
    #        if cs._arg2scopenum[argname] == scopenum:
    #            key = (argname, param, getfslineno(item.obj))
    #            if key in ignore:
    #                continue
    #            argparams.append(key)
    return argparams


def xunitsetup(obj, name):
    meth = getattr(obj, name, None)
    if meth is not None:
        if not hasattr(meth, "_pytestsetup"):
            return meth
