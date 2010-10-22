""" basic test session implementation.

* drives collection of tests
* triggers executions of tests
"""

import py
import pytest
import os, sys

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

def pytest_namespace():
    return dict(collect=dict(Item=Item, Collector=Collector,
        File=File, Directory=Directory))
        
def pytest_configure(config):
    py.test.config = config # compatibiltiy
    if config.getvalue("exitfirst"):
        config.option.maxfail = 1

def pytest_cmdline_main(config):
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
    return Directory(path, parent=parent)

def pytest_report_iteminfo(item):
    return item.reportinfo()


# exitcodes for the command line
EXIT_OK = 0
EXIT_TESTSFAILED = 1
EXIT_INTERRUPTED = 2
EXIT_INTERNALERROR = 3
EXIT_NOHOSTS = 4

class Session(object):
    nodeid = ""
    class Interrupted(KeyboardInterrupt):
        """ signals an interrupted test run. """
        __module__ = 'builtins' # for py3

    def __init__(self, config):
        self.config = config
        self.config.pluginmanager.register(self, name="session", prepend=True)
        self._testsfailed = 0
        self.shouldstop = False
        self.collection = Collection(config) # XXX move elswehre

    def pytest_runtest_logreport(self, report):
        if report.failed and 'xfail' not in getattr(report, 'keywords', []):
            self._testsfailed += 1
            maxfail = self.config.getvalue("maxfail")
            if maxfail and self._testsfailed >= maxfail:
                self.shouldstop = "stopping after %d failures" % (
                    self._testsfailed)
                self.collection.shouldstop = self.shouldstop
    pytest_collectreport = pytest_runtest_logreport

    def main(self):
        """ main loop for running tests. """
        self.shouldstop = False
        self.exitstatus = EXIT_OK
        config = self.config
        try:
            config.pluginmanager.do_configure(config)
            config.hook.pytest_sessionstart(session=self)
            config.hook.pytest_perform_collection(session=self)
            config.hook.pytest_runtest_mainloop(session=self)
        except self.config.Error:
            raise
        except KeyboardInterrupt:
            excinfo = py.code.ExceptionInfo()
            self.config.hook.pytest_keyboard_interrupt(excinfo=excinfo)
            self.exitstatus = EXIT_INTERRUPTED
        except:
            excinfo = py.code.ExceptionInfo()
            self.config.pluginmanager.notify_exception(excinfo)
            self.exitstatus = EXIT_INTERNALERROR
            if excinfo.errisinstance(SystemExit):
                sys.stderr.write("mainloop: caught Spurious SystemExit!\n")

        if not self.exitstatus and self._testsfailed:
            self.exitstatus = EXIT_TESTSFAILED
        self.config.hook.pytest_sessionfinish(
            session=self, exitstatus=self.exitstatus,
        )
        config.pluginmanager.do_unconfigure(config)
        return self.exitstatus

