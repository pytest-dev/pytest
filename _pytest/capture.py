""" per-test stdout/stderr capturing mechanisms, ``capsys`` and ``capfd`` function arguments.  """

import pytest, py
import os

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group._addoption('--capture', action="store", default=None,
        metavar="method", type="choice", choices=['fd', 'sys', 'no'],
        help="per-test capturing method: one of fd (default)|sys|no.")
    group._addoption('-s', action="store_const", const="no", dest="capture",
        help="shortcut for --capture=no.")

@pytest.mark.tryfirst
def pytest_cmdline_parse(pluginmanager, args):
    # we want to perform capturing already for plugin/conftest loading
    if '-s' in args or "--capture=no" in args:
        method = "no"
    elif hasattr(os, 'dup') and '--capture=sys' not in args:
        method = "fd"
    else:
        method = "sys"
    capman = CaptureManager(method)
    pluginmanager.register(capman, "capturemanager")

def addouterr(rep, outerr):
    for secname, content in zip(["out", "err"], outerr):
        if content:
            rep.sections.append(("Captured std%s" % secname, content))

class NoCapture:
    def startall(self):
        pass
    def resume(self):
        pass
    def reset(self):
        pass
    def suspend(self):
        return "", ""

class CaptureManager:
    def __init__(self, defaultmethod=None):
        self._method2capture = {}
        self._defaultmethod = defaultmethod

    def _maketempfile(self):
        f = py.std.tempfile.TemporaryFile()
        newf = py.io.dupfile(f, encoding="UTF-8")
        f.close()
        return newf

    def _makestringio(self):
        return py.io.TextIO()

    def _getcapture(self, method):
        if method == "fd":
            return py.io.StdCaptureFD(now=False,
                out=self._maketempfile(), err=self._maketempfile()
            )
        elif method == "sys":
            return py.io.StdCapture(now=False,
                out=self._makestringio(), err=self._makestringio()
            )
        elif method == "no":
            return NoCapture()
        else:
            raise ValueError("unknown capturing method: %r" % method)

    def _getmethod(self, config, fspath):
        if config.option.capture:
            method = config.option.capture
        else:
            try:
                method = config._conftest.rget("option_capture", path=fspath)
            except KeyError:
                method = "fd"
        if method == "fd" and not hasattr(os, 'dup'): # e.g. jython
            method = "sys"
        return method

    def reset_capturings(self):
        for name, cap in self._method2capture.items():
            cap.reset()

    def resumecapture_item(self, item):
        method = self._getmethod(item.config, item.fspath)
        if not hasattr(item, 'outerr'):
            item.outerr = ('', '') # we accumulate outerr on the item
        return self.resumecapture(method)

    def resumecapture(self, method=None):
        if hasattr(self, '_capturing'):
            raise ValueError("cannot resume, already capturing with %r" %
                (self._capturing,))
        if method is None:
            method = self._defaultmethod
        cap = self._method2capture.get(method)
        self._capturing = method
        if cap is None:
            self._method2capture[method] = cap = self._getcapture(method)
            cap.startall()
        else:
            cap.resume()

    def suspendcapture(self, item=None):
        self.deactivate_funcargs()
        if hasattr(self, '_capturing'):
            method = self._capturing
            cap = self._method2capture.get(method)
            if cap is not None:
                outerr = cap.suspend()
            del self._capturing
            if item:
                outerr = (item.outerr[0] + outerr[0],
                          item.outerr[1] + outerr[1])
            return outerr
        if hasattr(item, 'outerr'):
            return item.outerr
        return "", ""

    def activate_funcargs(self, pyfuncitem):
        if not hasattr(pyfuncitem, 'funcargs'):
            return
        assert not hasattr(self, '_capturing_funcargs')
        self._capturing_funcargs = capturing_funcargs = []
        for name, capfuncarg in pyfuncitem.funcargs.items():
            if name in ('capsys', 'capfd'):
                capturing_funcargs.append(capfuncarg)
                capfuncarg._start()

    def deactivate_funcargs(self):
        capturing_funcargs = getattr(self, '_capturing_funcargs', None)
        if capturing_funcargs is not None:
            while capturing_funcargs:
                capfuncarg = capturing_funcargs.pop()
                capfuncarg._finalize()
            del self._capturing_funcargs

    def pytest_make_collect_report(self, __multicall__, collector):
        method = self._getmethod(collector.config, collector.fspath)
        try:
            self.resumecapture(method)
        except ValueError:
            return # recursive collect, XXX refactor capturing
                   # to allow for more lightweight recursive capturing
        try:
            rep = __multicall__.execute()
        finally:
            outerr = self.suspendcapture()
        addouterr(rep, outerr)
        return rep

    @pytest.mark.tryfirst
    def pytest_runtest_setup(self, item):
        self.resumecapture_item(item)

    @pytest.mark.tryfirst
    def pytest_runtest_call(self, item):
        self.resumecapture_item(item)
        self.activate_funcargs(item)

    @pytest.mark.tryfirst
    def pytest_runtest_teardown(self, item):
        self.resumecapture_item(item)

    def pytest_keyboard_interrupt(self, excinfo):
        if hasattr(self, '_capturing'):
            self.suspendcapture()

    @pytest.mark.tryfirst
    def pytest_runtest_makereport(self, __multicall__, item, call):
        self.deactivate_funcargs()
        rep = __multicall__.execute()
        outerr = self.suspendcapture(item)
        if not rep.passed:
            addouterr(rep, outerr)
        if not rep.passed or rep.when == "teardown":
            outerr = ('', '')
        item.outerr = outerr
        return rep

def pytest_funcarg__capsys(request):
    """enables capturing of writes to sys.stdout/sys.stderr and makes
    captured output available via ``capsys.readouterr()`` method calls
    which return a ``(out, err)`` tuple.
    """
    return CaptureFuncarg(py.io.StdCapture)

def pytest_funcarg__capfd(request):
    """enables capturing of writes to file descriptors 1 and 2 and makes
    captured output available via ``capsys.readouterr()`` method calls
    which return a ``(out, err)`` tuple.
    """
    if not hasattr(os, 'dup'):
        py.test.skip("capfd funcarg needs os.dup")
    return CaptureFuncarg(py.io.StdCaptureFD)

class CaptureFuncarg:
    def __init__(self, captureclass):
        self.capture = captureclass(now=False)

    def _start(self):
        self.capture.startall()

    def _finalize(self):
        if hasattr(self, 'capture'):
            self.capture.reset()
            del self.capture

    def readouterr(self):
        return self.capture.readouterr()

    def close(self):
        self._finalize()
