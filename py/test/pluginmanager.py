"""
managing loading and interacting with pytest plugins. 
"""
import py
from py.__.test.plugin import hookspec
from py.__.test.outcome import Skipped

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
        self.MultiCall = self.comregistry.MultiCall
        self.impname2plugin = {}

        self.hook = py._com.Hooks(
            hookspecs=hookspec, 
            registry=self.comregistry) 

    def _getpluginname(self, plugin, name):
        if name is None:
            if hasattr(plugin, '__name__'):
                name = plugin.__name__.split(".")[-1]
            else:
                name = id(plugin) 
        return name 

    def register(self, plugin, name=None):
        assert not self.isregistered(plugin)
        name = self._getpluginname(plugin, name)
        if name in self.impname2plugin:
            return False
        self.impname2plugin[name] = plugin
        self.hook.pytest_plugin_registered(plugin=plugin)
        self._checkplugin(plugin)
        self.comregistry.register(plugin)
        return True

    def unregister(self, plugin):
        self.hook.pytest_plugin_unregistered(plugin=plugin)
        self.comregistry.unregister(plugin)
        for name, value in self.impname2plugin.items():
            if value == plugin:
                del self.impname2plugin[name]

    def isregistered(self, plugin, name=None):
        return self._getpluginname(plugin, name) in self.impname2plugin

    def getplugins(self):
        return list(self.comregistry)

    def getplugin(self, importname):
        impname = canonical_importname(importname)
        return self.impname2plugin[impname]

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
        if modname in self.impname2plugin:
            return
        try:
            mod = importplugin(modname)
        except KeyboardInterrupt:
            raise
        except Skipped, e:
            self._warn("could not import plugin %r, reason: %r" %(
                (modname, e.msg)))
        else:
            check_old_use(mod, modname) 
            self.register(mod)
            self.consider_module(mod)

    def _warn(self, msg):
        print "===WARNING=== %s" % (msg,)

    def _checkplugin(self, plugin):
        # =====================================================
        # check plugin hooks 
        # =====================================================
        methods = collectattr(plugin)
        hooks = collectattr(hookspec)
        stringio = py.std.StringIO.StringIO()
        def Print(*args):
            if args:
                stringio.write(" ".join(map(str, args)))
            stringio.write("\n")

        fail = False
        while methods:
            name, method = methods.popitem()
            #print "checking", name
            if isgenerichook(name):
                continue
            if name not in hooks: 
                Print("found unknown hook:", name)
                fail = True
            else:
                method_args = getargs(method)
                if '__call__' in method_args:
                    method_args.remove('__call__')
                hook = hooks[name]
                hookargs = getargs(hook)
                for arg, hookarg in zip(method_args, hookargs):
                    if arg != hookarg: 
                        Print("argument mismatch: %r != %r"  %(arg, hookarg))
                        Print("actual  : %s" %(formatdef(method)))
                        Print("required:", formatdef(hook))
                        fail = True
                        break 
                #if not fail:
                #    print "matching hook:", formatdef(method)
            if fail:
                name = getattr(plugin, '__name__', plugin)
                raise self.Error("%s:\n%s" %(name, stringio.getvalue()))
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
        methods = self.comregistry.listattr("pytest_addoption", reverse=True)
        mc = py._com.MultiCall(methods, parser=parser)
        mc.execute()

    def pytest_plugin_registered(self, plugin):
        if hasattr(self, '_config'):
            self.call_plugin(plugin, "pytest_addoption", parser=self._config._parser)
            self.call_plugin(plugin, "pytest_configure", config=self._config)
            #dic = self.call_plugin(plugin, "pytest_namespace", config=self._config)
            #self._updateext(dic)

    def call_plugin(self, plugin, methname, **kwargs):
        return self.MultiCall(self.listattr(methname, plugins=[plugin]), 
                **kwargs).execute(firstresult=True)

    def _updateext(self, dic):
        if dic:
            for name, value in dic.items():
                setattr(py.test, name, value)

    def do_configure(self, config):
        assert not hasattr(self, '_config')
        config.pluginmanager.register(self)
        self._config = config
        config.hook.pytest_configure(config=self._config)
        for dic in config.hook.pytest_namespace(config=config) or []:
            self._updateext(dic)

    def do_unconfigure(self, config):
        config = self._config 
        del self._config 
        config.hook.pytest_unconfigure(config=config)
        config.pluginmanager.unregister(self)

class Ext:
    """ namespace for extension objects. """ 
    
# 
#  XXX old code to automatically load classes
#
def canonical_importname(name):
    name = name.lower()
    modprefix = "pytest_"
    if not name.startswith(modprefix):
        name = modprefix + name 
    return name 

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



def isgenerichook(name):
    return name == "pytest_plugins" or \
           name.startswith("pytest_funcarg__") or \
           name.startswith("pytest_option_")

def getargs(func):
    args = py.std.inspect.getargs(func.func_code)[0]
    startindex = hasattr(func, 'im_self') and 1 or 0
    return args[startindex:]

def collectattr(obj, prefixes=("pytest_",)):
    methods = {}
    for apiname in dir(obj):
        for prefix in prefixes:
            if apiname.startswith(prefix):
                methods[apiname] = getattr(obj, apiname) 
    return methods 

def formatdef(func):
    return "%s%s" %(
        func.func_name, 
        py.std.inspect.formatargspec(*py.std.inspect.getargspec(func))
    )

if __name__ == "__main__":
    import py.__.test.plugin
    basedir = py.path.local(py.__.test.plugin.__file__).dirpath()
    name2text = {}
    for p in basedir.listdir("pytest_*"):
        if p.ext == ".py" or (
           p.check(dir=1) and p.join("__init__.py").check()):
            impname = p.purebasename 
            if impname.find("__") != -1:
                continue
            try:
                plugin = importplugin(impname)
            except (ImportError, py.__.test.outcome.Skipped):
                name2text[impname] = "IMPORT ERROR"
            else:
                doc = plugin.__doc__ or ""
                doc = doc.strip()
                name2text[impname] = doc
           
    for name in sorted(name2text.keys()):
        text = name2text[name]
        if name[0] == "_":
            continue
        print "%-20s %s" % (name, text.split("\n")[0])

        #text = py.std.textwrap.wrap(name2text[name], 
        #    width = 80,
        #    initial_indent="%s: " % name, 
        #    replace_whitespace = False)
        #for line in text:
        #    print line
     

