import py
import sys, os

default_plugins = (
 "session terminal python runner pdb capture mark skipping tmpdir monkeypatch "
 "recwarn pastebin unittest helpconfig nose assertion genscript "
 "junitxml doctest keyword").split()

def main(args=None):
    import sys
    if args is None:
        args = sys.argv[1:]
    config = py.test.config
    config.parse(args)
    try:
        exitstatus = config.hook.pytest_cmdline_main(config=config)
    except config.Error:
        e = sys.exc_info()[1]
        sys.stderr.write("ERROR: %s\n" %(e.args[0],))
        exitstatus = 3
    py.test.config = config.__class__()
    return exitstatus

class Parser:
    """ Parser for command line arguments. """

    def __init__(self, usage=None, processopt=None):
        self._anonymous = OptionGroup("custom options", parser=self)
        self._groups = []
        self._processopt = processopt
        self._usage = usage
        self.hints = []

    def processoption(self, option):
        if self._processopt:
            if option.dest:
                self._processopt(option)

    def addnote(self, note):
        self._notes.append(note)

    def getgroup(self, name, description="", after=None):
        for group in self._groups:
            if group.name == name:
                return group
        group = OptionGroup(name, description, parser=self)
        i = 0
        for i, grp in enumerate(self._groups):
            if grp.name == after:
                break
        self._groups.insert(i+1, group)
        return group

    addgroup = getgroup
    def addgroup(self, name, description=""):
        py.log._apiwarn("1.1", "use getgroup() which gets-or-creates")
        return self.getgroup(name, description)

    def addoption(self, *opts, **attrs):
        """ add an optparse-style option. """
        self._anonymous.addoption(*opts, **attrs)

    def parse(self, args):
        optparser = MyOptionParser(self)
        groups = self._groups + [self._anonymous]
        for group in groups:
            if group.options:
                desc = group.description or group.name
                optgroup = py.std.optparse.OptionGroup(optparser, desc)
                optgroup.add_options(group.options)
                optparser.add_option_group(optgroup)
        return optparser.parse_args([str(x) for x in args])

    def parse_setoption(self, args, option):
        parsedoption, args = self.parse(args)
        for name, value in parsedoption.__dict__.items():
            setattr(option, name, value)
        return args


class OptionGroup:
    def __init__(self, name, description="", parser=None):
        self.name = name
        self.description = description
        self.options = []
        self.parser = parser

    def addoption(self, *optnames, **attrs):
        """ add an option to this group. """
        option = py.std.optparse.Option(*optnames, **attrs)
        self._addoption_instance(option, shortupper=False)

    def _addoption(self, *optnames, **attrs):
        option = py.std.optparse.Option(*optnames, **attrs)
        self._addoption_instance(option, shortupper=True)

    def _addoption_instance(self, option, shortupper=False):
        if not shortupper:
            for opt in option._short_opts:
                if opt[0] == '-' and opt[1].islower():
                    raise ValueError("lowercase shortoptions reserved")
        if self.parser:
            self.parser.processoption(option)
        self.options.append(option)


class MyOptionParser(py.std.optparse.OptionParser):
    def __init__(self, parser):
        self._parser = parser
        py.std.optparse.OptionParser.__init__(self, usage=parser._usage)
    def format_epilog(self, formatter):
        hints = self._parser.hints
        if hints:
            s = "\n".join(["hint: " + x for x in hints]) + "\n"
            s = "\n" + s + "\n"
            return s
        return ""

