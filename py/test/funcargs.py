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
    if function._args:
        # functions yielded from a generator: we don't want
        # to support that because we want to go here anyway: 
        # http://bitbucket.org/hpk42/py-trunk/issue/2/next-generation-generative-tests
        pass
    else:
        # standard Python Test function/method case  
        for argname in getfuncargnames(function.obj):
            if argname not in function.funcargs:
                request = FuncargRequest(pyfuncitem=function, argname=argname) 
                try:
                    function.funcargs[argname] = request.call_next_provider()
                except request.Error:
                    request._raiselookupfailed()

class RunSpecs:
    def __init__(self, function, config=None, cls=None, module=None):
        self.config = config
        self.module = module 
        self.function = function
        self.funcargnames = getfuncargnames(function)
        self.cls = cls
        self.module = module
        self._combinations = []

    def addfuncarg(self, argname, value):
        if argname not in self.funcargnames:
            raise ValueError("function %r has no funcarg %r" %(
                    self.function, argname))
        newcombi = []
        if not self._combinations:
            newcombi.append({argname:value})
        else:
            for combi in self._combinations:
                if argname in combi:
                    combi = combi.copy()
                    newcombi.append(combi)
                combi[argname] = value 
        self._combinations.extend(newcombi)

class FunctionCollector(py.test.collect.Collector):
    def __init__(self, name, parent, combinations):
        super(FunctionCollector, self).__init__(name, parent)
        self.combinations = combinations
        self.obj = getattr(self.parent.obj, name) 
       
    def collect(self):
        l = []
        for i, funcargs in py.builtin.enumerate(self.combinations):
            function = self.parent.Function(name="%s[%s]" %(self.name, i),
                parent=self, funcargs=funcargs, callobj=self.obj)
            l.append(function)
        return l 

class FuncargRequest:
    _argprefix = "pytest_funcarg__"

    class Error(LookupError):
        """ error on performing funcarg request. """ 
        
    def __init__(self, pyfuncitem, argname):
        self._pyfuncitem = pyfuncitem
        self.argname = argname 
        self.function = pyfuncitem.obj
        self.module = pyfuncitem.getmodulecollector().obj 
        self.cls = getattr(self.function, 'im_class', None)
        self.config = pyfuncitem.config
        self.fspath = pyfuncitem.fspath
        self._plugins = self.config.pluginmanager.getplugins()
        self._plugins.append(pyfuncitem.getmodulecollector().obj)
        self._provider = self.config.pluginmanager.listattr(
            plugins=self._plugins, 
            attrname=self._argprefix + str(argname)
        )

    def __repr__(self):
        return "<FuncargRequest %r for %r>" %(self.argname, self._pyfuncitem)

    def call_next_provider(self):
        if not self._provider:
            raise self.Error("no provider methods left")
        next_provider = self._provider.pop()
        return next_provider(request=self)

    def addfinalizer(self, finalizer):
        self._pyfuncitem.addfinalizer(finalizer)

    def _raiselookupfailed(self):
        available = []
        for plugin in self._plugins:
            for name in vars(plugin.__class__):
                if name.startswith(self._argprefix):
                    name = name[len(self._argprefix):]
                    if name not in available:
                        available.append(name) 
        fspath, lineno, msg = self._pyfuncitem.metainfo()
        line = "%s:%s" %(fspath, lineno)
        msg = "funcargument %r not found for: %s" %(self.argname, line)
        msg += "\n available funcargs: %s" %(", ".join(available),)
        raise LookupError(msg)


        
