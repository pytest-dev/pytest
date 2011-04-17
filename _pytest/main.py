""" core implementation of testing process: init, session, runtest loop. """

import py
import pytest, _pytest
import os, sys
tracebackcutdir = py.path.local(_pytest.__file__).dirpath()

# exitcodes for the command line
EXIT_OK = 0
EXIT_TESTSFAILED = 1
EXIT_INTERRUPTED = 2
EXIT_INTERNALERROR = 3

def pytest_addoption(parser):
    parser.addini("norecursedirs", "directory patterns to avoid for recursion",
        type="args", default=('.*', 'CVS', '_darcs', '{arch}'))
    #parser.addini("dirpatterns",
    #    "patterns specifying possible locations of test files",
    #    type="linelist", default=["**/test_*.txt",
    #            "**/test_*.py", "**/*_test.py"]
    #)
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
    group.addoption('--pyargs', action="store_true",
        help="try to interpret all arguments as python packages.")
    group.addoption("--ignore", action="append", metavar="path",
        help="ignore path during collection (multi-allowed).")
    group.addoption('--confcutdir', dest="confcutdir", default=None,
        metavar="dir",
        help="only load conftest.py's relative to specified dir.")

    group = parser.getgroup("debugconfig",
        "test session debugging and configuration")
    group.addoption('--basetemp', dest="basetemp", default=None, metavar="dir",
               help="base temporary directory for this test run.")


def pytest_namespace():
    return dict(collect=dict(Item=Item, Collector=Collector, File=File))
        
def pytest_configure(config):
    py.test.config = config # compatibiltiy
    if config.option.exitfirst:
        config.option.maxfail = 1

def pytest_cmdline_main(config):
    """ default command line protocol for initialization, session,
    running tests and reporting. """
    session = Session(config)
    session.exitstatus = EXIT_OK
    try:
        config.pluginmanager.do_configure(config)
        config.hook.pytest_sessionstart(session=session)
        config.hook.pytest_collection(session=session)
        config.hook.pytest_runtestloop(session=session)
    except pytest.UsageError:
        raise
    except KeyboardInterrupt:
        excinfo = py.code.ExceptionInfo()
        config.hook.pytest_keyboard_interrupt(excinfo=excinfo)
        session.exitstatus = EXIT_INTERRUPTED
    except:
        excinfo = py.code.ExceptionInfo()
        config.pluginmanager.notify_exception(excinfo, config.option)
        session.exitstatus = EXIT_INTERNALERROR
        if excinfo.errisinstance(SystemExit):
            sys.stderr.write("mainloop: caught Spurious SystemExit!\n")
    if not session.exitstatus and session._testsfailed:
        session.exitstatus = EXIT_TESTSFAILED
    config.hook.pytest_sessionfinish(session=session,
        exitstatus=session.exitstatus)
    config.pluginmanager.do_unconfigure(config)
    return session.exitstatus

def pytest_collection(session):
    session.perform_collect()
    hook = session.config.hook
    hook.pytest_collection_modifyitems(session=session,
        config=session.config, items=session.items)
    hook.pytest_collection_finish(session=session)
    return True

def pytest_runtestloop(session):
    if session.config.option.collectonly:
        return True
    for item in session.session.items:
        item.config.hook.pytest_runtest_protocol(item=item)
        if session.shouldstop:
            raise session.Interrupted(session.shouldstop)
    return True

def pytest_ignore_collect(path, config):
    p = path.dirpath()
    ignore_paths = config._getconftest_pathlist("collect_ignore", path=p)
    ignore_paths = ignore_paths or []
    excludeopt = config.getvalue("ignore")
    if excludeopt:
        ignore_paths.extend([py.path.local(x) for x in excludeopt])
    return path in ignore_paths

class HookProxy:
    def __init__(self, fspath, config):
        self.fspath = fspath
        self.config = config
    def __getattr__(self, name):
        hookmethod = getattr(self.config.hook, name)
        def call_matching_hooks(**kwargs):
            plugins = self.config._getmatchingplugins(self.fspath)
            return hookmethod.pcall(plugins, **kwargs)
        return call_matching_hooks

def compatproperty(name):
    def fget(self):
        return getattr(pytest, name)
    return property(fget, None, None,
        "deprecated attribute %r, use pytest.%s" % (name,name))
    
