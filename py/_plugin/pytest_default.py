""" default hooks and general py.test options. """

import sys
import py

def pytest_cmdline_main(config):
    from py._test.session import Session
    return Session(config).main()

def pytest_perform_collection(session):
    collection = session.collection
    assert not hasattr(collection, 'items')
    hook = session.config.hook
    collection.items = items = collection.perform_collect()
    hook.pytest_collection_modifyitems(config=session.config, items=items)
    hook.pytest_log_finishcollection(collection=collection)
    return True

def pytest_runtest_mainloop(session):
    if session.config.option.collectonly:
        return True
    for item in session.collection.items:
        item.config.hook.pytest_runtest_protocol(item=item)
        if session.shouldstop:
            raise session.Interrupted(session.shouldstop)
    return True

def pytest_ignore_collect(path, config):
    p = path.dirpath()
    ignore_paths = config.getconftest_pathlist("collect_ignore", path=p)
    ignore_paths = ignore_paths or []
    excludeopt = config.getvalue("ignore")
    if excludeopt:
        ignore_paths.extend([py.path.local(x) for x in excludeopt])
    return path in ignore_paths

def pytest_collect_directory(path, parent):
    if not parent.recfilter(path): # by default special ".cvs", ...
        # check if cmdline specified this dir or a subdir directly
        for arg in parent.collection._argfspaths:
            if path == arg or arg.relto(path):
                break
        else:
            return
    return parent.Directory(path, parent=parent)

def pytest_report_iteminfo(item):
    return item.reportinfo()

def pytest_addoption(parser):
    group = parser.getgroup("general", "running and selection options")
    group._addoption('-x', '--exitfirst', action="store_true", default=False,
               dest="exitfirst",
               help="exit instantly on first error or failed test."),
    group._addoption('--maxfail', metavar="num",
               action="store", type="int", dest="maxfail", default=0,
               help="exit after first num failures or errors.")

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
    # compat
    if config.getvalue("exitfirst"):
        config.option.maxfail = 1