class Collection:
    def __init__(self, config):
        self.config = config
        self.topdir = gettopdir(self.config.args)
        self._argfspaths = [py.path.local(decodearg(x)[0])
                                     for x in self.config.args]
        x = pytest.collect.Directory(fspath=self.topdir,
            config=config, collection=self)
        self._topcollector = x.consider_dir(self.topdir)
        self._topcollector.parent = None

    def _normalizearg(self, arg):
        return "::".join(self._parsearg(arg))

    def _parsearg(self, arg, base=None):
        """ return normalized name list for a command line specified id
        which might be of the form x/y/z::name1::name2
        and should result into the form x::y::z::name1::name2
        """
        if base is None:
            base = py.path.local()
        parts = str(arg).split("::")
        path = base.join(parts[0], abs=True)
        if not path.check():
            raise self.config.Error("file not found: %s" %(path,))
        topdir = self.topdir
        if path != topdir and not path.relto(topdir):
            raise self.config.Error("path %r is not relative to %r" %
                (str(path), str(topdir)))
        topparts = path.relto(topdir).split(path.sep)
        return topparts + parts[1:]

    def getid(self, node):
        """ return id for node, relative to topdir. """
        path = node.fspath
        chain = [x for x in node.listchain() if x.fspath == path]
        chain = chain[1:]
        names = [x.name for x in chain if x.name != "()"]
        relpath = path.relto(self.topdir)
        if not relpath:
            assert path == self.topdir
            path = ''
        else:
            path = relpath
            if os.sep != "/":
                path = str(path).replace(os.sep, "/")
        names.insert(0, path)
        return "::".join(names)

    def getbyid(self, id):
        """ return one or more nodes matching the id. """
        names = [x for x in id.split("::") if x]
        if names and '/' in names[0]:
            names[:1] = names[0].split("/")
        return self._match([self._topcollector], names)

    def _match(self, matching, names):
        while names:
            name = names.pop(0)
            l = []
            for current in matching:
                for x in current._memocollect():
                    if x.name == name:
                        l.append(x)
                    elif x.name == "()":
                        names.insert(0, name)
                        l.append(x)
                        break
            if not l:
                raise ValueError("no node named %r below %r" %(name, current))
            matching = l
        return matching

    def perform_collect(self):
        nodes = []
        for arg in self.config.args:
            names = self._parsearg(arg)
            try:
                self.genitems([self._topcollector], names, nodes)
            except NoMatch:
                raise self.config.Error("can't collect: %s" % (arg,))
        return nodes

    def genitems(self, matching, names, result):
        if not matching:
            assert not names
            return
        if names:
            name = names[0]
            names = names[1:]
        else:
            name = None
        for node in matching:
            if isinstance(node, pytest.collect.Item):
                if name is None:
                    node.ihook.pytest_log_itemcollect(item=node)
                    result.append(node)
                continue
            assert isinstance(node, pytest.collect.Collector)
            node.ihook.pytest_collectstart(collector=node)
            rep = node.ihook.pytest_make_collect_report(collector=node)
            #print "matching", rep.result, "against name", name
            if rep.passed:
                if not name:
                    self.genitems(rep.result, [], result)
                else:
                    matched = False
                    for x in rep.result:
                        try:
                            if x.name == name or x.fspath.basename == name:
                                self.genitems([x], names, result)
                                matched = True
                            elif x.name == "()": # XXX special Instance() case
                                self.genitems([x], [name] + names, result)
                                matched = True
                        except NoMatch:
                            pass
                    if not matched:
                        node.ihook.pytest_collectreport(report=rep)
                        raise NoMatch(name)
            node.ihook.pytest_collectreport(report=rep)
            x = getattr(self, 'shouldstop', None)
            if x:
                raise Session.Interrupted(x)

class NoMatch(Exception):
    """ raised if genitems cannot locate a matching names. """

def gettopdir(args):
    """ return the top directory for the given paths.
        if the common base dir resides in a python package
        parent directory of the root package is returned.
    """
    fsargs = [py.path.local(decodearg(arg)[0]) for arg in args]
    p = fsargs and fsargs[0] or None
    for x in fsargs[1:]:
        p = p.common(x)
    assert p, "cannot determine common basedir of %s" %(fsargs,)
    pkgdir = p.pypkgpath()
    if pkgdir is None:
        if p.check(file=1):
            p = p.dirpath()
        return p
    else:
        return pkgdir.dirpath()

def decodearg(arg):
    arg = str(arg)
    return arg.split("::")

class HookProxy:
    def __init__(self, node):
        self.node = node
    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError(name)
        hookmethod = getattr(self.node.config.hook, name)
        def call_matching_hooks(**kwargs):
            plugins = self.node.config._getmatchingplugins(self.node.fspath)
            return hookmethod.pcall(plugins, **kwargs)
        return call_matching_hooks

