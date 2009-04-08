import py
pytest_plugins = "pytester"
from py.__.execnet.gateway import ExecnetAPI

class TestExecnetEvents:
    def test_popengateway_events(self, _pytest):
        rec = _pytest.getcallrecorder(ExecnetAPI)
        gw = py.execnet.PopenGateway()
        call = rec.popcall("pyexecnet_gateway_init") 
        assert call.gateway == gw
        gw.exit()
        call = rec.popcall("pyexecnet_gateway_exit")
        assert call.gateway == gw
