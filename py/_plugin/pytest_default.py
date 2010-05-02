""" default hooks and general py.test options. """ 

import sys
import py

def pytest_pyfunc_call(__multicall__, pyfuncitem):
    if not __multicall__.execute():
        testfunction = pyfuncitem.obj 
        if pyfuncitem._isyieldedfunction():
            testfunction(*pyfuncitem._args)
        else:
            funcargs = pyfuncitem.funcargs
            testfunction(**funcargs)

def pytest_collect_file(path, parent):
    ext = path.ext 
    pb = path.purebasename
    if pb.startswith("test_") or pb.endswith("_test") or \
       path in parent.config._argfspaths:
        if ext == ".py":
            return parent.ihook.pytest_pycollect_makemodule(
                path=path, parent=parent)

def pytest_pycollect_makemodule(path, parent):
    return parent.Module(path, parent)

def pytest_funcarg__pytestconfig(request):
    """ the pytest config object with access to command line opts."""
    return request.config

def pytest_ignore_collect(path, config):
    ignore_paths = config.getconftest_pathlist("collect_ignore", path=path) 
    ignore_paths = ignore_paths or []
    excludeopt = config.getvalue("ignore")
    if excludeopt:
        ignore_paths.extend([py.path.local(x) for x in excludeopt])
    return path in ignore_paths
    # XXX more refined would be: 
    if ignore_paths:
        for p in ignore_paths:
            if path == p or path.relto(p):
                return True


def pytest_collect_directory(path, parent):
    # XXX reconsider the following comment 
    # not use parent.Directory here as we generally 
    # want dir/conftest.py to be able to 
    # define Directory(dir) already 
    if not parent.recfilter(path): # by default special ".cvs", ... 
        # check if cmdline specified this dir or a subdir directly
        for arg in parent.config._argfspaths:
            if path == arg or arg.relto(path):
                break
        else:
            return 
    Directory = parent.config._getcollectclass('Directory', path) 
    return Directory(path, parent=parent)

def pytest_report_iteminfo(item):
    return item.reportinfo()

def pytest_addoption(parser):
    group = parser.getgroup("general", "running and selection options")
    group._addoption('-x', '--exitfirst',
               action="store_true", dest="exitfirst", default=False,
               help="exit instantly on first error or failed test."),
    group._addoption('-k',
        action="store", dest="keyword", default='',
        help="only run test items matching the given "
             "space separated keywords.  precede a keyword with '-' to negate. "
             "Terminate the expression with ':' to treat a match as a signal "
             "to run all subsequent tests. ")

    group = parser.getgroup("collect", "collection")
    group.addoption('--collectonly',
        action="store_true", dest="collectonly",
        help="only collect tests, don't execute them."),
    group.addoption("--ignore", action="append", metavar="path", 
        help="ignore path during collection (multi-allowed).")
    group.addoption('--confcutdir', dest="confcutdir", default=None, 
        metavar="dir",
        help="only load conftest.py's relative to specified dir.")

    group = parser.getgroup("debugconfig", 
        "test process debugging and configuration")
    group.addoption('--basetemp', dest="basetemp", default=None, metavar="dir",
               help="base temporary directory for this test run.")

def pytest_configure(config):
    setsession(config)

def setsession(config):
    val = config.getvalue
    if val("collectonly"):
        from py._test.session import Session
        config.setsessionclass(Session)
      
# pycollect related hooks and code, should move to pytest_pycollect.py
 
def pytest_pycollect_makeitem(__multicall__, collector, name, obj):
    res = __multicall__.execute()
    if res is not None:
        return res
    if collector._istestclasscandidate(name, obj):
        res = collector._deprecated_join(name)
        if res is not None:
            return res 
        return collector.Class(name, parent=collector)
    elif collector.funcnamefilter(name) and hasattr(obj, '__call__'):
        res = collector._deprecated_join(name)
        if res is not None:
            return res 
        if is_generator(obj):
            # XXX deprecation warning 
            return collector.Generator(name, parent=collector)
        else:
            return collector._genfunctions(name, obj) 

def is_generator(func):
    try:
        return py.code.getrawcode(func).co_flags & 32 # generator function 
    except AttributeError: # builtin functions have no bytecode
        # assume them to not be generators
        return False 