class Node(object):
    """ base class for all Nodes in the collection tree.
    Collector subclasses have children, Items are terminal nodes."""

    def __init__(self, name, parent=None, config=None, collection=None):
        #: a unique name with the scope of the parent
        self.name = name

        #: the parent collector node.
        self.parent = parent
        
        #: the test config object
        self.config = config or parent.config

        #: the collection this node is part of.
        self.collection = collection or getattr(parent, 'collection', None)
        
        #: the file where this item is contained/collected from.
        self.fspath = getattr(parent, 'fspath', None)
        self.ihook = HookProxy(self)
        self.keywords = self.readkeywords()

    def __repr__(self):
        if getattr(self.config.option, 'debug', False):
            return "<%s %r %0x>" %(self.__class__.__name__,
                getattr(self, 'name', None), id(self))
        else:
            return "<%s %r>" %(self.__class__.__name__,
                getattr(self, 'name', None))

    # methods for ordering nodes

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.__class__ == other.__class__ and \
               self.name == other.name and self.parent == other.parent 

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.name, self.parent))

    def setup(self):
        pass

    def teardown(self):
        pass

    def _memoizedcall(self, attrname, function):
        exattrname = "_ex_" + attrname
        failure = getattr(self, exattrname, None)
        if failure is not None:
            py.builtin._reraise(failure[0], failure[1], failure[2])
        if hasattr(self, attrname):
            return getattr(self, attrname)
        try:
            res = function()
        except py.builtin._sysex:
            raise
        except:
            failure = py.std.sys.exc_info()
            setattr(self, exattrname, failure)
            raise
        setattr(self, attrname, res)
        return res

    def listchain(self):
        """ return list of all parent collectors up to self,
            starting from root of collection tree. """
        l = [self]
        while 1:
            x = l[0]
            if x.parent is not None: # and x.parent.parent is not None:
                l.insert(0, x.parent)
            else:
                return l

    def listnames(self):
        return [x.name for x in self.listchain()]

    def getparent(self, cls):
        current = self
        while current and not isinstance(current, cls):
            current = current.parent
        return current

    def readkeywords(self):
        return dict([(x, True) for x in self._keywords()])

    def _keywords(self):
        return [self.name]

    def _prunetraceback(self, traceback):
        return traceback

    def _repr_failure_py(self, excinfo, style=None):
        if self.config.option.fulltrace:
            style="long"
        else:
            excinfo.traceback = self._prunetraceback(excinfo.traceback)
        # XXX should excinfo.getrepr record all data and toterminal()
        # process it?
        if style is None:
            if self.config.option.tbstyle == "short":
                style = "short"
            else:
                style = "long"
        return excinfo.getrepr(funcargs=True,
                               showlocals=self.config.option.showlocals,
                               style=style)

    repr_failure = _repr_failure_py

class Collector(Node):
    """ Collector instances create children through collect()
        and thus iteratively build a tree.
    """
    class CollectError(Exception):
        """ an error during collection, contains a custom message. """

    def collect(self):
        """ returns a list of children (items and collectors)
            for this collection node.
        """
        raise NotImplementedError("abstract")

    def collect_by_name(self, name):
        """ return a child matching the given name, else None. """
        for colitem in self._memocollect():
            if colitem.name == name:
                return colitem

    def repr_failure(self, excinfo):
        """ represent a failure. """
        if excinfo.errisinstance(self.CollectError):
            exc = excinfo.value
            return str(exc.args[0])
        return self._repr_failure_py(excinfo, style="short")

    def _memocollect(self):
        """ internal helper method to cache results of calling collect(). """
        return self._memoizedcall('_collected', self.collect)

    def _prunetraceback(self, traceback):
        if hasattr(self, 'fspath'):
            path = self.fspath
            ntraceback = traceback.cut(path=self.fspath)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(excludepath=py._pydir)
            traceback = ntraceback.filter()
        return traceback

class FSCollector(Collector):
    def __init__(self, fspath, parent=None, config=None, collection=None):
        fspath = py.path.local(fspath)
        super(FSCollector, self).__init__(fspath.basename,
            parent, config, collection)
        self.fspath = fspath

class File(FSCollector):
    """ base class for collecting tests from a file. """

class Directory(FSCollector):
    def recfilter(self, path):
        if path.check(dir=1, dotfile=0):
            return path.basename not in ('CVS', '_darcs', '{arch}')

    def collect(self):
        l = []
        for path in self.fspath.listdir(sort=True):
            res = self.consider(path)
            if res is not None:
                if isinstance(res, (list, tuple)):
                    l.extend(res)
                else:
                    l.append(res)
        return l

    def consider(self, path):
        if self.ihook.pytest_ignore_collect(path=path, config=self.config):
           return
        if path.check(file=1):
            res = self.consider_file(path)
        elif path.check(dir=1):
            res = self.consider_dir(path)
        else:
            res = None
        if isinstance(res, list):
            # throw out identical results
            l = []
            for x in res:
                if x not in l:
                    assert x.parent == self, (x.parent, self)
                    assert x.fspath == path, (x.fspath, path)
                    l.append(x)
            res = l
        return res

    def consider_file(self, path):
        return self.ihook.pytest_collect_file(path=path, parent=self)

    def consider_dir(self, path):
        return self.ihook.pytest_collect_directory(path=path, parent=self)

class Item(Node):
    """ a basic test invocation item. Note that for a single function
    there might be multiple test invocation items. Attributes:
    
    """
    def reportinfo(self):
        return self.fspath, None, ""
