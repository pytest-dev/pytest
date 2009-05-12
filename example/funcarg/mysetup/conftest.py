
from myapp import MyApp

class ConftestPlugin:
    def pytest_funcarg__mysetup(self, request):
        return MySetup()

class MySetup:
    def myapp(self):
        return MyApp()
