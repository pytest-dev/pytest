"""
py lib plugins and events. 

you can write plugins that extend the py lib API. 
currently this is mostly used by py.test 

registering a plugin
++++++++++++++++++++++++++++++++++

::
    >>> class MyPlugin:
    ...    def pyevent__plugin_registered(self, plugin):
    ...       print "registering", plugin.__class__.__name__
    ... 
    >>> import py
    >>> py._com.pyplugins.register(MyPlugin())
    registering MyPlugin

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
            self.currentmethod = currentmethod = self.methods.pop()
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
                res = currentmethod(self, *self.args, **self.kwargs)
            else:
                res = currentmethod(*self.args, **self.kwargs)
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

    def exclude_other_results(self):
        self._ex1 = True


class PyPlugins:
    """
        Manage Plugins: Load plugins and manage calls to plugins. 
    """
    MultiCall = MultiCall

    def __init__(self, plugins=None):
        if plugins is None:
            plugins = []
        self._plugins = plugins

    def import_module(self, modspec):
        # XXX allow modspec to specify version / lookup 
        modpath = modspec
        self.notify("importingmodule", modpath)
        __import__(modpath) 

    def consider_env(self):
        """ consider ENV variable for loading modules. """ 
        for spec in self._envlist("PYLIB"):
            self.import_module(spec)

    def _envlist(self, varname):
        val = py.std.os.environ.get(varname, None)
        if val is not None:
            return val.split(',')
        return ()

    def consider_module(self, mod, varname="pylib"):
        speclist = getattr(mod, varname, ())
        if not isinstance(speclist, (list, tuple)):
            speclist = (speclist,)
        for spec in speclist:
            self.import_module(spec)

    def register(self, plugin):
        assert not isinstance(plugin, str)
        self._plugins.append(plugin)
        self.notify("plugin_registered", plugin)

    def unregister(self, plugin):
        self.notify("plugin_unregistered", plugin)
        self._plugins.remove(plugin)

    def getplugins(self):
        return list(self._plugins)

    def isregistered(self, plugin):
        return plugin in self._plugins 

    def listattr(self, attrname, plugins=None, extra=(), reverse=False):
        l = []
        if plugins is None:
            plugins = self._plugins
        if extra:
            plugins += list(extra)
        for plugin in plugins:
            try:
                l.append(getattr(plugin, attrname))
            except AttributeError:
                continue 
        if reverse:
            l.reverse()
        return l

    def call_each(self, methname, *args, **kwargs):
        """ return call object for executing a plugin call. """
        return MultiCall(self.listattr(methname), *args, **kwargs).execute()

    def call_firstresult(self, methname, *args, **kwargs):
        """ return first non-None result of a plugin method. """ 
        return MultiCall(self.listattr(methname), *args, **kwargs).execute(firstresult=True)

    def call_plugin(self, plugin, methname, *args, **kwargs):
        return MultiCall(self.listattr(methname, plugins=[plugin]), 
                    *args, **kwargs).execute(firstresult=True)

    def notify(self, eventname, *args, **kwargs):
        #print "notifying", eventname, args, kwargs
        MultiCall(self.listattr("pyevent__" + eventname), 
             *args, **kwargs).execute()
        #print "calling anonymous hooks", args, kwargs
        MultiCall(self.listattr("pyevent"), 
             eventname, *args, **kwargs).execute()

pyplugins = PyPlugins()
