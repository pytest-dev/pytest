"""
configurable per-test stdout/stderr capturing mechanisms. 

This plugin captures stdout/stderr output for each test separately. 
In case of test failures this captured output is shown grouped 
togtther with the test. 

The plugin also provides test function arguments that help to
assert stdout/stderr output from within your tests, see the 
`funcarg example`_. 


Capturing of input/output streams during tests 
---------------------------------------------------

By default ``sys.stdout`` and ``sys.stderr`` are substituted with
temporary streams during the execution of tests and setup/teardown code.  
During the whole testing process it will re-use the same temporary 
streams allowing to play well with the logging module which easily
takes ownership on these streams. 

Also, 'sys.stdin' is substituted with a file-like "null" object that 
does not return any values.  This is to immediately error out
on tests that wait on reading something from stdin. 

You can influence output capturing mechanisms from the command line::

    py.test -s            # disable all capturing
    py.test --capture=sys # replace sys.stdout/stderr with in-mem files
    py.test --capture=fd  # point filedescriptors 1 and 2 to temp file

If you set capturing values in a conftest file like this::

    # conftest.py
    option_capture = 'fd'

then all tests in that directory will execute with "fd" style capturing. 

sys-level capturing 
------------------------------------------

Capturing on 'sys' level means that ``sys.stdout`` and ``sys.stderr`` 
will be replaced with in-memory files (``py.io.TextIO`` to be precise)  
that capture writes and decode non-unicode strings to a unicode object
(using a default, usually, UTF-8, encoding). 

FD-level capturing and subprocesses
------------------------------------------

The ``fd`` based method means that writes going to system level files
based on the standard file descriptors will be captured, for example 
writes such as ``os.write(1, 'hello')`` will be captured properly. 
Capturing on fd-level will include output generated from 
any subprocesses created during a test. 

.. _`funcarg example`:

Example Usage of the capturing Function arguments
---------------------------------------------------

You can use the `capsys funcarg`_ and `capfd funcarg`_ to 
capture writes to stdout and stderr streams.  Using the
funcargs frees your test from having to care about setting/resetting 
the old streams and also interacts well with py.test's own 
per-test capturing.  Here is an example test function:

.. sourcecode:: python

    def test_myoutput(capsys):
        print ("hello")
        sys.stderr.write("world\\n")
        out, err = capsys.readouterr()
        assert out == "hello\\n"
        assert err == "world\\n"
        print "next"
        out, err = capsys.readouterr()
        assert out == "next\\n" 

The ``readouterr()`` call snapshots the output so far - 
and capturing will be continued.  After the test 
function finishes the original streams will 
be restored.  If you want to capture on 
the filedescriptor level you can use the ``capfd`` function
argument which offers the same interface. 
"""

import py
import os

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group._addoption('--capture', action="store", default=None,
        metavar="method", type="choice", choices=['fd', 'sys', 'no'],
        help="per-test capturing method: one of fd (default)|sys|no.")
    group._addoption('-s', action="store_const", const="no", dest="capture", 
        help="shortcut for --capture=no.")

def addouterr(rep, outerr):
    repr = getattr(rep, 'longrepr', None)
    if not hasattr(repr, 'addsection'):
        return
    for secname, content in zip(["out", "err"], outerr):
        if content:
            repr.addsection("Captured std%s" % secname, content.rstrip())

def pytest_configure(config):
    config.pluginmanager.register(CaptureManager(), 'capturemanager')

class NoCapture:
    def startall(self):
        pass
    def resume(self):
        pass
    def suspend(self):
        return "", ""

class CaptureManager:
    def __init__(self):
        self._method2capture = {}

    def _maketempfile(self):
        f = py.std.tempfile.TemporaryFile()
        newf = py.io.dupfile(f, encoding="UTF-8") 
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

    def resumecapture_item(self, item):
        method = self._getmethod(item.config, item.fspath)
        if not hasattr(item, 'outerr'):
            item.outerr = ('', '') # we accumulate outerr on the item
        return self.resumecapture(method)

    def resumecapture(self, method):
        if hasattr(self, '_capturing'):
            raise ValueError("cannot resume, already capturing with %r" % 
                (self._capturing,))
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
        self.resumecapture(method)
        try:
            rep = __multicall__.execute()
        finally:
            outerr = self.suspendcapture()
        addouterr(rep, outerr)
        return rep

    def pytest_runtest_setup(self, item):
        self.resumecapture_item(item)

    def pytest_runtest_call(self, item):
        self.resumecapture_item(item)
        self.activate_funcargs(item)

    def pytest_runtest_teardown(self, item):
        self.resumecapture_item(item)

    def pytest__teardown_final(self, __multicall__, session):
        method = self._getmethod(session.config, None)
        self.resumecapture(method)
        try:
            rep = __multicall__.execute()
        finally:
            outerr = self.suspendcapture()
        if rep:
            addouterr(rep, outerr)
        return rep

    def pytest_keyboard_interrupt(self, excinfo):
        if hasattr(self, '_capturing'):
            self.suspendcapture()

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
    """captures writes to sys.stdout/sys.stderr and makes 
    them available successively via a ``capsys.readouterr()`` method 
    which returns a ``(out, err)`` tuple of captured snapshot strings. 
    """ 
    return CaptureFuncarg(request, py.io.StdCapture)

def pytest_funcarg__capfd(request):
    """captures writes to file descriptors 1 and 2 and makes 
    snapshotted ``(out, err)`` string tuples available 
    via the ``capsys.readouterr()`` method.  If the underlying
    platform does not have ``os.dup`` (e.g. Jython) tests using
    this funcarg will automatically skip. 
    """ 
    if not hasattr(os, 'dup'):
        py.test.skip("capfd funcarg needs os.dup")
    return CaptureFuncarg(request, py.io.StdCaptureFD)


class CaptureFuncarg:
    def __init__(self, request, captureclass):
        self._cclass = captureclass
        self.capture = self._cclass(now=False)
        #request.addfinalizer(self._finalize)

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