class Node(object):
    """ base class for all Nodes in the collection tree.
    Collector subclasses have children, Items are terminal nodes."""

    def __init__(self, name, parent=None, config=None, session=None):
        #: a unique name with the scope of the parent
        self.name = name

        #: the parent collector node.
        self.parent = parent
        
        #: the test config object
        self.config = config or parent.config

        #: the collection this node is part of
        self.session = session or parent.session
        
        #: filesystem path where this node was collected from
        self.fspath = getattr(parent, 'fspath', None)
        self.ihook = self.session.gethookproxy(self.fspath)
        self.keywords = {self.name: True}

    Module = compatproperty("Module")
    Class = compatproperty("Class")
    Instance = compatproperty("Instance")
    Function = compatproperty("Function")
    File = compatproperty("File")
    Item = compatproperty("Item")

    def _getcustomclass(self, name):
        cls = getattr(self, name)
        if cls != getattr(pytest, name):
            py.log._apiwarn("2.0", "use of node.%s is deprecated, "
                "use pytest_pycollect_makeitem(...) to create custom "
                "collection nodes" % name)
        return cls

    def __repr__(self):
        return "<%s %r>" %(self.__class__.__name__, getattr(self, 'name', None))

    # methods for ordering nodes
    @property
    def nodeid(self):
        try:
            return self._nodeid
        except AttributeError:
            self._nodeid = x = self._makeid()
            return x

    def _makeid(self):
        return self.parent.nodeid + "::" + self.name

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

    def getplugins(self):
        return self.config._getmatchingplugins(self.fspath)

    def getparent(self, cls):
        current = self
        while current and not isinstance(current, cls):
            current = current.parent
        return current

    def _prunetraceback(self, excinfo):
        pass

    def _repr_failure_py(self, excinfo, style=None):
        if self.config.option.fulltrace:
            style="long"
        else:
            self._prunetraceback(excinfo)
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

    def repr_failure(self, excinfo):
        """ represent a collection failure. """
        if excinfo.errisinstance(self.CollectError):
            exc = excinfo.value
            return str(exc.args[0])
        return self._repr_failure_py(excinfo, style="short")

    def _memocollect(self):
        """ internal helper method to cache results of calling collect(). """
        return self._memoizedcall('_collected', lambda: list(self.collect()))

    def _prunetraceback(self, excinfo):
        if hasattr(self, 'fspath'):
            path = self.fspath
            traceback = excinfo.traceback
            ntraceback = traceback.cut(path=self.fspath)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(excludepath=tracebackcutdir)
            excinfo.traceback = ntraceback.filter()

class FSCollector(Collector):
    def __init__(self, fspath, parent=None, config=None, session=None):
        fspath = py.path.local(fspath) # xxx only for test_resultlog.py?
        name = fspath.basename
        if parent is not None:
            rel = fspath.relto(parent.fspath)
            if rel:
                name = rel
            name = name.replace(os.sep, "/")
        super(FSCollector, self).__init__(name, parent, config, session)
        self.fspath = fspath

    def _makeid(self):
        if self == self.session:
            return "."
        relpath = self.session.fspath.bestrelpath(self.fspath)
        if os.sep != "/":
            relpath = relpath.replace(os.sep, "/")
        return relpath

class File(FSCollector):
    """ base class for collecting tests from a file. """

class Item(Node):
    """ a basic test invocation item. Note that for a single function
    there might be multiple test invocation items.
    """
    def reportinfo(self):
        return self.fspath, None, ""

    @property
    def location(self):
        try:
            return self._location
        except AttributeError:
            location = self.reportinfo()
            # bestrelpath is a quite slow function
            cache = self.config.__dict__.setdefault("_bestrelpathcache", {})
            try:
                fspath = cache[location[0]]
            except KeyError:
                fspath = self.session.fspath.bestrelpath(location[0])
                cache[location[0]] = fspath
            location = (fspath, location[1], str(location[2]))
            self._location = location
            return location

class NoMatch(Exception):
    """ raised if matching cannot locate a matching names. """

