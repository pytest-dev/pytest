""" Python test discovery, setup and run of test functions. """
from __future__ import absolute_import, division, print_function

import fnmatch
import inspect
import sys
import os
import collections
import math
from itertools import count

import py
from _pytest.mark import MarkerError
from _pytest.config import hookimpl

import _pytest
import _pytest._pluggy as pluggy
from _pytest import fixtures
from _pytest import main
from _pytest.compat import (
    isclass, isfunction, is_generator, _escape_strings,
    REGEX_TYPE, STRING_TYPES, NoneType, NOTSET,
    get_real_func, getfslineno, safe_getattr,
    safe_str, getlocation, enum,
)
from _pytest.runner import fail

cutdir1 = py.path.local(pluggy.__file__.rstrip("oc"))
cutdir2 = py.path.local(_pytest.__file__).dirpath()
cutdir3 = py.path.local(py.__file__).dirpath()


def filter_traceback(entry):
    """Return True if a TracebackEntry instance should be removed from tracebacks:
    * dynamically generated code (no code to show up for it);
    * internal traceback from pytest or its internal libraries, py and pluggy.
    """
    # entry.path might sometimes return a str object when the entry
    # points to dynamically generated code
    # see https://bitbucket.org/pytest-dev/py/issues/71
    raw_filename = entry.frame.code.raw.co_filename
    is_generated = '<' in raw_filename and '>' in raw_filename
    if is_generated:
        return False
    # entry.path might point to an inexisting file, in which case it will
    # alsso return a str object. see #1133
    p = py.path.local(entry.path)
    return p != cutdir1 and not p.relto(cutdir2) and not p.relto(cutdir3)



def pyobj_property(name):
    def get(self):
        node = self.getparent(getattr(__import__('pytest'), name))
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
    group.addoption(
        '--fixtures-per-test',
        action="store_true",
        dest="show_fixtures_per_test",
        default=False,
        help="show fixtures per test",
    )
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

    group.addoption("--import-mode", default="prepend",
        choices=["prepend", "append"], dest="importmode",
        help="prepend/append to sys.path when importing test modules, "
             "default is to prepend.")


def pytest_cmdline_main(config):
    if config.option.showfixtures:
        showfixtures(config)
        return 0
    if config.option.show_fixtures_per_test:
        show_fixtures_per_test(config)
        return 0


def pytest_generate_tests(metafunc):
    # those alternative spellings are common - raise a specific error to alert
    # the user
    alt_spellings = ['parameterize', 'parametrise', 'parameterise']
    for attr in alt_spellings:
        if hasattr(metafunc.function, attr):
            msg = "{0} has '{1}', spelling should be 'parametrize'"
            raise MarkerError(msg.format(metafunc.function.__name__, attr))
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


@hookimpl(trylast=True)
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

@hookimpl(hookwrapper=True)
def pytest_pycollect_makeitem(collector, name, obj):
    outcome = yield
    res = outcome.get_result()
    if res is not None:
        return
    # nothing was collected elsewhere, let's do it here
    if isclass(obj):
        if collector.istestclass(obj, name):
            Class = collector._getcustomclass("Class")
            outcome.force_result(Class(name, parent=collector))
    elif collector.istestfunction(obj, name):
        # mock seems to store unbound methods (issue473), normalize it
        obj = getattr(obj, "__func__", obj)
        # We need to try and unwrap the function if it's a functools.partial
        # or a funtools.wrapped.
        # We musn't if it's been wrapped with mock.patch (python 2 only)
        if not (isfunction(obj) or isfunction(get_real_func(obj))):
            collector.warn(code="C2", message=
                "cannot collect %r because it is not a function."
                % name, )
        elif getattr(obj, "__test__", True):
            if is_generator(obj):
                res = Generator(name, parent=collector)
            else:
                res = list(collector._genfunctions(name, obj))
            outcome.force_result(res)

def pytest_make_parametrize_id(config, val, argname=None):
    return None



class PyobjContext(object):
    module = pyobj_property("Module")
    cls = pyobj_property("Class")
    instance = pyobj_property("Instance")

class PyobjMixin(PyobjContext):
    def obj():
        def fget(self):
            obj = getattr(self, '_obj', None)
            if obj is None:
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
                name = os.path.splitext(name)[0]
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
        compat_co_firstlineno = getattr(obj, 'compat_co_firstlineno', None)
        if isinstance(compat_co_firstlineno, int):
            # nose compatibility
            fspath = sys.modules[obj.__module__].__file__
            if fspath.endswith(".pyc"):
                fspath = fspath[:-1]
            lineno = compat_co_firstlineno
        else:
            fspath, lineno = getfslineno(obj)
        modpath = self.getmodpath()
        assert isinstance(lineno, int)
        return fspath, lineno, modpath

