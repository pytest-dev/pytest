import py

class IocapturePlugin:
    """ capture sys.stdout/sys.stderr / fd1/fd2. """
    def pytest_funcarg__stdcapture(self, pyfuncitem):
        capture = Capture(py.io.StdCapture)
        pyfuncitem.addfinalizer(capture.finalize)
        return capture 

    def pytest_funcarg__stdcapturefd(self, pyfuncitem):
        capture = Capture(py.io.StdCaptureFD)
        pyfuncitem.addfinalizer(capture.finalize)
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
    plugintester.apicheck(IocapturePlugin)

class TestCapture:
    def test_std_functional(self, testdir):        
        testdir.plugins.append(IocapturePlugin())
        evrec = testdir.inline_runsource("""
            def test_hello(stdcapture):
                print 42
                out, err = stdcapture.reset()
                assert out.startswith("42")
        """)
        evrec.assertoutcome(passed=1)
        
    def test_stdfd_functional(self, testdir):        
        testdir.plugins.append(IocapturePlugin())
        evrec = testdir.inline_runsource("""
            def test_hello(stdcapturefd):
                import os
                os.write(1, "42")
                out, err = stdcapturefd.reset()
                assert out.startswith("42")
        """)
        evrec.assertoutcome(passed=1)
