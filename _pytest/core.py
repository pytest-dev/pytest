"""
PluginManager, basic initialization and tracing.
"""
import sys
import inspect
import py

py3 = sys.version_info > (3,0)

class TagTracer:
    def __init__(self):
        self._tag2proc = {}
        self.writer = None
        self.indent = 0

    def get(self, name):
        return TagTracerSub(self, (name,))

    def format_message(self, tags, args):
        if isinstance(args[-1], dict):
            extra = args[-1]
            args = args[:-1]
        else:
            extra = {}

        content = " ".join(map(str, args))
        indent = "  " * self.indent

        lines = [
            "%s%s [%s]\n" %(indent, content, ":".join(tags))
        ]

        for name, value in extra.items():
            lines.append("%s    %s: %s\n" % (indent, name, value))
        return lines

    def processmessage(self, tags, args):
        if self.writer is not None and args:
            lines = self.format_message(tags, args)
            self.writer(''.join(lines))
        try:
            self._tag2proc[tags](tags, args)
        except KeyError:
            pass

    def setwriter(self, writer):
        self.writer = writer

    def setprocessor(self, tags, processor):
        if isinstance(tags, str):
            tags = tuple(tags.split(":"))
        else:
            assert isinstance(tags, tuple)
        self._tag2proc[tags] = processor

class TagTracerSub:
    def __init__(self, root, tags):
        self.root = root
        self.tags = tags
    def __call__(self, *args):
        self.root.processmessage(self.tags, args)
    def setmyprocessor(self, processor):
        self.root.setprocessor(self.tags, processor)
    def get(self, name):
        return self.__class__(self.root, self.tags + (name,))


def add_method_wrapper(cls, wrapper_func):
    """ Substitute the function named "wrapperfunc.__name__" at class
    "cls" with a function that wraps the call to the original function.
    Return an undo function which can be called to reset the class to use
    the old method again.

    wrapper_func is called with the same arguments as the method
    it wraps and its result is used as a wrap_controller for
    calling the original function.
    """
    name = wrapper_func.__name__
    oldcall = getattr(cls, name)
    def wrap_exec(*args, **kwargs):
        gen = wrapper_func(*args, **kwargs)
        return wrapped_call(gen, lambda: oldcall(*args, **kwargs))

    setattr(cls, name, wrap_exec)
    return lambda: setattr(cls, name, oldcall)

def raise_wrapfail(wrap_controller, msg):
    co = wrap_controller.gi_code
    raise RuntimeError("wrap_controller at %r %s:%d %s" %
                   (co.co_name, co.co_filename, co.co_firstlineno, msg))

def wrapped_call(wrap_controller, func):
    """ Wrap calling to a function with a generator which needs to yield
    exactly once.  The yield point will trigger calling the wrapped function
    and return its CallOutcome to the yield point.  The generator then needs
    to finish (raise StopIteration) in order for the wrapped call to complete.
    """
    try:
        next(wrap_controller)   # first yield
    except StopIteration:
        raise_wrapfail(wrap_controller, "did not yield")
    call_outcome = CallOutcome(func)
    try:
        wrap_controller.send(call_outcome)
        raise_wrapfail(wrap_controller, "has second yield")
    except StopIteration:
        pass
    return call_outcome.get_result()


class CallOutcome:
    """ Outcome of a function call, either an exception or a proper result.
    Calling the ``get_result`` method will return the result or reraise
    the exception raised when the function was called. """
    excinfo = None
    def __init__(self, func):
        try:
            self.result = func()
        except BaseException:
            self.excinfo = sys.exc_info()

    def force_result(self, result):
        self.result = result
        self.excinfo = None

    def get_result(self):
        if self.excinfo is None:
            return self.result
        else:
            ex = self.excinfo
            if py3:
                raise ex[1].with_traceback(ex[2])
            py.builtin._reraise(*ex)


