"""
plugin with support classes and functions for testing pytest functionality 
"""
import py

class PlugintesterPlugin:
    """ test support code for testing pytest plugins. """
    def pytest_pyfuncarg_plugintester(self, pyfuncitem):
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
        #     FSTester = self.pyfuncitem._config.pytestplugins.getpluginattr("pytester", "FSTester")
        from pytest_pytester import TmpTestdir
        crunner = TmpTestdir(self.pyfuncitem)
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
        hooks = collectattr(PytestPluginHooks)
        getargs = py.std.inspect.getargs

        def isgenerichook(name):
            return name.startswith("pytest_pyfuncarg_")

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

def collectattr(obj, prefixes=("pytest_", "pyevent_")):
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


class PytestPluginHooks:
    def __init__(self):
        """ usually called only once per test process. """ 

    def pytest_addoption(self, parser):
        """ called before commandline parsing.  """

    def pytest_configure(self, config):
        """ called after command line options have been parsed. 
            and all plugins and initial conftest files been loaded. 
            ``config`` provides access to all such configuration values. 
        """
    def pytest_unconfigure(self, config):
        """ called before test process is exited. 
        """

    def pytest_event(self, event):
        """ called for each internal py.test event.  """

    #def pytest_pyfuncarg_NAME(self, pyfuncitem, argname):
    #    """ provide (value, finalizer) for an open test function argument. 
    #
    #            the finalizer (if not None) will be called after the test 
    #            function has been executed (i.e. pyfuncitem.execute() returns). 
    #    """ 

    def pytest_pyfunc_call(self, pyfuncitem, args, kwargs):
        """ return True if we consumed/did the call to the python function item. """

    # collection hooks
    def pytest_collect_file(self, path, parent):
        """ return Collection node or None. """

    def pytest_collect_recurse(self, path, parent):
        """ return True/False to cause/prevent recursion into given directory. 
            return None if you do not want to make the decision. 
        """ 

    def pytest_collect_directory(self, path, parent):
        """ return Collection node or None. """

    def pytest_pymodule_makeitem(self, modcol, name, obj):
        """ return custom item/collector for a python object in a module, or None.  """

    # from pytest_terminal plugin
    def pytest_report_teststatus(self, event):
        """ return shortletter and verbose word. """

    def pytest_terminal_summary(self, terminalreporter):
        """ add additional section in terminal summary reporting. """

    # events
    def pyevent(self, eventname, *args, **kwargs):
        """ called for each testing event. """

    def pyevent_internalerror(self, event):
        """ called for internal errors. """

    def pyevent_itemstart(self, event):
        """ test item gets collected. """

    def pyevent_itemtestreport(self, event):
        """ test has been run. """

    def pyevent_deselected(self, event):
        """ item has been dselected. """

    def pyevent_collectionstart(self, event):
        """ collector starts collecting. """

    def pyevent_collectionreport(self, event):
        """ collector finished collecting. """

    def pyevent_testrunstart(self, event):
        """ whole test run starts. """

    def pyevent_testrunfinish(self, event):
        """ whole test run starts. """

    def pyevent_hostup(self, event):
        """ Host is up. """

    def pyevent_hostgatewayready(self, event):
        """ Connection to Host is ready. """

    def pyevent_hostdown(self, event):
        """ Host is down. """

    def pyevent_rescheduleitems(self, event):
        """ Items from a host that went down. """

    def pyevent_looponfailinginfo(self, event):
        """ info for repeating failing tests. """

    def pyevent_plugin_registered(self, plugin):
        """ a new py lib plugin got registered. """
        
   
# ===============================================================================
# plugin tests 
# ===============================================================================

def test_generic(plugintester):
    plugintester.apicheck(PlugintesterPlugin)
