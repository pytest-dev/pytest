import py
import subprocess
import os

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
        args = [self._cmd("python"), self._cmd("py.test")] + list(args)
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