class PluginManager(object):
    """ Core Pluginmanager class which manages registration
    of plugin objects and 1:N hook calling.

    You can register new hooks by calling ``addhooks(module_or_class)``.
    You can register plugin objects (which contain hooks) by calling
    ``register(plugin)``.  The Pluginmanager is initialized with a
    prefix that is searched for in the names of the dict of registered
    plugin objects.  An optional excludefunc allows to blacklist names which
    are not considered as hooks despite a matching prefix.

    For debugging purposes you can call ``set_tracing(writer)``
    which will subsequently send debug information to the specified
    write function.
    """

    def __init__(self, prefix, excludefunc=None):
        self._prefix = prefix
        self._excludefunc = excludefunc
        self._name2plugin = {}
        self._plugins = []
        self._plugin2hookcallers = {}
        self.trace = TagTracer().get("pluginmanage")
        self.hook = HookRelay(pm=self)

    def set_tracing(self, writer):
        """ turn on tracing to the given writer method and
        return an undo function. """
        self.trace.root.setwriter(writer)
        # reconfigure HookCalling to perform tracing
        assert not hasattr(self, "_wrapping")
        self._wrapping = True

        def _docall(self, methods, kwargs):
            trace = self.hookrelay.trace
            trace.root.indent += 1
            trace(self.name, kwargs)
            box = yield
            if box.excinfo is None:
                trace("finish", self.name, "-->", box.result)
            trace.root.indent -= 1

        return add_method_wrapper(HookCaller, _docall)

    def make_hook_caller(self, name, plugins):
        caller = getattr(self.hook, name)
        methods = self.listattr(name, plugins=plugins)
        if methods:
            return HookCaller(self.hook, caller.name, caller.firstresult,
                              argnames=caller.argnames, methods=methods)
        return caller

    def register(self, plugin, name=None):
        """ Register a plugin with the given name and ensure that all its
        hook implementations are integrated.  If the name is not specified
        we use the ``__name__`` attribute of the plugin object or, if that
        doesn't exist, the id of the plugin.  This method will raise a
        ValueError if the eventual name is already registered. """
        name = name or self._get_canonical_name(plugin)
        if self._name2plugin.get(name, None) == -1:
            return
        if self.hasplugin(name):
            raise ValueError("Plugin already registered: %s=%s\n%s" %(
                              name, plugin, self._name2plugin))
        #self.trace("registering", name, plugin)
        # allow subclasses to intercept here by calling a helper
        return self._do_register(plugin, name)

    def _do_register(self, plugin, name):
        hookcallers = list(self._scan_plugin(plugin))
        self._plugin2hookcallers[plugin] = hookcallers
        self._name2plugin[name] = plugin
        self._plugins.append(plugin)
        # rescan all methods for the hookcallers we found
        for hookcaller in hookcallers:
            hookcaller.scan_methods()
        return True

    def unregister(self, plugin):
        """ unregister the plugin object and all its contained hook implementations
        from internal data structures. """
        self._plugins.remove(plugin)
        for name, value in list(self._name2plugin.items()):
            if value == plugin:
                del self._name2plugin[name]
        hookcallers = self._plugin2hookcallers.pop(plugin)
        for hookcaller in hookcallers:
            hookcaller.scan_methods()

    def addhooks(self, module_or_class):
        """ add new hook definitions from the given module_or_class using
        the prefix/excludefunc with which the PluginManager was initialized. """
        isclass = int(inspect.isclass(module_or_class))
        names = []
        for name in dir(module_or_class):
            if name.startswith(self._prefix):
                method = module_or_class.__dict__[name]
                firstresult = getattr(method, 'firstresult', False)
                hc = HookCaller(self.hook, name, firstresult=firstresult,
                                argnames=varnames(method, startindex=isclass))
                setattr(self.hook, name, hc)
                names.append(name)
        if not names:
            raise ValueError("did not find new %r hooks in %r"
                             %(self._prefix, module_or_class))

    def getplugins(self):
        """ return the complete list of registered plugins. NOTE that
        you will get the internal list and need to make a copy if you
        modify the list."""
        return self._plugins

    def isregistered(self, plugin):
        """ Return True if the plugin is already registered under its
        canonical name. """
        return self.hasplugin(self._get_canonical_name(plugin)) or \
               plugin in self._plugins

    def hasplugin(self, name):
        """ Return True if there is a registered with the given name. """
        return name in self._name2plugin

    def getplugin(self, name):
        """ Return a plugin or None for the given name. """
        return self._name2plugin.get(name)

    def listattr(self, attrname, plugins=None):
        if plugins is None:
            plugins = self._plugins
        l = []
        last = []
        wrappers = []
        for plugin in plugins:
            try:
                meth = getattr(plugin, attrname)
            except AttributeError:
                continue
            if hasattr(meth, 'hookwrapper'):
                wrappers.append(meth)
            elif hasattr(meth, 'tryfirst'):
                last.append(meth)
            elif hasattr(meth, 'trylast'):
                l.insert(0, meth)
            else:
                l.append(meth)
        l.extend(last)
        l.extend(wrappers)
        return l

    def call_plugin(self, plugin, methname, kwargs):
        return MultiCall(methods=self.listattr(methname, plugins=[plugin]),
                kwargs=kwargs, firstresult=True).execute()


    def _scan_plugin(self, plugin):
        def fail(msg, *args):
            name = getattr(plugin, '__name__', plugin)
            raise PluginValidationError("plugin %r\n%s" %(name, msg % args))

        for name in dir(plugin):
            if name[0] == "_" or not name.startswith(self._prefix):
                continue
            hook = getattr(self.hook, name, None)
            method = getattr(plugin, name)
            if hook is None:
                if self._excludefunc is not None and self._excludefunc(name):
                    continue
                if getattr(method, 'optionalhook', False):
                    continue
                fail("found unknown hook: %r", name)
            for arg in varnames(method):
                if arg not in hook.argnames:
                    fail("argument %r not available\n"
                         "actual definition: %s\n"
                         "available hookargs: %s",
                         arg, formatdef(method),
                           ", ".join(hook.argnames))
            yield hook

    def _get_canonical_name(self, plugin):
        return getattr(plugin, "__name__", None) or str(id(plugin))