class Session(FSCollector):
    class Interrupted(KeyboardInterrupt):
        """ signals an interrupted test run. """
        __module__ = 'builtins' # for py3

    def __init__(self, config):
        super(Session, self).__init__(py.path.local(), parent=None,
            config=config, session=self)
        assert self.config.pluginmanager.register(self, name="session", prepend=True)
        self._testsfailed = 0
        self.shouldstop = False
        self.trace = config.trace.root.get("collection")
        self._norecursepatterns = config.getini("norecursedirs")

    def pytest_collectstart(self):
        if self.shouldstop:
            raise self.Interrupted(self.shouldstop)

    def pytest_runtest_logreport(self, report):
        if report.failed and 'xfail' not in getattr(report, 'keywords', []):
            self._testsfailed += 1
            maxfail = self.config.getvalue("maxfail")
            if maxfail and self._testsfailed >= maxfail:
                self.shouldstop = "stopping after %d failures" % (
                    self._testsfailed)
    pytest_collectreport = pytest_runtest_logreport

    def isinitpath(self, path):
        return path in self._initialpaths

    def gethookproxy(self, fspath):
        return HookProxy(fspath, self.config)

    def perform_collect(self, args=None, genitems=True):
        if args is None:
            args = self.config.args
        self.trace("perform_collect", self, args)
        self.trace.root.indent += 1
        self._notfound = []
        self._initialpaths = set()
        self._initialparts = []
        for arg in args:
            parts = self._parsearg(arg)
            self._initialparts.append(parts)
            self._initialpaths.add(parts[0])
        self.ihook.pytest_collectstart(collector=self)
        rep = self.ihook.pytest_make_collect_report(collector=self)
        self.ihook.pytest_collectreport(report=rep)
        self.trace.root.indent -= 1
        if self._notfound:
            for arg, exc in self._notfound:
                line = "(no name %r in any of %r)" % (arg, exc.args[0])
                raise pytest.UsageError("not found: %s\n%s" %(arg, line))
        if not genitems:
            return rep.result
        else:
            self.items = items = []
            if rep.passed:
                for node in rep.result:
                    self.items.extend(self.genitems(node))
            return items

    def collect(self):
        for parts in self._initialparts:
            arg = "::".join(map(str, parts))
            self.trace("processing argument", arg)
            self.trace.root.indent += 1
            try:
                for x in self._collect(arg):
                    yield x
            except NoMatch:
                # we are inside a make_report hook so
                # we cannot directly pass through the exception
                self._notfound.append((arg, sys.exc_info()[1]))
                self.trace.root.indent -= 1
                break
            self.trace.root.indent -= 1

    def _collect(self, arg):
        names = self._parsearg(arg)
        path = names.pop(0)
        if path.check(dir=1):
            assert not names, "invalid arg %r" %(arg,)
            for path in path.visit(fil=lambda x: x.check(file=1),
                rec=self._recurse, bf=True, sort=True):
                for x in self._collectfile(path):
                    yield x
        else:
            assert path.check(file=1)
            for x in self.matchnodes(self._collectfile(path), names):
                yield x

    def _collectfile(self, path):
        ihook = self.gethookproxy(path)
        if not self.isinitpath(path):
            if ihook.pytest_ignore_collect(path=path, config=self.config):
               return ()
        return ihook.pytest_collect_file(path=path, parent=self)

    def _recurse(self, path):
        ihook = self.gethookproxy(path.dirpath())
        if ihook.pytest_ignore_collect(path=path, config=self.config):
           return
        for pat in self._norecursepatterns:
            if path.check(fnmatch=pat):
                return False
        ihook = self.gethookproxy(path)
        ihook.pytest_collect_directory(path=path, parent=self)
        return True

    def _tryconvertpyarg(self, x):
        try:
            mod = __import__(x, None, None, ['__doc__'])
        except (ValueError, ImportError):
            return x
        p = py.path.local(mod.__file__)
        if p.purebasename == "__init__":
            p = p.dirpath()
        else:
            p = p.new(basename=p.purebasename+".py")
        return str(p)

    def _parsearg(self, arg):
        """ return (fspath, names) tuple after checking the file exists. """
        arg = str(arg)
        if self.config.option.pyargs:
            arg = self._tryconvertpyarg(arg)
        parts = str(arg).split("::")
        relpath = parts[0].replace("/", os.sep)
        path = self.fspath.join(relpath, abs=True)
        if not path.check():
            if self.config.option.pyargs:
                msg = "file or package not found: "
            else:
                msg = "file not found: "
            raise pytest.UsageError(msg + arg)
        parts[0] = path
        return parts
   
    def matchnodes(self, matching, names):
        self.trace("matchnodes", matching, names)
        self.trace.root.indent += 1
        nodes = self._matchnodes(matching, names)
        num = len(nodes)
        self.trace("matchnodes finished -> ", num, "nodes")
        self.trace.root.indent -= 1
        if num == 0:
            raise NoMatch(matching, names[:1])
        return nodes

    def _matchnodes(self, matching, names):
        if not matching or not names:
            return matching
        name = names[0]
        assert name
        nextnames = names[1:]
        resultnodes = []
        for node in matching:
            if isinstance(node, pytest.Item):
                if not names:
                    resultnodes.append(node)
                continue
            assert isinstance(node, pytest.Collector)
            node.ihook.pytest_collectstart(collector=node)
            rep = node.ihook.pytest_make_collect_report(collector=node)
            if rep.passed:
                has_matched = False
                for x in rep.result:
                    if x.name == name:
                        resultnodes.extend(self.matchnodes([x], nextnames))
                        has_matched = True
                # XXX accept IDs that don't have "()" for class instances
                if not has_matched and len(rep.result) == 1 and x.name == "()":
                    nextnames.insert(0, name)
                    resultnodes.extend(self.matchnodes([x], nextnames))
            node.ihook.pytest_collectreport(report=rep)
        return resultnodes

    def genitems(self, node):
        self.trace("genitems", node)
        if isinstance(node, pytest.Item):
            node.ihook.pytest_itemcollected(item=node)
            yield node
        else:
            assert isinstance(node, pytest.Collector)
            node.ihook.pytest_collectstart(collector=node)
            rep = node.ihook.pytest_make_collect_report(collector=node)
            if rep.passed:
                for subnode in rep.result:
                    for x in self.genitems(subnode):
                        yield x
            node.ihook.pytest_collectreport(report=rep)
