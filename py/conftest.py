dist_rsync_roots = ['.'] # XXX

pytest_plugins = 'pytest_doctest', 'pytest_pytester', 'pytest_restdoc'

import py
class PylibTestPlugin:
    def pytest_addoption(self, parser):
        group = parser.addgroup("pylib", "py lib testing options")
        group.addoption('--sshhost', 
               action="store", dest="sshhost", default=None,
               help=("target to run tests requiring ssh, e.g. "
                     "user@codespeak.net"))
        group.addoption('--runslowtests',
               action="store_true", dest="runslowtests", default=False,
               help="run slow tests")

ConftestPlugin = PylibTestPlugin

