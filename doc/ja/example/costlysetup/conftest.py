
def pytest_funcarg__setup(request):
    return request.cached_setup(
        setup=lambda: CostlySetup(),
        teardown=lambda costlysetup: costlysetup.finalize(),
        scope="session",
    )

class CostlySetup:
    def __init__(self):
        import time
        print ("performing costly setup")
        time.sleep(5)
        self.timecostly = 1

    def finalize(self):
        del self.timecostly
