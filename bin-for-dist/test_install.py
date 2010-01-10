import py
import subprocess
import os, sys

execnet = py.test.importorskip("execnet")


#
# experimental funcargs for venv/install-tests
#

pytest_plugins = 'pytest_pytester',

def pytest_funcarg__venv(request):
    p = request.config.mktemp(request.function.__name__, numbered=True)
    venv = VirtualEnv(str(p)) 
    return venv 
   
def pytest_funcarg__py_setup(request):
    testdir = request.getfuncargvalue('testdir')
    rootdir = py.path.local(py.__file__).dirpath().dirpath()
    setup = rootdir.join('setup.py')
    if not setup.check():
        py.test.skip("not found: %r" % setup)
    return SetupBuilder(setup, testdir.tmpdir)

class SetupBuilder:
    def __init__(self, setup_path, tmpdir):
        self.setup_path = setup_path
        self.tmpdir = tmpdir
        assert setup_path.check()

    def make_sdist(self, destdir=None):
        temp = self.tmpdir.mkdir('dist')
        args = ['python', 'setup.py', 'sdist', '--dist-dir', str(temp)]
        old = self.setup_path.dirpath().chdir()
        try:
            subcall(args)
        finally:
            old.chdir()
        l = temp.listdir('py-*')
        assert len(l) == 1
        sdist = l[0]
        if destdir is None:
            destdir = self.setup_path.dirpath('build')
            assert destdir.check()
        else:
            destdir = py.path.local(destdir)
        target = destdir.join(sdist.basename)
        sdist.copy(target)
        return target 

def subcall(args):
    if hasattr(subprocess, 'check_call'):
        subprocess.check_call(args)
    else:
        subprocess.call(args)
# code taken from Ronny Pfannenschmidt's virtualenvmanager 

class VirtualEnv(object):
    def __init__(self, path):
        #XXX: supply the python executable
        self.path = path

    def __repr__(self):
        return "<VirtualEnv at %r>" %(self.path)

    def _cmd(self, name):
        if sys.platform == "win32":
            return os.path.join(self.path, 'Scripts', name)
        else:
            return os.path.join(self.path, 'bin', name)

    def ensure(self):
        if not os.path.exists(self._cmd('python')):
            self.create()

    def create(self, sitepackages=False):
        args = ['virtualenv', self.path]
        if not sitepackages:
            args.append('--no-site-packages')
        subcall(args)

    def makegateway(self):
        python = self._cmd('python')
        return execnet.makegateway("popen//python=%s" %(python,))

    def pcall(self, cmd, *args, **kw):
        self.ensure()
        return subprocess.call([
                self._cmd(cmd)
            ] + list(args),
            **kw)

    def pytest_getouterr(self, *args):
        self.ensure()
        args = [self._cmd("py.test")] + list(args)
        popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = popen.communicate()
        return out

    def setup_develop(self):
        self.ensure()
        return self.pcall("python", "setup.py", "develop")

    def easy_install(self, *packages, **kw):
        args = []
        if 'index' in kw:
            index = kw['index']
            if isinstance(index, (list, tuple)):
                for i in index:
                    args.extend(['-i', i])
            else:
                args.extend(['-i', index])

        args.extend(packages)
        self.pcall('easy_install', *args)


def test_make_sdist_and_run_it(py_setup, venv):
    sdist = py_setup.make_sdist(venv.path)
    venv.easy_install(str(sdist)) 
    gw = venv.makegateway()
    ch = gw.remote_exec("import py ; channel.send(py.__version__)")
    version = ch.receive()
    assert version == py.__version__

def test_plugin_setuptools_entry_point_integration(py_setup, venv, tmpdir):
    sdist = py_setup.make_sdist(venv.path)
    venv.easy_install(str(sdist)) 
    # create a sample plugin
    basedir = tmpdir.mkdir("testplugin")
    basedir.join("setup.py").write("""if 1:
        from setuptools import setup
        setup(name="testplugin",
            entry_points = {'pytest11': ['testplugin=tp1']},
            py_modules = ['tp1'],
        )
    """)
    basedir.join("tp1.py").write(py.code.Source("""
        def pytest_addoption(parser):
            parser.addoption("--testpluginopt", action="store_true")
    """))
    basedir.chdir()
    print ("created sample plugin in %s" %basedir)
    venv.setup_develop()
    out = venv.pytest_getouterr("-h")
    assert "testpluginopt" in out

def test_cmdline_entrypoints(monkeypatch):
    monkeypatch.syspath_prepend(py.path.local(__file__).dirpath().dirpath())
    from setup import cmdline_entrypoints
    versioned_scripts = ['py.test', 'py.which']
    unversioned_scripts = versioned_scripts + [ 'py.cleanup', 
        'py.convert_unittest', 'py.countloc', 'py.lookup', 'py.svnwcrevert']
    for ver in [(2,4,0), (2,5,0), (2,6,0), (2,7,0), (3,0,1), (3,1,1)]:
        for platform in ('posix', 'win32'):
            points = cmdline_entrypoints(ver, "posix", 'python')
            for script in versioned_scripts:
                script_ver = script + "-%s.%s" % ver[:2]
                assert script_ver in points
            for script in unversioned_scripts:
                assert script in points
    points = cmdline_entrypoints((2,5,1), "java1.6.123", 'jython')
    for script in versioned_scripts:
        expected = "%s-jython" % script
        assert expected in points
    for script in unversioned_scripts:
        assert script not in points

    points = cmdline_entrypoints((2,5,1), "xyz", 'pypy-c-XYZ')
    for script in versioned_scripts:
        expected = "%s-pypy-c-XYZ" % script
        assert expected in points
    for script in unversioned_scripts:
        assert script in points

def test_slave_popen_needs_no_pylib(testdir, venv):
    venv.ensure()
    #xxx execnet optimizes popen
    #ch = venv.makegateway().remote_exec("import execnet")
    #py.test.raises(ch.RemoteError, ch.waitclose)
    python = venv._cmd("python")
    p = testdir.makepyfile("""
        import py
        def test_func():
            pass
     """)
    result = testdir.runpytest(p, '--rsyncdir=%s' % str(p), 
            '--dist=each', '--tx=popen//python=%s' % python)
    result.stdout.fnmatch_lines([
        "*1 passed*"
    ])

def test_slave_needs_no_execnet(testdir, specssh):
    gw = execnet.makegateway(specssh)
    ch = gw.remote_exec("""
        import os, subprocess
        subprocess.call(["virtualenv", "--no-site-packages", "subdir"])
        channel.send(os.path.join(os.path.abspath("subdir"), 'bin', 'python'))
        channel.send(os.path.join(os.path.abspath("subdir")))
    """)
    try:
        path = ch.receive()
        chdir = ch.receive()
    except ch.RemoteError:
        e = sys.exc_info()[1]
        py.test.skip("could not prepare ssh slave:%s" % str(e))
    gw.exit()
    newspec = "%s//python=%s//chdir=%s" % (specssh, path, chdir)
    gw = execnet.makegateway(newspec)
    ch = gw.remote_exec("import execnet")
    py.test.raises(ch.RemoteError, ch.waitclose)
    gw.exit()
    
    p = testdir.makepyfile("""
        import py
        def test_func():
            pass
     """)
    result = testdir.runpytest(p, '--rsyncdir=%s' % str(p), 
            '--dist=each', '--tx=%s' % newspec)
    result.stdout.fnmatch_lines([
        "*1 passed*"
    ])
