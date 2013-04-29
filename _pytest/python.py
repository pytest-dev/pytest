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

callable = py.builtin.callable

def getimfunc(func):
    try:
        return func.__func__
    except AttributeError:
        try:
            return func.im_func
        except AttributeError:
            return func


class FixtureFunctionMarker:
    def __init__(self, scope, params, autouse=False):
        self.scope = scope
        self.params = params
        self.autouse = autouse

    def __call__(self, function):
        if inspect.isclass(function):
            raise ValueError("class fixtures not supported (may be in the future)")
        function._pytestfixturefunction = self
        return function


def fixture(scope="function", params=None, autouse=False):
    """ (return a) decorator to mark a fixture factory function.

    This decorator can be used (with or or without parameters) to define
    a fixture function.  The name of the fixture function can later be
    referenced to cause its invocation ahead of running tests: test
    modules or classes can use the pytest.mark.usefixtures(fixturename)
    marker.  Test functions can directly use fixture names as input
    arguments in which case the fixture instance returned from the fixture
    function will be injected.

    :arg scope: the scope for which this fixture is shared, one of
                "function" (default), "class", "module", "session".

    :arg params: an optional list of parameters which will cause multiple
                invocations of the fixture function and all of the tests
                using it.

    :arg autouse: if True, the fixture func is activated for all tests that
                can see it.  If False (the default) then an explicit
                reference is needed to activate the fixture.
    """
    if callable(scope) and params is None and autouse == False:
        # direct decoration
        return FixtureFunctionMarker("function", params, autouse)(scope)
    else:
        return FixtureFunctionMarker(scope, params, autouse=autouse)

defaultfuncargprefixmarker = fixture()

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
    group.addoption('--fixtures', '--funcargs',
               action="store_true", dest="showfixtures", default=False,
               help="show available fixtures, sorted by plugin appearance")
    parser.addini("usefixtures", type="args", default=[],
        help="list of default fixtures to be used with this project")
    parser.addini("python_files", type="args",
        default=('test_*.py', '*_test.py'),
        help="glob-style file patterns for Python test module discovery")
    parser.addini("python_classes", type="args", default=("Test",),
        help="prefixes for Python test class discovery")
    parser.addini("python_functions", type="args", default=("test",),
        help="prefixes for Python test function and method discovery")

def pytest_cmdline_main(config):
    if config.option.showfixtures:
        showfixtures(config)
        return 0


def pytest_generate_tests(metafunc):
    try:
        markers = metafunc.function.parametrize
    except AttributeError:
        return
    for marker in markers:
        metafunc.parametrize(*marker.args, **marker.kwargs)

def pytest_configure(config):
    config.addinivalue_line("markers",
        "parametrize(argnames, argvalues): call a test function multiple "
        "times passing in multiple different argument value sets. Example: "
        "@parametrize('arg1', [1,2]) would lead to two calls of the decorated "
        "test function, one with arg1=1 and another with arg1=2."
        " see http://pytest.org/latest/parametrize.html for more info and "
        "examples."
    )
    config.addinivalue_line("markers",
        "usefixtures(fixturename1, fixturename2, ...): mark tests as needing "
        "all of the specified fixtures. see http://pytest.org/latest/fixture.html#usefixtures "
    )

def pytest_sessionstart(session):
    session._fixturemanager = FixtureManager(session)

@pytest.mark.trylast
def pytest_namespace():
    raises.Exception = pytest.fail.Exception
    return {
        'fixture': fixture,
        'raises' : raises,
        'collect': {
        'Module': Module, 'Class': Class, 'Instance': Instance,
        'Function': Function, 'Generator': Generator,
        '_fillfuncargs': fillfixtures}
    }

@fixture()
def pytestconfig(request):
    """ the pytest config object with access to command line opts."""
    return request.config


