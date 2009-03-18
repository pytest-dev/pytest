import py
pytest_plugins = "pytester"

class TestExecnetEvents:
    def test_popengateway(self, eventrecorder):
        gw = py.execnet.PopenGateway()
        event = eventrecorder.popevent("gateway_init")
        assert event.args[0] == gw 
        gw.exit()
        event = eventrecorder.popevent("gateway_exit")
        assert event.args[0] == gw 
