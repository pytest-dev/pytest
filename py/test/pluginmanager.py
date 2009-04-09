"""
managing loading and interacting with pytest plugins. 
"""
import py
from py.__.test.plugin import api

class PluginManager(object):
    def __init__(self, comregistry=None):
        if comregistry is None: 
            comregistry = py._com.Registry()
        self.comregistry = comregistry 
        self.MultiCall = self.comregistry.MultiCall
        self.impname2plugin = {}

        self.api = py._com.PluginAPI(
            apiclass=api.PluginHooks, 
            registry=self.comregistry) 

    def register(self, plugin):
        self.api.pytest_plugin_registered(plugin=plugin)
        self.comregistry.register(plugin)

    def unregister(self, plugin):
        self.api.pytest_plugin_unregistered(plugin=plugin)
        self.comregistry.unregister(plugin)

    def isregistered(self, plugin):
        return self.comregistry.isregistered(plugin)

    def getplugins(self):
        return list(self.comregistry)

    # API for bootstrapping 
    #
    def getplugin(self, importname):
        impname, clsname = canonical_names(importname)
        return self.impname2plugin[impname]

    def _envlist(self, varname):
        val = py.std.os.environ.get(varname, None)
        if val is not None:
            return val.split(',')
        return ()
    
    def consider_env(self):
        for spec in self._envlist("PYTEST_PLUGINS"):
            self.import_plugin(spec)

    def consider_conftest(self, conftestmodule):
        cls = getattr(conftestmodule, 'ConftestPlugin', None)
        if cls is not None and cls not in self.impname2plugin:
            self.impname2plugin[cls] = True
            self.register(cls())
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
        modname, clsname = canonical_names(spec)
        if modname in self.impname2plugin:
            return
        mod = importplugin(modname)
        plugin = registerplugin(self.register, mod, clsname)
        self.impname2plugin[modname] = plugin
        self.consider_module(mod)
    # 
    #
    # API for interacting with registered and instantiated plugin objects 
    #
    # 
    def getfirst(self, attrname):
        for x in self.comregistry.listattr(attrname):
            return x

    def listattr(self, attrname):
        return self.comregistry.listattr(attrname)

    def call_firstresult(self, *args, **kwargs):
        return self.comregistry.call_firstresult(*args, **kwargs)

    def call_each(self, *args, **kwargs):
        #print "plugins.call_each", args[0], args[1:], kwargs
        return self.comregistry.call_each(*args, **kwargs)

    def notify_exception(self, excinfo=None):
        if excinfo is None:
            excinfo = py.code.ExceptionInfo()
        excrepr = excinfo.getrepr(funcargs=True, showlocals=True)
        return self.api.pytest_internalerror(excrepr=excrepr)

    def do_addoption(self, parser):
        methods = self.comregistry.listattr("pytest_addoption", reverse=True)
        mc = py._com.MultiCall(methods, parser=parser)
        mc.execute()

    def pytest_plugin_registered(self, plugin):
        if hasattr(self, '_config'):
            self.comregistry.call_plugin(plugin, "pytest_addoption", parser=self._config._parser)
            self.comregistry.call_plugin(plugin, "pytest_configure", config=self._config)

    def do_configure(self, config):
        assert not hasattr(self, '_config')
        config.pluginmanager.register(self)
        self._config = config
        config.api.pytest_configure(config=self._config)

    def do_unconfigure(self, config):
        config = self._config 
        del self._config 
        config.api.pytest_unconfigure(config=config)
        config.pluginmanager.unregister(self)

    def do_itemrun(self, item, pdb=None):
        res = self.comregistry.call_firstresult("pytest_itemrun", item=item, pdb=pdb)
        if res is None:
            raise ValueError("could not run %r" %(item,))

# 
#  XXX old code to automatically load classes
#
def canonical_names(importspec):
    importspec = importspec.lower()
    modprefix = "pytest_"
    if not importspec.startswith(modprefix):
        importspec = modprefix + importspec
    clsname = importspec[len(modprefix):].capitalize() + "Plugin"
    return importspec, clsname

def registerplugin(registerfunc, mod, clsname):
    pluginclass = getattr(mod, clsname) 
    plugin = pluginclass()
    registerfunc(plugin)
    return plugin

def importplugin(importspec):
    try:
        return __import__(importspec) 
    except ImportError, e:
        if str(e).find(importspec) == -1:
            raise
        try:
            return __import__("py.__.test.plugin.%s" %(importspec), None, None, '__doc__')
        except ImportError, e:
            if str(e).find(importspec) == -1:
                raise
            #print "syspath:", py.std.sys.path
            #print "curdir:", py.std.os.getcwd()
            return __import__(importspec)  # show the original exception
