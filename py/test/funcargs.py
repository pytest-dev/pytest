import py

def getfuncargnames(function):
    argnames = py.std.inspect.getargs(function.func_code)[0]
    startindex = hasattr(function, 'im_self') and 1 or 0 
    numdefaults = len(function.func_defaults or ()) 
    if numdefaults:
        return argnames[startindex:-numdefaults]
    return argnames[startindex:]
    
def fillfuncargs(function):
    """ fill missing funcargs. """ 
    request = FuncargRequest(pyfuncitem=function)
    request._fillfuncargs()


_notexists = object()
class CallSpec:
    def __init__(self, funcargs, id, param):
        self.funcargs = funcargs 
        self.id = id
        if param is not _notexists:
            self.param = param 

class Metafunc:
    def __init__(self, function, config=None, cls=None, module=None):
        self.config = config
        self.module = module 
        self.function = function
        self.funcargnames = getfuncargnames(function)
        self.cls = cls
        self.module = module
        self._calls = []
        self._ids = py.builtin.set()

    def addcall(self, funcargs=None, id=_notexists, param=_notexists):
        assert funcargs is None or isinstance(funcargs, dict)
        if id is None:
            raise ValueError("id=None not allowed") 
        if id is _notexists:
            id = len(self._calls)
        id = str(id)
        if id in self._ids:
            raise ValueError("duplicate id %r" % id)
        self._ids.add(id)
        self._calls.append(CallSpec(funcargs, id, param))

class FunctionCollector(py.test.collect.Collector):
    def __init__(self, name, parent, calls):
        super(FunctionCollector, self).__init__(name, parent)
        self.calls = calls 
        self.obj = getattr(self.parent.obj, name) 
       
    def collect(self):
        l = []
        for callspec in self.calls:
            name = "%s[%s]" %(self.name, callspec.id)
            function = self.parent.Function(name=name, parent=self, 
                callspec=callspec, callobj=self.obj)
            l.append(function)
        return l

    def reportinfo(self):
        try:
            return self._fslineno, self.name
        except AttributeError:
            pass        
        fspath, lineno = py.code.getfslineno(self.obj)
        self._fslineno = fspath, lineno
        return fspath, lineno, self.name
    

class FuncargRequest:
    _argprefix = "pytest_funcarg__"
    _argname = None

    class Error(LookupError):
        """ error on performing funcarg request. """ 

    def __init__(self, pyfuncitem):
        self._pyfuncitem = pyfuncitem
        self.function = pyfuncitem.obj
        self.module = pyfuncitem.getparent(py.test.collect.Module).obj
        self.cls = getattr(self.function, 'im_class', None)
        self.instance = getattr(self.function, 'im_self', None)
        self.config = pyfuncitem.config
        self.fspath = pyfuncitem.fspath
        if hasattr(pyfuncitem, '_requestparam'):
            self.param = pyfuncitem._requestparam 
        self._plugins = self.config.pluginmanager.getplugins()
        self._plugins.append(self.module)
        if self.instance is not None:
            self._plugins.append(self.instance)
        self._funcargs  = self._pyfuncitem.funcargs.copy()
        self._provider = {}

    def _fillfuncargs(self):
        argnames = getfuncargnames(self.function)
        if argnames:
            assert not getattr(self._pyfuncitem, '_args', None), "yielded functions cannot have funcargs" 
        for argname in argnames:
            if argname not in self._pyfuncitem.funcargs:
                self._pyfuncitem.funcargs[argname] = self.getfuncargvalue(argname)

    def cached_setup(self, setup, teardown=None, scope="module", extrakey=None):
        if not hasattr(self.config, '_setupcache'):
            self.config._setupcache = {} # XXX weakref? 
        cachekey = (self._getscopeitem(scope), extrakey)
        cache = self.config._setupcache
        try:
            val = cache[cachekey]
        except KeyError:
            val = setup()
            cache[cachekey] = val 
            if teardown is not None:
                self.addfinalizer(lambda: teardown(val), scope=scope)
        return val 

    def getfuncargvalue(self, argname):
        try:
            return self._funcargs[argname]
        except KeyError:
            pass
        if argname not in self._provider:
            self._provider[argname] = self.config.pluginmanager.listattr(
                    plugins=self._plugins, 
                    attrname=self._argprefix + str(argname)
            )
        #else: we are called recursively  
        if not self._provider[argname]:
            self._raiselookupfailed(argname)
        funcargprovider = self._provider[argname].pop()
        self._funcargs[argname] = res = funcargprovider(request=self)
        return res

    def _getscopeitem(self, scope):
        if scope == "function":
            return self._pyfuncitem
        elif scope == "module":
            return self._pyfuncitem.getparent(py.test.collect.Module)
        elif scope == "session":
            return None
        raise ValueError("unknown finalization scope %r" %(scope,))

    def addfinalizer(self, finalizer, scope="function"):
        colitem = self._getscopeitem(scope)
        self.config._setupstate.addfinalizer(finalizer=finalizer, colitem=colitem)

    def __repr__(self):
        return "<FuncargRequest for %r>" %(self._pyfuncitem)

    def _raiselookupfailed(self, argname):
        available = []
        for plugin in self._plugins:
            for name in vars(plugin):
                if name.startswith(self._argprefix):
                    name = name[len(self._argprefix):]
                    if name not in available:
                        available.append(name) 
        fspath, lineno, msg = self._pyfuncitem.reportinfo()
        line = "%s:%s" %(fspath, lineno)
        msg = "funcargument %r not found for: %s" %(argname, line)
        msg += "\n available funcargs: %s" %(", ".join(available),)
        raise LookupError(msg)


        