class Conftest(object):
    """ the single place for accessing values and interacting
        towards conftest modules from py.test objects.
    """
    def __init__(self, onimport=None, confcutdir=None):
        self._path2confmods = {}
        self._onimport = onimport
        self._conftestpath2mod = {}
        self._confcutdir = confcutdir
        self._md5cache = {}

    def setinitial(self, args):
        """ try to find a first anchor path for looking up global values
            from conftests. This function is usually called _before_
            argument parsing.  conftest files may add command line options
            and we thus have no completely safe way of determining
            which parts of the arguments are actually related to options
            and which are file system paths.  We just try here to get
            bootstrapped ...
        """
        current = py.path.local()
        opt = '--confcutdir'
        for i in range(len(args)):
            opt1 = str(args[i])
            if opt1.startswith(opt):
                if opt1 == opt:
                    if len(args) > i:
                        p = current.join(args[i+1], abs=True)
                elif opt1.startswith(opt + "="):
                    p = current.join(opt1[len(opt)+1:], abs=1)
                self._confcutdir = p
                break
        for arg in args + [current]:
            if hasattr(arg, 'startswith') and arg.startswith("--"):
                continue
            anchor = current.join(arg, abs=1)
            if anchor.check(): # we found some file object
                self._path2confmods[None] = self.getconftestmodules(anchor)
                # let's also consider test* dirs
                if anchor.check(dir=1):
                    for x in anchor.listdir("test*"):
                        if x.check(dir=1):
                            self.getconftestmodules(x)
                break
        else:
            assert 0, "no root of filesystem?"

    def getconftestmodules(self, path):
        """ return a list of imported conftest modules for the given path.  """
        try:
            clist = self._path2confmods[path]
        except KeyError:
            if path is None:
                raise ValueError("missing default confest.")
            dp = path.dirpath()
            clist = []
            if dp != path:
                cutdir = self._confcutdir
                if cutdir and path != cutdir and not path.relto(cutdir):
                    pass
                else:
                    conftestpath = path.join("conftest.py")
                    if conftestpath.check(file=1):
                        key = conftestpath.computehash()
                        # XXX logging about conftest loading
                        if key not in self._md5cache:
                            clist.append(self.importconftest(conftestpath))
                            self._md5cache[key] = conftestpath
                        else:
                            # use some kind of logging
                            print ("WARN: not loading %s" % conftestpath)
                clist[:0] = self.getconftestmodules(dp)
            self._path2confmods[path] = clist
        # be defensive: avoid changes from caller side to
        # affect us by always returning a copy of the actual list
        return clist[:]

    def rget(self, name, path=None):
        mod, value = self.rget_with_confmod(name, path)
        return value

    def rget_with_confmod(self, name, path=None):
        modules = self.getconftestmodules(path)
        modules.reverse()
        for mod in modules:
            try:
                return mod, getattr(mod, name)
            except AttributeError:
                continue
        raise KeyError(name)

    def importconftest(self, conftestpath):
        assert conftestpath.check(), conftestpath
        try:
            return self._conftestpath2mod[conftestpath]
        except KeyError:
            if not conftestpath.dirpath('__init__.py').check(file=1):
                # HACK: we don't want any "globally" imported conftest.py,
                #       prone to conflicts and subtle problems
                modname = str(conftestpath).replace('.', conftestpath.sep)
                mod = conftestpath.pyimport(modname=modname)
            else:
                mod = conftestpath.pyimport()
            self._conftestpath2mod[conftestpath] = mod
            dirpath = conftestpath.dirpath()
            if dirpath in self._path2confmods:
                for path, mods in self._path2confmods.items():
                    if path and path.relto(dirpath) or path == dirpath:
                        assert mod not in mods
                        mods.append(mod)
            self._postimport(mod)
            return mod

    def _postimport(self, mod):
        if self._onimport:
            self._onimport(mod)
        return mod


