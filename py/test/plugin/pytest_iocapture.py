"""
'capsys' and 'capfd' funcargs for capturing stdout/stderror.

Calling the reset() method of the capture funcargs gives 
a out/err tuple of strings representing the captured streams. 
You can call reset() multiple times each time getting
the chunk of output that was captured between the invocations. 

"""
import py

def pytest_funcarg__capsys(request):
    """ capture writes to sys.stdout/sys.stderr. """ 
    capture = Capture(py.io.StdCapture)
    request.addfinalizer(capture.finalize)
    return capture 

def pytest_funcarg__capfd(request):
    """ capture writes to filedescriptors 1 and 2"""
    capture = Capture(py.io.StdCaptureFD)
    request.addfinalizer(capture.finalize)
    return capture 

def pytest_pyfunc_call(pyfuncitem):
    if hasattr(pyfuncitem, 'funcargs'):
        for funcarg, value in pyfuncitem.funcargs.items():
            if funcarg == "capsys" or funcarg == "capfd":
                value.reset()

class Capture:
    _capture = None
    def __init__(self, captureclass):
        self._captureclass = captureclass

    def finalize(self):
        if self._capture:
            self._capture.reset()

    def reset(self):
        res = None
        if self._capture:
            res = self._capture.reset()
        self._capture = self._captureclass()
        return res 

class TestCapture:
    def test_std_functional(self, testdir):        
        reprec = testdir.inline_runsource("""
            def test_hello(capsys):
                print 42
                out, err = capsys.reset()
                assert out.startswith("42")
        """)
        reprec.assertoutcome(passed=1)
        
    def test_stdfd_functional(self, testdir):        
        reprec = testdir.inline_runsource("""
            def test_hello(capfd):
                import os
                os.write(1, "42")
                out, err = capfd.reset()
                assert out.startswith("42")
        """)
        reprec.assertoutcome(passed=1)

    def test_funcall_yielded_no_funcargs(self, testdir):        
        reprec = testdir.inline_runsource("""
            def test_hello():
                yield lambda: None
        """)
        reprec.assertoutcome(passed=1)

