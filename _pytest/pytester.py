""" (disabled by default) support for testing pytest and pytest plugins. """

import py, pytest
import sys, os
import codecs
import re
import time
from fnmatch import fnmatch
from _pytest.main import Session, EXIT_OK
from py.builtin import print_
from _pytest.core import HookRelay


def get_public_names(l):
    """Only return names from iterator l without a leading underscore."""
    return [x for x in l if x[0] != "_"]


def pytest_addoption(parser):
    group = parser.getgroup("pylib")
    group.addoption('--no-tools-on-path',
           action="store_true", dest="notoolsonpath", default=False,
           help=("discover tools on PATH instead of going through py.cmdline.")
    )

def pytest_configure(config):
    # This might be called multiple times. Only take the first.
    global _pytest_fullpath
    try:
        _pytest_fullpath
    except NameError:
        _pytest_fullpath = os.path.abspath(pytest.__file__.rstrip("oc"))
        _pytest_fullpath = _pytest_fullpath.replace("$py.class", ".py")

def pytest_funcarg___pytest(request):
    return PytestArg(request)

class PytestArg:
    def __init__(self, request):
        self.request = request

    def gethookrecorder(self, hook):
        hookrecorder = HookRecorder(hook._pm)
        hookrecorder.start_recording(hook._hookspecs)
        self.request.addfinalizer(hookrecorder.finish_recording)
        return hookrecorder

class ParsedCall:
    def __init__(self, name, locals):
        assert '_name' not in locals
        self.__dict__.update(locals)
        self.__dict__.pop('self')
        self._name = name

    def __repr__(self):
        d = self.__dict__.copy()
        del d['_name']
        return "<ParsedCall %r(**%r)>" %(self._name, d)

