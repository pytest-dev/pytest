""" Python test discovery, setup and run of test functions. """
import fnmatch
import functools
import py
import inspect
import sys
import pytest
from _pytest.mark import MarkDecorator, MarkerError
from py._code.code import TerminalRepr

import _pytest
cutdir = py.path.local(_pytest.__file__).dirpath()

NoneType = type(None)
NOTSET = object()
isfunction = inspect.isfunction
isclass = inspect.isclass
callable = py.builtin.callable
# used to work around a python2 exception info leak
exc_clear = getattr(sys, 'exc_clear', lambda: None)

def get_real_func(obj):
    """gets the real function object of the (possibly) wrapped object by
    functools.wraps or functools.partial.
    """
    while hasattr(obj, "__wrapped__"):
        obj = obj.__wrapped__
    if isinstance(obj, functools.partial):
        obj = obj.func
    return obj

def getfslineno(obj):
    # xxx let decorators etc specify a sane ordering
    obj = get_real_func(obj)
    if hasattr(obj, 'place_as'):
        obj = obj.place_as
    fslineno = py.code.getfslineno(obj)
    assert isinstance(fslineno[1], int), obj
    return fslineno

def getimfunc(func):
    try:
        return func.__func__
    except AttributeError:
        try:
            return func.im_func
        except AttributeError:
            return func


class FixtureFunctionMarker:
    def __init__(self, scope, params,
                 autouse=False, yieldctx=False, ids=None):
        self.scope = scope
        self.params = params
        self.autouse = autouse
        self.yieldctx = yieldctx
        self.ids = ids

    def __call__(self, function):
        if isclass(function):
            raise ValueError(
                    "class fixtures not supported (may be in the future)")
        function._pytestfixturefunction = self
        return function