class CmdOptions(object):
    """ holds cmdline options as attributes."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        return "<CmdOptions %r>" %(self.__dict__,)

class Error(Exception):
    """ Test Configuration Error. """

class Config(object):
    """ access to configuration values, pluginmanager and plugin hooks.  """
    Option = py.std.optparse.Option
    Error = Error
    basetemp = None

    def __init__(self):
        #: command line option values
        self.option = CmdOptions()
        self._parser = Parser(
            usage="usage: %prog [options] [file_or_dir] [file_or_dir] [...]",
            processopt=self._processopt,
        )
        #: a pluginmanager instance
        self.pluginmanager = PluginManager()
        self._conftest = Conftest(onimport=self._onimportconftest)
        self.hook = self.pluginmanager.hook

    def _onimportconftest(self, conftestmodule):
        self.trace("loaded conftestmodule %r" %(conftestmodule,))
        self.pluginmanager.consider_conftest(conftestmodule)

    def _getmatchingplugins(self, fspath):
        allconftests = self._conftest._conftestpath2mod.values()
        plugins = [x for x in self.pluginmanager.getplugins()
                        if x not in allconftests]
        plugins += self._conftest.getconftestmodules(fspath)
        return plugins

    def trace(self, msg):
        if getattr(self.option, 'traceconfig', None):
            self.hook.pytest_trace(category="config", msg=msg)

    def _processopt(self, opt):
        if hasattr(opt, 'default') and opt.dest:
            val = os.environ.get("PYTEST_OPTION_" + opt.dest.upper(), None)
            if val is not None:
                if opt.type == "int":
                    val = int(val)
                elif opt.type == "long":
                    val = long(val)
                elif opt.type == "float":
                    val = float(val)
                elif not opt.type and opt.action in ("store_true", "store_false"):
                    val = eval(val)
                opt.default = val
            else:
                name = "option_" + opt.dest
                try:
                    opt.default = self._conftest.rget(name)
                except (ValueError, KeyError):
                    pass
            if not hasattr(self.option, opt.dest):
                setattr(self.option, opt.dest, opt.default)

    def _preparse(self, args):
        self.pluginmanager.consider_setuptools_entrypoints()
        self.pluginmanager.consider_env()
        self.pluginmanager.consider_preparse(args)
        self._conftest.setinitial(args)
        self.pluginmanager.do_addoption(self._parser)

    def parse(self, args):
        # cmdline arguments into this config object.
        # Note that this can only be called once per testing process.
        assert not hasattr(self, 'args'), (
                "can only parse cmdline args at most once per Config object")
        self._preparse(args)
        self._parser.hints.extend(self.pluginmanager._hints)
        args = self._parser.parse_setoption(args, self.option)
        if not args:
            args.append(py.std.os.getcwd())
        self.args = args

    def ensuretemp(self, string, dir=True):
        return self.getbasetemp().ensure(string, dir=dir)

    def getbasetemp(self):
        if self.basetemp is None:
            basetemp = self.option.basetemp
            if basetemp:
                basetemp = py.path.local(basetemp)
                if not basetemp.check(dir=1):
                    basetemp.mkdir()
            else:
                basetemp = py.path.local.make_numbered_dir(prefix='pytest-')
            self.basetemp = basetemp
        return self.basetemp

    def mktemp(self, basename, numbered=False):
        basetemp = self.getbasetemp()
        if not numbered:
            return basetemp.mkdir(basename)
        else:
            return py.path.local.make_numbered_dir(prefix=basename,
                keep=0, rootdir=basetemp, lock_timeout=None)

    def _getcollectclass(self, name, path):
        try:
            cls = self._conftest.rget(name, path)
        except KeyError:
            return getattr(py.test.collect, name)
        else:
            py.log._apiwarn(">1.1", "%r was found in a conftest.py file, "
                "use pytest_collect hooks instead." % (cls,))
            return cls

    def getconftest_pathlist(self, name, path=None):
        """ return a matching value, which needs to be sequence
            of filenames that will be returned as a list of Path
            objects (they can be relative to the location
            where they were found).
        """
        try:
            mod, relroots = self._conftest.rget_with_confmod(name, path)
        except KeyError:
            return None
        modpath = py.path.local(mod.__file__).dirpath()
        l = []
        for relroot in relroots:
            if not isinstance(relroot, py.path.local):
                relroot = relroot.replace("/", py.path.local.sep)
                relroot = modpath.join(relroot, abs=True)
            l.append(relroot)
        return l

    def addoptions(self, groupname, *specs):
        # add a named group of options to the current testing session.
        # This function gets invoked during testing session initialization.
        py.log._apiwarn("1.0",
            "define pytest_addoptions(parser) to add options", stacklevel=2)
        group = self._parser.getgroup(groupname)
        for opt in specs:
            group._addoption_instance(opt)
        return self.option

    def addoption(self, *optnames, **attrs):
        return self._parser.addoption(*optnames, **attrs)

    def getvalueorskip(self, name, path=None):
        """ return getvalue(name) or call py.test.skip if no value exists. """
        try:
            val = self.getvalue(name, path)
            if val is None:
                raise KeyError(name)
            return val
        except KeyError:
            py.test.skip("no %r value found" %(name,))

    def getvalue(self, name, path=None):
        """ return 'name' value looked up from the 'options'
            and then from the first conftest file found up
            the path (including the path itself).
            if path is None, lookup the value in the initial
            conftest modules found during command line parsing.
        """
        try:
            return getattr(self.option, name)
        except AttributeError:
            return self._conftest.rget(name, path)

class PluginManager(object):
    def __init__(self):
        from pytest import hookspec
        self.registry = Registry()
        self._name2plugin = {}
        self._hints = []
        self.hook = HookRelay([hookspec], registry=self.registry)
        self.register(self)
        for spec in default_plugins:
            self.import_plugin(spec)

    def _getpluginname(self, plugin, name):
        if name is None:
            if hasattr(plugin, '__name__'):
                name = plugin.__name__.split(".")[-1]
            else:
                name = id(plugin)
        return name

    def register(self, plugin, name=None, prepend=False):
        assert not self.isregistered(plugin), plugin
        assert not self.registry.isregistered(plugin), plugin
        name = self._getpluginname(plugin, name)
        if name in self._name2plugin:
            return False
        self._name2plugin[name] = plugin
        self.call_plugin(plugin, "pytest_addhooks", {'pluginmanager': self})
        self.hook.pytest_plugin_registered(manager=self, plugin=plugin)
        self.registry.register(plugin, prepend=prepend)
        return True

    def unregister(self, plugin):
        self.hook.pytest_plugin_unregistered(plugin=plugin)
        self.registry.unregister(plugin)
        for name, value in list(self._name2plugin.items()):
            if value == plugin:
                del self._name2plugin[name]

    def isregistered(self, plugin, name=None):
        if self._getpluginname(plugin, name) in self._name2plugin:
            return True
        for val in self._name2plugin.values():
            if plugin == val:
                return True

    def addhooks(self, spec):
        self.hook._addhooks(spec, prefix="pytest_")

    def getplugins(self):
        return list(self.registry)

    def skipifmissing(self, name):
        if not self.hasplugin(name):
            py.test.skip("plugin %r is missing" % name)

    def hasplugin(self, name):
        try:
            self.getplugin(name)
        except KeyError:
            return False
        else:
            return True

    def getplugin(self, name):
        try:
            return self._name2plugin[name]
        except KeyError:
            impname = canonical_importname(name)
            return self._name2plugin[impname]

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
            from pkg_resources import iter_entry_points
        except ImportError:
            return # XXX issue a warning
        for ep in iter_entry_points('pytest11'):
            name = canonical_importname(ep.name)
            if name in self._name2plugin:
                continue
            plugin = ep.load()
            self.register(plugin, name=name)

    def consider_preparse(self, args):
        for opt1,opt2 in zip(args, args[1:]):
            if opt1 == "-p":
                self.import_plugin(opt2)

    def consider_conftest(self, conftestmodule):
        cls = getattr(conftestmodule, 'ConftestPlugin', None)
        if cls is not None:
            raise ValueError("%r: 'ConftestPlugins' only existed till 1.0.0b1, "
                "were removed in 1.0.0b2" % (cls,))
        if self.register(conftestmodule, name=conftestmodule.__file__):
            self.consider_module(conftestmodule)

    def consider_module(self, mod):
        attr = getattr(mod, "pytest_plugins", ())
        if attr:
            if not isinstance(attr, (list, tuple)):
                attr = (attr,)
            for spec in attr:
                self.import_plugin(spec)

    def import_plugin(self, spec):
        assert isinstance(spec, str)
        modname = canonical_importname(spec)
        if modname in self._name2plugin:
            return
        try:
            mod = importplugin(modname)
        except KeyboardInterrupt:
            raise
        except py.test.skip.Exception:
            e = py.std.sys.exc_info()[1]
            self._hints.append("skipped plugin %r: %s" %((modname, e.msg)))
        else:
            self.register(mod, modname)
            self.consider_module(mod)

    def pytest_terminal_summary(self, terminalreporter):
        tw = terminalreporter._tw
        if terminalreporter.config.option.traceconfig:
            for hint in self._hints:
                tw.line("hint: %s" % hint)

    #
    #
    # API for interacting with registered and instantiated plugin objects
    #
    #
    def listattr(self, attrname, plugins=None):
        return self.registry.listattr(attrname, plugins=plugins)

    def notify_exception(self, excinfo=None):
        if excinfo is None:
            excinfo = py.code.ExceptionInfo()
        excrepr = excinfo.getrepr(funcargs=True, showlocals=True)
        res = self.hook.pytest_internalerror(excrepr=excrepr)
        if not py.builtin.any(res):
            for line in str(excrepr).split("\n"):
                sys.stderr.write("INTERNALERROR> %s\n" %line)
                sys.stderr.flush()

    def do_addoption(self, parser):
        mname = "pytest_addoption"
        methods = self.registry.listattr(mname, reverse=True)
        mc = MultiCall(methods, {'parser': parser})
        mc.execute()

    def _setns(self, obj, dic):
        for name, value in dic.items():
            if isinstance(value, dict):
                mod = getattr(obj, name, None)
                if mod is None:
                    mod = py.std.types.ModuleType(name)
                    sys.modules['pytest.%s' % name] = mod
                    sys.modules['py.test.%s' % name] = mod
                    mod.__all__ = []
                    setattr(obj, name, mod)
                self._setns(mod, value)
            else:
                #print "setting", name, value, "on", obj
                setattr(obj, name, value)
                obj.__all__.append(name)

    def pytest_plugin_registered(self, plugin):
        dic = self.call_plugin(plugin, "pytest_namespace", {}) or {}
        if dic:
            self._setns(py.test, dic)
        if hasattr(self, '_config'):
            self.call_plugin(plugin, "pytest_addoption",
                {'parser': self._config._parser})
            self.call_plugin(plugin, "pytest_configure",
                {'config': self._config})

    def call_plugin(self, plugin, methname, kwargs):
        return MultiCall(
                methods=self.listattr(methname, plugins=[plugin]),
                kwargs=kwargs, firstresult=True).execute()

    def do_configure(self, config):
        assert not hasattr(self, '_config')
        self._config = config
        config.hook.pytest_configure(config=self._config)

    def do_unconfigure(self, config):
        config = self._config
        del self._config
        config.hook.pytest_unconfigure(config=config)
        config.pluginmanager.unregister(self)

def canonical_importname(name):
    name = name.lower()
    modprefix = "pytest_"
    if not name.startswith(modprefix):
        name = modprefix + name
    return name

def importplugin(importspec):
    #print "importing", importspec
    try:
        return __import__(importspec)
    except ImportError:
        e = py.std.sys.exc_info()[1]
        if str(e).find(importspec) == -1:
            raise
        name = importspec
        try:
            if name.startswith("pytest_"):
                name = importspec[7:]
            return __import__("pytest.plugin.%s" %(name), None, None, '__doc__')
        except ImportError:
            e = py.std.sys.exc_info()[1]
            if str(e).find(name) == -1:
                raise
            # show the original exception, not the failing internal one
            return __import__(importspec)


class MultiCall:
    """ execute a call into multiple python functions/methods.  """

    def __init__(self, methods, kwargs, firstresult=False):
        self.methods = methods[:]
        self.kwargs = kwargs.copy()
        self.kwargs['__multicall__'] = self
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
                pass # might be optional param
        return kwargs

def varnames(func):
    import inspect
    if not inspect.isfunction(func) and not inspect.ismethod(func):
        func = getattr(func, '__call__', func)
    ismethod = inspect.ismethod(func)
    rawcode = py.code.getrawcode(func)
    try:
        return rawcode.co_varnames[ismethod:]
    except AttributeError:
        return ()

class Registry:
    """
        Manage Plugins: register/unregister call calls to plugins.
    """
    def __init__(self, plugins=None):
        if plugins is None:
            plugins = []
        self._plugins = plugins

    def register(self, plugin, prepend=False):
        assert not isinstance(plugin, str)
        assert not plugin in self._plugins
        if not prepend:
            self._plugins.append(plugin)
        else:
            self._plugins.insert(0, plugin)

    def unregister(self, plugin):
        self._plugins.remove(plugin)

    def isregistered(self, plugin):
        return plugin in self._plugins

    def __iter__(self):
        return iter(self._plugins)

    def listattr(self, attrname, plugins=None, reverse=False):
        l = []
        if plugins is None:
            plugins = self._plugins
        for plugin in plugins:
            try:
                l.append(getattr(plugin, attrname))
            except AttributeError:
                continue
        if reverse:
            l.reverse()
        return l

class HookRelay:
    def __init__(self, hookspecs, registry, prefix="pytest_"):
        if not isinstance(hookspecs, list):
            hookspecs = [hookspecs]
        self._hookspecs = []
        self._registry = registry
        for hookspec in hookspecs:
            self._addhooks(hookspec, prefix)

    def _addhooks(self, hookspecs, prefix):
        self._hookspecs.append(hookspecs)
        added = False
        for name, method in vars(hookspecs).items():
            if name.startswith(prefix):
                if not method.__doc__:
                    raise ValueError("docstring required for hook %r, in %r"
                        % (method, hookspecs))
                firstresult = getattr(method, 'firstresult', False)
                hc = HookCaller(self, name, firstresult=firstresult)
                setattr(self, name, hc)
                added = True
                #print ("setting new hook", name)
        if not added:
            raise ValueError("did not find new %r hooks in %r" %(
                prefix, hookspecs,))


    def _performcall(self, name, multicall):
        return multicall.execute()

class HookCaller:
    def __init__(self, hookrelay, name, firstresult):
        self.hookrelay = hookrelay
        self.name = name
        self.firstresult = firstresult

    def __repr__(self):
        return "<HookCaller %r>" %(self.name,)

    def __call__(self, **kwargs):
        methods = self.hookrelay._registry.listattr(self.name)
        mc = MultiCall(methods, kwargs, firstresult=self.firstresult)
        return self.hookrelay._performcall(self.name, mc)

    def pcall(self, plugins, **kwargs):
        methods = self.hookrelay._registry.listattr(self.name, plugins=plugins)
        mc = MultiCall(methods, kwargs, firstresult=self.firstresult)
        return self.hookrelay._performcall(self.name, mc)

