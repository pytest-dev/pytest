"""
cleanup gateways that were instantiated during a test function run. 
"""
import py

def pytest_configure(config):
    config.pluginmanager.register(Execnetcleanup())

class Execnetcleanup:
    _gateways = None
    def __init__(self, debug=False):
        self._debug = debug 

    def pyexecnet_gateway_init(self, gateway):
        if self._gateways is not None:
            self._gateways.append(gateway)
        
    def pyexecnet_gateway_exit(self, gateway):
        if self._gateways is not None:
            self._gateways.remove(gateway)

    def pytest_sessionstart(self, session):
        self._gateways = []

    def pytest_sessionfinish(self, session, exitstatus, excrepr=None):
        l = []
        for gw in self._gateways:
            gw.exit()
            l.append(gw)
        #for gw in l:
        #    gw.join()
        
    def pytest_pyfunc_call(self, __call__, pyfuncitem):
        if self._gateways is not None:
            gateways = self._gateways[:]
            res = __call__.execute(firstresult=True)
            while len(self._gateways) > len(gateways):
                self._gateways[-1].exit()
            return res
   
@py.test.mark.xfail("clarify plugin registration/unregistration")
def test_execnetplugin(testdir):
    p = ExecnetcleanupPlugin()
    testdir.plugins.append(p)
    testdir.inline_runsource("""
        import py
        import sys
        def test_hello():
            sys._gw = py.execnet.PopenGateway()
    """, "-s", "--debug")
    assert not p._gateways 
    assert py.std.sys._gw
    py.test.raises(KeyError, "py.std.sys._gw.exit()") # already closed 
    