class MultiCall:
    """ execute a call into multiple python functions/methods. """

    def __init__(self, methods, kwargs, firstresult=False):
        self.methods = list(methods)
        self.kwargs = kwargs
        self.kwargs["__multicall__"] = self
        self.results = []
        self.firstresult = firstresult

    def __repr__(self):
        status = "%d results, %d meths" % (len(self.results), len(self.methods))
        return "<MultiCall %s, kwargs=%r>" %(status, self.kwargs)

    def execute(self):
        all_kwargs = self.kwargs
        while self.methods:
            method = self.methods.pop()
            args = [all_kwargs[argname] for argname in varnames(method)]
            if hasattr(method, "hookwrapper"):
                return wrapped_call(method(*args), self.execute)
            res = method(*args)
            if res is not None:
                self.results.append(res)
                if self.firstresult:
                    return res
        if not self.firstresult:
            return self.results


def varnames(func, startindex=None):
    """ return argument name tuple for a function, method, class or callable.

    In case of a class, its "__init__" method is considered.
    For methods the "self" parameter is not included unless you are passing
    an unbound method with Python3 (which has no supports for unbound methods)
    """
    cache = getattr(func, "__dict__", {})
    try:
        return cache["_varnames"]
    except KeyError:
        pass
    if inspect.isclass(func):
        try:
            func = func.__init__
        except AttributeError:
            return ()
        startindex = 1
    else:
        if not inspect.isfunction(func) and not inspect.ismethod(func):
            func = getattr(func, '__call__', func)
        if startindex is None:
            startindex = int(inspect.ismethod(func))

    rawcode = py.code.getrawcode(func)
    try:
        x = rawcode.co_varnames[startindex:rawcode.co_argcount]
    except AttributeError:
        x = ()
    else:
        defaults = func.__defaults__
        if defaults:
            x = x[:-len(defaults)]
    try:
        cache["_varnames"] = x
    except TypeError:
        pass
    return x


class HookRelay:
    def __init__(self, pm):
        self._pm = pm
        self.trace = pm.trace.root.get("hook")


class HookCaller:
    def __init__(self, hookrelay, name, firstresult, argnames, methods=()):
        self.hookrelay = hookrelay
        self.name = name
        self.firstresult = firstresult
        self.argnames = ["__multicall__"]
        self.argnames.extend(argnames)
        assert "self" not in argnames  # sanity check
        self.methods = methods

    def __repr__(self):
        return "<HookCaller %r>" %(self.name,)

    def scan_methods(self):
        self.methods = self.hookrelay._pm.listattr(self.name)

    def __call__(self, **kwargs):
        return self._docall(self.methods, kwargs)

    def callextra(self, methods, **kwargs):
        return self._docall(self.methods + methods, kwargs)

    def _docall(self, methods, kwargs):
        return MultiCall(methods, kwargs,
                         firstresult=self.firstresult).execute()


class PluginValidationError(Exception):
    """ plugin failed validation. """


def formatdef(func):
    return "%s%s" % (
        func.__name__,
        inspect.formatargspec(*inspect.getargspec(func))
    )
