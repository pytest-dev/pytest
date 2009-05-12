
class ConftestPlugin:
    def pytest_configure(self, config):
        self._setup = None

    def pytest_funcarg__setup(self, request):
        if self._setup is None:
            self._setup = CostlySetup()
        return self._setup

    def pytest_unconfigure(self, config):
        if self._setup is not None:
            self._setup.finalize()

class CostlySetup:
    def __init__(self):
        import time
        time.sleep(5)
        self.timecostly = 1

    def finalize(self):
        del self.timecostly 
