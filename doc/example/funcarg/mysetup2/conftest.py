import py
from mysetup2.myapp import MyApp

def pytest_funcarg__mysetup(request):
    return MySetup(request)

def pytest_addoption(parser):
    parser.addoption("--ssh", action="store", default=None,
        help="specify ssh host to run tests with")
    

class MySetup:
    def __init__(self, request):
        self.config = request.config 

    def myapp(self):
        return MyApp()

    def getsshconnection(self):
        host = self.config.option.ssh
        if host is None:
            py.test.skip("specify ssh host with --ssh")
        return execnet.SshGateway(host)
        