def fixture(scope="function", params=None, autouse=False, ids=None):
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

    :arg ids: list of string ids each corresponding to the params
       so that they are part of the test id. If no ids are provided
       they will be generated automatically from the params.

    """
    if callable(scope) and params is None and autouse == False:
        # direct decoration
        return FixtureFunctionMarker(
                "function", params, autouse)(scope)
    if params is not None and not isinstance(params, (list, tuple)):
        params = list(params)
    return FixtureFunctionMarker(scope, params, autouse, ids=ids)

def yield_fixture(scope="function", params=None, autouse=False, ids=None):
    """ (return a) decorator to mark a yield-fixture factory function
    (EXPERIMENTAL).

    This takes the same arguments as :py:func:`pytest.fixture` but
    expects a fixture function to use a ``yield`` instead of a ``return``
    statement to provide a fixture.  See
    http://pytest.org/en/latest/yieldfixture.html for more info.
    """
    if callable(scope) and params is None and autouse == False:
        # direct decoration
        return FixtureFunctionMarker(
                "function", params, autouse, yieldctx=True)(scope)
    else:
        return FixtureFunctionMarker(scope, params, autouse,
                                     yieldctx=True, ids=ids)

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
        default=['test_*.py', '*_test.py'],
        help="glob-style file patterns for Python test module discovery")
    parser.addini("python_classes", type="args", default=["Test",],
        help="prefixes or glob names for Python test class discovery")
    parser.addini("python_functions", type="args", default=["test",],
        help="prefixes or glob names for Python test function and "
             "method discovery")

def pytest_cmdline_main(config):
    if config.option.showfixtures:
        showfixtures(config)
        return 0


def pytest_generate_tests(metafunc):
    # this misspelling is common - raise a specific error to alert the user
    if hasattr(metafunc.function, 'parameterize'):
        msg = "{0} has 'parameterize', spelling should be 'parametrize'"
        raise MarkerError(msg.format(metafunc.function.__name__))
    try:
        markers = metafunc.function.parametrize
    except AttributeError:
        return
    for marker in markers:
        metafunc.parametrize(*marker.args, **marker.kwargs)

def pytest_configure(config):
    config.addinivalue_line("markers",
        "parametrize(argnames, argvalues): call a test function multiple "
        "times passing in different arguments in turn. argvalues generally "
        "needs to be a list of values if argnames specifies only one name "
        "or a list of tuples of values if argnames specifies multiple names. "
        "Example: @parametrize('arg1', [1,2]) would lead to two calls of the "
        "decorated test function, one with arg1=1 and another with arg1=2."
        "see http://pytest.org/latest/parametrize.html for more info and "
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
        'yield_fixture': yield_fixture,
        'raises' : raises,
        'collect': {
        'Module': Module, 'Class': Class, 'Instance': Instance,
        'Function': Function, 'Generator': Generator,
        '_fillfuncargs': fillfixtures}
    }

@fixture(scope="session")
def pytestconfig(request):
    """ the pytest config object with access to command line opts."""
    return request.config


@pytest.mark.trylast
def pytest_pyfunc_call(pyfuncitem):
    testfunction = pyfuncitem.obj
    if pyfuncitem._isyieldedfunction():
        testfunction(*pyfuncitem._args)
    else:
        funcargs = pyfuncitem.funcargs
        testargs = {}
        for arg in pyfuncitem._fixtureinfo.argnames:
            testargs[arg] = funcargs[arg]
        testfunction(**testargs)
    return True

def pytest_collect_file(path, parent):
    ext = path.ext
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

@pytest.mark.hookwrapper
def pytest_pycollect_makeitem(collector, name, obj):
    outcome = yield
    res = outcome.get_result()
    if res is not None:
        raise StopIteration
    # nothing was collected elsewhere, let's do it here
    if isclass(obj):
        if collector.classnamefilter(name):
            Class = collector._getcustomclass("Class")
            outcome.force_result(Class(name, parent=collector))
    elif collector.funcnamefilter(name) and hasattr(obj, "__call__") and\
        getfixturemarker(obj) is None:
        # mock seems to store unbound methods (issue473), normalize it
        obj = getattr(obj, "__func__", obj)
        if not isfunction(obj):
            collector.warn(code="C2", message=
                "cannot collect %r because it is not a function."
                % name, )
        if getattr(obj, "__test__", True):
            if is_generator(obj):
                res = Generator(name, parent=collector)
            else:
                res = list(collector._genfunctions(name, obj))
            outcome.force_result(res)

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
        else:
            fspath, lineno = getfslineno(obj)
        modpath = self.getmodpath()
        assert isinstance(lineno, int)
        return fspath, lineno, modpath

class PyCollector(PyobjMixin, pytest.Collector):

    def funcnamefilter(self, name):
        return self._matches_prefix_or_glob_option('python_functions', name)

    def classnamefilter(self, name):
        return self._matches_prefix_or_glob_option('python_classes', name)

    def _matches_prefix_or_glob_option(self, option_name, name):
        """
        checks if the given name matches the prefix or glob-pattern defined
        in ini configuration.
        """
        for option in self.config.getini(option_name):
            if name.startswith(option):
                return True
            # check that name looks like a glob-string before calling fnmatch
            # because this is called for every name in each collected module,
            # and fnmatch is somewhat expensive to call
            elif ('*' in option or '?' in option or '[' in option) and \
                    fnmatch.fnmatch(name, option):
                return True
        return False

    def collect(self):
        if not getattr(self.obj, "__test__", True):
            return []

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
        try:
            methods = [module.pytest_generate_tests]
        except AttributeError:
            methods = []
        if hasattr(cls, "pytest_generate_tests"):
            methods.append(cls().pytest_generate_tests)
        self.ihook.pytest_generate_tests.callextra(methods, metafunc=metafunc)

        Function = self._getcustomclass("Function")
        if not metafunc._calls:
            yield Function(name, parent=self, fixtureinfo=fixtureinfo)
        else:
            # add funcargs() as fixturedefs to fixtureinfo.arg2fixturedefs
            add_funcarg_pseudo_fixture_def(self, metafunc, fm)

            for callspec in metafunc._calls:
                subname = "%s[%s]" %(name, callspec.id)
                yield Function(name=subname, parent=self,
                               callspec=callspec, callobj=funcobj,
                               fixtureinfo=fixtureinfo,
                               keywords={callspec.id:True})

def add_funcarg_pseudo_fixture_def(collector, metafunc, fixturemanager):
    # this function will transform all collected calls to a functions
    # if they use direct funcargs (i.e. direct parametrization)
    # because we want later test execution to be able to rely on
    # an existing FixtureDef structure for all arguments.
    # XXX we can probably avoid this algorithm  if we modify CallSpec2
    # to directly care for creating the fixturedefs within its methods.
    if not metafunc._calls[0].funcargs:
        return # this function call does not have direct parametrization
    # collect funcargs of all callspecs into a list of values
    arg2params = {}
    arg2scope = {}
    for callspec in metafunc._calls:
        for argname, argvalue in callspec.funcargs.items():
            assert argname not in callspec.params
            callspec.params[argname] = argvalue
            arg2params_list = arg2params.setdefault(argname, [])
            callspec.indices[argname] = len(arg2params_list)
            arg2params_list.append(argvalue)
            if argname not in arg2scope:
                scopenum = callspec._arg2scopenum.get(argname,
                                                      scopenum_function)
                arg2scope[argname] = scopes[scopenum]
        callspec.funcargs.clear()

    # register artificial FixtureDef's so that later at test execution
    # time we can rely on a proper FixtureDef to exist for fixture setup.
    arg2fixturedefs = metafunc._arg2fixturedefs
    for argname, valuelist in arg2params.items():
        # if we have a scope that is higher than function we need
        # to make sure we only ever create an according fixturedef on
        # a per-scope basis. We thus store and cache the fixturedef on the
        # node related to the scope.
        scope = arg2scope[argname]
        node = None
        if scope != "function":
            node = get_scope_node(collector, scope)
            if node is None:
                assert scope == "class" and isinstance(collector, Module)
                # use module-level collector for class-scope (for now)
                node = collector
        if node and argname in node._name2pseudofixturedef:
            arg2fixturedefs[argname] = [node._name2pseudofixturedef[argname]]
        else:
            fixturedef =  FixtureDef(fixturemanager, '', argname,
                           get_direct_param_fixture_func,
                           arg2scope[argname],
                           valuelist, False, False)
            arg2fixturedefs[argname] = [fixturedef]
            if node is not None:
                node._name2pseudofixturedef[argname] = fixturedef


def get_direct_param_fixture_func(request):
    return request.param

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
            raise self.CollectError(
                py.code.ExceptionInfo().getrepr(style="short"))
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
        setup_module = xunitsetup(self.obj, "setUpModule")
        if setup_module is None:
            setup_module = xunitsetup(self.obj, "setup_module")
        if setup_module is not None:
            #XXX: nose compat hack, move to nose plugin
            # if it takes a positional arg, its probably a pytest style one
            # so we pass the current module object
            if inspect.getargspec(setup_module)[0]:
                setup_module(self.obj)
            else:
                setup_module()
        fin = getattr(self.obj, 'tearDownModule', None)
        if fin is None:
            fin = getattr(self.obj, 'teardown_module', None)
        if fin is not None:
            #XXX: nose compat hack, move to nose plugin
            # if it takes a positional arg, it's probably a pytest style one
            # so we pass the current module object
            if inspect.getargspec(fin)[0]:
                finalizer = lambda: fin(self.obj)
            else:
                finalizer = fin
            self.addfinalizer(finalizer)


class Class(PyCollector):
    """ Collector for test methods. """
    def collect(self):
        if hasinit(self.obj):
            self.warn("C1", "cannot collect test class %r because it has a "
                "__init__ constructor" % self.obj.__name__)
            return []
        return [self._getcustomclass("Instance")(name="()", parent=self)]

    def setup(self):
        setup_class = xunitsetup(self.obj, 'setup_class')
        if setup_class is not None:
            setup_class = getattr(setup_class, 'im_func', setup_class)
            setup_class = getattr(setup_class, '__func__', setup_class)
            setup_class(self.obj)

        fin_class = getattr(self.obj, 'teardown_class', None)
        if fin_class is not None:
            fin_class = getattr(fin_class, 'im_func', fin_class)
            fin_class = getattr(fin_class, '__func__', fin_class)
            self.addfinalizer(lambda: fin_class(self.obj))

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
            setup_name = 'setup_method'
            teardown_name = 'teardown_method'
        else:
            setup_name = 'setup_function'
            teardown_name = 'teardown_function'
        setup_func_or_method = xunitsetup(obj, setup_name)
        if setup_func_or_method is not None:
            setup_func_or_method(self.obj)
        fin = getattr(obj, teardown_name, None)
        if fin is not None:
            self.addfinalizer(lambda: fin(self.obj))

    def _prunetraceback(self, excinfo):
        if hasattr(self, '_obj') and not self.config.option.fulltrace:
            code = py.code.Code(get_real_func(self.obj))
            path, firstlineno = code.path, code.firstlineno
            traceback = excinfo.traceback
            ntraceback = traceback.cut(path=path, firstlineno=firstlineno)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(path=path)
                if ntraceback == traceback:
                    ntraceback = ntraceback.cut(excludepath=cutdir)
            excinfo.traceback = ntraceback.filter()
            # issue364: mark all but first and last frames to
            # only show a single-line message for each frame
            if self.config.option.tbstyle == "auto":
                if len(excinfo.traceback) > 2:
                    for entry in excinfo.traceback[1:-1]:
                        entry.set_repr_style('short')

    def _repr_failure_py(self, excinfo, style="long"):
        if excinfo.errisinstance(pytest.fail.Exception):
            if not excinfo.value.pytrace:
                return str(excinfo.value)
        return super(FunctionMixin, self)._repr_failure_py(excinfo,
            style=style)

    def repr_failure(self, excinfo, outerr=None):
        assert outerr is None, "XXX outerr usage is deprecated"
        style = self.config.option.tbstyle
        if style == "auto":
            style = "long"
        return self._repr_failure_py(excinfo, style=style)


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
        self.keywords = {}
        self.indices = {}

    def copy(self, metafunc):
        cs = CallSpec2(self.metafunc)
        cs.funcargs.update(self.funcargs)
        cs.params.update(self.params)
        cs.keywords.update(self.keywords)
        cs.indices.update(self.indices)
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

    def setmulti(self, valtype, argnames, valset, id, keywords, scopenum,
                 param_index):
        for arg,val in zip(argnames, valset):
            self._checkargnotcontained(arg)
            getattr(self, valtype)[arg] = val
            self.indices[arg] = param_index
            self._arg2scopenum[arg] = scopenum
            if val is _notexists:
                self._emptyparamspecified = True
        self._idlist.append(id)
        self.keywords.update(keywords)

    def setall(self, funcargs, id, param):
        for x in funcargs:
            self._checkargnotcontained(x)
        self.funcargs.update(funcargs)
        if id is not _notexists:
            self._idlist.append(id)
        if param is not _notexists:
            assert self._globalparam is _notexists
            self._globalparam = param
        for arg in funcargs:
            self._arg2scopenum[arg] = scopenum_function


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
        self._calls = []
        self._ids = py.builtin.set()

    def parametrize(self, argnames, argvalues, indirect=False, ids=None,
        scope=None):
        """ Add new invocations to the underlying test function using the list
        of argvalues for the given argnames.  Parametrization is performed
        during the collection phase.  If you need to setup expensive resources
        see about setting indirect=True to do it rather at test setup time.

        :arg argnames: a comma-separated string denoting one or more argument
                       names, or a list/tuple of argument strings.

        :arg argvalues: The list of argvalues determines how often a
            test is invoked with different argument values.  If only one
            argname was specified argvalues is a list of simple values.  If N
            argnames were specified, argvalues must be a list of N-tuples,
            where each tuple-element specifies a value for its respective
            argname.

        :arg indirect: if True each argvalue corresponding to an argname will
            be passed as request.param to its respective argname fixture
            function so that it can perform more expensive setups during the
            setup phase of a test rather than at collection time.

        :arg ids: list of string ids, or a callable.
            If strings, each is corresponding to the argvalues so that they are
            part of the test id.
            If callable, it should take one argument (a single argvalue) and return
            a string or return None. If None, the automatically generated id for that
            argument will be used.
            If no ids are provided they will be generated automatically from
            the argvalues.

        :arg scope: if specified it denotes the scope of the parameters.
            The scope is used for grouping tests by parameter instances.
            It will also override any fixture-function defined scope, allowing
            to set a dynamic scope using test context or configuration.
        """

        # individual parametrized argument sets can be wrapped in a series
        # of markers in which case we unwrap the values and apply the mark
        # at Function init
        newkeywords = {}
        unwrapped_argvalues = []
        for i, argval in enumerate(argvalues):
            while isinstance(argval, MarkDecorator):
                newmark = MarkDecorator(argval.markname,
                                        argval.args[:-1], argval.kwargs)
                newmarks = newkeywords.setdefault(i, {})
                newmarks[newmark.markname] = newmark
                argval = argval.args[-1]
            unwrapped_argvalues.append(argval)
        argvalues = unwrapped_argvalues

        if not isinstance(argnames, (tuple, list)):
            argnames = [x.strip() for x in argnames.split(",") if x.strip()]
            if len(argnames) == 1:
                argvalues = [(val,) for val in argvalues]
        if not argvalues:
            argvalues = [(_notexists,) * len(argnames)]

        if scope is None:
            scope = "function"
        scopenum = scopes.index(scope)
        if not indirect:
            #XXX should we also check for the opposite case?
            for arg in argnames:
                if arg not in self.fixturenames:
                    raise ValueError("%r uses no fixture %r" %(
                                     self.function, arg))
        valtype = indirect and "params" or "funcargs"
        idfn = None
        if callable(ids):
            idfn = ids
            ids = None
        if ids and len(ids) != len(argvalues):
            raise ValueError('%d tests specified with %d ids' %(
                             len(argvalues), len(ids)))
        if not ids:
            ids = idmaker(argnames, argvalues, idfn)
        newcalls = []
        for callspec in self._calls or [CallSpec2(self)]:
            for param_index, valset in enumerate(argvalues):
                assert len(valset) == len(argnames)
                newcallspec = callspec.copy(self)
                newcallspec.setmulti(valtype, argnames, valset, ids[param_index],
                                     newkeywords.get(param_index, {}), scopenum,
                                     param_index)
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


def _idval(val, argname, idx, idfn):
    if idfn:
        try:
            s = idfn(val)
            if s:
                return s
        except Exception:
            pass
    if isinstance(val, (float, int, str, bool, NoneType)):
        return str(val)
    return str(argname)+str(idx)

def _idvalset(idx, valset, argnames, idfn):
    this_id = [_idval(val, argname, idx, idfn)
               for val, argname in zip(valset, argnames)]
    return "-".join(this_id)

def idmaker(argnames, argvalues, idfn=None):
    ids = [_idvalset(valindex, valset, argnames, idfn)
           for valindex, valset in enumerate(argvalues)]
    if len(set(ids)) < len(ids):
        # user may have provided a bad idfn which means the ids are not unique
        ids = [str(i) + testid for i, testid in enumerate(ids)]
    return ids

def showfixtures(config):
    from _pytest.main import wrap_session
    return wrap_session(config, _showfixtures_main)

def _showfixtures_main(config, session):
    import _pytest.config
    session.perform_collect()
    curdir = py.path.local()
    tw = _pytest.config.create_terminal_writer(config)
    verbose = config.getvalue("verbose")

    fm = session._fixturemanager

    available = []
    for argname, fixturedefs in fm._arg2fixturedefs.items():
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
            for line in doc.strip().split("\n"):
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

    This helper produces a ``py.code.ExceptionInfo()`` object.

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

    Performance note:
    -----------------

    Similar to caught exception objects in Python, explicitly clearing
    local references to returned ``py.code.ExceptionInfo`` objects can
    help the Python interpreter speed up its garbage collection.

    Clearing those references breaks a reference cycle
    (``ExceptionInfo`` --> caught exception --> frame stack raising
    the exception --> current frame stack --> local variables -->
    ``ExceptionInfo``) which makes Python keep all objects referenced
    from that cycle (including all local variables in the current
    frame) alive until the next cyclic garbage collection run. See the
    official Python ``try`` statement documentation for more detailed
    information.

    """
    __tracebackhide__ = True
    if ExpectedException is AssertionError:
        # we want to catch a AssertionError
        # replace our subclass with the builtin one
        # see https://bitbucket.org/pytest-dev/pytest/issue/176/pytestraises
        from _pytest.assertion.util import BuiltinAssertionError \
            as ExpectedException
    msg = ("exceptions must be old-style classes or"
           " derived from BaseException, not %s")
    if isinstance(ExpectedException, tuple):
        for exc in ExpectedException:
            if not inspect.isclass(exc):
                raise TypeError(msg % type(exc))
    elif not inspect.isclass(ExpectedException):
        raise TypeError(msg % type(ExpectedException))

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
        if sys.version_info < (2, 7):
            # py26: on __exit__() exc_value often does not contain the
            # exception value.
            # http://bugs.python.org/issue7853
            if not isinstance(tp[1], BaseException):
                exc_type, value, traceback = tp
                tp = exc_type, exc_type(value), traceback
        self.excinfo.__init__(tp)
        return issubclass(self.excinfo.type, self.ExpectedException)

