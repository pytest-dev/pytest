"""
py lib plugins and plugin call management
"""

import py
 
class MultiCall:
    """ Manage a specific call into many python functions/methods. 

        Simple example: 
        MultiCall([list1.append, list2.append], 42).execute()
    """
    NONEASRESULT = object()

    def __init__(self, methods, *args, **kwargs):
        self.methods = methods[:]
        self.args = args 
        self.kwargs = kwargs 
        self.results = []

    def execute(self, firstresult=False):
        while self.methods:
            currentmethod = self.methods.pop()
            res = self.execute_method(currentmethod)
            if hasattr(self, '_ex1'):
                self.results = [res]
                break
            if res is not None:
                if res is self.NONEASRESULT:
                    res = None
                self.results.append(res) 
                if firstresult:
                    break 
        if not firstresult:
            return self.results 
        if self.results:
            return self.results[-1] 

    def execute_method(self, currentmethod):
        self.currentmethod = currentmethod
        # provide call introspection if "__call__" is the first positional argument 
        if hasattr(currentmethod, 'im_self'):
            varnames = currentmethod.im_func.func_code.co_varnames
            needscall = varnames[1:2] == ('__call__',)
        else:
            try:
                varnames = currentmethod.func_code.co_varnames
            except AttributeError:
                # builtin function
                varnames = ()
            needscall = varnames[:1] == ('__call__',)
        if needscall:
            return currentmethod(self, *self.args, **self.kwargs)
        else:
            #try:
                return currentmethod(*self.args, **self.kwargs)
            #except TypeError:
            #    print currentmethod.__module__, currentmethod.__name__, self.args, self.kwargs
            #    raise

    def exclude_other_results(self):
        self._ex1 = True


class Registry:
    """
        Manage Plugins: Load plugins and manage calls to plugins. 
    """
    MultiCall = MultiCall

    def __init__(self, plugins=None):
        if plugins is None:
            plugins = []
        self._plugins = plugins

    def register(self, plugin):
        assert not isinstance(plugin, str)
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

    def call_firstresult(self, methname, *args, **kwargs):
        """ return first non-None result of a plugin method. """ 
        return MultiCall(self.listattr(methname), *args, **kwargs).execute(firstresult=True)

    def call_plugin(self, plugin, methname, *args, **kwargs):
        return MultiCall(self.listattr(methname, plugins=[plugin]), 
                    *args, **kwargs).execute(firstresult=True)


class PluginAPI: 
    def __init__(self, apiclass, registry=None):
        self._apiclass = apiclass
        if registry is None:
            registry = comregistry
        self.registry = registry
        for name, method in vars(apiclass).items():
            if name[:2] != "__":
                firstresult = getattr(method, 'firstresult', False)
                mm = ApiCall(registry, name, firstresult=firstresult)
                setattr(self, name, mm)
    def __repr__(self):
        return "<PluginAPI %r %r>" %(self._apiclass, self._plugins)

class ApiCall:
    def __init__(self, registry, name, firstresult):
        self.registry = registry
        self.name = name 
        self.firstresult = firstresult 

    def __repr__(self):
        mode = self.firstresult and "firstresult" or "each"
        return "<ApiCall %r mode=%s %s>" %(self.name, mode, self.registry)

    def __call__(self, *args, **kwargs):
        if args:
            raise TypeError("only keyword arguments allowed "
                            "for api call to %r" % self.name)
        mc = MultiCall(self.registry.listattr(self.name), **kwargs)
        return mc.execute(firstresult=self.firstresult)

comregistry = Registry()
