"""
py lib plugins and plugin call management
"""

import py
 
class MultiCall:
    """ execute a call into multiple python functions/methods.  """

    def __init__(self, methods, kwargs, firstresult=False):
        self.methods = methods[:]
        self.kwargs = kwargs 
        self.results = []
        self.firstresult = firstresult

    def __repr__(self):
        status = "%d results, %d meths" % (len(self.results), len(self.methods))
        return "<MultiCall %s, kwargs=%r>" %(status, self.kwargs)

    def execute(self):
        while self.methods:
            method = self.methods.pop()
            res = self._call1(method)
            if res is not None:
                self.results.append(res) 
                if self.firstresult:
                    break
        if not self.firstresult:
            return self.results 
        if self.results:
            return self.results[-1]

    def _call1(self, method):
        kwargs = self.kwargs
        if '__call__' in varnames(method):
            kwargs = kwargs.copy()
            kwargs['__call__'] = self
        return method(**kwargs)

def varnames(rawcode):
    rawcode = getattr(rawcode, 'im_func', rawcode)
    rawcode = getattr(rawcode, 'func_code', rawcode)
    try:
        return rawcode.co_varnames 
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
        for plugin in list(plugins) + list(extra):
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
        
    def __repr__(self):
        return "<HookRelay %r %r>" %(self._hookspecs, self._registry)

class HookCaller:
    def __init__(self, hookrelay, name, firstresult, extralookup=()):
        self.hookrelay = hookrelay 
        self.name = name 
        self.firstresult = firstresult 
        self.extralookup = extralookup and [extralookup] or ()

    def __repr__(self):
        return "<HookCaller %r firstresult=%s %s>" %(
            self.name, self.firstresult, self.hookrelay)

    def __call__(self, **kwargs):
        methods = self.hookrelay._getmethods(self.name, 
            extralookup=self.extralookup)
        mc = MultiCall(methods, kwargs, firstresult=self.firstresult)
        return self.hookrelay._performcall(self.name, mc)
   
comregistry = Registry([])
