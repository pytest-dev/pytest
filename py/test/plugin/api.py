"""
API definitions for pytest plugin hooks and events
"""

class PluginHooks:
    # ------------------------------------------------------------------------------
    # Command line and configuration hooks 
    # ------------------------------------------------------------------------------
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


    # ------------------------------------------------------------------------------
    # collection hooks
    # ------------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------------
    # runtest related hooks 
    # ------------------------------------------------------------------------------

    def pytest_pyfunc_call(self, pyfuncitem, args, kwargs):
        """ return True if we consumed/did the call to the python function item. """

    def pytest_item_makereport(self, item, excinfo, when, outerr):
        """ return ItemTestReport event for the given test outcome. """

    # reporting hooks (invoked from pytest_terminal.py) 
    def pytest_report_teststatus(self, event):
        """ return shortletter and verbose word. """

    def pytest_terminal_summary(self, terminalreporter):
        """ add additional section in terminal summary reporting. """

class Events:
    # Events 
    def pyevent(self, eventname, args, kwargs):
        """ generically called for each notification event. """

    def pyevent__gateway_init(self, gateway):
        """ called after a gateway has been initialized. """

    def pyevent__gateway_exit(self, gateway):
        """ called when gateway is being exited. """

    def pyevent__gwmanage_rsyncstart(self, source, gateways):
        """ called before rsyncing a directory to remote gateways takes place. """

    def pyevent__gwmanage_rsyncfinish(self, source, gateways):
        """ called after rsyncing a directory to remote gateways takes place. """

    def pyevent__trace(self, category, msg):
        """ called for tracing events. """

    def pyevent__internalerror(self, excrepr):
        """ called for internal errors. """

    def pyevent__itemstart(self, item, node=None):
        """ test item gets collected. """

    def pyevent__itemtestreport(self, event):
        """ test has been run. """

    def pyevent__deselected(self, event):
        """ item has been dselected. """

    def pyevent__collectionstart(self, event):
        """ collector starts collecting. """

    def pyevent__collectionreport(self, event):
        """ collector finished collecting. """

    def pyevent__testrunstart(self):
        """ whole test run starts. """

    def pyevent__testrunfinish(self, exitstatus, excrepr=None):
        """ whole test run finishes. """

    def pyevent__gwmanage_newgateway(self, gateway):
        """ execnet gateway manager has instantiated a gateway. 
            The gateway will have an 'id' attribute that is unique 
            within the gateway manager context. 
        """
    def pyevent__testnodeready(self, node):
        """ Test Node is ready to operate. """

    def pyevent__testnodedown(self, node, error):
        """ Test Node is down. """

    def pyevent__rescheduleitems(self, event):
        """ reschedule Items from a node that went down. """

    def pyevent__looponfailinfo(self, event):
        """ info for repeating failing tests. """

    def pyevent__plugin_registered(self, plugin):
        """ a new py lib plugin got registered. """
        
   
