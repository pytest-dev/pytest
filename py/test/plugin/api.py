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
    pytest_pymodule_makeitem.firstresult = True

    def pytest_itemrun(self, item, pdb=None):
        """ run given test item and return test report. """ 

    def pytest_item_runtest_finished(self, item, excinfo, outerr):
        """ called in-process after runtest() returned. """ 
        

    # ------------------------------------------------------------------------------
    # runtest related hooks 
    # ------------------------------------------------------------------------------

    def pytest_pyfunc_call(self, pyfuncitem, args, kwargs):
        """ return True if we consumed/did the call to the python function item. """

    def pytest_item_makereport(self, item, excinfo, when, outerr):
        """ return ItemTestReport event for the given test outcome. """
    pytest_item_makereport.firstresult = True

    # reporting hooks (invoked from pytest_terminal.py) 
    def pytest_report_teststatus(self, rep):
        """ return shortletter and verbose word. """
    pytest_report_teststatus.firstresult = True

    def pytest_terminal_summary(self, terminalreporter):
        """ add additional section in terminal summary reporting. """

    # doctest hooks (invoked from pytest_terminal.py) 
    def pytest_doctest_prepare_content(self, content):
        """ return processed content for a given doctest"""
    pytest_doctest_prepare_content.firstresult = True

    def pytest_itemstart(self, item, node=None):
        """ test item gets collected. """

    def pytest_itemtestreport(self, rep):
        """ test has been run. """

    def pytest_item_runtest_finished(self, item, excinfo, outerr):
        """ test has been run. """

    def pytest_itemsetupreport(self, rep):
        """ a report on running a fixture function. """ 

    def pytest_collectstart(self, collector):
        """ collector starts collecting. """

    def pytest_collectreport(self, rep):
        """ collector finished collecting. """

    def pytest_plugin_registered(self, plugin):
        """ a new py lib plugin got registered. """

    def pytest_plugin_unregistered(self, plugin):
        """ a py lib plugin got unregistered. """

    def pytest_testnodeready(self, node):
        """ Test Node is ready to operate. """

    def pytest_testnodedown(self, node, error):
        """ Test Node is down. """

    def pytest_testrunstart(self):
        """ whole test run starts. """

    def pytest_testrunfinish(self, exitstatus, excrepr=None):
        """ whole test run finishes. """



class Events:
    # Events 
    def pyevent(self, eventname, args, kwargs):
        """ generically called for each notification event. """

    def pyevent__NOP(self, *args, **kwargs):
        """ the no-operation call. """ 

    def pyevent__trace(self, category, msg):
        """ called for tracing events. """

    def pyevent__internalerror(self, excrepr):
        """ called for internal errors. """

    def pyevent__deselected(self, items):
        """ collected items that were deselected (by keyword). """

    def pytest_rescheduleitems(self, items):
        """ reschedule Items from a node that went down. """

    def pyevent__looponfailinfo(self, failreports, rootdirs):
        """ info for repeating failing tests. """

   
