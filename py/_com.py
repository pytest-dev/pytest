"""
py lib plugins and plugin call management
"""

import py
 
class MultiCall:
    """ Manage a specific call into many python functions/methods. 

        Simple example: 
        MultiCall([list1.append, list2.append], 42).execute()
    """

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
    logfile = None
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

class Hooks: 
    def __init__(self, hookspecs, registry=None):
        self._hookspecs = hookspecs
        if registry is None:
            registry = py._com.comregistry
        self.registry = registry
        for name, method in vars(hookspecs).items():
            if name[:2] != "__":
                firstresult = getattr(method, 'firstresult', False)
                mm = HookCall(registry, name, firstresult=firstresult)
                setattr(self, name, mm)
    def __repr__(self):
        return "<Hooks %r %r>" %(self._hookspecs, self._plugins)

class HookCall:
    def __init__(self, registry, name, firstresult, extralookup=None):
        self.registry = registry
        self.name = name 
        self.firstresult = firstresult 
        self.extralookup = extralookup and [extralookup] or ()

    def clone(self, extralookup):
        return HookCall(self.registry, self.name, self.firstresult, extralookup)

    def __repr__(self):
        mode = self.firstresult and "firstresult" or "each"
        return "<HookCall %r mode=%s %s>" %(self.name, mode, self.registry)

    def __call__(self, *args, **kwargs):
        if args:
            raise TypeError("only keyword arguments allowed "
                            "for api call to %r" % self.name)
        attr = self.registry.listattr(self.name, extra=self.extralookup)
        mc = MultiCall(attr, **kwargs)
        # XXX this should be doable from a hook impl:
        if self.registry.logfile:
            self.registry.logfile.write("%s(**%s) # firstresult=%s\n" %
                (self.name, kwargs, self.firstresult))
            self.registry.logfile.flush()
        return mc.execute(firstresult=self.firstresult)

comregistry = Registry()