class PyCollector(PyobjMixin, main.Collector):

    def funcnamefilter(self, name):
        return self._matches_prefix_or_glob_option('python_functions', name)

    def isnosetest(self, obj):
        """ Look for the __test__ attribute, which is applied by the
        @nose.tools.istest decorator
        """
        # We explicitly check for "is True" here to not mistakenly treat
        # classes with a custom __getattr__ returning something truthy (like a
        # function) as test classes.
        return safe_getattr(obj, '__test__', False) is True

    def classnamefilter(self, name):
        return self._matches_prefix_or_glob_option('python_classes', name)

    def istestfunction(self, obj, name):
        return (
            (self.funcnamefilter(name) or self.isnosetest(obj)) and
            safe_getattr(obj, "__call__", False) and fixtures.getfixturemarker(obj) is None
        )

    def istestclass(self, obj, name):
        return self.classnamefilter(name) or self.isnosetest(obj)

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
            for name, obj in list(dic.items()):
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
        methods = []
        if hasattr(module, "pytest_generate_tests"):
            methods.append(module.pytest_generate_tests)
        if hasattr(cls, "pytest_generate_tests"):
            methods.append(cls().pytest_generate_tests)
        if methods:
            self.ihook.pytest_generate_tests.call_extra(methods,
                                                        dict(metafunc=metafunc))
        else:
            self.ihook.pytest_generate_tests(metafunc=metafunc)

        Function = self._getcustomclass("Function")
        if not metafunc._calls:
            yield Function(name, parent=self, fixtureinfo=fixtureinfo)
        else:
            # add funcargs() as fixturedefs to fixtureinfo.arg2fixturedefs
            fixtures.add_funcarg_pseudo_fixture_def(self, metafunc, fm)

            for callspec in metafunc._calls:
                subname = "%s[%s]" % (name, callspec.id)
                yield Function(name=subname, parent=self,
                               callspec=callspec, callobj=funcobj,
                               fixtureinfo=fixtureinfo,
                               keywords={callspec.id:True},
                               originalname=name,
                               )


def _marked(func, mark):
    """ Returns True if :func: is already marked with :mark:, False otherwise.
    This can happen if marker is applied to class and the test file is
    invoked more than once.
    """
    try:
        func_mark = getattr(func, mark.name)
    except AttributeError:
        return False
    return mark.args == func_mark.args and mark.kwargs == func_mark.kwargs


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
                if not _marked(funcobj, mark):
                    mark(funcobj)
        else:
            if not _marked(funcobj, pytestmark):
                pytestmark(funcobj)


class Module(main.File, PyCollector):
    """ Collector for test classes and functions. """

    def _getobj(self):
        return self._importtestmodule()

    def collect(self):
        self.session._fixturemanager.parsefactories(self)
        return super(Module, self).collect()

    def _importtestmodule(self):
        # we assume we are only called once per module
        importmode = self.config.getoption("--import-mode")
        try:
            mod = self.fspath.pyimport(ensuresyspath=importmode)
        except SyntaxError:
            raise self.CollectError(
                _pytest._code.ExceptionInfo().getrepr(style="short"))
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
        except ImportError:
            from _pytest._code.code import ExceptionInfo
            exc_info = ExceptionInfo()
            if self.config.getoption('verbose') < 2:
                exc_info.traceback = exc_info.traceback.filter(filter_traceback)
            exc_repr = exc_info.getrepr(style='short') if exc_info.traceback else exc_info.exconly()
            formatted_tb = safe_str(exc_repr)
            raise self.CollectError(
                "ImportError while importing test module '{fspath}'.\n"
                "Hint: make sure your test modules/packages have valid Python names.\n"
                "Traceback:\n"
                "{traceback}".format(fspath=self.fspath, traceback=formatted_tb)
            )
        except _pytest.runner.Skipped as e:
            if e.allow_module_level:
                raise
            raise self.CollectError(
                "Using pytest.skip outside of a test is not allowed. If you are "
                "trying to decorate a test function, use the @pytest.mark.skip "
                "or @pytest.mark.skipif decorators instead."
            )
        self.config.pluginmanager.consider_module(mod)
        return mod

    def setup(self):
        setup_module = _get_xunit_setup_teardown(self.obj, "setUpModule")
        if setup_module is None:
            setup_module = _get_xunit_setup_teardown(self.obj, "setup_module")
        if setup_module is not None:
            setup_module()

        teardown_module = _get_xunit_setup_teardown(self.obj, 'tearDownModule')
        if teardown_module is None:
            teardown_module = _get_xunit_setup_teardown(self.obj, 'teardown_module')
        if teardown_module is not None:
            self.addfinalizer(teardown_module)


def _get_xunit_setup_teardown(holder, attr_name, param_obj=None):
    """
    Return a callable to perform xunit-style setup or teardown if
    the function exists in the ``holder`` object.
    The ``param_obj`` parameter is the parameter which will be passed to the function
    when the callable is called without arguments, defaults to the ``holder`` object.
    Return ``None`` if a suitable callable is not found.
    """
    param_obj = param_obj if param_obj is not None else holder
    result = _get_xunit_func(holder, attr_name)
    if result is not None:
        arg_count = result.__code__.co_argcount
        if inspect.ismethod(result):
            arg_count -= 1
        if arg_count:
            return lambda: result(param_obj)
        else:
            return result


