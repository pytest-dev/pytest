"""
pytest PluginManager, basic initialization and tracing.
(c) Holger Krekel 2004-2010
"""
import sys, os
import inspect
import py
from _pytest import hookspec # the extension point definitions

assert py.__version__.split(".")[:2] >= ['1', '4'], ("installation problem: "
    "%s is too old, remove or upgrade 'py'" % (py.__version__))

default_plugins = (
 "config mark main terminal runner python pdb unittest capture skipping "
 "tmpdir monkeypatch recwarn pastebin helpconfig nose assertion genscript "
 "junitxml resultlog doctest").split()

class TagTracer:
    def __init__(self, prefix="[pytest] "):
        self._tag2proc = {}
        self.writer = None
        self.indent = 0
        self.prefix = prefix

    def get(self, name):
        return TagTracerSub(self, (name,))

    def processmessage(self, tags, args):
        if self.writer is not None:
            if args:
                indent = "  " * self.indent
                content = " ".join(map(str, args))
                self.writer("%s%s%s\n" %(self.prefix, indent, content))
        try:
            self._tag2proc[tags](tags, args)
        except KeyError:
            pass

    def setwriter(self, writer):
        self.writer = writer

    def setprocessor(self, tags, processor):
        if isinstance(tags, str):
            tags = tuple(tags.split(":"))
        else:
            assert isinstance(tags, tuple)
        self._tag2proc[tags] = processor

class TagTracerSub:
    def __init__(self, root, tags):
        self.root = root
        self.tags = tags
    def __call__(self, *args):
        self.root.processmessage(self.tags, args)
    def setmyprocessor(self, processor):
        self.root.setprocessor(self.tags, processor)
    def get(self, name):
        return self.__class__(self.root, self.tags + (name,))

