"""
plugin with support classes and functions for testing pytest functionality 
"""
import py
from py.__.test.plugin import api

def pytest_funcarg__plugintester(request):
    return PluginTester(request) 

class PluginTester:
    def __init__(self, request):
        self.request = request

    def testdir(self, globs=None):
        from pytest_pytester import TmpTestdir
        testdir = TmpTestdir(self.request)
        self.request.addfinalizer(testdir.finalize)
        if globs is None:
            globs = py.std.sys._getframe(-1).f_globals
        testdir.plugins.append(globs) 
        # 
        #for colitem in self.request.listchain():
        #    if isinstance(colitem, py.test.collect.Module) and \
        #       colitem.name.startswith("pytest_"):
        #            crunner.plugins.append(colitem.fspath.purebasename)
        #            break 
        return testdir 

    def hookcheck(self, name=None, cls=None): 
        if cls is None:
            if name is None: 
                name = py.std.sys._getframe(-1).f_globals['__name__']
            plugin = __import__(name) 
        else:
            plugin = cls
        print "checking", plugin
        fail = False 
        pm = py.test._PluginManager()
        methods = collectattr(plugin)
        hooks = collectattr(api.PluginHooks)
        getargs = py.std.inspect.getargs

        def isgenerichook(name):
            return name.startswith("pytest_funcarg__")

        while methods:
            name, method = methods.popitem()
            if isgenerichook(name):
                continue
            if name not in hooks:
                print "found unknown hook: %s" % name 
                fail = True
            else:
                hook = hooks[name]
                if not hasattr(hook, 'func_code'):
                    continue # XXX do some checks on attributes as well? 
                method_args = getargs(method.func_code) 
                if '__call__' in method_args[0]:
                    method_args[0].remove('__call__')
                hookargs = getargs(hook.func_code)
                for arg, hookarg in zip(method_args[0], hookargs[0]):
                    if arg != hookarg: 
                        print "argument mismatch:" 
                        print "actual  : %s.%s" %(pluginclass.__name__, formatdef(method))
                        print "required:", formatdef(hook)
                        fail = True
                        break 
                if not fail:
                    print "matching hook:", formatdef(method)
        if fail:
            py.test.fail("Plugin API error")

def collectattr(obj, prefixes=("pytest_",)):
    methods = {}
    for apiname in vars(obj): 
        for prefix in prefixes:
            if apiname.startswith(prefix):
                methods[apiname] = getattr(obj, apiname) 
    return methods 

def formatdef(func):
    formatargspec = py.std.inspect.formatargspec
    getargspec = py.std.inspect.formatargspec
    return "%s%s" %(
        func.func_name, 
        py.std.inspect.formatargspec(*py.std.inspect.getargspec(func))
    )

# ===============================================================================
# plugin tests 
# ===============================================================================

def test_generic(plugintester):
    plugintester.hookcheck()
