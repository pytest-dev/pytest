"""
cleanup execnet gateways during test function runs.
"""
import py

pytest_plugins = "xfail"

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

    def pytest_sessionfinish(self, session, exitstatus):
        l = []
        for gw in self._gateways:
            gw.exit()
            l.append(gw)
        #for gw in l:
        #    gw.join()
        
    def pytest_pyfunc_call(self, __multicall__, pyfuncitem):
        if self._gateways is not None:
            gateways = self._gateways[:]
            res = __multicall__.execute()
            while len(self._gateways) > len(gateways):
                self._gateways[-1].exit()
            return res