def _get_xunit_func(obj, name):
    """Return the attribute from the given object to be used as a setup/teardown
    xunit-style function, but only if not marked as a fixture to
    avoid calling it twice.
    """
    meth = getattr(obj, name, None)
    if fixtures.getfixturemarker(meth) is None:
        return meth


class Class(PyCollector):
    """ Collector for test methods. """
    def collect(self):
        if not safe_getattr(self.obj, "__test__", True):
            return []
        if hasinit(self.obj):
            self.warn("C1", "cannot collect test class %r because it has a "
                "__init__ constructor" % self.obj.__name__)
            return []
        elif hasnew(self.obj):
            self.warn("C1", "cannot collect test class %r because it has a "
                            "__new__ constructor" % self.obj.__name__)
            return []
        return [self._getcustomclass("Instance")(name="()", parent=self)]

    def setup(self):
        setup_class = _get_xunit_func(self.obj, 'setup_class')
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
        return self.parent.obj()

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
        setup_func_or_method = _get_xunit_setup_teardown(obj, setup_name, param_obj=self.obj)
        if setup_func_or_method is not None:
            setup_func_or_method()
        teardown_func_or_method = _get_xunit_setup_teardown(obj, teardown_name, param_obj=self.obj)
        if teardown_func_or_method is not None:
            self.addfinalizer(teardown_func_or_method)

    def _prunetraceback(self, excinfo):
        if hasattr(self, '_obj') and not self.config.option.fulltrace:
            code = _pytest._code.Code(get_real_func(self.obj))
            path, firstlineno = code.path, code.firstlineno
            traceback = excinfo.traceback
            ntraceback = traceback.cut(path=path, firstlineno=firstlineno)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(path=path)
                if ntraceback == traceback:
                    #ntraceback = ntraceback.cut(excludepath=cutdir2)
                    ntraceback = ntraceback.filter(filter_traceback)
                    if not ntraceback:
                        ntraceback = traceback

            excinfo.traceback = ntraceback.filter()
            # issue364: mark all but first and last frames to
            # only show a single-line message for each frame
            if self.config.option.tbstyle == "auto":
                if len(excinfo.traceback) > 2:
                    for entry in excinfo.traceback[1:-1]:
                        entry.set_repr_style('short')

    def _repr_failure_py(self, excinfo, style="long"):
        if excinfo.errisinstance(fail.Exception):
            if not excinfo.value.pytrace:
                return py._builtin._totext(excinfo.value)
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
        from _pytest import deprecated
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
            self.config.warn('C1', deprecated.YIELD_TESTS, fslocation=self.fspath)
        return l

    def getcallargs(self, obj):
        if not isinstance(obj, (tuple, list)):
            obj = (obj,)
        # explicit naming
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
        return init != object.__init__


def hasnew(obj):
    new = getattr(obj, '__new__', None)
    if new:
        return new != object.__new__


class CallSpec2(object):
    def __init__(self, metafunc):
        self.metafunc = metafunc
        self.funcargs = {}
        self._idlist = []
        self.params = {}
        self._globalid = NOTSET
        self._globalid_args = set()
        self._globalparam = NOTSET
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
            if self._globalparam is NOTSET:
                raise ValueError(name)
            return self._globalparam

    @property
    def id(self):
        return "-".join(map(str, filter(None, self._idlist)))

    def setmulti(self, valtypes, argnames, valset, id, keywords, scopenum,
                 param_index):
        for arg,val in zip(argnames, valset):
            self._checkargnotcontained(arg)
            valtype_for_arg = valtypes[arg]
            getattr(self, valtype_for_arg)[arg] = val
            self.indices[arg] = param_index
            self._arg2scopenum[arg] = scopenum
        self._idlist.append(id)
        self.keywords.update(keywords)

    def setall(self, funcargs, id, param):
        for x in funcargs:
            self._checkargnotcontained(x)
        self.funcargs.update(funcargs)
        if id is not NOTSET:
            self._idlist.append(id)
        if param is not NOTSET:
            assert self._globalparam is NOTSET
            self._globalparam = param
        for arg in funcargs:
            self._arg2scopenum[arg] = fixtures.scopenum_function


