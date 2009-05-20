"""
cleanup gateways that were instantiated during a test function run. 
"""
import py

def pytest_configure(config):
    debug = config.option.debug
    config.pluginmanager.register(Execnetcleanup(debug))

class Execnetcleanup:
    _gateways = None
    def __init__(self, debug=False):
        self._debug = debug 

    def trace(self, msg, *args):
        if self._debug:
            print "[execnetcleanup %0x] %s %s" %(id(self), msg, args)
        
    def pyexecnet_gateway_init(self, gateway):
        self.trace("init", gateway)
        if self._gateways is not None:
            self._gateways.append(gateway)
        
    def pyexecnet_gateway_exit(self, gateway):
        self.trace("exit", gateway)
        if self._gateways is not None:
            self._gateways.remove(gateway)

    def pytest_testrunstart(self):
        self.trace("testrunstart")
        self._gateways = []

    def pytest_testrunfinish(self, exitstatus, excrepr=None):
        self.trace("testrunfinish", exitstatus)
        l = []
        for gw in self._gateways:
            gw.exit()
            l.append(gw)
        #for gw in l:
        #    gw.join()
        #
    def pytest_pyfunc_call(self, __call__, pyfuncitem, args, kwargs):
        if self._gateways is not None:
            gateways = self._gateways[:]
            res = __call__.execute(firstresult=True)
            while len(self._gateways) > len(gateways):
                self._gateways[-1].exit()
            return res
   
def test_generic(plugintester):
    plugintester.hookcheck(cls=Execnetcleanup)
    plugintester.hookcheck()

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
    
