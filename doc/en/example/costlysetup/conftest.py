
import pytest

@pytest.factory("session")
def setup(testcontext):
    setup = CostlySetup()
    testcontext.addfinalizer(setup.finalize)
    return setup

class CostlySetup:
    def __init__(self):
        import time
        print ("performing costly setup")
        time.sleep(5)
        self.timecostly = 1

    def finalize(self):
        del self.timecostly
