"""
py.test hooks / extension points 
"""

# ------------------------------------------------------------------------------
# Command line and configuration hooks 
# ------------------------------------------------------------------------------
def pytest_addoption(parser):
    """ called before commandline parsing.  """

def pytest_configure(config):
    """ called after command line options have been parsed. 
        and all plugins and initial conftest files been loaded. 
        ``config`` provides access to all such configuration values. 
    """

def pytest_unconfigure(config):
    """ called before test process is exited. 
    """

# ------------------------------------------------------------------------------
# test Session related hooks 
# ------------------------------------------------------------------------------

def pytest_sessionstart(session):
    """ before session.main() is called. """

def pytest_sessionfinish(session, exitstatus, excrepr=None):
    """ whole test run finishes. """

def pytest_deselected(items):
    """ collected items that were deselected (by keyword). """

# ------------------------------------------------------------------------------
# collection hooks
# ------------------------------------------------------------------------------


def pytest_collect_file(path, parent):
    """ return Collection node or None. """

def pytest_collect_recurse(path, parent):
    """ return True/False to cause/prevent recursion into given directory. 
        return None if you do not want to make the decision. 
    """ 
pytest_collect_recurse.firstresult = True

def pytest_collect_directory(path, parent):
    """ return Collection node or None. """

def pytest_collectstart(collector):
    """ collector starts collecting. """

def pytest_collectreport(rep):
    """ collector finished collecting. """

def pytest_make_collect_report(collector):
    """ perform a collection and return a collection. """ 
pytest_make_collect_report.firstresult = True

# XXX rename to item_collected()?  meaning in distribution context? 
def pytest_itemstart(item, node=None):
    """ test item gets collected. """

# ------------------------------------------------------------------------------
# Python test function related hooks 
# ------------------------------------------------------------------------------

def pytest_pycollect_makeitem(collector, name, obj):
    """ return custom item/collector for a python object in a module, or None.  """
pytest_pycollect_makeitem.firstresult = True

def pytest_pyfunc_call(pyfuncitem):
    """ perform function call with the given function arguments. """ 
pytest_pyfunc_call.firstresult = True

def pytest_generate_tests(metafunc):
    """ generate (multiple) parametrized calls to a test function."""

# ------------------------------------------------------------------------------
# generic runtest related hooks 
# ------------------------------------------------------------------------------
def pytest_runtest_setup(item):
    """ called before pytest_runtest_call(). """ 

def pytest_runtest_call(item):
    """ execute test item. """ 

def pytest_runtest_teardown(item):
    """ called after pytest_runtest_call(). """ 

def pytest_runtest_protocol(item):
    """ run given test item and return test report. """ 
pytest_runtest_protocol.firstresult = True

def pytest_runtest_makereport(item, call):
    """ make ItemTestReport for the specified test outcome. """
pytest_runtest_makereport.firstresult = True

def pytest_runtest_logreport(rep):
    """ process item test report. """ 

# ------------------------------------------------------------------------------
# generic reporting hooks (invoked from pytest_terminal.py) 
# ------------------------------------------------------------------------------
def pytest_report_teststatus(rep):
    """ return shortletter and verbose word. """
pytest_report_teststatus.firstresult = True

def pytest_terminal_summary(terminalreporter):
    """ add additional section in terminal summary reporting. """

def pytest_report_iteminfo(item):
    """ return (fspath, lineno, name) for the item.
        the information is used for result display and to sort tests
    """
pytest_report_iteminfo.firstresult = True

# ------------------------------------------------------------------------------
# doctest hooks 
# ------------------------------------------------------------------------------
def pytest_doctest_prepare_content(content):
    """ return processed content for a given doctest"""
pytest_doctest_prepare_content.firstresult = True


# ------------------------------------------------------------------------------
# misc hooks 
# ------------------------------------------------------------------------------

def pytest_plugin_registered(plugin):
    """ a new py lib plugin got registered. """

def pytest_plugin_unregistered(plugin):
    """ a py lib plugin got unregistered. """

def pytest_internalerror(excrepr):
    """ called for internal errors. """

def pytest_trace(category, msg):
    """ called for debug info. """ 

# ------------------------------------------------------------------------------
# distributed testing 
# ------------------------------------------------------------------------------

def pytest_testnodeready(node):
    """ Test Node is ready to operate. """

def pytest_testnodedown(node, error):
    """ Test Node is down. """

def pytest_rescheduleitems(items):
    """ reschedule Items from a node that went down. """

def pytest_looponfailinfo(failreports, rootdirs):
    """ info for repeating failing tests. """