class HookRecorder:
    def __init__(self, pluginmanager):
        self._pluginmanager = pluginmanager
        self.calls = []
        self._recorders = {}

    def start_recording(self, hookspecs):
        if not isinstance(hookspecs, (list, tuple)):
            hookspecs = [hookspecs]
        for hookspec in hookspecs:
            assert hookspec not in self._recorders
            class RecordCalls:
                _recorder = self
            for name, method in vars(hookspec).items():
                if name[0] != "_":
                    setattr(RecordCalls, name, self._makecallparser(method))
            recorder = RecordCalls()
            self._recorders[hookspec] = recorder
            self._pluginmanager.register(recorder)
        self.hook = HookRelay(hookspecs, pm=self._pluginmanager,
            prefix="pytest_")

    def finish_recording(self):
        for recorder in self._recorders.values():
            if self._pluginmanager.isregistered(recorder):
                self._pluginmanager.unregister(recorder)
        self._recorders.clear()

    def _makecallparser(self, method):
        name = method.__name__
        args, varargs, varkw, default = py.std.inspect.getargspec(method)
        if not args or args[0] != "self":
            args.insert(0, 'self')
        fspec = py.std.inspect.formatargspec(args, varargs, varkw, default)
        # we use exec because we want to have early type
        # errors on wrong input arguments, using
        # *args/**kwargs delays this and gives errors
        # elsewhere
        exec (py.code.compile("""
            def %(name)s%(fspec)s:
                        self._recorder.calls.append(
                            ParsedCall(%(name)r, locals()))
        """ % locals()))
        return locals()[name]

    def getcalls(self, names):
        if isinstance(names, str):
            names = names.split()
        for name in names:
            for cls in self._recorders:
                if name in vars(cls):
                    break
            else:
                raise ValueError("callname %r not found in %r" %(
                name, self._recorders.keys()))
        l = []
        for call in self.calls:
            if call._name in names:
                l.append(call)
        return l

    def contains(self, entries):
        __tracebackhide__ = True
        i = 0
        entries = list(entries)
        backlocals = py.std.sys._getframe(1).f_locals
        while entries:
            name, check = entries.pop(0)
            for ind, call in enumerate(self.calls[i:]):
                if call._name == name:
                    print_("NAMEMATCH", name, call)
                    if eval(check, backlocals, call.__dict__):
                        print_("CHECKERMATCH", repr(check), "->", call)
                    else:
                        print_("NOCHECKERMATCH", repr(check), "-", call)
                        continue
                    i += ind + 1
                    break
                print_("NONAMEMATCH", name, "with", call)
            else:
                pytest.fail("could not find %r check %r" % (name, check))

    def popcall(self, name):
        __tracebackhide__ = True
        for i, call in enumerate(self.calls):
            if call._name == name:
                del self.calls[i]
                return call
        lines = ["could not find call %r, in:" % (name,)]
        lines.extend(["  %s" % str(x) for x in self.calls])
        pytest.fail("\n".join(lines))

    def getcall(self, name):
        l = self.getcalls(name)
        assert len(l) == 1, (name, l)
        return l[0]


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
        self.Config = request.config.__class__
        self._pytest = request.getfuncargvalue("_pytest")
        # XXX remove duplication with tmpdir plugin
        basetmp = request.config._tmpdirhandler.ensuretemp("testdir")
        name = request.function.__name__
        for i in range(100):
            try:
                tmpdir = basetmp.mkdir(name + str(i))
            except py.error.EEXIST:
                continue
            break
        self.tmpdir = tmpdir
        self.plugins = []
        self._syspathremove = []
        self.chdir() # always chdir
        self.request.addfinalizer(self.finalize)

    def __repr__(self):
        return "<TmpTestdir %r>" % (self.tmpdir,)

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
            source = py.builtin._totext("\n").join(
                map(py.builtin._totext, args)) + py.builtin._totext("\n")
            basename = self.request.function.__name__
            items.insert(0, (basename, source))
        ret = None
        for name, value in items:
            p = self.tmpdir.join(name).new(ext=ext)
            source = py.builtin._totext(py.code.Source(value)).strip()
            content = source.encode("utf-8") # + "\n"
            #content = content.rstrip() + "\n"
            p.write(content, "wb")
            if ret is None:
                ret = p
        return ret


    def makefile(self, ext, *args, **kwargs):
        return self._makefile(ext, args, kwargs)

    def makeconftest(self, source):
        return self.makepyfile(conftest=source)

    def makeini(self, source):
        return self.makefile('.ini', tox=source)

    def getinicfg(self, source):
        p = self.makeini(source)
        return py.iniconfig.IniConfig(p)['pytest']

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

    Session = Session
    def getnode(self, config, arg):
        session = Session(config)
        assert '::' not in str(arg)
        p = py.path.local(arg)
        x = session.fspath.bestrelpath(p)
        config.hook.pytest_sessionstart(session=session)
        res = session.perform_collect([x], genitems=False)[0]
        config.hook.pytest_sessionfinish(session=session, exitstatus=EXIT_OK)
        return res

    def getpathnode(self, path):
        config = self.parseconfigure(path)
        session = Session(config)
        x = session.fspath.bestrelpath(path)
        config.hook.pytest_sessionstart(session=session)
        res = session.perform_collect([x], genitems=False)[0]
        config.hook.pytest_sessionfinish(session=session, exitstatus=EXIT_OK)
        return res

    def genitems(self, colitems):
        session = colitems[0].session
        result = []
        for colitem in colitems:
            result.extend(session.genitems(colitem))
        return result

    def runitem(self, source):
        # used from runner functional tests
        item = self.getitem(source)
        # the test class where we are called from wants to provide the runner
        testclassinstance = self.request.instance
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
        assert len(reports) == 3, reports # setup/call/teardown
        return reports[1]

    def inline_genitems(self, *args):
        return self.inprocess_run(list(args) + ['--collectonly'])

    def inline_run(self, *args):
        items, rec = self.inprocess_run(args)
        return rec

    def inprocess_run(self, args, plugins=None):
        rec = []
        items = []
        class Collect:
            def pytest_configure(x, config):
                rec.append(self.getreportrecorder(config))
            def pytest_itemcollected(self, item):
                items.append(item)
        if not plugins:
            plugins = []
        plugins.append(Collect())
        ret = pytest.main(list(args), plugins=plugins)
        reprec = rec[0]
        reprec.ret = ret
        assert len(rec) == 1
        return items, reprec

    def parseconfig(self, *args):
        args = [str(x) for x in args]
        for x in args:
            if str(x).startswith('--basetemp'):
                break
        else:
            args.append("--basetemp=%s" % self.tmpdir.dirpath('basetemp'))
        import _pytest.config
        config = _pytest.config._prepareconfig(args, self.plugins)
        # we don't know what the test will do with this half-setup config
        # object and thus we make sure it gets unconfigured properly in any
        # case (otherwise capturing could still be active, for example)
        def ensure_unconfigure():
            if hasattr(config.pluginmanager, "_config"):
                config.pluginmanager.do_unconfigure(config)
            config.pluginmanager.ensure_shutdown()

        self.request.addfinalizer(ensure_unconfigure)
        return config

    def parseconfigure(self, *args):
        config = self.parseconfig(*args)
        config.do_configure()
        self.request.addfinalizer(lambda:
        config.do_unconfigure())
        return config

    def getitem(self,  source, funcname="test_func"):
        items = self.getitems(source)
        for item in items:
            if item.name == funcname:
                return item
        assert 0, "%r item not found in module:\n%s\nitems: %s" %(
                  funcname, source, items)

    def getitems(self,  source):
        modcol = self.getmodulecol(source)
        return self.genitems([modcol])

    def getmodulecol(self,  source, configargs=(), withinit=False):
        kw = {self.request.function.__name__: py.code.Source(source).strip()}
        path = self.makepyfile(**kw)
        if withinit:
            self.makepyfile(__init__ = "#")
        self.config = config = self.parseconfigure(path, *configargs)
        node = self.getnode(config, path)
        return node

    def collect_by_name(self, modcol, name):
        for colitem in modcol._memocollect():
            if colitem.name == name:
                return colitem

    def popen(self, cmdargs, stdout, stderr, **kw):
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join(filter(None, [
            str(os.getcwd()), env.get('PYTHONPATH', '')]))
        kw['env'] = env
        #print "env", env
        return py.std.subprocess.Popen(cmdargs,
                                       stdout=stdout, stderr=stderr, **kw)

    def run(self, *cmdargs):
        return self._run(*cmdargs)

    def _run(self, *cmdargs):
        cmdargs = [str(x) for x in cmdargs]
        p1 = self.tmpdir.join("stdout")
        p2 = self.tmpdir.join("stderr")
        print_("running", cmdargs, "curdir=", py.path.local())
        f1 = codecs.open(str(p1), "w", encoding="utf8")
        f2 = codecs.open(str(p2), "w", encoding="utf8")
        try:
            now = time.time()
            popen = self.popen(cmdargs, stdout=f1, stderr=f2,
                close_fds=(sys.platform != "win32"))
            ret = popen.wait()
        finally:
            f1.close()
            f2.close()
        f1 = codecs.open(str(p1), "r", encoding="utf8")
        f2 = codecs.open(str(p2), "r", encoding="utf8")
        try:
            out = f1.read().splitlines()
            err = f2.read().splitlines()
        finally:
            f1.close()
            f2.close()
        self._dump_lines(out, sys.stdout)
        self._dump_lines(err, sys.stderr)
        return RunResult(ret, out, err, time.time()-now)

    def _dump_lines(self, lines, fp):
        try:
            for line in lines:
                py.builtin.print_(line, file=fp)
        except UnicodeEncodeError:
            print("couldn't print to %s because of encoding" % (fp,))

    def runpybin(self, scriptname, *args):
        fullargs = self._getpybinargs(scriptname) + args
        return self.run(*fullargs)

    def _getpybinargs(self, scriptname):
        if not self.request.config.getvalue("notoolsonpath"):
            # XXX we rely on script referring to the correct environment
            # we cannot use "(py.std.sys.executable,script)"
            # because on windows the script is e.g. a py.test.exe
            return (py.std.sys.executable, _pytest_fullpath,) # noqa
        else:
            pytest.skip("cannot run %r with --no-tools-on-path" % scriptname)

    def runpython(self, script, prepend=True):
        if prepend:
            s = self._getsysprepend()
            if s:
                script.write(s + "\n" + script.read())
        return self.run(sys.executable, script)

    def _getsysprepend(self):
        if self.request.config.getvalue("notoolsonpath"):
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
        #for x in args:
        #    if '--confcutdir' in str(x):
        #        break
        #else:
        #    pass
        #    args = ('--confcutdir=.',) + args
        plugins = [x for x in self.plugins if isinstance(x, str)]
        if plugins:
            args = ('-p', plugins[0]) + args
        return self.runpybin("py.test", *args)

    def spawn_pytest(self, string, expect_timeout=10.0):
        if self.request.config.getvalue("notoolsonpath"):
            pytest.skip("--no-tools-on-path prevents running pexpect-spawn tests")
        basetemp = self.tmpdir.mkdir("pexpect")
        invoke = " ".join(map(str, self._getpybinargs("py.test")))
        cmd = "%s --basetemp=%s %s" % (invoke, basetemp, string)
        return self.spawn(cmd, expect_timeout=expect_timeout)

    def spawn(self, cmd, expect_timeout=10.0):
        pexpect = pytest.importorskip("pexpect", "3.0")
        if hasattr(sys, 'pypy_version_info') and '64' in py.std.platform.machine():
            pytest.skip("pypy-64 bit not supported")
        if sys.platform == "darwin":
            pytest.xfail("pexpect does not work reliably on darwin?!")
        if sys.platform.startswith("freebsd"):
            pytest.xfail("pexpect does not work reliably on freebsd")
        logfile = self.tmpdir.join("spawn.out").open("wb")
        child = pexpect.spawn(cmd, logfile=logfile)
        self.request.addfinalizer(logfile.close)
        child.timeout = expect_timeout
        return child

