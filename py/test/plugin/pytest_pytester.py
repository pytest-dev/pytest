"""
pytes plugin for easing testing of pytest runs themselves. 
"""

import py
import os
import inspect
from py.__.test import runner
from py.__.test.config import Config as pytestConfig
from pytest__pytest import CallRecorder
import api


class PytesterPlugin:
    def pytest_funcarg__linecomp(self, request):
        return LineComp()

    def pytest_funcarg__LineMatcher(self, request):
        return LineMatcher

    def pytest_funcarg__testdir(self, request):
        tmptestdir = TmpTestdir(request)
        return tmptestdir
 
    def pytest_funcarg__eventrecorder(self, request):
        evrec = EventRecorder(py._com.comregistry)
        request.addfinalizer(lambda: evrec.comregistry.unregister(evrec))
        return evrec

def test_generic(plugintester):
    plugintester.hookcheck(PytesterPlugin)

class RunResult:
    def __init__(self, ret, outlines, errlines):
        self.ret = ret
        self.outlines = outlines
        self.errlines = errlines
        self.stdout = LineMatcher(outlines)
        self.stderr = LineMatcher(errlines)

class TmpTestdir:
    def __init__(self, request):
        self.request = request
        # XXX remove duplication with tmpdir plugin 
        basetmp = request.config.ensuretemp("testdir")
        name = request.function.__name__
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
        self.chdir() # always chdir
        assert hasattr(self, '_olddir')
        self.request.addfinalizer(self.finalize)

    def __repr__(self):
        return "<TmpTestdir %r>" % (self.tmpdir,)

    def Config(self, comregistry=None, topdir=None):
        if topdir is None:
            topdir = self.tmpdir.dirpath()
        return pytestConfig(comregistry, topdir=topdir)

    def finalize(self):
        for p in self._syspathremove:
            py.std.sys.path.remove(p)
        if hasattr(self, '_olddir'):
            self._olddir.chdir()

    def geteventrecorder(self, registry):
        sorter = EventRecorder(registry)
        sorter.callrecorder = CallRecorder(registry)
        sorter.callrecorder.start_recording(api.PluginHooks)
        sorter.hook = sorter.callrecorder.hook
        self.request.addfinalizer(sorter.callrecorder.finalize)
        return sorter

    def chdir(self):
        old = self.tmpdir.chdir()
        if not hasattr(self, '_olddir'):
            self._olddir = old 

    def _makefile(self, ext, args, kwargs):
        items = kwargs.items()
        if args:
            source = "\n".join(map(str, args))
            basename = self.request.function.__name__
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
    
    def genitems(self, colitems):
        return list(self.session.genitems(colitems))

    def inline_genitems(self, *args):
        #config = self.parseconfig(*args)
        config = self.parseconfig(*args)
        session = config.initsession()
        rec = self.geteventrecorder(config.pluginmanager)
        colitems = [config.getfsnode(arg) for arg in config.args]
        items = list(session.genitems(colitems))
        return items, rec 

    def runitem(self, source, **runnerargs):
        # used from runner functional tests 
        item = self.getitem(source)
        # the test class where we are called from wants to provide the runner 
        testclassinstance = self.request.function.im_self
        runner = testclassinstance.getrunner()
        return runner(item, **runnerargs)

    def inline_runsource(self, source, *cmdlineargs):
        p = self.makepyfile(source)
        l = list(cmdlineargs) + [p]
        return self.inline_run(*l)

    def inline_run(self, *args):
        config = self.parseconfig(*args)
        config.pluginmanager.do_configure(config)
        session = config.initsession()
        sorter = self.geteventrecorder(config.pluginmanager)
        session.main()
        config.pluginmanager.do_unconfigure(config)
        return sorter 

    def config_preparse(self):
        config = self.Config()
        for plugin in self.plugins:
            if isinstance(plugin, str):
                config.pluginmanager.import_plugin(plugin)
            else:
                config.pluginmanager.register(plugin)
        return config

    def parseconfig(self, *args):
        if not args:
            args = (self.tmpdir,)
        config = self.config_preparse()
        args = list(args) + ["--basetemp=%s" % self.tmpdir.dirpath('basetemp')]
        config.parse(args)
        return config 

    def parseconfigure(self, *args):
        config = self.parseconfig(*args)
        config.pluginmanager.do_configure(config)
        return config

    def getitem(self,  source, funcname="test_func"):
        modcol = self.getmodulecol(source)
        moditems = modcol.collect()
        for item in modcol.collect():
            if item.name == funcname:
                return item 
        else:
            assert 0, "%r item not found in module:\n%s" %(funcname, source)

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
        kw = {self.request.function.__name__: py.code.Source(source).strip()}
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
        env = os.environ.copy()
        env['PYTHONPATH'] = "%s:%s" % (os.getcwd(), env['PYTHONPATH'])
        kw['env'] = env
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
        fullargs = self._getpybinargs(scriptname) + args
        return self.run(*fullargs)

    def _getpybinargs(self, scriptname):
        bindir = py.path.local(py.__file__).dirpath("bin")
        script = bindir.join(scriptname)
        assert script.check()
        return py.std.sys.executable, script

    def runpytest(self, *args):
        p = py.path.local.make_numbered_dir(prefix="runpytest-", 
            keep=None, rootdir=self.tmpdir)
        args = ('--basetemp=%s' % p, ) + args 
        return self.runpybin("py.test", *args)

    def spawn_pytest(self, string, expect_timeout=10.0):
        pexpect = py.test.importorskip("pexpect", "2.3")
        basetemp = self.tmpdir.mkdir("pexpect")
        invoke = "%s %s" % self._getpybinargs("py.test")
        cmd = "%s --basetemp=%s %s" % (invoke, basetemp, string)
        child = pexpect.spawn(cmd, logfile=basetemp.join("spawn.out").open("w"))
        child.timeout = expect_timeout
        return child