def pytest_pyfunc_call(__multicall__, pyfuncitem):
    if not __multicall__.execute():
        testfunction = pyfuncitem.obj
        if pyfuncitem._isyieldedfunction():
            testfunction(*pyfuncitem._args)
        else:
            funcargs = pyfuncitem.funcargs
            testargs = {}
            for arg in pyfuncitem._fixtureinfo.argnames:
                testargs[arg] = funcargs[arg]
            testfunction(**testargs)

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
        ihook = parent.session.gethookproxy(path)
        return ihook.pytest_pycollect_makemodule(path=path, parent=parent)

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
            Class = collector._getcustomclass("Class")
            return Class(name, parent=collector)
    elif collector.funcnamefilter(name) and hasattr(obj, '__call__') and \
        getfixturemarker(obj) is None:
        if is_generator(obj):
            return Generator(name, parent=collector)
        else:
            return list(collector._genfunctions(name, obj))

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
                res = self.makeitem(name, obj)
                if res is None:
                    continue
                if not isinstance(res, list):
                    res = [res]
                l.extend(res)
        l.sort(key=lambda item: item.reportinfo()[:2])
        return l

    def makeitem(self, name, obj):
        #assert self.ihook.fspath == self.fspath, self
        return self.ihook.pytest_pycollect_makeitem(
            collector=self, name=name, obj=obj)

    def _genfunctions(self, name, funcobj):
        module = self.getparent(Module).obj
        clscol = self.getparent(Class)
        cls = clscol and clscol.obj or None
        transfer_markers(funcobj, cls, module)
        fm = self.session._fixturemanager
        fixtureinfo = fm.getfixtureinfo(self, funcobj, cls)
        metafunc = Metafunc(funcobj, fixtureinfo, self.config,
                            cls=cls, module=module)
        gentesthook = self.config.hook.pytest_generate_tests
        extra = [module]
        if cls is not None:
            extra.append(cls())
        plugins = self.getplugins() + extra
        gentesthook.pcall(plugins, metafunc=metafunc)
        Function = self._getcustomclass("Function")
        if not metafunc._calls:
            yield Function(name, parent=self)
        else:
            for callspec in metafunc._calls:
                subname = "%s[%s]" %(name, callspec.id)
                yield Function(name=subname, parent=self,
                               callspec=callspec, callobj=funcobj,
                               keywords={callspec.id:True})


class FuncFixtureInfo:
    def __init__(self, argnames, names_closure, name2fixturedefs):
        self.argnames = argnames
        self.names_closure = names_closure
        self.name2fixturedefs = name2fixturedefs

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
        self.session._fixturemanager.parsefactories(self)
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
        if hasinit(self.obj):
            pytest.skip("class %s.%s with __init__ won't get collected" % (
                self.obj.__module__,
                self.obj.__name__,
            ))
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
        self.session._fixturemanager.parsefactories(self)
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



def fillfixtures(function):
    """ fill missing funcargs for a test function. """
    if 1 or getattr(function, "_args", None) is None:  # not a yielded function
        try:
            request = function._request
        except AttributeError:
            # XXX this special code path is only expected to execute
            # with the oejskit plugin.  It uses classes with funcargs
            # and we thus have to work a bit to allow this.
            fm = function.session._fixturemanager
            fi = fm.getfixtureinfo(function.parent, function.obj, None)
            function._fixtureinfo = fi
            request = function._request = FixtureRequest(function)
            request._fillfixtures()
            # prune out funcargs for jstests
            newfuncargs = {}
            for name in fi.argnames:
                newfuncargs[name] = function.funcargs[name]
            function.funcargs = newfuncargs
        else:
            request._fillfixtures()


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
            if val is _notexists:
                self._emptyparamspecified = True
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


class FuncargnamesCompatAttr:
    """ helper class so that Metafunc, Function and FixtureRequest
    don't need to each define the "funcargnames" compatibility attribute.
    """
    @property
    def funcargnames(self):
        """ alias attribute for ``fixturenames`` for pre-2.3 compatibility"""
        return self.fixturenames

