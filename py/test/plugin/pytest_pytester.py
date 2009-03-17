"""
pytes plugin for easing testing of pytest runs themselves. 
"""

import py
from py.__.test import event
from py.__.test.config import Config as pytestConfig

class PytesterPlugin:
    def pytest_pyfuncarg_linecomp(self, pyfuncitem):
        return LineComp()

    def pytest_pyfuncarg_LineMatcher(self, pyfuncitem):
        return LineMatcher

    def pytest_pyfuncarg_testdir(self, pyfuncitem):
        tmptestdir = TmpTestdir(pyfuncitem)
        pyfuncitem.addfinalizer(tmptestdir.finalize)
        return tmptestdir
 
    def pytest_pyfuncarg_EventRecorder(self, pyfuncitem):
        return EventRecorder

def test_generic(plugintester):
    plugintester.apicheck(PytesterPlugin)

class RunResult:
    def __init__(self, ret, outlines, errlines):
        self.ret = ret
        self.outlines = outlines
        self.errlines = errlines
        self.stdout = LineMatcher(outlines)
        self.stderr = LineMatcher(errlines)

class TmpTestdir:
    def __init__(self, pyfuncitem):
        self.pyfuncitem = pyfuncitem
        # XXX remove duplication with tmpdir plugin 
        basetmp = pyfuncitem.config.ensuretemp("testdir")
        name = pyfuncitem.name
        for i in range(100):
            try:
                tmpdir = basetmp.mkdir(name + str(i))
            except py.error.EEXIST:
                continue
            break
        # we need to create another subdir
        # because Directory.collect() currently loads
        # conftest.py from sibling directories
        self.tmpdir = tmpdir.mkdir(name)
        self.plugins = []
        self._syspathremove = []

    def Config(self, pyplugins=None, topdir=None):
        if topdir is None:
            topdir = self.tmpdir.dirpath()
        return pytestConfig(pyplugins, topdir=topdir)

    def finalize(self):
        for p in self._syspathremove:
            py.std.sys.path.remove(p)
        if hasattr(self, '_olddir'):
            self._olddir.chdir()

    def chdir(self):
        old = self.testdir.chdir()
        if not hasattr(self, '_olddir'):
            self._olddir = old 

    def _makefile(self, ext, args, kwargs):
        items = kwargs.items()
        if args:
            source = "\n".join(map(str, args))
            basename = self.pyfuncitem.name 
            items.insert(0, (basename, source))
        ret = None
        for name, value in items:
            p = self.tmpdir.join(name).new(ext=ext)
            source = py.code.Source(value)
            p.write(str(py.code.Source(value)).lstrip())
            if ret is None:
                ret = p
        return ret 


    def makefile(self, ext, *args, **kwargs):
        return self._makefile(ext, args, kwargs)

    def makeconftest(self, source):
        return self.makepyfile(conftest=source)

    def makepyfile(self, *args, **kwargs):
        return self._makefile('.py', args, kwargs)

    def maketxtfile(self, *args, **kwargs):
        return self._makefile('.txt', args, kwargs)

    def syspathinsert(self, path=None):
        if path is None:
            path = self.tmpdir
        py.std.sys.path.insert(0, str(path))
        self._syspathremove.append(str(path))
            
    def mkdir(self, name):
        return self.tmpdir.mkdir(name)
    
    def chdir(self):
        return self.tmpdir.chdir()

    def genitems(self, colitems):
        return list(self.session.genitems(colitems))

    def inline_genitems(self, *args):
        #config = self.parseconfig(*args)
        config = self.parseconfig(*args)
        session = config.initsession()
        rec = EventRecorder(config.bus)
        colitems = [config.getfsnode(arg) for arg in config.args]
        items = list(session.genitems(colitems))
        return items, rec 

    def runitem(self, source, **runnerargs):
        # used from runner functional tests 
        item = self.getitem(source)
        # the test class where we are called from wants to provide the runner 
        testclassinstance = self.pyfuncitem.obj.im_self
        runner = testclassinstance.getrunner()
        return runner(item, **runnerargs)

    def inline_runsource(self, source, *cmdlineargs):
        p = self.makepyfile(source)
        l = list(cmdlineargs) + [p]
        return self.inline_run(*l)

    def inline_run(self, *args):
        config = self.parseconfig(*args)
        config.pytestplugins.do_configure(config)
        session = config.initsession()
        sorter = EventRecorder(config.bus)
        session.main()
        config.pytestplugins.do_unconfigure(config)
        return sorter

    def config_preparse(self):
        config = self.Config()
        for plugin in self.plugins:
            if isinstance(plugin, str):
                config.pytestplugins.import_plugin(plugin)
            else:
                config.pytestplugins.register(plugin)
        return config

    def parseconfig(self, *args):
        if not args:
            args = (self.tmpdir,)
        config = self.config_preparse()
        args = list(args) + ["--basetemp=%s" % self.tmpdir.dirpath('basetemp')]
        config.parse(args)
        return config 

    def getitem(self,  source, funcname="test_func"):
        modcol = self.getmodulecol(source)
        item = modcol.join(funcname) 
        assert item is not None, "%r item not found in module:\n%s" %(funcname, source)
        return item 

    def getitems(self,  source):
        modcol = self.getmodulecol(source)
        return list(modcol.config.initsession().genitems([modcol]))
        #assert item is not None, "%r item not found in module:\n%s" %(funcname, source)
        #return item 

    def getfscol(self,  path, configargs=()):
        self.config = self.parseconfig(path, *configargs)
        self.session = self.config.initsession()
        return self.config.getfsnode(path)

    def getmodulecol(self,  source, configargs=(), withinit=False):
        kw = {self.pyfuncitem.name: py.code.Source(source).strip()}
        path = self.makepyfile(**kw)
        if withinit:
            self.makepyfile(__init__ = "#")
        self.config = self.parseconfig(path, *configargs)
        self.session = self.config.initsession()
        return self.config.getfsnode(path)

    def prepare(self):
        p = self.tmpdir.join("conftest.py") 
        if not p.check():
            plugins = [x for x in self.plugins if isinstance(x, str)]
            if not plugins:
                return
            p.write("import py ; pytest_plugins = %r" % plugins)
        else:
            if self.plugins:
                print "warning, ignoring reusing existing con", p 

    def popen(self, cmdargs, stdout, stderr, **kw):
        if not hasattr(py.std, 'subprocess'):
            py.test.skip("no subprocess module")
        return py.std.subprocess.Popen(cmdargs, stdout=stdout, stderr=stderr, **kw)

    def run(self, *cmdargs):
        self.prepare()
        old = self.tmpdir.chdir()
        #print "chdir", self.tmpdir
        try:
            return self._run(*cmdargs)
        finally:
            old.chdir()

    def _run(self, *cmdargs):
        cmdargs = map(str, cmdargs)
        p1 = py.path.local("stdout")
        p2 = py.path.local("stderr")
        print "running", cmdargs, "curdir=", py.path.local()
        popen = self.popen(cmdargs, stdout=p1.open("w"), stderr=p2.open("w"))
        ret = popen.wait()
        out, err = p1.readlines(cr=0), p2.readlines(cr=0)
        if err:
            for line in err: 
                print >>py.std.sys.stderr, line
        if out:
            for line in out: 
                print >>py.std.sys.stdout, line
        return RunResult(ret, out, err)

    def runpybin(self, scriptname, *args):
        bindir = py.path.local(py.__file__).dirpath("bin")
        if py.std.sys.platform == "win32":
            script = bindir.join("win32", scriptname + ".cmd")
        else:
            script = bindir.join(scriptname)
        assert script.check()
        return self.run(script, *args)

    def runpytest(self, *args):
        p = py.path.local.make_numbered_dir(prefix="runpytest-", 
            keep=None, rootdir=self.tmpdir)
        args = ('--basetemp=%s' % p, ) + args 
        return self.runpybin("py.test", *args)

