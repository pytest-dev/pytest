"""
funcargs and support code for testing py.test's own functionality. 
"""

import py
import sys, os
import re
import inspect
import time
from py._test.config import Config as pytestConfig
from py.builtin import print_

def pytest_addoption(parser):
    group = parser.getgroup("pylib")
    group.addoption('--tools-on-path',
           action="store_true", dest="toolsonpath", default=False,
           help=("discover tools on PATH instead of going through py.cmdline.")
    )

pytest_plugins = '_pytest'

def pytest_funcarg__linecomp(request):
    return LineComp()

def pytest_funcarg__LineMatcher(request):
    return LineMatcher

def pytest_funcarg__testdir(request):
    tmptestdir = TmpTestdir(request)
    return tmptestdir

rex_outcome = re.compile("(\d+) (\w+)")
class RunResult:
    def __init__(self, ret, outlines, errlines, duration):
        self.ret = ret
        self.outlines = outlines
        self.errlines = errlines
        self.stdout = LineMatcher(outlines)
        self.stderr = LineMatcher(errlines)
        self.duration = duration

    def parseoutcomes(self):
        for line in reversed(self.outlines):
            if 'seconds' in line:
                outcomes = rex_outcome.findall(line)
                if outcomes:
                    d = {}
                    for num, cat in outcomes:
                        d[cat] = int(num)
                    return d

