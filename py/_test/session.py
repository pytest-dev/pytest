""" basic test session implementation.

* drives collection of tests
* triggers executions of tests
* produces events used by reporting
"""

import py
import sys

#
# main entry point
#

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    config = py.test.config
    try:
        config.parse(args)
        config.pluginmanager.do_configure(config)
        exitstatus = config.hook.pytest_cmdline_main(config=config)
        config.pluginmanager.do_unconfigure(config)
    except config.Error:
        e = sys.exc_info()[1]
        sys.stderr.write("ERROR: %s\n" %(e.args[0],))
        exitstatus = EXIT_INTERNALERROR
    py.test.config = py.test.config.__class__()
    return exitstatus


# exitcodes for the command line
EXIT_OK = 0
EXIT_TESTSFAILED = 1
EXIT_INTERRUPTED = 2
EXIT_INTERNALERROR = 3
EXIT_NOHOSTS = 4

# imports used for genitems()
Item = py.test.collect.Item
Collector = py.test.collect.Collector

class Session(object):
    nodeid = ""
    class Interrupted(KeyboardInterrupt):
        """ signals an interrupted test run. """
        __module__ = 'builtins' # for py3

    def __init__(self, config, collection):
        self.config = config
        self.pluginmanager = config.pluginmanager # shortcut
        self.pluginmanager.register(self)
        self._testsfailed = 0
        self.shouldstop = False
        self.collection = collection

    def sessionstarts(self):
        """ setup any neccessary resources ahead of the test run. """
        self.config.hook.pytest_sessionstart(session=self)

    def pytest_runtest_logreport(self, report):
        if report.failed:
            self._testsfailed += 1
            maxfail = self.config.getvalue("maxfail")
            if maxfail and self._testsfailed >= maxfail:
                self.shouldstop = "stopping after %d failures" % (
                    self._testsfailed)
                self.collection.shouldstop = self.shouldstop
    pytest_collectreport = pytest_runtest_logreport

    def sessionfinishes(self, exitstatus):
        """ teardown any resources after a test run. """
        self.config.hook.pytest_sessionfinish(
            session=self,
            exitstatus=exitstatus,
        )

    def main(self):
        """ main loop for running tests. """
        self.shouldstop = False

        self.sessionstarts()
        exitstatus = EXIT_OK
        try:
            self._mainloop()
            if self._testsfailed:
                exitstatus = EXIT_TESTSFAILED
            self.sessionfinishes(exitstatus=exitstatus)
        except KeyboardInterrupt:
            excinfo = py.code.ExceptionInfo()
            self.config.hook.pytest_keyboard_interrupt(excinfo=excinfo)
            exitstatus = EXIT_INTERRUPTED
        except:
            excinfo = py.code.ExceptionInfo()
            self.config.pluginmanager.notify_exception(excinfo)
            exitstatus = EXIT_INTERNALERROR
        if exitstatus in (EXIT_INTERNALERROR, EXIT_INTERRUPTED):
            self.sessionfinishes(exitstatus=exitstatus)
        return exitstatus

    def _mainloop(self):
        if self.config.option.collectonly:
            return
        for item in self.collection.items:
            item.config.hook.pytest_runtest_protocol(item=item)
            if self.shouldstop:
                raise self.Interrupted(self.shouldstop)


class Collection:
    def __init__(self, config):
        self.config = config
        self.topdir = gettopdir(self.config.args)
        self._argfspaths = [py.path.local(decodearg(x)[0])
                                     for x in self.config.args]
        x = py.test.collect.Directory(fspath=self.topdir,
            config=config, collection=self)
        self._topcollector = x.consider_dir(self.topdir)
        self._topcollector.parent = None

    def _normalizearg(self, arg):
        return "::".join(self._parsearg(arg))

    def _parsearg(self, arg):
        """ return normalized name list for a command line specified id
        which might be of the form x/y/z::name1::name2
        and should result into the form x::y::z::name1::name2
        """
        parts = str(arg).split("::")
        path = py.path.local(parts[0])
        if not path.check():
            raise self.config.Error("file not found: %s" %(path,))
        topdir = self.topdir
        if path != topdir and not path.relto(topdir):
            raise self.config.Error("path %r is not relative to %r" %
                (str(path), str(topdir)))
        topparts = path.relto(topdir).split(path.sep)
        return topparts + parts[1:]

    def getid(self, node, relative=True):
        """ return id for node, relative to topdir. """
        path = node.fspath
        chain = [x for x in node.listchain() if x.fspath == path]
        chain = chain[1:]
        names = [x.name for x in chain if x.name != "()"]
        if relative:
            relpath = path.relto(self.topdir)
            if relpath:
                path = relpath
        names = relpath.split(node.fspath.sep) + names
        return "::".join(names)

    def getbyid(self, id):
        """ return one or more nodes matching the id. """
        matching = [self._topcollector]
        if not id:
            return matching
        names = id.split("::")
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

    def do_collection(self):
        assert not hasattr(self, 'items')
        hook = self.config.hook
        hook.pytest_log_startcollection(collection=self)
        try:
            self.items = self.perform_collect()
        except self.config.Error:
            raise
        except Exception:
            self.config.pluginmanager.notify_exception()
            return EXIT_INTERNALERROR
        else:
            hook.pytest_collection_modifyitems(collection=self)
            res = hook.pytest_log_finishcollection(collection=self)
            return res and max(res) or 0 # returncode

    def getinitialnodes(self):
        idlist = [self._normalizearg(arg) for arg in self.config.args]
        nodes = []
        for id in idlist:
            nodes.extend(self.getbyid(id))
        return nodes

    def perform_collect(self):
        idlist = [self._parsearg(arg) for arg in self.config.args]
        nodes = []
        for names in idlist:
            self.genitems([self._topcollector], names, nodes)
        return nodes

    def genitems(self, matching, names, result):
        names = list(names)
        name = names and names.pop(0) or None
        for node in matching:
            if isinstance(node, Item):
                if name is None:
                    self.config.hook.pytest_log_itemcollect(item=node)
                    result.append(node)
            else:
                assert isinstance(node, Collector)
                node.ihook.pytest_collectstart(collector=node)
                rep = node.ihook.pytest_make_collect_report(collector=node)
                #print "matching", rep.result, "against name", name
                if rep.passed:
                    if name:
                        matched = False
                        for subcol in rep.result:
                            if subcol.name != name and subcol.name == "()":
                                names.insert(0, name)
                                name = "()"
                            # see doctests/custom naming XXX
                            if subcol.name == name or subcol.fspath.basename == name:
                                self.genitems([subcol], names, result)
                                matched = True
                        if not matched:
                            raise self.config.Error(
                                "can't collect: %s" % (name,))

                    else:
                        self.genitems(rep.result, [], result)
                node.ihook.pytest_collectreport(report=rep)
                x = getattr(self, 'shouldstop', None)
                if x:
                    raise self.Interrupted(x)

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