def getdecoded(out):
        try:
            return out.decode("utf-8")
        except UnicodeDecodeError:
            return "INTERNAL not-utf8-decodeable, truncated string:\n%s" % (
                    py.io.saferepr(out),)

class ReportRecorder(object):
    def __init__(self, hook):
        self.hook = hook
        self.pluginmanager = hook._pm
        self.pluginmanager.register(self)

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

    def matchreport(self, inamepart="",
        names="pytest_runtest_logreport pytest_collectreport", when=None):
        """ return a testreport whose dotted import path matches """
        l = []
        for rep in self.getreports(names=names):
            try:
                if not when and rep.when != "call" and rep.passed:
                    # setup/teardown passing reports - let's ignore those
                    continue
            except AttributeError:
                pass
            if when and getattr(rep, 'when', None) != when:
                continue
            if not inamepart or inamepart in rep.nodeid.split("::"):
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
        for rep in self.getreports(
            "pytest_collectreport pytest_runtest_logreport"):
            if rep.passed:
                if getattr(rep, "when", None) == "call":
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
        self.pluginmanager.unregister(self)
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

    def _getlines(self, lines2):
        if isinstance(lines2, str):
            lines2 = py.code.Source(lines2)
        if isinstance(lines2, py.code.Source):
            lines2 = lines2.strip().lines
        return lines2

    def fnmatch_lines_random(self, lines2):
        lines2 = self._getlines(lines2)
        for line in lines2:
            for x in self.lines:
                if line == x or fnmatch(x, line):
                    print_("matched: ", repr(line))
                    break
            else:
                raise ValueError("line %r not found in output" % line)

    def get_lines_after(self, fnline):
        for i, line in enumerate(self.lines):
            if fnline == line or fnmatch(line, fnline):
                return self.lines[i+1:]
        raise ValueError("line %r not found in output" % fnline)

    def fnmatch_lines(self, lines2):
        def show(arg1, arg2):
            py.builtin.print_(arg1, arg2, file=py.std.sys.stderr)
        lines2 = self._getlines(lines2)
        lines1 = self.lines[:]
        nextline = None
        extralines = []
        __tracebackhide__ = True
        for line in lines2:
            nomatchprinted = False
            while lines1:
                nextline = lines1.pop(0)
                if line == nextline:
                    show("exact match:", repr(line))
                    break
                elif fnmatch(nextline, line):
                    show("fnmatch:", repr(line))
                    show("   with:", repr(nextline))
                    break
                else:
                    if not nomatchprinted:
                        show("nomatch:", repr(line))
                        nomatchprinted = True
                    show("    and:", repr(nextline))
                extralines.append(nextline)
            else:
                pytest.fail("remains unmatched: %r, see stderr" % (line,))