class TmpTestdir:
    def __init__(self, request):
        self.request = request
        self._pytest = request.getfuncargvalue("_pytest")
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
        self.request.addfinalizer(self.finalize)

    def __repr__(self):
        return "<TmpTestdir %r>" % (self.tmpdir,)

    def Config(self, topdir=None):
        if topdir is None:
            topdir = self.tmpdir.dirpath()
        return pytestConfig(topdir=topdir)

    def finalize(self):
        for p in self._syspathremove:
            py.std.sys.path.remove(p)
        if hasattr(self, '_olddir'):
            self._olddir.chdir()
        # delete modules that have been loaded from tmpdir
        for name, mod in list(sys.modules.items()):
            if mod:
                fn = getattr(mod, '__file__', None)
                if fn and fn.startswith(str(self.tmpdir)):
                    del sys.modules[name]

    def getreportrecorder(self, obj):
        if hasattr(obj, 'config'):
            obj = obj.config
        if hasattr(obj, 'hook'):
            obj = obj.hook
        assert hasattr(obj, '_hookspecs'), obj
        reprec = ReportRecorder(obj)
        reprec.hookrecorder = self._pytest.gethookrecorder(obj)
        reprec.hook = reprec.hookrecorder.hook
        return reprec

    def chdir(self):
        old = self.tmpdir.chdir()
        if not hasattr(self, '_olddir'):
            self._olddir = old 

    def _makefile(self, ext, args, kwargs):
        items = list(kwargs.items())
        if args:
            source = "\n".join(map(str, args)) + "\n"
            basename = self.request.function.__name__
            items.insert(0, (basename, source))
        ret = None
        for name, value in items:
            p = self.tmpdir.join(name).new(ext=ext)
            source = str(py.code.Source(value)).lstrip()
            p.write(source.encode("utf-8"), "wb")
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

    def mkpydir(self, name):
        p = self.mkdir(name)
        p.ensure("__init__.py")
        return p

    def genitems(self, colitems):
        return list(self.session.genitems(colitems))

    def inline_genitems(self, *args):
        #config = self.parseconfig(*args)
        config = self.parseconfig(*args)
        session = config.initsession()
        rec = self.getreportrecorder(config)
        colitems = [config.getnode(arg) for arg in config.args]
        items = list(session.genitems(colitems))
        return items, rec 

    def runitem(self, source):
        # used from runner functional tests 
        item = self.getitem(source)
        # the test class where we are called from wants to provide the runner 
        testclassinstance = py.builtin._getimself(self.request.function)
        runner = testclassinstance.getrunner()
        return runner(item)

    def inline_runsource(self, source, *cmdlineargs):
        p = self.makepyfile(source)
        l = list(cmdlineargs) + [p]
        return self.inline_run(*l)

    def inline_runsource1(self, *args):
        args = list(args)
        source = args.pop()
        p = self.makepyfile(source)
        l = list(args) + [p]
        reprec = self.inline_run(*l)
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 1, reports 
        return reports[0]

    def inline_run(self, *args):
        args = ("-s", ) + args # otherwise FD leakage
        config = self.parseconfig(*args)
        config.pluginmanager.do_configure(config)
        session = config.initsession()
        reprec = self.getreportrecorder(config)
        colitems = config.getinitialnodes()
        session.main(colitems)
        config.pluginmanager.do_unconfigure(config)
        return reprec 

    def config_preparse(self):
        config = self.Config()
        for plugin in self.plugins:
            if isinstance(plugin, str):
                config.pluginmanager.import_plugin(plugin)
            else:
                if isinstance(plugin, dict):
                    plugin = PseudoPlugin(plugin) 
                if not config.pluginmanager.isregistered(plugin):
                    config.pluginmanager.register(plugin)
        return config

    def parseconfig(self, *args):
        if not args:
            args = (self.tmpdir,)
        config = self.config_preparse()
        args = list(args) + ["--basetemp=%s" % self.tmpdir.dirpath('basetemp')]
        config.parse(args)
        return config 

    def reparseconfig(self, args=None):
        """ this is used from tests that want to re-invoke parse(). """
        if not args:
            args = [self.tmpdir]
        from py._test import config 
        oldconfig = config.config_per_process # py.test.config
        try:
            c = config.config_per_process = py.test.config = pytestConfig()
            c.basetemp = oldconfig.mktemp("reparse", numbered=True)
            c.parse(args) 
            return c
        finally: 
            config.config_per_process = py.test.config = oldconfig 

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
        return self.config.getnode(path)

    def getmodulecol(self,  source, configargs=(), withinit=False):
        kw = {self.request.function.__name__: py.code.Source(source).strip()}
        path = self.makepyfile(**kw)
        if withinit:
            self.makepyfile(__init__ = "#")
        self.config = self.parseconfig(path, *configargs)
        self.session = self.config.initsession()
        #self.config.pluginmanager.do_configure(config=self.config)
        # XXX 
        self.config.pluginmanager.import_plugin("runner") 
        plugin = self.config.pluginmanager.getplugin("runner") 
        plugin.pytest_configure(config=self.config)

        return self.config.getnode(path)

    def popen(self, cmdargs, stdout, stderr, **kw):
        if not hasattr(py.std, 'subprocess'):
            py.test.skip("no subprocess module")
        env = os.environ.copy()
        env['PYTHONPATH'] = ":".join(filter(None, [
            str(os.getcwd()), env.get('PYTHONPATH', '')]))
        kw['env'] = env
        #print "env", env
        return py.std.subprocess.Popen(cmdargs, stdout=stdout, stderr=stderr, **kw)

    def run(self, *cmdargs):
        return self._run(*cmdargs)

    def _run(self, *cmdargs):
        cmdargs = [str(x) for x in cmdargs]
        p1 = self.tmpdir.join("stdout")
        p2 = self.tmpdir.join("stderr")
        print_("running", cmdargs, "curdir=", py.path.local())
        f1 = p1.open("wb")
        f2 = p2.open("wb")
        now = time.time()
        popen = self.popen(cmdargs, stdout=f1, stderr=f2, 
            close_fds=(sys.platform != "win32"))
        ret = popen.wait()
        f1.close()
        f2.close()
        out = p1.read("rb")
        out = getdecoded(out).splitlines()
        err = p2.read("rb")
        err = getdecoded(err).splitlines()
        def dump_lines(lines, fp):
            try:
                for line in lines:
                    py.builtin.print_(line, file=fp)
            except UnicodeEncodeError:
                print("couldn't print to %s because of encoding" % (fp,))
        dump_lines(out, sys.stdout)
        dump_lines(err, sys.stderr)
        return RunResult(ret, out, err, time.time()-now)

    def runpybin(self, scriptname, *args):
        fullargs = self._getpybinargs(scriptname) + args
        return self.run(*fullargs)

    def _getpybinargs(self, scriptname):
        if self.request.config.getvalue("toolsonpath"):
            script = py.path.local.sysfind(scriptname)
            assert script, "script %r not found" % scriptname
            return (script,)
        else:
            cmdlinename = scriptname.replace(".", "")
            assert hasattr(py.cmdline, cmdlinename), cmdlinename
            source = ("import sys;sys.path.insert(0,%r);"
                      "import py;py.cmdline.%s()" % 
                (str(py._pydir.dirpath()), cmdlinename))
            return (sys.executable, "-c", source,)

    def runpython(self, script):
        s = self._getsysprepend()
        if s:
            script.write(s + "\n" + script.read())
        return self.run(sys.executable, script)

    def _getsysprepend(self):
        if not self.request.config.getvalue("toolsonpath"):
            s = "import sys;sys.path.insert(0,%r);" % str(py._pydir.dirpath())
        else:
            s = ""
        return s

    def runpython_c(self, command):
        command = self._getsysprepend() + command
        return self.run(py.std.sys.executable, "-c", command)

    def runpytest(self, *args):
        p = py.path.local.make_numbered_dir(prefix="runpytest-", 
            keep=None, rootdir=self.tmpdir)
        args = ('--basetemp=%s' % p, ) + args 
        plugins = [x for x in self.plugins if isinstance(x, str)]
        if plugins:
            args = ('-p', plugins[0]) + args
        return self.runpybin("py.test", *args)

    def spawn_pytest(self, string, expect_timeout=10.0):
        pexpect = py.test.importorskip("pexpect", "2.4")
        if not self.request.config.getvalue("toolsonpath"):
            py.test.skip("need --tools-on-path to run py.test script")
        basetemp = self.tmpdir.mkdir("pexpect")
        invoke = self._getpybinargs("py.test")[0]
        cmd = "%s --basetemp=%s %s" % (invoke, basetemp, string)
        child = pexpect.spawn(cmd, logfile=basetemp.join("spawn.out").open("w"))
        child.timeout = expect_timeout
        return child

