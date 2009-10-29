import py

pytest_plugins = '_pytest doctest pytester'.split()


rsyncdirs = ['conftest.py', 'bin', 'py', 'doc', 'testing']
try:
    import execnet
except ImportError:
    pass
else:
    rsyncdirs.append(str(py.path.local(execnet.__file__).dirpath()))

import py
def pytest_addoption(parser):
    group = parser.getgroup("pylib", "py lib testing options")
    group.addoption('--sshhost', 
           action="store", dest="sshhost", default=None,
           help=("ssh xspec for ssh functional tests. "))
    group.addoption('--gx', 
           action="append", dest="gspecs", default=None,
           help=("add a global test environment, XSpec-syntax. "))
    group.addoption('--runslowtests',
           action="store_true", dest="runslowtests", default=False,
           help=("run slow tests"))

def pytest_funcarg__specssh(request):
    return getspecssh(request.config)
def getgspecs(config=None):
    if config is None:
        config = py.test.config
    return [execnet.XSpec(spec)
                for spec in config.getvalueorskip("gspecs")]


# configuration information for tests 
def getgspecs(config=None):
    if config is None:
        config = py.test.config
    return [execnet.XSpec(spec) 
                for spec in config.getvalueorskip("gspecs")]

def getspecssh(config=None):
    xspecs = getgspecs(config)
    for spec in xspecs:
        if spec.ssh:
            if not py.path.local.sysfind("ssh"):
                py.test.skip("command not found: ssh")
            return spec
    py.test.skip("need '--gx ssh=...'")

def getsocketspec(config=None):
    xspecs = getgspecs(config)
    for spec in xspecs:
        if spec.socket:
            return spec
    py.test.skip("need '--gx socket=...'")


def pytest_generate_tests(metafunc):
    multi = getattr(metafunc.function, 'multi', None)
    if multi is None:
        return
    assert len(multi.kwargs) == 1
    for name, l in multi.kwargs.items():
        for val in l:
            metafunc.addcall(funcargs={name: val})
