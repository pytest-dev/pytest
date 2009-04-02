import py

class ExecnetcleanupPlugin:
    _gateways = None
    _debug = None

    def pytest_configure(self, config):
        self._debug = config.option.debug

    def trace(self, msg, *args):
        if self._debug:
            print "[execnetcleanup %0x] %s %s" %(id(self), msg, args)
        
    def pyevent__gateway_init(self, gateway):
        self.trace("init", gateway)
        if self._gateways is not None:
            self._gateways.append(gateway)
        
    def pyevent__gateway_exit(self, gateway):
        self.trace("exit", gateway)
        if self._gateways is not None:
            self._gateways.remove(gateway)

    def pyevent__testrunstart(self, event):
        self.trace("testrunstart", event)
        self._gateways = []

    def pyevent__testrunfinish(self, event):
        self.trace("testrunfinish", event)
        l = []
        for gw in self._gateways:
            gw.exit()
            l.append(gw)
        #for gw in l:
        #    gw.join()
   
def test_generic(plugintester):
    plugintester.apicheck(ExecnetcleanupPlugin)

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
    