class Metafunc(FuncargnamesCompatAttr):
    def __init__(self, function, fixtureinfo, config, cls=None, module=None):
        self.config = config
        self.module = module
        self.function = function
        self.fixturenames = fixtureinfo.names_closure
        self._arg2fixturedefs = fixtureinfo.name2fixturedefs
        self.cls = cls
        self.module = module
        self._calls = []
        self._ids = py.builtin.set()

    def parametrize(self, argnames, argvalues, indirect=False, ids=None,
        scope=None):
        """ Add new invocations to the underlying test function using the list
        of argvalues for the given argnames.  Parametrization is performed
        during the collection phase.  If you need to setup expensive resources
        see about setting indirect=True to do it rather at test setup time.

        :arg argnames: an argument name or a list of argument names

        :arg argvalues: The list of argvalues determines how often a test is invoked
            with different argument values.  If only one argname was specified argvalues
            is a list of simple values.  If N argnames were specified, argvalues must
            be a list of N-tuples, where each tuple-element specifies a value for its
            respective argname.

        :arg indirect: if True each argvalue corresponding to an argname will
            be passed as request.param to its respective argname fixture
            function so that it can perform more expensive setups during the
            setup phase of a test rather than at collection time.

        :arg ids: list of string ids each corresponding to the argvalues so
            that they are part of the test id. If no ids are provided they will
            be generated automatically from the argvalues.

        :arg scope: if specified it denotes the scope of the parameters.
            The scope is used for grouping tests by parameter instances.
            It will also override any fixture-function defined scope, allowing
            to set a dynamic scope using test context or configuration.
        """
        if not isinstance(argnames, (tuple, list)):
            argnames = (argnames,)
            argvalues = [(val,) for val in argvalues]
        if not argvalues:
            argvalues = [(_notexists,) * len(argnames)]

        if scope is None:
            scope = "subfunction"
        scopenum = scopes.index(scope)
        if not indirect:
            #XXX should we also check for the opposite case?
            for arg in argnames:
                if arg not in self.fixturenames:
                    raise ValueError("%r uses no fixture %r" %(
                                     self.function, arg))
        valtype = indirect and "params" or "funcargs"
        if not ids:
            ids = idmaker(argnames, argvalues)
        newcalls = []
        for callspec in self._calls or [CallSpec2(self)]:
            for i, valset in enumerate(argvalues):
                assert len(valset) == len(argnames)
                newcallspec = callspec.copy(self)
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

        :arg param: a parameter which will be exposed to a later fixture function
            invocation through the ``request.param`` attribute.
        """
        assert funcargs is None or isinstance(funcargs, dict)
        if funcargs is not None:
            for name in funcargs:
                if name not in self.fixturenames:
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

def idmaker(argnames, argvalues):
    idlist = []
    for valindex, valset in enumerate(argvalues):
        this_id = []
        for nameindex, val in enumerate(valset):
            if not isinstance(val, (float, int, str)):
                this_id.append(str(argnames[nameindex])+str(valindex))
            else:
                this_id.append(str(val))
        idlist.append("-".join(this_id))
    return idlist

def showfixtures(config):
    from _pytest.main import wrap_session
    return wrap_session(config, _showfixtures_main)

def _showfixtures_main(config, session):
    session.perform_collect()
    curdir = py.path.local()
    if session.items:
        nodeid = session.items[0].nodeid
    else:
        part = session._initialparts[0]
        nodeid = "::".join(map(str, [curdir.bestrelpath(part[0])] + part[1:]))
        nodeid.replace(session.fspath.sep, "/")

    tw = py.io.TerminalWriter()
    verbose = config.getvalue("verbose")

    fm = session._fixturemanager

    available = []
    for argname in fm._arg2fixturedefs:
        fixturedefs = fm.getfixturedefs(argname, nodeid)
        assert fixturedefs is not None
        if not fixturedefs:
            continue
        fixturedef = fixturedefs[-1]
        loc = getlocation(fixturedef.func, curdir)
        available.append((len(fixturedef.baseid),
                          fixturedef.func.__module__,
                          curdir.bestrelpath(loc),
                          fixturedef.argname, fixturedef))

    available.sort()
    currentmodule = None
    for baseid, module, bestrel, argname, fixturedef in available:
        if currentmodule != module:
            if not module.startswith("_pytest."):
                tw.line()
                tw.sep("-", "fixtures defined from %s" %(module,))
                currentmodule = module
        if verbose <= 0 and argname[0] == "_":
            continue
        if verbose > 0:
            funcargspec = "%s -- %s" %(argname, bestrel,)
        else:
            funcargspec = argname
        tw.line(funcargspec, green=True)
        loc = getlocation(fixturedef.func, curdir)
        doc = fixturedef.func.__doc__ or ""
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
class Function(FunctionMixin, pytest.Item, FuncargnamesCompatAttr):
    """ a Function Item is responsible for setting up and executing a
    Python test function.
    """
    _genid = None
    def __init__(self, name, parent, args=None, config=None,
                 callspec=None, callobj=_dummy, keywords=None, session=None):
        super(Function, self).__init__(name, parent, config=config,
                                       session=session)
        self._args = args
        if callobj is not _dummy:
            self.obj = callobj

        for name, val in (py.builtin._getfuncdict(self.obj) or {}).items():
            self.keywords[name] = val
        if keywords:
            for name, val in keywords.items():
                self.keywords[name] = val

        fm = self.session._fixturemanager
        isyield = self._isyieldedfunction()
        self._fixtureinfo = fi = fm.getfixtureinfo(self.parent, self.obj,
                                                   self.cls,
                                                   funcargs=not isyield)
        self.fixturenames = fi.names_closure
        if callspec is not None:
            self.callspec = callspec
        self._initrequest()

    def _initrequest(self):
        if self._isyieldedfunction():
            assert not hasattr(self, "callspec"), (
                "yielded functions (deprecated) cannot have funcargs")
            self.funcargs = {}
        else:
            if hasattr(self, "callspec"):
                callspec = self.callspec
                self.funcargs = callspec.funcargs.copy()
                self._genid = callspec.id
                if hasattr(callspec, "param"):
                    self.param = callspec.param
            else:
                self.funcargs = {}
        self._request = FixtureRequest(self)

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
        # check if parametrization happend with an empty list
        try:
            empty = self.callspec._emptyparamspecified
        except AttributeError:
            pass
        else:
            fs, lineno = self._getfslineno()
            pytest.skip("got empty parameter set, function %s at %s:%d" %(
                self.function.__name__, fs, lineno))
        super(Function, self).setup()
        fillfixtures(self)

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


class FixtureRequest(FuncargnamesCompatAttr):
    """ A request for a fixture from a test or fixture function.

    A request object gives access to the requesting test context
    and has an optional ``param`` attribute in case
    the fixture is parametrized indirectly.
    """

    def __init__(self, pyfuncitem):
        self._pyfuncitem = pyfuncitem
        if hasattr(pyfuncitem, '_requestparam'):
            self.param = pyfuncitem._requestparam
        #: fixture for which this request is being performed
        self.fixturename = None
        #: Scope string, one of "function", "cls", "module", "session"
        self.scope = "function"
        self.getparent = pyfuncitem.getparent
        self._funcargs  = self._pyfuncitem.funcargs.copy()
        self._fixtureinfo = fi = pyfuncitem._fixtureinfo
        self._arg2fixturedefs = fi.name2fixturedefs
        self._arg2index = {}
        self.fixturenames = self._fixtureinfo.names_closure
        self._fixturemanager = pyfuncitem.session._fixturemanager
        self._parentid = pyfuncitem.parent.nodeid
        self._fixturestack = []

    @property
    def node(self):
        """ underlying collection node (depends on current request scope)"""
        return self._getscopeitem(self.scope)

    def _getnextfixturedef(self, argname):
        fixturedefs = self._arg2fixturedefs.get(argname, None)
        if fixturedefs is None:
            # we arrive here because of a getfuncargvalue(argname) usage which
            # was naturally not knowable at parsing/collection time
            fixturedefs = self._fixturemanager.getfixturedefs(
                            argname, self._parentid)
            self._arg2fixturedefs[argname] = fixturedefs
        # fixturedefs is immutable so we maintain a decreasing index
        index = self._arg2index.get(argname, 0) - 1
        if fixturedefs is None or (-index > len(fixturedefs)):
            raise FixtureLookupError(argname, self)
        self._arg2index[argname] = index
        return fixturedefs[index]

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
        """ keywords/markers dictionary for the underlying node. """
        return self.node.keywords

    @property
    def session(self):
        """ pytest session object. """
        return self._pyfuncitem.session

    def addfinalizer(self, finalizer):
        """add finalizer/teardown function to be called after the
        last test within the requesting test context finished
        execution. """
        # XXX usually this method is shadowed by fixturedef specific ones
        self._addfinalizer(finalizer, scope=self.scope)

    def _addfinalizer(self, finalizer, scope):
        if scope != "function" and hasattr(self, "param"):
            # parametrized resources are sorted by param
            # so we rather store finalizers per (argname, param)
            colitem = (self.fixturename, self.param)
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
        try:
            self.node.keywords[marker.markname] = marker
        except AttributeError:
            raise ValueError(marker)

    def raiseerror(self, msg):
        """ raise a FixtureLookupError with the given message. """
        raise self._fixturemanager.FixtureLookupError(None, self, msg)

    def _fillfixtures(self):
        item = self._pyfuncitem
        fixturenames = getattr(item, "fixturenames", self.fixturenames)
        for argname in fixturenames:
            if argname not in item.funcargs:
                item.funcargs[argname] = self.getfuncargvalue(argname)

    def cached_setup(self, setup, teardown=None, scope="module", extrakey=None):
        """ (deprecated) Return a testing resource managed by ``setup`` &
        ``teardown`` calls.  ``scope`` and ``extrakey`` determine when the
        ``teardown`` function will be called so that subsequent calls to
        ``setup`` would recreate the resource.  With pytest-2.3 you often
        do not need ``cached_setup()`` as you can directly declare a scope
        on a fixture function and register a finalizer through
        ``request.addfinalizer()``.

        :arg teardown: function receiving a previously setup resource.
        :arg setup: a no-argument function creating a resource.
        :arg scope: a string value out of ``function``, ``class``, ``module``
            or ``session`` indicating the caching lifecycle of the resource.
        :arg extrakey: added to internal caching key of (funcargname, scope).
        """
        if not hasattr(self.config, '_setupcache'):
            self.config._setupcache = {} # XXX weakref?
        cachekey = (self.fixturename, self._getscopeitem(scope), extrakey)
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
        """ Dynamically retrieve a named fixture function argument.

        As of pytest-2.3, it is easier and usually better to access other
        fixture values by stating it as an input argument in the fixture
        function.  If you only can decide about using another fixture at test
        setup time, you may use this function to retrieve it inside a fixture
        function body.
        """
        try:
            return self._funcargs[argname]
        except KeyError:
            pass
        try:
            fixturedef = self._getnextfixturedef(argname)
        except FixtureLookupError:
            if argname == "request":
                return self
            raise
        self._fixturestack.append(fixturedef)
        try:
            result = self._getfuncargvalue(fixturedef)
            self._funcargs[argname] = result
            return result
        finally:
            self._fixturestack.pop()

    def _getfuncargvalue(self, fixturedef):
        try:
            return fixturedef.cached_result # set by fixturedef.execute()
        except AttributeError:
            pass

        # prepare request fixturename and param attributes before
        # calling into fixture function
        argname = fixturedef.argname
        node = self._pyfuncitem
        mp = monkeypatch()
        mp.setattr(self, 'fixturename', argname)
        try:
            param = node.callspec.getparam(argname)
        except (AttributeError, ValueError):
            pass
        else:
            mp.setattr(self, 'param', param, raising=False)

        # if a parametrize invocation set a scope it will override
        # the static scope defined with the fixture function
        scope = fixturedef.scope
        try:
            paramscopenum = node.callspec._arg2scopenum[argname]
        except (KeyError, AttributeError):
            pass
        else:
            if paramscopenum != scopenum_subfunction:
                scope = scopes[paramscopenum]

        # check if a higher-level scoped fixture accesses a lower level one
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

        # route request.addfinalizer to fixturedef
        mp.setattr(self, "addfinalizer", fixturedef.addfinalizer)

        # perform the fixture call
        val = fixturedef.execute(request=self)

        # prepare finalization according to scope
        # (XXX analyse exact finalizing mechanics / cleanup)
        self.session._setupstate.addfinalizer(fixturedef.finish, self.node)
        self._fixturemanager.addargfinalizer(fixturedef.finish, argname)
        for subargname in fixturedef.argnames: # XXX all deps?
            self._fixturemanager.addargfinalizer(fixturedef.finish, subargname)
        mp.undo()
        return val

    def _factorytraceback(self):
        lines = []
        for fixturedef in self._fixturestack:
            factory = fixturedef.func
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
            return self.session
        elif scope == "class":
            x = self._pyfuncitem.getparent(pytest.Class)
            if x is not None:
                return x
            scope = "module"
        if scope == "module":
            return self._pyfuncitem.getparent(pytest.Module)
        raise ValueError("unknown finalization scope %r" %(scope,))

    def __repr__(self):
        return "<FixtureRequest for %r>" %(self.node)

class ScopeMismatchError(Exception):
    """ A fixture function tries to use a different fixture function which
    which has a lower scope (e.g. a Session one calls a function one)
    """

scopes = "session module class function subfunction".split()
scopenum_subfunction = scopes.index("subfunction")
def scopemismatch(currentscope, newscope):
    return scopes.index(newscope) > scopes.index(currentscope)

class FixtureLookupError(LookupError):
    """ could not return a requested Fixture (missing or invalid). """
    def __init__(self, argname, request, msg=None):
        self.argname = argname
        self.request = request
        self.fixturestack = list(request._fixturestack)
        self.msg = msg

    def formatrepr(self):
        tblines = []
        addline = tblines.append
        stack = [self.request._pyfuncitem.obj]
        stack.extend(map(lambda x: x.func, self.fixturestack))
        msg = self.msg
        if msg is not None:
            stack = stack[:-1] # the last fixture raise an error, let's present
                               # it at the requesting side
        for function in stack:
            fspath, lineno = getfslineno(function)
            lines, _ = inspect.getsourcelines(function)
            addline("file %s, line %s" % (fspath, lineno+1))
            for i, line in enumerate(lines):
                line = line.rstrip()
                addline("  " + line)
                if line.lstrip().startswith('def'):
                    break

        if msg is None:
            fm = self.request._fixturemanager
            nodeid = self.request._parentid
            available = []
            for name, fixturedef in fm._arg2fixturedefs.items():
                faclist = list(fm._matchfactories(fixturedef, self.request._parentid))
                if faclist:
                    available.append(name)
            msg = "fixture %r not found" % (self.argname,)
            msg += "\n available fixtures: %s" %(", ".join(available),)
            msg += "\n use 'py.test --fixtures [testpath]' for help on them."

        return FixtureLookupErrorRepr(fspath, lineno, tblines, msg, self.argname)

class FixtureLookupErrorRepr(TerminalRepr):
    def __init__(self, filename, firstlineno, tblines, errorstring, argname):
        self.tblines = tblines
        self.errorstring = errorstring
        self.filename = filename
        self.firstlineno = firstlineno
        self.argname = argname

    def toterminal(self, tw):
        #tw.line("FixtureLookupError: %s" %(self.argname), red=True)
        for tbline in self.tblines:
            tw.line(tbline.rstrip())
        for line in self.errorstring.split("\n"):
            tw.line("        " + line.strip(), red=True)
        tw.line()
        tw.line("%s:%d" % (self.filename, self.firstlineno+1))

class FixtureManager:
    """
    pytest fixtures definitions and information is stored and managed
    from this class.

    During collection fm.parsefactories() is called multiple times to parse
    fixture function definitions into FixtureDef objects and internal
    data structures.

    During collection of test functions, metafunc-mechanics instantiate
    a FuncFixtureInfo object which is cached per node/func-name.
    This FuncFixtureInfo object is later retrieved by Function nodes
    which themselves offer a fixturenames attribute.

    The FuncFixtureInfo object holds information about fixtures and FixtureDefs
    relevant for a particular function.  An initial list of fixtures is
    assembled like this:

    - ini-defined usefixtures
    - autouse-marked fixtures along the collection chain up from the function
    - usefixtures markers at module/class/function level
    - test function funcargs

    Subsequently the funcfixtureinfo.fixturenames attribute is computed
    as the closure of the fixtures needed to setup the initial fixtures,
    i. e. fixtures needed by fixture functions themselves are appended
    to the fixturenames list.

    Upon the test-setup phases all fixturenames are instantiated, retrieved
    by a lookup of their FuncFixtureInfo.
    """

    _argprefix = "pytest_funcarg__"
    FixtureLookupError = FixtureLookupError
    FixtureLookupErrorRepr = FixtureLookupErrorRepr

    def __init__(self, session):
        self.session = session
        self.config = session.config
        self._arg2fixturedefs = {}
        self._seenplugins = set()
        self._holderobjseen = set()
        self._arg2finish = {}
        self._nodeid_and_autousenames = [("", self.config.getini("usefixtures"))]
        session.config.pluginmanager.register(self, "funcmanage")

        self._nodename2fixtureinfo = {}

    def getfixtureinfo(self, node, func, cls, funcargs=True):
        key = (node, func.__name__)
        try:
            return self._nodename2fixtureinfo[key]
        except KeyError:
            pass
        if funcargs and not hasattr(node, "nofuncargs"):
            if cls is not None:
                startindex = 1
            else:
                startindex = None
            argnames = getfuncargnames(func, startindex)
        else:
            argnames = ()
        usefixtures = getattr(func, "usefixtures", None)
        initialnames = argnames
        if usefixtures is not None:
            initialnames = usefixtures.args + initialnames
        fm = node.session._fixturemanager
        names_closure, arg2fixturedefs = fm.getfixtureclosure(initialnames,
                                                              node)
        fixtureinfo = FuncFixtureInfo(argnames, names_closure,
                                      arg2fixturedefs)
        self._nodename2fixtureinfo[key] = fixtureinfo
        return fixtureinfo

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
                if p.sep != "/":
                    nodeid = nodeid.replace(p.sep, "/")
        self.parsefactories(plugin, nodeid)
        self._seenplugins.add(plugin)

    @pytest.mark.tryfirst
    def pytest_configure(self, config):
        plugins = config.pluginmanager.getplugins()
        for plugin in plugins:
            self.pytest_plugin_registered(plugin)

    def _getautousenames(self, nodeid):
        """ return a tuple of fixture names to be used. """
        autousenames = []
        for baseid, basenames in self._nodeid_and_autousenames:
            if nodeid.startswith(baseid):
                if baseid:
                    i = len(baseid)
                    nextchar = nodeid[i:i+1]
                    if nextchar and nextchar not in ":/":
                        continue
                autousenames.extend(basenames)
        # make sure autousenames are sorted by scope, scopenum 0 is session
        autousenames.sort(
            key=lambda x: self._arg2fixturedefs[x][-1].scopenum)
        return autousenames

    def getfixtureclosure(self, fixturenames, parentnode):
        # collect the closure of all fixtures , starting with the given
        # fixturenames as the initial set.  As we have to visit all
        # factory definitions anyway, we also return a arg2fixturedefs
        # mapping so that the caller can reuse it and does not have
        # to re-discover fixturedefs again for each fixturename
        # (discovering matching fixtures for a given name/node is expensive)

        parentid = parentnode.nodeid
        fixturenames_closure = self._getautousenames(parentid)
        def merge(otherlist):
            for arg in otherlist:
                if arg not in fixturenames_closure:
                    fixturenames_closure.append(arg)
        merge(fixturenames)
        arg2fixturedefs = {}
        lastlen = -1
        while lastlen != len(fixturenames_closure):
            lastlen = len(fixturenames_closure)
            for argname in fixturenames_closure:
                if argname in arg2fixturedefs:
                    continue
                fixturedefs = self.getfixturedefs(argname, parentid)
                arg2fixturedefs[argname] = fixturedefs
                if fixturedefs is not None:
                    for fixturedef in fixturedefs:
                        merge(fixturedef.argnames)
        return fixturenames_closure, arg2fixturedefs

    def pytest_generate_tests(self, metafunc):
        for argname in metafunc.fixturenames:
            faclist = metafunc._arg2fixturedefs[argname]
            if faclist is None:
                continue # will raise FixtureLookupError at setup time
            for fixturedef in faclist:
                if fixturedef.params is not None:
                    metafunc.parametrize(argname, fixturedef.params, indirect=True,
                                         scope=fixturedef.scope)

    def pytest_collection_modifyitems(self, items):
        # separate parametrized setups
        items[:] = parametrize_sorted(items, set(), {}, 0)

    def pytest_runtest_teardown(self, item, nextitem):
        # XXX teardown needs to be normalized for parametrized and
        # no-parametrized functions
        try:
            cs1 = item.callspec
        except AttributeError:
            return

        # determine which fixtures are not needed anymore for the next test
        keylist = []
        for name in cs1.params:
            try:
                if name in nextitem.callspec.params and \
                    cs1.params[name] == nextitem.callspec.params[name]:
                    continue
            except AttributeError:
                pass
            key = (-cs1._arg2scopenum[name], name, cs1.params[name])
            keylist.append(key)

        # sort by scope (function scope first, then higher ones)
        keylist.sort()
        for (scopenum, name, param) in keylist:
            item.session._setupstate._callfinalizers((name, param))
            l = self._arg2finish.pop(name, None)
            if l is not None:
                for fin in reversed(l):
                    fin()

    def parsefactories(self, node_or_obj, nodeid=None, unittest=False):
        if nodeid is not None:
            holderobj = node_or_obj
        else:
            holderobj = node_or_obj.obj
            nodeid = node_or_obj.nodeid
        if holderobj in self._holderobjseen:
            return
        self._holderobjseen.add(holderobj)
        autousenames = []
        for name in dir(holderobj):
            obj = getattr(holderobj, name, None)
            if not callable(obj):
                continue
            # fixture functions have a pytest_funcarg__ prefix (pre-2.3 style)
            # or are "@pytest.fixture" marked
            marker = getfixturemarker(obj)
            if marker is None:
                if not name.startswith(self._argprefix):
                    continue
                marker = defaultfuncargprefixmarker
                name = name[len(self._argprefix):]
            elif not isinstance(marker, FixtureFunctionMarker):
                # magic globals  with __getattr__ might have got us a wrong
                # fixture attribute
                continue
            else:
                assert not name.startswith(self._argprefix)
            fixturedef = FixtureDef(self, nodeid, name, obj,
                                    marker.scope, marker.params,
                                    unittest=unittest)
            faclist = self._arg2fixturedefs.setdefault(name, [])
            faclist.append(fixturedef)
            if marker.autouse:
                autousenames.append(name)
        if autousenames:
            self._nodeid_and_autousenames.append((nodeid, autousenames))

    def getfixturedefs(self, argname, nodeid):
        try:
            fixturedefs = self._arg2fixturedefs[argname]
        except KeyError:
            return None
        else:
            return tuple(self._matchfactories(fixturedefs, nodeid))

    def _matchfactories(self, fixturedefs, nodeid):
        for fixturedef in fixturedefs:
            if nodeid.startswith(fixturedef.baseid):
                yield fixturedef

    def addargfinalizer(self, finalizer, argname):
        l = self._arg2finish.setdefault(argname, [])
        l.append(finalizer)

    def removefinalizer(self, finalizer):
        for l in self._arg2finish.values():
            try:
                l.remove(finalizer)
            except ValueError:
                pass

class FixtureDef:
    """ A container for a factory definition. """
    def __init__(self, fixturemanager, baseid, argname, func, scope, params,
        unittest=False):
        self._fixturemanager = fixturemanager
        self.baseid = baseid
        self.func = func
        self.argname = argname
        self.scope = scope
        self.scopenum = scopes.index(scope or "function")
        self.params = params
        startindex = unittest and 1 or None
        self.argnames = getfuncargnames(func, startindex=startindex)
        self.unittest = unittest
        self._finalizer = []

    def addfinalizer(self, finalizer):
        self._finalizer.append(finalizer)

    def finish(self):
        while self._finalizer:
            func = self._finalizer.pop()
            func()
        # check neccesity of next commented call
        self._fixturemanager.removefinalizer(self.finish)
        #print "finished", self
        try:
            del self.cached_result
        except AttributeError:
            pass

    def execute(self, request):
        kwargs = {}
        for newname in self.argnames:
            kwargs[newname] = request.getfuncargvalue(newname)
        if self.unittest:
            result = self.func(request.instance, **kwargs)
        else:
            fixturefunc = self.func
            # the fixture function needs to be bound to the actual
            # request.instance so that code working with "self" behaves
            # as expected. XXX request.instance should maybe return None
            # instead of raising AttributeError
            try:
                if request.instance is not None:
                    fixturefunc = getimfunc(self.func)
                    if fixturefunc != self.func:
                        fixturefunc = fixturefunc.__get__(request.instance)
            except AttributeError:
                pass
            result = fixturefunc(**kwargs)
        assert not hasattr(self, "cached_result")
        self.cached_result = result
        return result

    def __repr__(self):
        return "<FixtureDef name=%r scope=%r>" % (self.argname, self.scope)

def getfuncargnames(function, startindex=None):
    # XXX merge with main.py's varnames
    #assert not inspect.isclass(function)
    realfunction = function
    while hasattr(realfunction, "__wrapped__"):
        realfunction = realfunction.__wrapped__
    if startindex is None:
        startindex = inspect.ismethod(function) and 1 or 0
    if realfunction != function:
        startindex += len(getattr(function, "patchings", []))
        function = realfunction
    argnames = inspect.getargs(py.code.getrawcode(function))[0]
    defaults = getattr(function, 'func_defaults',
                       getattr(function, '__defaults__', None)) or ()
    numdefaults = len(defaults)
    if numdefaults:
        return tuple(argnames[startindex:-numdefaults])
    return tuple(argnames[startindex:])

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
    if getfixturemarker(meth) is None:
        return meth

def getfixturemarker(obj):
    """ return fixturemarker or None if it doesn't exist or raised
    exceptions."""
    try:
        return getattr(obj, "_pytestfixturefunction", None)
    except KeyboardInterrupt:
        raise
    except Exception:
        # some objects raise errors like request (from flask import request)
        # we don't expect them to be fixture functions
        return None