def getdecoded(out):
        try:
            return out.decode("utf-8")
        except UnicodeDecodeError:
            return "INTERNAL not-utf8-decodeable, truncated string:\n%s" % (
                    py.io.saferepr(out),)

class PseudoPlugin:
    def __init__(self, vars):
        self.__dict__.update(vars) 

class ReportRecorder(object):
    def __init__(self, hook):
        self.hook = hook
        self.registry = hook._registry
        self.registry.register(self)

    def getcall(self, name):
        return self.hookrecorder.getcall(name)

    def popcall(self, name):
        return self.hookrecorder.popcall(name)

    def getcalls(self, names):
        """ return list of ParsedCall instances matching the given eventname. """
        return self.hookrecorder.getcalls(names)

    # functionality for test reports 

    def getreports(self, names="pytest_runtest_logreport pytest_collectreport"):
        return [x.report for x in self.getcalls(names)]

    def matchreport(self, inamepart="", names="pytest_runtest_logreport pytest_collectreport"):
        """ return a testreport whose dotted import path matches """
        l = []
        for rep in self.getreports(names=names):
            colitem = rep.getnode()
            if not inamepart or inamepart in colitem.listnames():
                l.append(rep)
        if not l:
            raise ValueError("could not find test report matching %r: no test reports at all!" %
                (inamepart,))
        if len(l) > 1:
            raise ValueError("found more than one testreport matching %r: %s" %(
                             inamepart, l))
        return l[0]

    def getfailures(self, names='pytest_runtest_logreport pytest_collectreport'):
        return [rep for rep in self.getreports(names) if rep.failed]

    def getfailedcollections(self):
        return self.getfailures('pytest_collectreport')

    def listoutcomes(self):
        passed = []
        skipped = []
        failed = []
        for rep in self.getreports("pytest_runtest_logreport"):
            if rep.passed: 
                if rep.when == "call": 
                    passed.append(rep) 
            elif rep.skipped: 
                skipped.append(rep) 
            elif rep.failed:
                failed.append(rep) 
        return passed, skipped, failed 

    def countoutcomes(self):
        return [len(x) for x in self.listoutcomes()]

    def assertoutcome(self, passed=0, skipped=0, failed=0):
        realpassed, realskipped, realfailed = self.listoutcomes()
        assert passed == len(realpassed)
        assert skipped == len(realskipped)
        assert failed == len(realfailed)

    def clear(self):
        self.hookrecorder.calls[:] = []

    def unregister(self):
        self.registry.unregister(self)
        self.hookrecorder.finish_recording()

class LineComp:
    def __init__(self):
        self.stringio = py.io.TextIO()

    def assert_contains_lines(self, lines2):
        """ assert that lines2 are contained (linearly) in lines1. 
            return a list of extralines found.
        """
        __tracebackhide__ = True
        val = self.stringio.getvalue()
        self.stringio.truncate(0)
        self.stringio.seek(0)
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
        lines1 = self.lines[:]
        nextline = None
        extralines = []
        __tracebackhide__ = True
        for line in lines2:
            nomatchprinted = False
            while lines1:
                nextline = lines1.pop(0)
                if line == nextline:
                    print_("exact match:", repr(line))
                    break 
                elif fnmatch(nextline, line):
                    print_("fnmatch:", repr(line))
                    print_("   with:", repr(nextline))
                    break
                else:
                    if not nomatchprinted:
                        print_("nomatch:", repr(line))
                        nomatchprinted = True
                    print_("    and:", repr(nextline))
                extralines.append(nextline)
            else:
                assert line == nextline
