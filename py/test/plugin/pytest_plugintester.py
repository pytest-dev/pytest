"""
plugin with support classes and functions for testing pytest functionality 
"""
import py
from py.__.test.plugin import api

class PlugintesterPlugin:
    """ test support code for testing pytest plugins. """
    def pytest_funcarg__plugintester(self, pyfuncitem):
        pt = PluginTester(pyfuncitem) 
        pyfuncitem.addfinalizer(pt.finalize)
        return pt

class Support(object):
    def __init__(self, pyfuncitem):
        """ instantiated per function that requests it. """
        self.pyfuncitem = pyfuncitem

    def getmoditem(self):
        for colitem in self.pyfuncitem.listchain():
            if isinstance(colitem, colitem.Module):
                return colitem 

    def finalize(self):
        """ called after test function finished execution"""

class PluginTester(Support):
    def testdir(self):
        # XXX import differently, eg. 
        #     FSTester = self.pyfuncitem.config.pytestplugins.getpluginattr("pytester", "FSTester")
        from pytest_pytester import TmpTestdir
        crunner = TmpTestdir(self.pyfuncitem)
        self.pyfuncitem.addfinalizer(crunner.finalize)
        # 
        for colitem in self.pyfuncitem.listchain():
            if isinstance(colitem, py.test.collect.Module) and \
               colitem.name.startswith("pytest_"):
                    crunner.plugins.append(colitem.fspath.purebasename)
                    break 
        return crunner 

    def apicheck(self, pluginclass):
        print "loading and checking", pluginclass 
        fail = False 
        pm = py.test._PytestPlugins()
        methods = collectattr(pluginclass)
        hooks = collectattr(api.PluginHooks)
        hooks.update(collectattr(api.Events))
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

def collectattr(obj, prefixes=("pytest_", "pyevent__")):
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
    plugintester.apicheck(PlugintesterPlugin)