class PluginManager(object):
    def __init__(self, load=False):
        self._name2plugin = {}
        self._listattrcache = {}
        self._plugins = []
        self._hints = []
        self.trace = TagTracer().get("pluginmanage")
        self._plugin_distinfo = []
        if os.environ.get('PYTEST_DEBUG'):
            err = sys.stderr
            encoding = getattr(err, 'encoding', 'utf8')
            try:
                err = py.io.dupfile(err, encoding=encoding)
            except Exception:
                pass
            self.trace.root.setwriter(err.write)
        self.hook = HookRelay([hookspec], pm=self)
        self.register(self)
        if load:
            for spec in default_plugins:
                self.import_plugin(spec)

    def register(self, plugin, name=None, prepend=False):
        assert not self.isregistered(plugin), plugin
        name = name or getattr(plugin, '__name__', str(id(plugin)))
        if name in self._name2plugin:
            return False
        #self.trace("registering", name, plugin)
        self._name2plugin[name] = plugin
        self.call_plugin(plugin, "pytest_addhooks", {'pluginmanager': self})
        self.hook.pytest_plugin_registered(manager=self, plugin=plugin)
        if not prepend:
            self._plugins.append(plugin)
        else:
            self._plugins.insert(0, plugin)
        return True

    def unregister(self, plugin=None, name=None):
        if plugin is None:
            plugin = self.getplugin(name=name)
        self._plugins.remove(plugin)
        self.hook.pytest_plugin_unregistered(plugin=plugin)
        for name, value in list(self._name2plugin.items()):
            if value == plugin:
                del self._name2plugin[name]

    def isregistered(self, plugin, name=None):
        if self.getplugin(name) is not None:
            return True
        for val in self._name2plugin.values():
            if plugin == val:
                return True

    def addhooks(self, spec):
        self.hook._addhooks(spec, prefix="pytest_")

    def getplugins(self):
        return list(self._plugins)

    def skipifmissing(self, name):
        if not self.hasplugin(name):
            py.test.skip("plugin %r is missing" % name)

    def hasplugin(self, name):
        return bool(self.getplugin(name))

    def getplugin(self, name):
        if name is None:
            return None
        try:
            return self._name2plugin[name]
        except KeyError:
            return self._name2plugin.get("_pytest." + name, None)

    # API for bootstrapping
    #
    def _envlist(self, varname):
        val = py.std.os.environ.get(varname, None)
        if val is not None:
            return val.split(',')
        return ()

    def consider_env(self):
        for spec in self._envlist("PYTEST_PLUGINS"):
            self.import_plugin(spec)

    def consider_setuptools_entrypoints(self):
        try:
            from pkg_resources import iter_entry_points, DistributionNotFound
        except ImportError:
            return # XXX issue a warning
        for ep in iter_entry_points('pytest11'):
            name = ep.name
            if name.startswith("pytest_"):
                name = name[7:]
            if ep.name in self._name2plugin or name in self._name2plugin:
                continue
            try:
                plugin = ep.load()
            except DistributionNotFound:
                continue
            self._plugin_distinfo.append((ep.dist, plugin))
            self.register(plugin, name=name)

    def consider_preparse(self, args):
        for opt1,opt2 in zip(args, args[1:]):
            if opt1 == "-p":
                self.consider_pluginarg(opt2)

    def consider_pluginarg(self, arg):
        if arg.startswith("no:"):
            name = arg[3:]
            if self.getplugin(name) is not None:
                self.unregister(None, name=name)
            self._name2plugin[name] = -1
        else:
            if self.getplugin(arg) is None:
                self.import_plugin(arg)

    def consider_conftest(self, conftestmodule):
        if self.register(conftestmodule, name=conftestmodule.__file__):
            self.consider_module(conftestmodule)

    def consider_module(self, mod):
        attr = getattr(mod, "pytest_plugins", ())
        if attr:
            if not isinstance(attr, (list, tuple)):
                attr = (attr,)
            for spec in attr:
                self.import_plugin(spec)

    def import_plugin(self, modname):
        assert isinstance(modname, str)
        if self.getplugin(modname) is not None:
            return
        try:
            #self.trace("importing", modname)
            mod = importplugin(modname)
        except KeyboardInterrupt:
            raise
        except ImportError:
            if modname.startswith("pytest_"):
                return self.import_plugin(modname[7:])
            raise
        except:
            e = py.std.sys.exc_info()[1]
            if not hasattr(py.test, 'skip'):
                raise
            elif not isinstance(e, py.test.skip.Exception):
                raise
            self._hints.append("skipped plugin %r: %s" %((modname, e.msg)))
        else:
            self.register(mod, modname)
            self.consider_module(mod)

    def pytest_plugin_registered(self, plugin):
        import pytest
        dic = self.call_plugin(plugin, "pytest_namespace", {}) or {}
        if dic:
            self._setns(pytest, dic)
        if hasattr(self, '_config'):
            self.call_plugin(plugin, "pytest_addoption",
                {'parser': self._config._parser})
            self.call_plugin(plugin, "pytest_configure",
                {'config': self._config})

    def _setns(self, obj, dic):
        import pytest
        for name, value in dic.items():
            if isinstance(value, dict):
                mod = getattr(obj, name, None)
                if mod is None:
                    modname = "pytest.%s" % name
                    mod = py.std.types.ModuleType(modname)
                    sys.modules[modname] = mod
                    mod.__all__ = []
                    setattr(obj, name, mod)
                obj.__all__.append(name)
                self._setns(mod, value)
            else:
                setattr(obj, name, value)
                obj.__all__.append(name)
                #if obj != pytest:
                #    pytest.__all__.append(name)
                setattr(pytest, name, value)

    def pytest_terminal_summary(self, terminalreporter):
        tw = terminalreporter._tw
        if terminalreporter.config.option.traceconfig:
            for hint in self._hints:
                tw.line("hint: %s" % hint)

    def do_addoption(self, parser):
        mname = "pytest_addoption"
        methods = reversed(self.listattr(mname))
        MultiCall(methods, {'parser': parser}).execute()

    def do_configure(self, config):
        assert not hasattr(self, '_config')
        self._config = config
        config.hook.pytest_configure(config=self._config)

    def do_unconfigure(self, config):
        config = self._config
        del self._config
        config.hook.pytest_unconfigure(config=config)
        config.pluginmanager.unregister(self)

    def notify_exception(self, excinfo):
        excrepr = excinfo.getrepr(funcargs=True, showlocals=True)
        res = self.hook.pytest_internalerror(excrepr=excrepr)
        if not py.builtin.any(res):
            for line in str(excrepr).split("\n"):
                sys.stderr.write("INTERNALERROR> %s\n" %line)
                sys.stderr.flush()

    def listattr(self, attrname, plugins=None):
        if plugins is None:
            plugins = self._plugins
        key = (attrname,) + tuple(plugins)
        try:
            return list(self._listattrcache[key])
        except KeyError:
            pass
        l = []
        last = []
        for plugin in plugins:
            try:
                meth = getattr(plugin, attrname)
                if hasattr(meth, 'tryfirst'):
                    last.append(meth)
                elif hasattr(meth, 'trylast'):
                    l.insert(0, meth)
                else:
                    l.append(meth)
            except AttributeError:
                continue
        l.extend(last)
        self._listattrcache[key] = list(l)
        return l

    def call_plugin(self, plugin, methname, kwargs):
        return MultiCall(methods=self.listattr(methname, plugins=[plugin]),
                kwargs=kwargs, firstresult=True).execute()


