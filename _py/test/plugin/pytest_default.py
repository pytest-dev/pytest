""" default hooks and general py.test options. """ 

import sys
import py

try:
    import execnet
except ImportError:
    execnet = None

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
       path in parent.config.args:
        if ext == ".py":
            return parent.Module(path, parent=parent) 

def pytest_collect_directory(path, parent):
    # XXX reconsider the following comment 
    # not use parent.Directory here as we generally 
    # want dir/conftest.py to be able to 
    # define Directory(dir) already 
    if not parent.recfilter(path): # by default special ".cvs", ... 
        # check if cmdline specified this dir or a subdir directly
        for arg in parent.config.args:
            if path == arg or arg.relto(path):
                break
        else:
            return 
    Directory = parent.config.getvalue('Directory', path) 
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
    group._addoption('-p', action="append", dest="plugins", default = [],
               help=("load the specified plugin after command line parsing. "))
    if execnet:
        group._addoption('-f', '--looponfail',
                   action="store_true", dest="looponfail", default=False,
                   help="run tests, re-run failing test set until all pass.")

    group = parser.getgroup("debugconfig", 
        "test process debugging and configuration")
    group.addoption('--basetemp', dest="basetemp", default=None, metavar="dir",
               help="base temporary directory for this test run.")

    if execnet:
        add_dist_options(parser)
    else:
        parser.epilog = (
        "execnet missing: --looponfailing and distributed testing not available.")

def add_dist_options(parser):
    #  see http://pytest.org/help/dist")
    group = parser.getgroup("dist", "distributed testing") 
    group._addoption('--dist', metavar="distmode", 
               action="store", choices=['load', 'each', 'no'], 
               type="choice", dest="dist", default="no", 
               help=("set mode for distributing tests to exec environments.\n\n"
                     "each: send each test to each available environment.\n\n"
                     "load: send each test to available environment.\n\n"
                     "(default) no: run tests inprocess, don't distribute."))
    group._addoption('--tx', dest="tx", action="append", default=[], metavar="xspec",
               help=("add a test execution environment. some examples: "
                     "--tx popen//python=python2.5 --tx socket=192.168.1.102:8888 "
                     "--tx ssh=user@codespeak.net//chdir=testcache"))
    group._addoption('-d', 
               action="store_true", dest="distload", default=False,
               help="load-balance tests.  shortcut for '--dist=load'")
    group._addoption('-n', dest="numprocesses", metavar="numprocesses", 
               action="store", type="int", 
               help="shortcut for '--dist=load --tx=NUM*popen'")
    group.addoption('--rsyncdir', action="append", default=[], metavar="dir1", 
               help="add directory for rsyncing to remote tx nodes.")

def pytest_configure(config):
    fixoptions(config)
    setsession(config)

def fixoptions(config):
    if execnet:
        if config.option.numprocesses:
            config.option.dist = "load"
            config.option.tx = ['popen'] * int(config.option.numprocesses)
        if config.option.distload:
            config.option.dist = "load"

def setsession(config):
    val = config.getvalue
    if val("collectonly"):
        from _py.test.session import Session
        config.setsessionclass(Session)
    elif execnet:
        if val("looponfail"):
            from _py.test.looponfail.remote import LooponfailingSession
            config.setsessionclass(LooponfailingSession)
        elif val("dist") != "no":
            from _py.test.dist.dsession import  DSession
            config.setsessionclass(DSession)
      
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
