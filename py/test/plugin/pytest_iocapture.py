"""
convenient capturing of writes to stdout/stderror streams and file descriptors. 

Example Usage
----------------------

You can use the `capsys funcarg`_ to capture writes 
to stdout and stderr streams by using it in a test 
likes this:

.. sourcecode:: python

    def test_myoutput(capsys):
        print "hello" 
        print >>sys.stderr, "world"
        out, err = capsys.reset()
        assert out == "hello\\n"
        assert err == "world\\n"
        print "next"
        out, err = capsys.reset()
        assert out == "next\\n" 

The ``reset()`` call returns a tuple and will restart 
capturing so that you can successively check for output. 
After the test function finishes the original streams
will be restored. 
"""

import py

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group._addoption('-s', 
       action="store_true", dest="nocapture", default=False,
       help="disable catching of stdout/stderr during test run.")

def determine_capturing(config, path=None):
    iocapture = config.getvalue("iocapture", path=path)
    if iocapture == "fd": 
        return py.io.StdCaptureFD()
    elif iocapture == "sys":
        return py.io.StdCapture()
    elif iocapture == "no": 
        return py.io.StdCapture(out=False, err=False, in_=False)
    else:
        # how to raise errors here? 
        raise config.Error("unknown io capturing: " + iocapture)

def pytest_make_collect_report(__call__, collector):
    cap = determine_capturing(collector.config, collector.fspath)
    try:
        rep = __call__.execute(firstresult=True)
    finally:
        outerr = cap.reset()
    addouterr(rep, outerr)
    return rep
   
def addouterr(rep, outerr):
    repr = getattr(rep, 'longrepr', None)
    if not hasattr(repr, 'addsection'):
        return
    for secname, content in zip(["out", "err"], outerr):
        if content:
            repr.addsection("Captured std%s" % secname, content.rstrip())

def pytest_configure(config):
    if not config.option.nocapture:
        config.pluginmanager.register(CapturePerTest())


class CapturePerTest:
    def __init__(self):
        self.item2capture = {}
        
    def _setcapture(self, item):
        assert item not in self.item2capture
        cap = determine_capturing(item.config, path=item.fspath)
        self.item2capture[item] = cap

    def pytest_runtest_setup(self, item):
        self._setcapture(item)

    def pytest_runtest_call(self, item):
        self._setcapture(item)

    def pytest_runtest_teardown(self, item):
        self._setcapture(item)

    def pytest_keyboard_interrupt(self, excinfo):
        for cap in self.item2capture.values():
            cap.reset()
        self.item2capture.clear()

    def pytest_runtest_makereport(self, __call__, item, call):
        capture = self.item2capture.pop(item)
        outerr = capture.reset()
        # XXX shift reporting elsewhere 
        rep = __call__.execute(firstresult=True)
        addouterr(rep, outerr)

        return rep

def pytest_funcarg__capsys(request):
    """captures writes to sys.stdout/sys.stderr and makes 
    them available successively via a ``capsys.reset()`` method 
    which returns a ``(out, err)`` tuple of captured strings. 
    """ 
    capture = CaptureFuncarg(py.io.StdCapture)
    request.addfinalizer(capture.finalize)
    return capture 

def pytest_funcarg__capfd(request):
    """captures writes to file descriptors 1 and 2 and makes 
    them available successively via a ``capsys.reset()`` method 
    which returns a ``(out, err)`` tuple of captured strings. 
    """ 
    capture = CaptureFuncarg(py.io.StdCaptureFD)
    request.addfinalizer(capture.finalize)
    return capture 

def pytest_pyfunc_call(pyfuncitem):
    if hasattr(pyfuncitem, 'funcargs'):
        for funcarg, value in pyfuncitem.funcargs.items():
            if funcarg == "capsys" or funcarg == "capfd":
                value.reset()

class CaptureFuncarg:
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

