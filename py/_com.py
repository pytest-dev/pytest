"""
py lib plugins and plugin call management
"""

import py
import inspect
 
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

    def register(self, plugin):
        assert not isinstance(plugin, str)
        assert not plugin in self._plugins
        self._plugins.append(plugin)

    def unregister(self, plugin):
        self._plugins.remove(plugin)

    def isregistered(self, plugin):
        return plugin in self._plugins 

    def __iter__(self):
        return iter(self._plugins)

    def listattr(self, attrname, plugins=None, extra=(), reverse=False):
        l = []
        if plugins is None:
            plugins = self._plugins
        candidates = list(plugins) + list(extra)
        for plugin in candidates:
            try:
                l.append(getattr(plugin, attrname))
            except AttributeError:
                continue 
        if reverse:
            l.reverse()
        return l

class HookRelay: 
    def __init__(self, hookspecs, registry):
        self._hookspecs = hookspecs
        self._registry = registry
        for name, method in vars(hookspecs).items():
            if name[:1] != "_":
                setattr(self, name, self._makecall(name))

    def _makecall(self, name, extralookup=None):
        hookspecmethod = getattr(self._hookspecs, name)
        firstresult = getattr(hookspecmethod, 'firstresult', False)
        return HookCaller(self, name, firstresult=firstresult,
            extralookup=extralookup)

    def _getmethods(self, name, extralookup=()):
        return self._registry.listattr(name, extra=extralookup)

    def _performcall(self, name, multicall):
        return multicall.execute()
        
class HookCaller:
    def __init__(self, hookrelay, name, firstresult, extralookup=None):
        self.hookrelay = hookrelay 
        self.name = name 
        self.firstresult = firstresult 
        self.extralookup = extralookup and [extralookup] or ()

    def __repr__(self):
        return "<HookCaller %r>" %(self.name,)

    def __call__(self, **kwargs):
        methods = self.hookrelay._getmethods(self.name, self.extralookup)
        mc = MultiCall(methods, kwargs, firstresult=self.firstresult)
        return self.hookrelay._performcall(self.name, mc)
   
comregistry = Registry([])
