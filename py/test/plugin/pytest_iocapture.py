import py

def pytest_funcarg__stdcapture(request):
    """ capture writes to sys.stdout/sys.stderr. """ 
    capture = Capture(py.io.StdCapture)
    request.addfinalizer(capture.finalize)
    return capture 

def pytest_funcarg__stdcapturefd(request):
    """ capture writes to filedescriptors 1 and 2"""
    capture = Capture(py.io.StdCaptureFD)
    request.addfinalizer(capture.finalize)
    return capture 

class Capture:
    def __init__(self, captureclass):
        self._captureclass = captureclass
        self._capture = self._captureclass()

    def finalize(self):
        self._capture.reset()

    def reset(self):
        res = self._capture.reset()
        self._capture = self._captureclass()
        return res 

def test_generic(plugintester):
    plugintester.hookcheck()

class TestCapture:
    def test_std_functional(self, testdir):        
        evrec = testdir.inline_runsource("""
            def test_hello(stdcapture):
                print 42
                out, err = stdcapture.reset()
                assert out.startswith("42")
        """)
        evrec.assertoutcome(passed=1)
        
    def test_stdfd_functional(self, testdir):        
        evrec = testdir.inline_runsource("""
            def test_hello(stdcapturefd):
                import os
                os.write(1, "42")
                out, err = stdcapturefd.reset()
                assert out.startswith("42")
        """)
        evrec.assertoutcome(passed=1)
