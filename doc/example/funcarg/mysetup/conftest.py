
from mysetup.myapp import MyApp

def pytest_funcarg__mysetup(request):
    return MySetup()

class MySetup:
    def myapp(self):
        return MyApp()