class Metafunc(fixtures.FuncargnamesCompatAttr):
    """
    Metafunc objects are passed to the ``pytest_generate_tests`` hook.
    They help to inspect a test function and to generate tests according to
    test configuration or values specified in the class or module where a
    test function is defined.
    """
    def __init__(self, function, fixtureinfo, config, cls=None, module=None):
        #: access to the :class:`_pytest.config.Config` object for the test session
        self.config = config

        #: the module object where the test function is defined in.
        self.module = module

        #: underlying python test function
        self.function = function

        #: set of fixture names required by the test function
        self.fixturenames = fixtureinfo.names_closure

        #: class object where the test function is defined in or ``None``.
        self.cls = cls

        self._calls = []
        self._ids = py.builtin.set()
        self._arg2fixturedefs = fixtureinfo.name2fixturedefs

    def parametrize(self, argnames, argvalues, indirect=False, ids=None,
        scope=None):
        """ Add new invocations to the underlying test function using the list
        of argvalues for the given argnames.  Parametrization is performed
        during the collection phase.  If you need to setup expensive resources
        see about setting indirect to do it rather at test setup time.

        :arg argnames: a comma-separated string denoting one or more argument
                       names, or a list/tuple of argument strings.

        :arg argvalues: The list of argvalues determines how often a
            test is invoked with different argument values.  If only one
            argname was specified argvalues is a list of values.  If N
            argnames were specified, argvalues must be a list of N-tuples,
            where each tuple-element specifies a value for its respective
            argname.

        :arg indirect: The list of argnames or boolean. A list of arguments'
            names (subset of argnames). If True the list contains all names from
            the argnames. Each argvalue corresponding to an argname in this list will
            be passed as request.param to its respective argname fixture
            function so that it can perform more expensive setups during the
            setup phase of a test rather than at collection time.

        :arg ids: list of string ids, or a callable.
            If strings, each is corresponding to the argvalues so that they are
            part of the test id. If None is given as id of specific test, the
            automatically generated id for that argument will be used.
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
        from _pytest.fixtures import scope2index
        from _pytest.mark import MARK_GEN, ParameterSet
        from py.io import saferepr

        if not isinstance(argnames, (tuple, list)):
            argnames = [x.strip() for x in argnames.split(",") if x.strip()]
            force_tuple = len(argnames) == 1
        else:
            force_tuple = False
        parameters = [
            ParameterSet.extract_from(x, legacy_force_tuple=force_tuple)
            for x in argvalues]
        del argvalues

        if not parameters:
            fs, lineno = getfslineno(self.function)
            reason = "got empty parameter set %r, function %s at %s:%d" % (
                    argnames, self.function.__name__, fs, lineno)
            mark = MARK_GEN.skip(reason=reason)
            parameters.append(ParameterSet(
                values=(NOTSET,) * len(argnames),
                marks=[mark],
                id=None,
            ))

        if scope is None:
            scope = _find_parametrized_scope(argnames, self._arg2fixturedefs, indirect)

        scopenum = scope2index(scope, descr='call to {0}'.format(self.parametrize))
        valtypes = {}
        for arg in argnames:
            if arg not in self.fixturenames:
                if isinstance(indirect, (tuple, list)):
                    name = 'fixture' if arg in indirect else 'argument'
                else:
                    name = 'fixture' if indirect else 'argument'
                raise ValueError(
                    "%r uses no %s %r" % (
                            self.function, name, arg))

        if indirect is True:
            valtypes = dict.fromkeys(argnames, "params")
        elif indirect is False:
            valtypes = dict.fromkeys(argnames, "funcargs")
        elif isinstance(indirect, (tuple, list)):
            valtypes = dict.fromkeys(argnames, "funcargs")
            for arg in indirect:
                if arg not in argnames:
                    raise ValueError("indirect given to %r: fixture %r doesn't exist" % (
                                     self.function, arg))
                valtypes[arg] = "params"
        idfn = None
        if callable(ids):
            idfn = ids
            ids = None
        if ids:
            if len(ids) != len(parameters):
                raise ValueError('%d tests specified with %d ids' % (
                                 len(parameters), len(ids)))
            for id_value in ids:
                if id_value is not None and not isinstance(id_value, py.builtin._basestring):
                    msg = 'ids must be list of strings, found: %s (type: %s)'
                    raise ValueError(msg % (saferepr(id_value), type(id_value).__name__))
        ids = idmaker(argnames, parameters, idfn, ids, self.config)
        newcalls = []
        for callspec in self._calls or [CallSpec2(self)]:
            elements = zip(ids, parameters, count())
            for a_id, param, param_index in elements:
                if len(param.values) != len(argnames):
                    raise ValueError(
                        'In "parametrize" the number of values ({0}) must be '
                        'equal to the number of names ({1})'.format(
                            param.values, argnames))
                newcallspec = callspec.copy(self)
                newcallspec.setmulti(valtypes, argnames, param.values, a_id,
                                     param.deprecated_arg_dict, scopenum, param_index)
                newcalls.append(newcallspec)
        self._calls = newcalls

    def addcall(self, funcargs=None, id=NOTSET, param=NOTSET):
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
                    fail("funcarg %r not used in this function." % name)
        else:
            funcargs = {}
        if id is None:
            raise ValueError("id=None not allowed")
        if id is NOTSET:
            id = len(self._calls)
        id = str(id)
        if id in self._ids:
            raise ValueError("duplicate id %r" % id)
        self._ids.add(id)

        cs = CallSpec2(self)
        cs.setall(funcargs, id, param)
        self._calls.append(cs)


def _find_parametrized_scope(argnames, arg2fixturedefs, indirect):
    """Find the most appropriate scope for a parametrized call based on its arguments.

    When there's at least one direct argument, always use "function" scope.

    When a test function is parametrized and all its arguments are indirect
    (e.g. fixtures), return the most narrow scope based on the fixtures used.

    Related to issue #1832, based on code posted by @Kingdread.
    """
    from _pytest.fixtures import scopes
    indirect_as_list = isinstance(indirect, (list, tuple))
    all_arguments_are_fixtures = indirect is True or \
                                 indirect_as_list and len(indirect) == argnames
    if all_arguments_are_fixtures:
        fixturedefs = arg2fixturedefs or {}
        used_scopes = [fixturedef[0].scope for name, fixturedef in fixturedefs.items()]
        if used_scopes:
            # Takes the most narrow scope from used fixtures
            for scope in reversed(scopes):
                if scope in used_scopes:
                    return scope

    return 'function'


def _idval(val, argname, idx, idfn, config=None):
    if idfn:
        s = None
        try:
            s = idfn(val)
        except Exception:
            # See issue https://github.com/pytest-dev/pytest/issues/2169
            import warnings
            msg = "Raised while trying to determine id of parameter %s at position %d." % (argname, idx)
            msg += '\nUpdate your code as this will raise an error in pytest-4.0.'
            warnings.warn(msg, DeprecationWarning)
        if s:
            return _escape_strings(s)

    if config:
        hook_id = config.hook.pytest_make_parametrize_id(
            config=config, val=val, argname=argname)
        if hook_id:
            return hook_id

    if isinstance(val, STRING_TYPES):
        return _escape_strings(val)
    elif isinstance(val, (float, int, bool, NoneType)):
        return str(val)
    elif isinstance(val, REGEX_TYPE):
        return _escape_strings(val.pattern)
    elif enum is not None and isinstance(val, enum.Enum):
        return str(val)
    elif isclass(val) and hasattr(val, '__name__'):
        return val.__name__
    return str(argname)+str(idx)


def _idvalset(idx, parameterset, argnames, idfn, ids, config=None):
    if parameterset.id is not None:
        return parameterset.id
    if ids is None or (idx >= len(ids) or ids[idx] is None):
        this_id = [_idval(val, argname, idx, idfn, config)
                   for val, argname in zip(parameterset.values, argnames)]
        return "-".join(this_id)
    else:
        return _escape_strings(ids[idx])


def idmaker(argnames, parametersets, idfn=None, ids=None, config=None):
    ids = [_idvalset(valindex, parameterset, argnames, idfn, ids, config)
           for valindex, parameterset in enumerate(parametersets)]
    if len(set(ids)) != len(ids):
        # The ids are not unique
        duplicates = [testid for testid in ids if ids.count(testid) > 1]
        counters = collections.defaultdict(lambda: 0)
        for index, testid in enumerate(ids):
            if testid in duplicates:
                ids[index] = testid + str(counters[testid])
                counters[testid] += 1
    return ids


def show_fixtures_per_test(config):
    from _pytest.main import wrap_session
    return wrap_session(config, _show_fixtures_per_test)


def _show_fixtures_per_test(config, session):
    import _pytest.config
    session.perform_collect()
    curdir = py.path.local()
    tw = _pytest.config.create_terminal_writer(config)
    verbose = config.getvalue("verbose")

    def get_best_rel(func):
        loc = getlocation(func, curdir)
        return curdir.bestrelpath(loc)

    def write_fixture(fixture_def):
        argname = fixture_def.argname

        if verbose <= 0 and argname.startswith("_"):
            return
        if verbose > 0:
            bestrel = get_best_rel(fixture_def.func)
            funcargspec = "{0} -- {1}".format(argname, bestrel)
        else:
            funcargspec = argname
        tw.line(funcargspec, green=True)

        INDENT = '    {0}'
        fixture_doc = fixture_def.func.__doc__

        if fixture_doc:
            for line in fixture_doc.strip().split('\n'):
                tw.line(INDENT.format(line.strip()))
        else:
            tw.line(INDENT.format('no docstring available'), red=True)

    def write_item(item):
        name2fixturedefs = item._fixtureinfo.name2fixturedefs

        if not name2fixturedefs:
            # The given test item does not use any fixtures
            return
        bestrel = get_best_rel(item.function)

        tw.line()
        tw.sep('-', 'fixtures used by {0}'.format(item.name))
        tw.sep('-', '({0})'.format(bestrel))
        for argname, fixture_defs in sorted(name2fixturedefs.items()):
            assert fixture_defs is not None
            if not fixture_defs:
                continue
            # The last fixture def item in the list is expected
            # to be the one used by the test item
            write_fixture(fixture_defs[-1])

    for item in session.items:
        write_item(item)


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
    seen = set()

    for argname, fixturedefs in fm._arg2fixturedefs.items():
        assert fixturedefs is not None
        if not fixturedefs:
            continue
        for fixturedef in fixturedefs:
            loc = getlocation(fixturedef.func, curdir)
            if (fixturedef.argname, loc) in seen:
                continue
            seen.add((fixturedef.argname, loc))
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


# builtin pytest.raises helper

def raises(expected_exception, *args, **kwargs):
    """
    Assert that a code block/function call raises ``expected_exception``
    and raise a failure exception otherwise.

    This helper produces a ``ExceptionInfo()`` object (see below).

    If using Python 2.5 or above, you may use this function as a
    context manager::

        >>> with raises(ZeroDivisionError):
        ...    1/0

    .. versionchanged:: 2.10

    In the context manager form you may use the keyword argument
    ``message`` to specify a custom failure message::

        >>> with raises(ZeroDivisionError, message="Expecting ZeroDivisionError"):
        ...    pass
        Traceback (most recent call last):
          ...
        Failed: Expecting ZeroDivisionError


    .. note::

       When using ``pytest.raises`` as a context manager, it's worthwhile to
       note that normal context manager rules apply and that the exception
       raised *must* be the final line in the scope of the context manager.
       Lines of code after that, within the scope of the context manager will
       not be executed. For example::

           >>> value = 15
           >>> with raises(ValueError) as exc_info:
           ...     if value > 10:
           ...         raise ValueError("value must be <= 10")
           ...     assert exc_info.type == ValueError  # this will not execute

       Instead, the following approach must be taken (note the difference in
       scope)::

           >>> with raises(ValueError) as exc_info:
           ...     if value > 10:
           ...         raise ValueError("value must be <= 10")
           ...
           >>> assert exc_info.type == ValueError

    Or you can use the keyword argument ``match`` to assert that the
    exception matches a text or regex::

        >>> with raises(ValueError, match='must be 0 or None'):
        ...     raise ValueError("value must be 0 or None")

        >>> with raises(ValueError, match=r'must be \d+$'):
        ...     raise ValueError("value must be 42")


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

    .. autoclass:: _pytest._code.ExceptionInfo
        :members:

    .. note::
        Similar to caught exception objects in Python, explicitly clearing
        local references to returned ``ExceptionInfo`` objects can
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
    msg = ("exceptions must be old-style classes or"
           " derived from BaseException, not %s")
    if isinstance(expected_exception, tuple):
        for exc in expected_exception:
            if not isclass(exc):
                raise TypeError(msg % type(exc))
    elif not isclass(expected_exception):
        raise TypeError(msg % type(expected_exception))

    message = "DID NOT RAISE {0}".format(expected_exception)
    match_expr = None

    if not args:
        if "message" in kwargs:
            message = kwargs.pop("message")
        if "match" in kwargs:
            match_expr = kwargs.pop("match")
            message += " matching '{0}'".format(match_expr)
        return RaisesContext(expected_exception, message, match_expr)
    elif isinstance(args[0], str):
        code, = args
        assert isinstance(code, str)
        frame = sys._getframe(1)
        loc = frame.f_locals.copy()
        loc.update(kwargs)
        #print "raises frame scope: %r" % frame.f_locals
        try:
            code = _pytest._code.Source(code).compile()
            py.builtin.exec_(code, frame.f_globals, loc)
            # XXX didn'T mean f_globals == f_locals something special?
            #     this is destroyed here ...
        except expected_exception:
            return _pytest._code.ExceptionInfo()
    else:
        func = args[0]
        try:
            func(*args[1:], **kwargs)
        except expected_exception:
            return _pytest._code.ExceptionInfo()
    fail(message)


