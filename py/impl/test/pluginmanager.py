"""
managing loading and interacting with pytest plugins. 
"""
import py
from py.plugin import hookspec
from py.impl.test.outcome import Skipped

default_plugins = (
    "default runner capture terminal mark skipping tmpdir monkeypatch "
    "recwarn pdb pastebin unittest helpconfig nose assertion").split()

def check_old_use(mod, modname):
    clsname = modname[len('pytest_'):].capitalize() + "Plugin" 
    assert not hasattr(mod, clsname), (mod, clsname)

class PluginManager(object):
    class Error(Exception):
        """signals a plugin specific error."""
    def __init__(self, comregistry=None):
        if comregistry is None: 
            comregistry = py._com.Registry()
        self.comregistry = comregistry 
        self._name2plugin = {}

        self.hook = py._com.HookRelay(
            hookspecs=hookspec, 
            registry=self.comregistry) 
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

    def register(self, plugin, name=None):
        assert not self.isregistered(plugin), plugin
        assert not self.comregistry.isregistered(plugin), plugin
        name = self._getpluginname(plugin, name)
        if name in self._name2plugin:
            return False
        self._name2plugin[name] = plugin
        self.hook.pytest_plugin_registered(manager=self, plugin=plugin)
        self.comregistry.register(plugin)
        return True

    def unregister(self, plugin):
        self.hook.pytest_plugin_unregistered(plugin=plugin)
        self.comregistry.unregister(plugin)
        for name, value in list(self._name2plugin.items()):
            if value == plugin:
                del self._name2plugin[name]

    def isregistered(self, plugin, name=None):
        if self._getpluginname(plugin, name) in self._name2plugin:
            return True
        for val in self._name2plugin.values():
            if plugin == val:
                return True

    def getplugins(self):
        return list(self.comregistry)

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
            if ep.name in self._name2plugin:
                continue
            plugin = ep.load()
            self.register(plugin, name=ep.name)

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
        except Skipped:
            e = py.std.sys.exc_info()[1]
            self._warn("could not import plugin %r, reason: %r" %(
                (modname, e.msg)))
        else:
            check_old_use(mod, modname) 
            self.register(mod)
            self.consider_module(mod)

    def _warn(self, msg):
        print ("===WARNING=== %s" % (msg,))

    # 
    #
    # API for interacting with registered and instantiated plugin objects 
    #
    # 
    def listattr(self, attrname, plugins=None, extra=()):
        return self.comregistry.listattr(attrname, plugins=plugins, extra=extra)

    def notify_exception(self, excinfo=None):
        if excinfo is None:
            excinfo = py.code.ExceptionInfo()
        excrepr = excinfo.getrepr(funcargs=True, showlocals=True)
        return self.hook.pytest_internalerror(excrepr=excrepr)

    def do_addoption(self, parser):
        mname = "pytest_addoption"
        methods = self.comregistry.listattr(mname, reverse=True)
        mc = py._com.MultiCall(methods, {'parser': parser})
        mc.execute()

    def pytest_plugin_registered(self, plugin):
        dic = self.call_plugin(plugin, "pytest_namespace", {}) or {}
        for name, value in dic.items():
            setattr(py.test, name, value)
        if hasattr(self, '_config'):
            self.call_plugin(plugin, "pytest_addoption", 
                {'parser': self._config._parser})
            self.call_plugin(plugin, "pytest_configure", 
                {'config': self._config})

    def call_plugin(self, plugin, methname, kwargs):
        return py._com.MultiCall(
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
    try:
        return __import__(importspec) 
    except ImportError:
        e = py.std.sys.exc_info()[1]
        if str(e).find(importspec) == -1:
            raise
        try:
            return __import__("py.plugin.%s" %(importspec), 
                None, None, '__doc__')
        except ImportError:
            e = py.std.sys.exc_info()[1]
            if str(e).find(importspec) == -1:
                raise
            #print "syspath:", py.std.sys.path
            #print "curdir:", py.std.os.getcwd()
            return __import__(importspec)  # show the original exception