def importplugin(importspec):
    name = importspec
    try:
        mod = "_pytest." + name
        return __import__(mod, None, None, '__doc__')
    except ImportError:
        #e = py.std.sys.exc_info()[1]
        #if str(e).find(name) == -1:
        #    raise
        pass #
    return __import__(importspec, None, None, '__doc__')

class MultiCall:
    """ execute a call into multiple python functions/methods. """
    def __init__(self, methods, kwargs, firstresult=False):
        self.methods = list(methods)
        self.kwargs = kwargs
        self.results = []
        self.firstresult = firstresult

    def __repr__(self):
        status = "%d results, %d meths" % (len(self.results), len(self.methods))
        return "<MultiCall %s, kwargs=%r>" %(status, self.kwargs)

    def execute(self):
        while self.methods:
            method = self.methods.pop()
            kwargs = self.getkwargs(method)
            res = method(**kwargs)
            if res is not None:
                self.results.append(res)
                if self.firstresult:
                    return res
        if not self.firstresult:
            return self.results

    def getkwargs(self, method):
        kwargs = {}
        for argname in varnames(method):
            try:
                kwargs[argname] = self.kwargs[argname]
            except KeyError:
                if argname == "__multicall__":
                    kwargs[argname] = self
        return kwargs

def varnames(func):
    try:
        return func._varnames
    except AttributeError:
        pass
    if not inspect.isfunction(func) and not inspect.ismethod(func):
        func = getattr(func, '__call__', func)
    ismethod = inspect.ismethod(func)
    rawcode = py.code.getrawcode(func)
    try:
        x = rawcode.co_varnames[ismethod:rawcode.co_argcount]
    except AttributeError:
        x = ()
    py.builtin._getfuncdict(func)['_varnames'] = x
    return x

class HookRelay:
    def __init__(self, hookspecs, pm, prefix="pytest_"):
        if not isinstance(hookspecs, list):
            hookspecs = [hookspecs]
        self._hookspecs = []
        self._pm = pm
        self.trace = pm.trace.root.get("hook")
        for hookspec in hookspecs:
            self._addhooks(hookspec, prefix)

    def _addhooks(self, hookspecs, prefix):
        self._hookspecs.append(hookspecs)
        added = False
        for name, method in vars(hookspecs).items():
            if name.startswith(prefix):
                firstresult = getattr(method, 'firstresult', False)
                hc = HookCaller(self, name, firstresult=firstresult)
                setattr(self, name, hc)
                added = True
                #print ("setting new hook", name)
        if not added:
            raise ValueError("did not find new %r hooks in %r" %(
                prefix, hookspecs,))


class HookCaller:
    def __init__(self, hookrelay, name, firstresult):
        self.hookrelay = hookrelay
        self.name = name
        self.firstresult = firstresult
        self.trace = self.hookrelay.trace

    def __repr__(self):
        return "<HookCaller %r>" %(self.name,)

    def __call__(self, **kwargs):
        methods = self.hookrelay._pm.listattr(self.name)
        return self._docall(methods, kwargs)

    def pcall(self, plugins, **kwargs):
        methods = self.hookrelay._pm.listattr(self.name, plugins=plugins)
        return self._docall(methods, kwargs)

    def _docall(self, methods, kwargs):
        self.trace(self.name, kwargs)
        self.trace.root.indent += 1
        mc = MultiCall(methods, kwargs, firstresult=self.firstresult)
        try:
            res = mc.execute()
            if res:
                self.trace("finish", self.name, "-->", res)
        finally:
            self.trace.root.indent -= 1
        return res

_preinit = []

def _preloadplugins():
    _preinit.append(PluginManager(load=True))

def main(args=None, plugins=None):
    """ returned exit code integer, after an in-process testing run
    with the given command line arguments, preloading an optional list
    of passed in plugin objects. """
    if args is None:
        args = sys.argv[1:]
    elif isinstance(args, py.path.local):
        args = [str(args)]
    elif not isinstance(args, (tuple, list)):
        if not isinstance(args, str):
            raise ValueError("not a string or argument list: %r" % (args,))
        args = py.std.shlex.split(args)
    if _preinit:
       _pluginmanager = _preinit.pop(0)
    else: # subsequent calls to main will create a fresh instance
        _pluginmanager = PluginManager(load=True)
    hook = _pluginmanager.hook
    try:
        if plugins:
            for plugin in plugins:
                _pluginmanager.register(plugin)
        config = hook.pytest_cmdline_parse(
                pluginmanager=_pluginmanager, args=args)
        exitstatus = hook.pytest_cmdline_main(config=config)
    except UsageError:
        e = sys.exc_info()[1]
        sys.stderr.write("ERROR: %s\n" %(e.args[0],))
        exitstatus = 3
    return exitstatus

class UsageError(Exception):
    """ error in py.test usage or invocation"""