raises.Exception = fail.Exception


class RaisesContext(object):
    def __init__(self, expected_exception, message, match_expr):
        self.expected_exception = expected_exception
        self.message = message
        self.match_expr = match_expr
        self.excinfo = None

    def __enter__(self):
        self.excinfo = object.__new__(_pytest._code.ExceptionInfo)
        return self.excinfo

    def __exit__(self, *tp):
        __tracebackhide__ = True
        if tp[0] is None:
            fail(self.message)
        if sys.version_info < (2, 7):
            # py26: on __exit__() exc_value often does not contain the
            # exception value.
            # http://bugs.python.org/issue7853
            if not isinstance(tp[1], BaseException):
                exc_type, value, traceback = tp
                tp = exc_type, exc_type(value), traceback
        self.excinfo.__init__(tp)
        suppress_exception = issubclass(self.excinfo.type, self.expected_exception)
        if sys.version_info[0] == 2 and suppress_exception:
            sys.exc_clear()
        if self.match_expr:
            self.excinfo.match(self.match_expr)
        return suppress_exception


# builtin pytest.approx helper

class approx(object):
    """
    Assert that two numbers (or two sets of numbers) are equal to each other
    within some tolerance.

    Due to the `intricacies of floating-point arithmetic`__, numbers that we
    would intuitively expect to be equal are not always so::

        >>> 0.1 + 0.2 == 0.3
        False

    __ https://docs.python.org/3/tutorial/floatingpoint.html

    This problem is commonly encountered when writing tests, e.g. when making
    sure that floating-point values are what you expect them to be.  One way to
    deal with this problem is to assert that two floating-point numbers are
    equal to within some appropriate tolerance::

        >>> abs((0.1 + 0.2) - 0.3) < 1e-6
        True

    However, comparisons like this are tedious to write and difficult to
    understand.  Furthermore, absolute comparisons like the one above are
    usually discouraged because there's no tolerance that works well for all
    situations.  ``1e-6`` is good for numbers around ``1``, but too small for
    very big numbers and too big for very small ones.  It's better to express
    the tolerance as a fraction of the expected value, but relative comparisons
    like that are even more difficult to write correctly and concisely.

    The ``approx`` class performs floating-point comparisons using a syntax
    that's as intuitive as possible::

        >>> from pytest import approx
        >>> 0.1 + 0.2 == approx(0.3)
        True

    The same syntax also works on sequences of numbers::

        >>> (0.1 + 0.2, 0.2 + 0.4) == approx((0.3, 0.6))
        True

    By default, ``approx`` considers numbers within a relative tolerance of
    ``1e-6`` (i.e. one part in a million) of its expected value to be equal.
    This treatment would lead to surprising results if the expected value was
    ``0.0``, because nothing but ``0.0`` itself is relatively close to ``0.0``.
    To handle this case less surprisingly, ``approx`` also considers numbers
    within an absolute tolerance of ``1e-12`` of its expected value to be
    equal.  Infinite numbers are another special case.  They are only
    considered equal to themselves, regardless of the relative tolerance.  Both
    the relative and absolute tolerances can be changed by passing arguments to
    the ``approx`` constructor::

        >>> 1.0001 == approx(1)
        False
        >>> 1.0001 == approx(1, rel=1e-3)
        True
        >>> 1.0001 == approx(1, abs=1e-3)
        True

    If you specify ``abs`` but not ``rel``, the comparison will not consider
    the relative tolerance at all.  In other words, two numbers that are within
    the default relative tolerance of ``1e-6`` will still be considered unequal
    if they exceed the specified absolute tolerance.  If you specify both
    ``abs`` and ``rel``, the numbers will be considered equal if either
    tolerance is met::

        >>> 1 + 1e-8 == approx(1)
        True
        >>> 1 + 1e-8 == approx(1, abs=1e-12)
        False
        >>> 1 + 1e-8 == approx(1, rel=1e-6, abs=1e-12)
        True

    If you're thinking about using ``approx``, then you might want to know how
    it compares to other good ways of comparing floating-point numbers.  All of
    these algorithms are based on relative and absolute tolerances and should
    agree for the most part, but they do have meaningful differences:

    - ``math.isclose(a, b, rel_tol=1e-9, abs_tol=0.0)``:  True if the relative
      tolerance is met w.r.t. either ``a`` or ``b`` or if the absolute
      tolerance is met.  Because the relative tolerance is calculated w.r.t.
      both ``a`` and ``b``, this test is symmetric (i.e.  neither ``a`` nor
      ``b`` is a "reference value").  You have to specify an absolute tolerance
      if you want to compare to ``0.0`` because there is no tolerance by
      default.  Only available in python>=3.5.  `More information...`__

      __ https://docs.python.org/3/library/math.html#math.isclose

    - ``numpy.isclose(a, b, rtol=1e-5, atol=1e-8)``: True if the difference
      between ``a`` and ``b`` is less that the sum of the relative tolerance
      w.r.t. ``b`` and the absolute tolerance.  Because the relative tolerance
      is only calculated w.r.t. ``b``, this test is asymmetric and you can
      think of ``b`` as the reference value.  Support for comparing sequences
      is provided by ``numpy.allclose``.  `More information...`__

      __ http://docs.scipy.org/doc/numpy-1.10.0/reference/generated/numpy.isclose.html

    - ``unittest.TestCase.assertAlmostEqual(a, b)``: True if ``a`` and ``b``
      are within an absolute tolerance of ``1e-7``.  No relative tolerance is
      considered and the absolute tolerance cannot be changed, so this function
      is not appropriate for very large or very small numbers.  Also, it's only
      available in subclasses of ``unittest.TestCase`` and it's ugly because it
      doesn't follow PEP8.  `More information...`__

      __ https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertAlmostEqual

    - ``a == pytest.approx(b, rel=1e-6, abs=1e-12)``: True if the relative
      tolerance is met w.r.t. ``b`` or if the absolute tolerance is met.
      Because the relative tolerance is only calculated w.r.t. ``b``, this test
      is asymmetric and you can think of ``b`` as the reference value.  In the
      special case that you explicitly specify an absolute tolerance but not a
      relative tolerance, only the absolute tolerance is considered.
    """

    def __init__(self, expected, rel=None, abs=None):
        self.expected = expected
        self.abs = abs
        self.rel = rel

    def __repr__(self):
        return ', '.join(repr(x) for x in self.expected)

    def __eq__(self, actual):
        from collections import Iterable
        if not isinstance(actual, Iterable):
            actual = [actual]
        if len(actual) != len(self.expected):
            return False
        return all(a == x for a, x in zip(actual, self.expected))

    __hash__ = None

    def __ne__(self, actual):
        return not (actual == self)

    @property
    def expected(self):
        # Regardless of whether the user-specified expected value is a number
        # or a sequence of numbers, return a list of ApproxNotIterable objects
        # that can be compared against.
        from collections import Iterable
        approx_non_iter = lambda x: ApproxNonIterable(x, self.rel, self.abs)
        if isinstance(self._expected, Iterable):
            return [approx_non_iter(x) for x in self._expected]
        else:
            return [approx_non_iter(self._expected)]

    @expected.setter
    def expected(self, expected):
        self._expected = expected


