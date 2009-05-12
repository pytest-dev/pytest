
from myapp import MyApp

class ConftestPlugin:
    def pytest_funcarg__mysetup(self, request):
        return MySetup(request)

class MySetup:
    def __init__(self, request):
        self.config = request.config 
    def myapp(self):
        return MyApp()