#
#  the basic pytest Function item
#

class Function(FunctionMixin, pytest.Item, FuncargnamesCompatAttr):
    """ a Function Item is responsible for setting up and executing a
    Python test function.
    """
    _genid = None
    def __init__(self, name, parent, args=None, config=None,
                 callspec=None, callobj=NOTSET, keywords=None, session=None,
                 fixtureinfo=None):
        super(Function, self).__init__(name, parent, config=config,
                                       session=session)
        self._args = args
        if callobj is not NOTSET:
            self.obj = callobj

        self.keywords.update(self.obj.__dict__)
        if callspec:
            self.callspec = callspec
            self.keywords.update(callspec.keywords)
        if keywords:
            self.keywords.update(keywords)

        if fixtureinfo is None:
            fixtureinfo = self.session._fixturemanager.getfixtureinfo(
                self.parent, self.obj, self.cls,
                funcargs=not self._isyieldedfunction())
        self._fixtureinfo = fixtureinfo
        self.fixturenames = fixtureinfo.names_closure
        self._initrequest()

    def _initrequest(self):
        self.funcargs = {}
        if self._isyieldedfunction():
            assert not hasattr(self, "callspec"), (
                "yielded functions (deprecated) cannot have funcargs")
        else:
            if hasattr(self, "callspec"):
                callspec = self.callspec
                assert not callspec.funcargs
                self._genid = callspec.id
                if hasattr(callspec, "param"):
                    self.param = callspec.param
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
            self.callspec._emptyparamspecified
        except AttributeError:
            pass
        else:
            fs, lineno = self._getfslineno()
            pytest.skip("got empty parameter set, function %s at %s:%d" %(
                self.function.__name__, fs, lineno))
        super(Function, self).setup()
        fillfixtures(self)


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
        #: fixture for which this request is being performed
        self.fixturename = None
        #: Scope string, one of "function", "cls", "module", "session"
        self.scope = "function"
        self._funcargs  = {}
        self._fixturedefs = {}
        fixtureinfo = pyfuncitem._fixtureinfo
        self._arg2fixturedefs = fixtureinfo.name2fixturedefs.copy()
        self._arg2index = {}
        self.fixturenames = fixtureinfo.names_closure
        self._fixturemanager = pyfuncitem.session._fixturemanager

    @property
    def node(self):
        """ underlying collection node (depends on current request scope)"""
        return self._getscopeitem(self.scope)


    def _getnextfixturedef(self, argname):
        fixturedefs = self._arg2fixturedefs.get(argname, None)
        if fixturedefs is None:
            # we arrive here because of a  a dynamic call to
            # getfuncargvalue(argname) usage which was naturally
            # not known at parsing/collection time
            fixturedefs = self._fixturemanager.getfixturedefs(
                            argname, self._pyfuncitem.parent.nodeid)
            self._arg2fixturedefs[argname] = fixturedefs
        # fixturedefs list is immutable so we maintain a decreasing index
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
            function = getattr(self, "function", None)
            if function is not None:
                return py.builtin._getimself(function)

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
        colitem = self._getscopeitem(scope)
        self._pyfuncitem.session._setupstate.addfinalizer(
            finalizer=finalizer, colitem=colitem)

    def applymarker(self, marker):
        """ Apply a marker to a single test function invocation.
        This method is useful if you don't want to have a keyword/marker
        on all function invocations.

        :arg marker: a :py:class:`_pytest.mark.MarkDecorator` object
            created by a call to ``pytest.mark.NAME(...)``.
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
            self._check_scope(self.fixturename, self.scope, scope)
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
        return self._get_active_fixturedef(argname).cached_result[0]

    def _get_active_fixturedef(self, argname):
        try:
            return self._fixturedefs[argname]
        except KeyError:
            try:
                fixturedef = self._getnextfixturedef(argname)
            except FixtureLookupError:
                if argname == "request":
                    class PseudoFixtureDef:
                        cached_result = (self, [0], None)
                        scope = "function"
                    return PseudoFixtureDef
                raise
        # remove indent to prevent the python3 exception
        # from leaking into the call
        result = self._getfuncargvalue(fixturedef)
        self._funcargs[argname] = result
        self._fixturedefs[argname] = fixturedef
        return fixturedef

    def _get_fixturestack(self):
        current = self
        l = []
        while 1:
            fixturedef = getattr(current, "_fixturedef", None)
            if fixturedef is None:
                l.reverse()
                return l
            l.append(fixturedef)
            current = current._parent_request

    def _getfuncargvalue(self, fixturedef):
        # prepare a subrequest object before calling fixture function
        # (latter managed by fixturedef)
        argname = fixturedef.argname
        funcitem = self._pyfuncitem
        scope = fixturedef.scope
        try:
            param = funcitem.callspec.getparam(argname)
        except (AttributeError, ValueError):
            param = NOTSET
            param_index = 0
        else:
            # indices might not be set if old-style metafunc.addcall() was used
            param_index = funcitem.callspec.indices.get(argname, 0)
            # if a parametrize invocation set a scope it will override
            # the static scope defined with the fixture function
            paramscopenum = funcitem.callspec._arg2scopenum.get(argname)
            if paramscopenum is not None:
                scope = scopes[paramscopenum]

        subrequest = SubRequest(self, scope, param, param_index, fixturedef)

        # check if a higher-level scoped fixture accesses a lower level one
        subrequest._check_scope(argname, self.scope, scope)

        # clear sys.exc_info before invoking the fixture (python bug?)
        # if its not explicitly cleared it will leak into the call
        exc_clear()
        try:
            # call the fixture function
            val = fixturedef.execute(request=subrequest)
        finally:
            # if fixture function failed it might have registered finalizers
            self.session._setupstate.addfinalizer(fixturedef.finish,
                                                  subrequest.node)
        return val

    def _check_scope(self, argname, invoking_scope, requested_scope):
        if argname == "request":
            return
        if scopemismatch(invoking_scope, requested_scope):
            # try to report something helpful
            lines = self._factorytraceback()
            pytest.fail("ScopeMismatch: You tried to access the %r scoped "
                "fixture %r with a %r scoped request object, "
                "involved factories\n%s" %(
                (requested_scope, argname, invoking_scope, "\n".join(lines))),
                pytrace=False)

    def _factorytraceback(self):
        lines = []
        for fixturedef in self._get_fixturestack():
            factory = fixturedef.func
            fs, lineno = getfslineno(factory)
            p = self._pyfuncitem.session.fspath.bestrelpath(fs)
            args = inspect.formatargspec(*inspect.getargspec(factory))
            lines.append("%s:%d:  def %s%s" %(
                p, lineno, factory.__name__, args))
        return lines

    def _getscopeitem(self, scope):
        if scope == "function":
            # this might also be a non-function Item despite its attribute name
            return self._pyfuncitem
        node = get_scope_node(self._pyfuncitem, scope)
        if node is None and scope == "class":
            # fallback to function item itself
            node = self._pyfuncitem
        assert node
        return node

    def __repr__(self):
        return "<FixtureRequest for %r>" %(self.node)


class SubRequest(FixtureRequest):
    """ a sub request for handling getting a fixture from a
    test function/fixture. """
    def __init__(self, request, scope, param, param_index, fixturedef):
        self._parent_request = request
        self.fixturename = fixturedef.argname
        if param is not NOTSET:
            self.param = param
        self.param_index = param_index
        self.scope = scope
        self._fixturedef = fixturedef
        self.addfinalizer = fixturedef.addfinalizer
        self._pyfuncitem = request._pyfuncitem
        self._funcargs  = request._funcargs
        self._fixturedefs = request._fixturedefs
        self._arg2fixturedefs = request._arg2fixturedefs
        self._arg2index = request._arg2index
        self.fixturenames = request.fixturenames
        self._fixturemanager = request._fixturemanager

    def __repr__(self):
        return "<SubRequest %r for %r>" % (self.fixturename, self._pyfuncitem)


class ScopeMismatchError(Exception):
    """ A fixture function tries to use a different fixture function which
    which has a lower scope (e.g. a Session one calls a function one)
    """

scopes = "session module class function".split()
scopenum_function = scopes.index("function")
def scopemismatch(currentscope, newscope):
    return scopes.index(newscope) > scopes.index(currentscope)


class FixtureLookupError(LookupError):
    """ could not return a requested Fixture (missing or invalid). """
    def __init__(self, argname, request, msg=None):
        self.argname = argname
        self.request = request
        self.fixturestack = request._get_fixturestack()
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
            try:
                lines, _ = inspect.getsourcelines(get_real_func(function))
            except IOError:
                error_msg = "file %s, line %s: source code not available"
                addline(error_msg % (fspath, lineno+1))
            else:
                addline("file %s, line %s" % (fspath, lineno+1))
                for i, line in enumerate(lines):
                    line = line.rstrip()
                    addline("  " + line)
                    if line.lstrip().startswith('def'):
                        break

        if msg is None:
            fm = self.request._fixturemanager
            available = []
            for name, fixturedef in fm._arg2fixturedefs.items():
                parentid = self.request._pyfuncitem.parent.nodeid
                faclist = list(fm._matchfactories(fixturedef, parentid))
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


    def getfixtureinfo(self, node, func, cls, funcargs=True):
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
        return FuncFixtureInfo(argnames, names_closure, arg2fixturedefs)

    ### XXX this hook should be called for historic events like pytest_configure
    ### so that we don't have to do the below pytest_configure hook
    def pytest_plugin_registered(self, plugin):
        if plugin in self._seenplugins:
            return
        nodeid = None
        try:
            p = py.path.local(plugin.__file__)
        except AttributeError:
            pass
        else:
            # construct the base nodeid which is later used to check
            # what fixtures are visible for particular tests (as denoted
            # by their test id)
            if p.basename.startswith("conftest.py"):
                nodeid = p.dirpath().relto(self.config.rootdir)
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
                if fixturedefs:
                    arg2fixturedefs[argname] = fixturedefs
                    merge(fixturedefs[-1].argnames)
        return fixturenames_closure, arg2fixturedefs

    def pytest_generate_tests(self, metafunc):
        for argname in metafunc.fixturenames:
            faclist = metafunc._arg2fixturedefs.get(argname)
            if faclist:
                fixturedef = faclist[-1]
                if fixturedef.params is not None:
                    func_params = getattr(getattr(metafunc.function, 'parametrize', None), 'args', [[None]])
                    # skip directly parametrized arguments
                    if argname not in func_params and argname not in func_params[0]:
                        metafunc.parametrize(argname, fixturedef.params,
                                             indirect=True, scope=fixturedef.scope,
                                             ids=fixturedef.ids)
            else:
                continue # will raise FixtureLookupError at setup time

    def pytest_collection_modifyitems(self, items):
        # separate parametrized setups
        items[:] = reorder_items(items)

    def parsefactories(self, node_or_obj, nodeid=NOTSET, unittest=False):
        if nodeid is not NOTSET:
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
                                    yieldctx=marker.yieldctx,
                                    unittest=unittest, ids=marker.ids)
            faclist = self._arg2fixturedefs.setdefault(name, [])
            if fixturedef.has_location:
                faclist.append(fixturedef)
            else:
                # fixturedefs with no location are at the front
                # so this inserts the current fixturedef after the
                # existing fixturedefs from external plugins but
                # before the fixturedefs provided in conftests.
                i = len([f for f in faclist if not f.has_location])
                faclist.insert(i, fixturedef)
            if marker.autouse:
                autousenames.append(name)
        if autousenames:
            self._nodeid_and_autousenames.append((nodeid or '', autousenames))

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


def fail_fixturefunc(fixturefunc, msg):
    fs, lineno = getfslineno(fixturefunc)
    location = "%s:%s" % (fs, lineno+1)
    source = py.code.Source(fixturefunc)
    pytest.fail(msg + ":\n\n" + str(source.indent()) + "\n" + location,
                pytrace=False)

def call_fixture_func(fixturefunc, request, kwargs, yieldctx):
    if yieldctx:
        if not is_generator(fixturefunc):
            fail_fixturefunc(fixturefunc,
                msg="yield_fixture requires yield statement in function")
        iter = fixturefunc(**kwargs)
        next = getattr(iter, "__next__", None)
        if next is None:
            next = getattr(iter, "next")
        res = next()
        def teardown():
            try:
                next()
            except StopIteration:
                pass
            else:
                fail_fixturefunc(fixturefunc,
                    "yield_fixture function has more than one 'yield'")
        request.addfinalizer(teardown)
    else:
        if is_generator(fixturefunc):
            fail_fixturefunc(fixturefunc,
                msg="pytest.fixture functions cannot use ``yield``. "
                    "Instead write and return an inner function/generator "
                    "and let the consumer call and iterate over it.")
        res = fixturefunc(**kwargs)
    return res

class FixtureDef:
    """ A container for a factory definition. """
    def __init__(self, fixturemanager, baseid, argname, func, scope, params,
                 yieldctx, unittest=False, ids=None):
        self._fixturemanager = fixturemanager
        self.baseid = baseid or ''
        self.has_location = baseid is not None
        self.func = func
        self.argname = argname
        self.scope = scope
        self.scopenum = scopes.index(scope or "function")
        self.params = params
        startindex = unittest and 1 or None
        self.argnames = getfuncargnames(func, startindex=startindex)
        self.yieldctx = yieldctx
        self.unittest = unittest
        self.ids = ids
        self._finalizer = []

    def addfinalizer(self, finalizer):
        self._finalizer.append(finalizer)

    def finish(self):
        try:
            while self._finalizer:
                func = self._finalizer.pop()
                func()
        finally:
            # even if finalization fails, we invalidate
            # the cached fixture value
            if hasattr(self, "cached_result"):
                del self.cached_result

    def execute(self, request):
        # get required arguments and register our own finish()
        # with their finalization
        kwargs = {}
        for argname in self.argnames:
            fixturedef = request._get_active_fixturedef(argname)
            result, arg_cache_key, exc = fixturedef.cached_result
            request._check_scope(argname, request.scope, fixturedef.scope)
            kwargs[argname] = result
            if argname != "request":
                fixturedef.addfinalizer(self.finish)

        my_cache_key = request.param_index
        cached_result = getattr(self, "cached_result", None)
        if cached_result is not None:
            result, cache_key, err = cached_result
            if my_cache_key == cache_key:
                if err is not None:
                    py.builtin._reraise(*err)
                else:
                    return result
            # we have a previous but differently parametrized fixture instance
            # so we need to tear it down before creating a new one
            self.finish()
            assert not hasattr(self, "cached_result")

        fixturefunc = self.func

        if self.unittest:
            if request.instance is not None:
                # bind the unbound method to the TestCase instance
                fixturefunc = self.func.__get__(request.instance)
        else:
            # the fixture function needs to be bound to the actual
            # request.instance so that code working with "self" behaves
            # as expected.
            if request.instance is not None:
                fixturefunc = getimfunc(self.func)
                if fixturefunc != self.func:
                    fixturefunc = fixturefunc.__get__(request.instance)

        try:
            result = call_fixture_func(fixturefunc, request, kwargs,
                                       self.yieldctx)
        except Exception:
            self.cached_result = (None, my_cache_key, sys.exc_info())
            raise
        self.cached_result = (result, my_cache_key, None)
        return result

    def __repr__(self):
        return ("<FixtureDef name=%r scope=%r baseid=%r >" %
                (self.argname, self.scope, self.baseid))

def num_mock_patch_args(function):
    """ return number of arguments used up by mock arguments (if any) """
    patchings = getattr(function, "patchings", None)
    if not patchings:
        return 0
    mock = sys.modules.get("mock", sys.modules.get("unittest.mock", None))
    if mock is not None:
        return len([p for p in patchings
                        if not p.attribute_name and p.new is mock.DEFAULT])
    return len(patchings)


def getfuncargnames(function, startindex=None):
    # XXX merge with main.py's varnames
    #assert not inspect.isclass(function)
    realfunction = function
    while hasattr(realfunction, "__wrapped__"):
        realfunction = realfunction.__wrapped__
    if startindex is None:
        startindex = inspect.ismethod(function) and 1 or 0
    if realfunction != function:
        startindex += num_mock_patch_args(function)
        function = realfunction
    if isinstance(function, functools.partial):
        argnames = inspect.getargs(py.code.getrawcode(function.func))[0]
        partial = function
        argnames = argnames[len(partial.args):]
        if partial.keywords:
            for kw in partial.keywords:
                argnames.remove(kw)
    else:
        argnames = inspect.getargs(py.code.getrawcode(function))[0]
    defaults = getattr(function, 'func_defaults',
                       getattr(function, '__defaults__', None)) or ()
    numdefaults = len(defaults)
    if numdefaults:
        return tuple(argnames[startindex:-numdefaults])
    return tuple(argnames[startindex:])

# algorithm for sorting on a per-parametrized resource setup basis
# it is called for scopenum==0 (session) first and performs sorting
# down to the lower scopes such as to minimize number of "high scope"
# setups and teardowns

def reorder_items(items):
    argkeys_cache = {}
    for scopenum in range(0, scopenum_function):
        argkeys_cache[scopenum] = d = {}
        for item in items:
            keys = set(get_parametrized_fixture_keys(item, scopenum))
            if keys:
                d[item] = keys
    return reorder_items_atscope(items, set(), argkeys_cache, 0)

def reorder_items_atscope(items, ignore, argkeys_cache, scopenum):
    if scopenum >= scopenum_function or len(items) < 3:
        return items
    items_done = []
    while 1:
        items_before, items_same, items_other, newignore = \
                slice_items(items, ignore, argkeys_cache[scopenum])
        items_before = reorder_items_atscope(
                            items_before, ignore, argkeys_cache,scopenum+1)
        if items_same is None:
            # nothing to reorder in this scope
            assert items_other is None
            return items_done + items_before
        items_done.extend(items_before)
        items = items_same + items_other
        ignore = newignore


def slice_items(items, ignore, scoped_argkeys_cache):
    # we pick the first item which uses a fixture instance in the
    # requested scope and which we haven't seen yet.  We slice the input
    # items list into a list of items_nomatch, items_same and
    # items_other
    if scoped_argkeys_cache:  # do we need to do work at all?
        it = iter(items)
        # first find a slicing key
        for i, item in enumerate(it):
            argkeys = scoped_argkeys_cache.get(item)
            if argkeys is not None:
                argkeys = argkeys.difference(ignore)
                if argkeys:  # found a slicing key
                    slicing_argkey = argkeys.pop()
                    items_before = items[:i]
                    items_same = [item]
                    items_other = []
                    # now slice the remainder of the list
                    for item in it:
                        argkeys = scoped_argkeys_cache.get(item)
                        if argkeys and slicing_argkey in argkeys and \
                            slicing_argkey not in ignore:
                            items_same.append(item)
                        else:
                            items_other.append(item)
                    newignore = ignore.copy()
                    newignore.add(slicing_argkey)
                    return (items_before, items_same, items_other, newignore)
    return items, None, None, None

def get_parametrized_fixture_keys(item, scopenum):
    """ return list of keys for all parametrized arguments which match
    the specified scope. """
    assert scopenum < scopenum_function  # function
    try:
        cs = item.callspec
    except AttributeError:
        pass
    else:
        # cs.indictes.items() is random order of argnames but
        # then again different functions (items) can change order of
        # arguments so it doesn't matter much probably
        for argname, param_index in cs.indices.items():
            if cs._arg2scopenum[argname] != scopenum:
                continue
            if scopenum == 0:    # session
                key = (argname, param_index)
            elif scopenum == 1:  # module
                key = (argname, param_index, item.fspath)
            elif scopenum == 2:  # class
                key = (argname, param_index, item.fspath, item.cls)
            yield key


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

scopename2class = {
    'class': Class,
    'module': Module,
    'function': pytest.Item,
}
def get_scope_node(node, scope):
    cls = scopename2class.get(scope)
    if cls is None:
        if scope == "session":
            return node.session
        raise ValueError("unknown scope")
    return node.getparent(cls)