class Event:
    def __init__(self, name, args, kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

class EventRecorder(object):
    def __init__(self, pyplugins, debug=False): # True):
        self.events = []
        self.pyplugins = pyplugins
        self.debug = debug
        pyplugins.register(self)

    def pyevent(self, name, *args, **kwargs):
        if name == "plugin_registered" and args == (self,):
            return
        if self.debug:
            print "[event: %s]: %s **%s" %(name, ", ".join(map(str, args)), kwargs,)
        self.events.append(Event(name, args, kwargs))

    def get(self, cls):
        l = []
        for event in self.events:
            value = event.args[0]
            if isinstance(value, cls):
                l.append(value)
        return l 

    def getnamed(self, *names):
        l = []
        for event in self.events:
            if event.name in names:
                l.append(event.args[0])
        return l 

    def getfirstnamed(self, name):
        for event in self.events:
            if event.name == name:
                return event.args[0]

    def getfailures(self, names='itemtestreport collectionreport'):
        l = []
        for ev in self.getnamed(*names.split()):
            if ev.failed:
                l.append(ev)
        return l

    def getfailedcollections(self):
        return self.getfailures('collectionreport')

    def listoutcomes(self):
        passed = []
        skipped = []
        failed = []
        for ev in self.getnamed('itemtestreport'): # , 'collectionreport'):
            if ev.passed: 
                passed.append(ev) 
            elif ev.skipped: 
                skipped.append(ev) 
            elif ev.failed:
                failed.append(ev) 
        return passed, skipped, failed 

    def countoutcomes(self):
        return map(len, self.listoutcomes())

    def assertoutcome(self, passed=0, skipped=0, failed=0):
        realpassed, realskipped, realfailed = self.listoutcomes()
        assert passed == len(realpassed)
        assert skipped == len(realskipped)
        assert failed == len(realfailed)

    def getreport(self, inamepart): 
        """ return a testreport whose dotted import path matches """
        __tracebackhide__ = True
        l = []
        for rep in self.get(event.ItemTestReport):
            if inamepart in rep.colitem.listnames():
                l.append(rep)
        if not l:
            raise ValueError("could not find test report matching %r: no test reports at all!" %
                (inamepart,))
        if len(l) > 1:
            raise ValueError("found more than one testreport matching %r: %s" %(
                             inamepart, l))
        return l[0]

    def clear(self):
        self.events[:] = []

    def unregister(self):
        self.pyplugins.unregister(self)

def test_eventrecorder():
    bus = py._com.PyPlugins()
    recorder = EventRecorder(bus)
    bus.notify("anonymous", event.NOP())
    assert recorder.events 
    assert not recorder.getfailures()
    rep = event.ItemTestReport(None, None)
    rep.passed = False
    rep.failed = True
    bus.notify("itemtestreport", rep)
    failures = recorder.getfailures()
    assert failures == [rep]
    failures = recorder.get(event.ItemTestReport)
    assert failures == [rep]
    failures = recorder.getnamed("itemtestreport")
    assert failures == [rep]

    rep = event.ItemTestReport(None, None)
    rep.passed = False
    rep.skipped = True
    bus.notify("itemtestreport", rep)

    rep = event.CollectionReport(None, None)
    rep.passed = False
    rep.failed = True
    bus.notify("itemtestreport", rep)

    passed, skipped, failed = recorder.listoutcomes()
    assert not passed and skipped and failed

    numpassed, numskipped, numfailed = recorder.countoutcomes()
    assert numpassed == 0
    assert numskipped == 1
    assert numfailed == 2

    recorder.unregister()
    recorder.clear() 
    assert not recorder.events
    assert not recorder.getfailures()
    bus.notify("itemtestreport", rep)
    assert not recorder.events 
    assert not recorder.getfailures()

class LineComp:
    def __init__(self):
        self.stringio = py.std.StringIO.StringIO()

    def assert_contains_lines(self, lines2):
        """ assert that lines2 are contained (linearly) in lines1. 
            return a list of extralines found.
        """
        __tracebackhide__ = True
        val = self.stringio.getvalue()
        self.stringio.truncate(0)  # remove what we got 
        lines1 = val.split("\n")
        return LineMatcher(lines1).fnmatch_lines(lines2)
            
class LineMatcher:
    def __init__(self,  lines):
        self.lines = lines

    def str(self):
        return "\n".join(self.lines)

    def fnmatch_lines(self, lines2):
        if isinstance(lines2, str):
            lines2 = py.code.Source(lines2)
        if isinstance(lines2, py.code.Source):
            lines2 = lines2.strip().lines

        from fnmatch import fnmatch
        __tracebackhide__ = True
        lines1 = self.lines[:]
        nextline = None
        extralines = []
        for line in lines2:
            nomatchprinted = False
            while lines1:
                nextline = lines1.pop(0)
                if line == nextline:
                    print "exact match:", repr(line)
                    break 
                elif fnmatch(nextline, line):
                    print "fnmatch:", repr(line)
                    print "   with:", repr(nextline)
                    break
                else:
                    if not nomatchprinted:
                        print "nomatch:", repr(line)
                        nomatchprinted = True
                    print "    and:", repr(nextline)
                extralines.append(nextline)
            else:
                if line != nextline:
                    #__tracebackhide__ = True
                    raise AssertionError("expected line not found: %r" % line)
        extralines.extend(lines1)
        return extralines 