class ApproxNonIterable(object):
    """
    Perform approximate comparisons for single numbers only.

    In other words, the ``expected`` attribute for objects of this class must
    be some sort of number.  This is in contrast to the ``approx`` class, where
    the ``expected`` attribute can either be a number of a sequence of numbers.
    This class is responsible for making comparisons, while ``approx`` is
    responsible for abstracting the difference between numbers and sequences of
    numbers.  Although this class can stand on its own, it's only meant to be
    used within ``approx``.
    """

    def __init__(self, expected, rel=None, abs=None):
        self.expected = expected
        self.abs = abs
        self.rel = rel

    def __repr__(self):
        if isinstance(self.expected, complex):
            return str(self.expected)

        # Infinities aren't compared using tolerances, so don't show a
        # tolerance.
        if math.isinf(self.expected):
            return str(self.expected)

        # If a sensible tolerance can't be calculated, self.tolerance will
        # raise a ValueError.  In this case, display '???'.
        try:
            vetted_tolerance = '{:.1e}'.format(self.tolerance)
        except ValueError:
            vetted_tolerance = '???'

        if sys.version_info[0] == 2:
            return '{0} +- {1}'.format(self.expected, vetted_tolerance)
        else:
            return u'{0} \u00b1 {1}'.format(self.expected, vetted_tolerance)

    def __eq__(self, actual):
        # Short-circuit exact equality.
        if actual == self.expected:
            return True

        # Infinity shouldn't be approximately equal to anything but itself, but
        # if there's a relative tolerance, it will be infinite and infinity
        # will seem approximately equal to everything.  The equal-to-itself
        # case would have been short circuited above, so here we can just
        # return false if the expected value is infinite.  The abs() call is
        # for compatibility with complex numbers.
        if math.isinf(abs(self.expected)):
            return False

        # Return true if the two numbers are within the tolerance.
        return abs(self.expected - actual) <= self.tolerance

    __hash__ = None

    def __ne__(self, actual):
        return not (actual == self)

    @property
    def tolerance(self):
        set_default = lambda x, default: x if x is not None else default

        # Figure out what the absolute tolerance should be.  ``self.abs`` is
        # either None or a value specified by the user.
        absolute_tolerance = set_default(self.abs, 1e-12)

        if absolute_tolerance < 0:
            raise ValueError("absolute tolerance can't be negative: {}".format(absolute_tolerance))
        if math.isnan(absolute_tolerance):
            raise ValueError("absolute tolerance can't be NaN.")

        # If the user specified an absolute tolerance but not a relative one,
        # just return the absolute tolerance.
        if self.rel is None:
            if self.abs is not None:
                return absolute_tolerance

        # Figure out what the relative tolerance should be.  ``self.rel`` is
        # either None or a value specified by the user.  This is done after
        # we've made sure the user didn't ask for an absolute tolerance only,
        # because we don't want to raise errors about the relative tolerance if
        # we aren't even going to use it.
        relative_tolerance = set_default(self.rel, 1e-6) * abs(self.expected)

        if relative_tolerance < 0:
            raise ValueError("relative tolerance can't be negative: {}".format(absolute_tolerance))
        if math.isnan(relative_tolerance):
            raise ValueError("relative tolerance can't be NaN.")

        # Return the larger of the relative and absolute tolerances.
        return max(relative_tolerance, absolute_tolerance)


#
#  the basic pytest Function item
#

class Function(FunctionMixin, main.Item, fixtures.FuncargnamesCompatAttr):
    """ a Function Item is responsible for setting up and executing a
    Python test function.
    """
    _genid = None
    def __init__(self, name, parent, args=None, config=None,
                 callspec=None, callobj=NOTSET, keywords=None, session=None,
                 fixtureinfo=None, originalname=None):
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

        #: original function name, without any decorations (for example
        #: parametrization adds a ``"[...]"`` suffix to function names).
        #:
        #: .. versionadded:: 3.0
        self.originalname = originalname

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
        self._request = fixtures.FixtureRequest(self)

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
        fixtures.fillfixtures(self)
