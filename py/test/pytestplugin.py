"""
handling py.test plugins. 
"""
import py

class PytestPlugins(object):
    def __init__(self, pyplugins=None):
        if pyplugins is None: 
            pyplugins = py._com.PyPlugins()
        self.pyplugins = pyplugins 
        self.MultiCall = self.pyplugins.MultiCall
        self._plugins = {}

    def register(self, plugin):
        self.pyplugins.register(plugin)
    def unregister(self, plugin):
        self.pyplugins.unregister(plugin)
    def isregistered(self, plugin):
        return self.pyplugins.isregistered(plugin)

    def getplugins(self):
        return self.pyplugins.getplugins()

    # API for bootstrapping 
    #
    def getplugin(self, importname):
        impname, clsname = canonical_names(importname)
        return self._plugins[impname]
    
    def consider_env(self):
        for spec in self.pyplugins._envlist("PYTEST_PLUGINS"):
            self.import_plugin(spec)

    def consider_conftest(self, conftestmodule):
        cls = getattr(conftestmodule, 'ConftestPlugin', None)
        if cls is not None and cls not in self._plugins:
            self._plugins[cls] = True
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
        if modname in self._plugins:
            return
        mod = importplugin(modname)
        plugin = registerplugin(self.pyplugins.register, mod, clsname)
        self._plugins[modname] = plugin
        self.consider_module(mod)
    # 
    #
    # API for interacting with registered and instantiated plugin objects 
    #
    # 
    def getfirst(self, attrname):
        for x in self.pyplugins.listattr(attrname):
            return x

    def listattr(self, attrname):
        return self.pyplugins.listattr(attrname)

    def call_firstresult(self, *args, **kwargs):
        return self.pyplugins.call_firstresult(*args, **kwargs)

    def call_each(self, *args, **kwargs):
        #print "plugins.call_each", args[0], args[1:], kwargs
        return self.pyplugins.call_each(*args, **kwargs)

    def notify(self, eventname, *args, **kwargs):
        return self.pyplugins.notify(eventname, *args, **kwargs)

    def do_addoption(self, parser):
        self.pyplugins.call_each('pytest_addoption', parser=parser)

    def pyevent_plugin_registered(self, plugin):
        if hasattr(self, '_config'):
            self.pyplugins.call_plugin(plugin, "pytest_addoption", parser=self._config._parser)
            self.pyplugins.call_plugin(plugin, "pytest_configure", config=self._config)

    def do_configure(self, config):
        assert not hasattr(self, '_config')
        config.bus.register(self)
        self._config = config
        self.pyplugins.call_each("pytest_configure", config=self._config)

    def do_unconfigure(self, config):
        config = self._config 
        del self._config 
        self.pyplugins.call_each("pytest_unconfigure", config=config)

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
            return __import__(importspec)  # show the original exception