class Event:
    def __init__(self, name, args, kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs
    def __repr__(self):
        return "<Event %r %r>" %(self.name, self.args)

class ParsedCall:
    def __init__(self, locals):
        self.__dict__ = locals.copy()

    def __repr__(self):
        return "<ParsedCall %r>" %(self.__dict__,)

class EventRecorder(object):
    def __init__(self, comregistry, debug=False): # True):
        self.comregistry = comregistry
        self.debug = debug
        comregistry.register(self)

    def getcall(self, name):
        l = self.getcalls(name)
        assert len(l) == 1, (name, l)
        return l[0]

    def getcalls(self, *names):
        """ return list of ParsedCall instances matching the given eventname. """
        if len(names) == 1 and isinstance(names, str):
            names = names.split()
        l = []
        for name in names:
            if self.callrecorder.recordsmethod("pytest_" + name):
                name = "pytest_" + name
            if self.callrecorder.recordsmethod(name):
                l.extend(self.callrecorder.getcalls(name))
        return l

    # functionality for test reports 

    def getreports(self, names="itemtestreport collectreport"):
        names = [("pytest_" + x) for x in names.split()]
        l = []
        for call in self.getcalls(*names):
            l.append(call.rep)
        return l 

    def matchreport(self, inamepart="", names="itemtestreport collectreport"):
        """ return a testreport whose dotted import path matches """
        l = []
        for rep in self.getreports(names=names):
            if not inamepart or inamepart in rep.colitem.listnames():
                l.append(rep)
        if not l:
            raise ValueError("could not find test report matching %r: no test reports at all!" %
                (inamepart,))
        if len(l) > 1:
            raise ValueError("found more than one testreport matching %r: %s" %(
                             inamepart, l))
        return l[0]

    def getfailures(self, names='itemtestreport collectreport'):
        l = []
        for call in self.getcalls(*names.split()):
            if call.rep.failed:
                l.append(call.rep)
        return l

    def getfailedcollections(self):
        return self.getfailures('collectreport')

    def listoutcomes(self):
        passed = []
        skipped = []
        failed = []
        for rep in self.getreports("itemtestreport"):
            if rep.passed: 
                passed.append(rep) 
            elif rep.skipped: 
                skipped.append(rep) 
            elif rep.failed:
                failed.append(rep) 
        return passed, skipped, failed 

    def countoutcomes(self):
        return map(len, self.listoutcomes())

    def assertoutcome(self, passed=0, skipped=0, failed=0):
        realpassed, realskipped, realfailed = self.listoutcomes()
        assert passed == len(realpassed)
        assert skipped == len(realskipped)
        assert failed == len(realfailed)

    def clear(self):
        self.callrecorder.calls[:] = []

    def unregister(self):
        self.comregistry.unregister(self)
        self.callrecorder.finalize()

def test_eventrecorder(testdir):
    registry = py._com.Registry()
    recorder = testdir.geteventrecorder(registry)
    assert not recorder.getfailures()
    rep = runner.ItemTestReport(None, None)
    rep.passed = False
    rep.failed = True
    recorder.hook.pytest_itemtestreport(rep=rep)
    failures = recorder.getfailures()
    assert failures == [rep]
    failures = recorder.getfailures()
    assert failures == [rep]

    rep = runner.ItemTestReport(None, None)
    rep.passed = False
    rep.skipped = True
    recorder.hook.pytest_itemtestreport(rep=rep)

    rep = runner.CollectReport(None, None)
    rep.passed = False
    rep.failed = True
    recorder.hook.pytest_itemtestreport(rep=rep)

    passed, skipped, failed = recorder.listoutcomes()
    assert not passed and skipped and failed

    numpassed, numskipped, numfailed = recorder.countoutcomes()
    assert numpassed == 0
    assert numskipped == 1
    assert numfailed == 2

    recorder.unregister()
    recorder.clear() 
    assert not recorder.getfailures()
    recorder.hook.pytest_itemtestreport(rep=rep)
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




def test_parseconfig(testdir):
    config1 = testdir.parseconfig()
    config2 = testdir.parseconfig()
    assert config2 != config1
    assert config1 != py.test.config
