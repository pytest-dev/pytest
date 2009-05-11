"""
API definitions for pytest plugin hooks 
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
    # test Session related hooks 
    # ------------------------------------------------------------------------------

    def pytest_testrunstart(self):
        """ whole test run starts. """

    def pytest_testrunfinish(self, exitstatus, excrepr=None):
        """ whole test run finishes. """

    def pytest_deselected(self, items):
        """ collected items that were deselected (by keyword). """



    # ------------------------------------------------------------------------------
    # collection hooks
    # ------------------------------------------------------------------------------
    def pytest_collect_file(self, path, parent):
        """ return Collection node or None. """

    def pytest_collect_recurse(self, path, parent):
        """ return True/False to cause/prevent recursion into given directory. 
            return None if you do not want to make the decision. 
        """ 
    pytest_collect_recurse.firstresult = True

    def pytest_collect_directory(self, path, parent):
        """ return Collection node or None. """

    def pytest_pycollect_obj(self, collector, name, obj):
        """ return custom item/collector for a python object in a module, or None.  """
    pytest_pycollect_obj.firstresult = True

    def pytest_genfunc(self, funcspec):
        """ generate (multiple) parametrized calls to a test function."""

    def pytest_collectstart(self, collector):
        """ collector starts collecting. """

    def pytest_collectreport(self, rep):
        """ collector finished collecting. """

    # ------------------------------------------------------------------------------
    # runtest related hooks 
    # ------------------------------------------------------------------------------
    #
    def pytest_itemrun(self, item, pdb=None):
        """ run given test item and return test report. """ 

    def pytest_pyfunc_call(self, pyfuncitem, args, kwargs):
        """ return True if we consumed/did the call to the python function item. """
    pytest_pyfunc_call.firstresult = True

    def pytest_item_makereport(self, item, excinfo, when, outerr):
        """ return ItemTestReport for the given test outcome. """
    pytest_item_makereport.firstresult = True

    def pytest_itemstart(self, item, node=None):
        """ test item gets collected. """

    def pytest_itemtestreport(self, rep):
        """ test has been run. """

    def pytest_item_runtest_finished(self, item, excinfo, outerr):
        """ test has been run. """

    def pytest_itemsetupreport(self, rep):
        """ a report on running a fixture function. """ 

    # ------------------------------------------------------------------------------
    # reporting hooks (invoked from pytest_terminal.py) 
    # ------------------------------------------------------------------------------
    def pytest_report_teststatus(self, rep):
        """ return shortletter and verbose word. """
    pytest_report_teststatus.firstresult = True

    def pytest_terminal_summary(self, terminalreporter):
        """ add additional section in terminal summary reporting. """

    # ------------------------------------------------------------------------------
    # doctest hooks 
    # ------------------------------------------------------------------------------
    def pytest_doctest_prepare_content(self, content):
        """ return processed content for a given doctest"""
    pytest_doctest_prepare_content.firstresult = True

    # ------------------------------------------------------------------------------
    # misc hooks 
    # ------------------------------------------------------------------------------

    def pytest_plugin_registered(self, plugin):
        """ a new py lib plugin got registered. """

    def pytest_plugin_unregistered(self, plugin):
        """ a py lib plugin got unregistered. """

    def pytest_internalerror(self, excrepr):
        """ called for internal errors. """

    def pytest_trace(self, category, msg):
        """ called for debug info. """ 
   


    # ------------------------------------------------------------------------------
    # distributed testing 
    # ------------------------------------------------------------------------------

    def pytest_testnodeready(self, node):
        """ Test Node is ready to operate. """

    def pytest_testnodedown(self, node, error):
        """ Test Node is down. """

    def pytest_rescheduleitems(self, items):
        """ reschedule Items from a node that went down. """

    def pytest_looponfailinfo(self, failreports, rootdirs):
        """ info for repeating failing tests. """

