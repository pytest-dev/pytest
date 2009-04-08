pytest_plugins = '_pytest doctest pytester'.split()

rsyncdirs = ['../doc']
rsyncignore = ['c-extension/greenlet/build']

import py
class PylibTestconfigPlugin:
    def pytest_funcarg__specssh(self, pyfuncitem):
        return getspecssh(pyfuncitem.config)
    def pytest_funcarg__specsocket(self, pyfuncitem):
        return getsocketspec(pyfuncitem.config)

    def pytest_addoption(self, parser):
        group = parser.addgroup("pylib", "py lib testing options")
        group.addoption('--sshhost', 
               action="store", dest="sshhost", default=None,
               help=("ssh xspec for ssh functional tests. "))
        group.addoption('--gx', 
               action="append", dest="gspecs", default=None,
               help=("add a global test environment, XSpec-syntax. "))
        group.addoption('--runslowtests',
               action="store_true", dest="runslowtests", default=False,
               help=("run slow tests"))

ConftestPlugin = PylibTestconfigPlugin

# configuration information for tests 
def getgspecs(config=None):
    if config is None:
        config = py.test.config
    return [py.execnet.XSpec(spec) 
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
