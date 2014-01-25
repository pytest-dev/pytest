"""
    per-test stdout/stderr capturing mechanisms,
    ``capsys`` and ``capfd`` function arguments.
"""
# note: py.io capture was where copied from
# pylib 1.4.20.dev2 (rev 13d9af95547e)
import sys
import os
import tempfile

import py
import pytest

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from io import BytesIO
except ImportError:
    class BytesIO(StringIO):
        def write(self, data):
            if isinstance(data, unicode):
                raise TypeError("not a byte value: %r" % (data,))
            StringIO.write(self, data)

if sys.version_info < (3, 0):
    class TextIO(StringIO):
        def write(self, data):
            if not isinstance(data, unicode):
                enc = getattr(self, '_encoding', 'UTF-8')
                data = unicode(data, enc, 'replace')
            StringIO.write(self, data)
else:
    TextIO = StringIO


patchsysdict = {0: 'stdin', 1: 'stdout', 2: 'stderr'}


def pytest_addoption(parser):
    group = parser.getgroup("general")
    group._addoption(
        '--capture', action="store", default=None,
        metavar="method", choices=['fd', 'sys', 'no'],
        help="per-test capturing method: one of fd (default)|sys|no.")
    group._addoption(
        '-s', action="store_const", const="no", dest="capture",
        help="shortcut for --capture=no.")


@pytest.mark.tryfirst
def pytest_load_initial_conftests(early_config, parser, args, __multicall__):
    ns = parser.parse_known_args(args)
    method = ns.capture
    if not method:
        method = "fd"
    if method == "fd" and not hasattr(os, "dup"):
        method = "sys"
    capman = CaptureManager(method)
    early_config.pluginmanager.register(capman, "capturemanager")

    # make sure that capturemanager is properly reset at final shutdown
    def teardown():
        try:
            capman.reset_capturings()
        except ValueError:
            pass

    early_config.pluginmanager.add_shutdown(teardown)

    # make sure logging does not raise exceptions at the end
    def silence_logging_at_shutdown():
        if "logging" in sys.modules:
            sys.modules["logging"].raiseExceptions = False
    early_config.pluginmanager.add_shutdown(silence_logging_at_shutdown)

    # finally trigger conftest loading but while capturing (issue93)
    capman.resumecapture()
    try:
        try:
            return __multicall__.execute()
        finally:
            out, err = capman.suspendcapture()
    except:
        sys.stdout.write(out)
        sys.stderr.write(err)
        raise


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
        newf = dupfile(f, encoding="UTF-8")
        f.close()
        return newf

    def _makestringio(self):
        return TextIO()

    def _getcapture(self, method):
        if method == "fd":
            return StdCaptureFD(
                out=self._maketempfile(),
                err=self._maketempfile(),
            )
        elif method == "sys":
            return StdCapture(
                out=self._makestringio(),
                err=self._makestringio(),
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
        if method == "fd" and not hasattr(os, 'dup'):  # e.g. jython
            method = "sys"
        return method

    def reset_capturings(self):
        for cap in self._method2capture.values():
            cap.reset()

    def resumecapture_item(self, item):
        method = self._getmethod(item.config, item.fspath)
        if not hasattr(item, 'outerr'):
            item.outerr = ('', '')  # we accumulate outerr on the item
        return self.resumecapture(method)

    def resumecapture(self, method=None):
        if hasattr(self, '_capturing'):
            raise ValueError(
                "cannot resume, already capturing with %r" %
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
        funcargs = getattr(pyfuncitem, "funcargs", None)
        if funcargs is not None:
            for name, capfuncarg in funcargs.items():
                if name in ('capsys', 'capfd'):
                    assert not hasattr(self, '_capturing_funcarg')
                    self._capturing_funcarg = capfuncarg
                    capfuncarg._start()

    def deactivate_funcargs(self):
        capturing_funcarg = getattr(self, '_capturing_funcarg', None)
        if capturing_funcarg:
            outerr = capturing_funcarg._finalize()
            del self._capturing_funcarg
            return outerr

    def pytest_make_collect_report(self, __multicall__, collector):
        method = self._getmethod(collector.config, collector.fspath)
        try:
            self.resumecapture(method)
        except ValueError:
            # recursive collect, XXX refactor capturing
            # to allow for more lightweight recursive capturing
            return
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
        funcarg_outerr = self.deactivate_funcargs()
        rep = __multicall__.execute()
        outerr = self.suspendcapture(item)
        if funcarg_outerr is not None:
            outerr = (outerr[0] + funcarg_outerr[0],
                      outerr[1] + funcarg_outerr[1])
        addouterr(rep, outerr)
        if not rep.passed or rep.when == "teardown":
            outerr = ('', '')
        item.outerr = outerr
        return rep

error_capsysfderror = "cannot use capsys and capfd at the same time"


def pytest_funcarg__capsys(request):
    """enables capturing of writes to sys.stdout/sys.stderr and makes
    captured output available via ``capsys.readouterr()`` method calls
    which return a ``(out, err)`` tuple.
    """
    if "capfd" in request._funcargs:
        raise request.raiseerror(error_capsysfderror)
    return CaptureFixture(StdCapture)


def pytest_funcarg__capfd(request):
    """enables capturing of writes to file descriptors 1 and 2 and makes
    captured output available via ``capsys.readouterr()`` method calls
    which return a ``(out, err)`` tuple.
    """
    if "capsys" in request._funcargs:
        request.raiseerror(error_capsysfderror)
    if not hasattr(os, 'dup'):
        pytest.skip("capfd funcarg needs os.dup")
    return CaptureFixture(StdCaptureFD)


class CaptureFixture:
    def __init__(self, captureclass):
        self._capture = captureclass()

    def _start(self):
        self._capture.startall()

    def _finalize(self):
        if hasattr(self, '_capture'):
            outerr = self._outerr = self._capture.reset()
            del self._capture
            return outerr

    def readouterr(self):
        try:
            return self._capture.readouterr()
        except AttributeError:
            return self._outerr

    def close(self):
        self._finalize()


class FDCapture:
    """ Capture IO to/from a given os-level filedescriptor. """

    def __init__(self, targetfd, tmpfile=None, patchsys=False):
        """ save targetfd descriptor, and open a new
            temporary file there.  If no tmpfile is
            specified a tempfile.Tempfile() will be opened
            in text mode.
        """
        self.targetfd = targetfd
        if tmpfile is None and targetfd != 0:
            f = tempfile.TemporaryFile('wb+')
            tmpfile = dupfile(f, encoding="UTF-8")
            f.close()
        self.tmpfile = tmpfile
        self._savefd = os.dup(self.targetfd)
        if patchsys:
            self._oldsys = getattr(sys, patchsysdict[targetfd])

    def start(self):
        try:
            os.fstat(self._savefd)
        except OSError:
            raise ValueError(
                "saved filedescriptor not valid, "
                "did you call start() twice?")
        if self.targetfd == 0 and not self.tmpfile:
            fd = os.open(os.devnull, os.O_RDONLY)
            os.dup2(fd, 0)
            os.close(fd)
            if hasattr(self, '_oldsys'):
                setattr(sys, patchsysdict[self.targetfd], DontReadFromInput())
        else:
            os.dup2(self.tmpfile.fileno(), self.targetfd)
            if hasattr(self, '_oldsys'):
                setattr(sys, patchsysdict[self.targetfd], self.tmpfile)

    def done(self):
        """ unpatch and clean up, returns the self.tmpfile (file object)
        """
        os.dup2(self._savefd, self.targetfd)
        os.close(self._savefd)
        if self.targetfd != 0:
            self.tmpfile.seek(0)
        if hasattr(self, '_oldsys'):
            setattr(sys, patchsysdict[self.targetfd], self._oldsys)
        return self.tmpfile

    def writeorg(self, data):
        """ write a string to the original file descriptor
        """
        tempfp = tempfile.TemporaryFile()
        try:
            os.dup2(self._savefd, tempfp.fileno())
            tempfp.write(data)
        finally:
            tempfp.close()


def dupfile(f, mode=None, buffering=0, raising=False, encoding=None):
    """ return a new open file object that's a duplicate of f

        mode is duplicated if not given, 'buffering' controls
        buffer size (defaulting to no buffering) and 'raising'
        defines whether an exception is raised when an incompatible
        file object is passed in (if raising is False, the file
        object itself will be returned)
    """
    try:
        fd = f.fileno()
        mode = mode or f.mode
    except AttributeError:
        if raising:
            raise
        return f
    newfd = os.dup(fd)
    if sys.version_info >= (3, 0):
        if encoding is not None:
            mode = mode.replace("b", "")
            buffering = True
        return os.fdopen(newfd, mode, buffering, encoding, closefd=True)
    else:
        f = os.fdopen(newfd, mode, buffering)
        if encoding is not None:
            return EncodedFile(f, encoding)
        return f


class EncodedFile(object):
    def __init__(self, _stream, encoding):
        self._stream = _stream
        self.encoding = encoding

    def write(self, obj):
        if isinstance(obj, unicode):
            obj = obj.encode(self.encoding)
        self._stream.write(obj)

    def writelines(self, linelist):
        data = ''.join(linelist)
        self.write(data)

    def __getattr__(self, name):
        return getattr(self._stream, name)


class Capture(object):
    def reset(self):
        """ reset sys.stdout/stderr and return captured output as strings. """
        if hasattr(self, '_reset'):
            raise ValueError("was already reset")
        self._reset = True
        outfile, errfile = self.done(save=False)
        out, err = "", ""
        if outfile and not outfile.closed:
            out = outfile.read()
            outfile.close()
        if errfile and errfile != outfile and not errfile.closed:
            err = errfile.read()
            errfile.close()
        return out, err

    def suspend(self):
        """ return current snapshot captures, memorize tempfiles. """
        outerr = self.readouterr()
        outfile, errfile = self.done()
        return outerr


class StdCaptureFD(Capture):
    """ This class allows to capture writes to FD1 and FD2
        and may connect a NULL file to FD0 (and prevent
        reads from sys.stdin).  If any of the 0,1,2 file descriptors
        is invalid it will not be captured.
    """
    def __init__(self, out=True, err=True, in_=True, patchsys=True):
        self._options = {
            "out": out,
            "err": err,
            "in_": in_,
            "patchsys": patchsys,
        }
        self._save()

    def _save(self):
        in_ = self._options['in_']
        out = self._options['out']
        err = self._options['err']
        patchsys = self._options['patchsys']
        if in_:
            try:
                self.in_ = FDCapture(
                    0, tmpfile=None,
                    patchsys=patchsys)
            except OSError:
                pass
        if out:
            tmpfile = None
            if hasattr(out, 'write'):
                tmpfile = out
            try:
                self.out = FDCapture(
                    1, tmpfile=tmpfile,
                    patchsys=patchsys)
                self._options['out'] = self.out.tmpfile
            except OSError:
                pass
        if err:
            if hasattr(err, 'write'):
                tmpfile = err
            else:
                tmpfile = None
            try:
                self.err = FDCapture(
                    2, tmpfile=tmpfile,
                    patchsys=patchsys)
                self._options['err'] = self.err.tmpfile
            except OSError:
                pass

    def startall(self):
        if hasattr(self, 'in_'):
            self.in_.start()
        if hasattr(self, 'out'):
            self.out.start()
        if hasattr(self, 'err'):
            self.err.start()

    def resume(self):
        """ resume capturing with original temp files. """
        self.startall()

    def done(self, save=True):
        """ return (outfile, errfile) and stop capturing. """
        outfile = errfile = None
        if hasattr(self, 'out') and not self.out.tmpfile.closed:
            outfile = self.out.done()
        if hasattr(self, 'err') and not self.err.tmpfile.closed:
            errfile = self.err.done()
        if hasattr(self, 'in_'):
            self.in_.done()
        if save:
            self._save()
        return outfile, errfile

    def readouterr(self):
        """ return snapshot value of stdout/stderr capturings. """
        out = self._readsnapshot('out')
        err = self._readsnapshot('err')
        return out, err

    def _readsnapshot(self, name):
        if hasattr(self, name):
            f = getattr(self, name).tmpfile
        else:
            return ''

        f.seek(0)
        res = f.read()
        enc = getattr(f, "encoding", None)
        if enc:
            res = py.builtin._totext(res, enc, "replace")
        f.truncate(0)
        f.seek(0)
        return res


class StdCapture(Capture):
    """ This class allows to capture writes to sys.stdout|stderr "in-memory"
        and will raise errors on tries to read from sys.stdin. It only
        modifies sys.stdout|stderr|stdin attributes and does not
        touch underlying File Descriptors (use StdCaptureFD for that).
    """
    def __init__(self, out=True, err=True, in_=True):
        self._oldout = sys.stdout
        self._olderr = sys.stderr
        self._oldin = sys.stdin
        if out and not hasattr(out, 'file'):
            out = TextIO()
        self.out = out
        if err:
            if not hasattr(err, 'write'):
                err = TextIO()
        self.err = err
        self.in_ = in_

    def startall(self):
        if self.out:
            sys.stdout = self.out
        if self.err:
            sys.stderr = self.err
        if self.in_:
            sys.stdin = self.in_ = DontReadFromInput()

    def done(self, save=True):
        """ return (outfile, errfile) and stop capturing. """
        outfile = errfile = None
        if self.out and not self.out.closed:
            sys.stdout = self._oldout
            outfile = self.out
            outfile.seek(0)
        if self.err and not self.err.closed:
            sys.stderr = self._olderr
            errfile = self.err
            errfile.seek(0)
        if self.in_:
            sys.stdin = self._oldin
        return outfile, errfile

    def resume(self):
        """ resume capturing with original temp files. """
        self.startall()

    def readouterr(self):
        """ return snapshot value of stdout/stderr capturings. """
        out = err = ""
        if self.out:
            out = self.out.getvalue()
            self.out.truncate(0)
            self.out.seek(0)
        if self.err:
            err = self.err.getvalue()
            self.err.truncate(0)
            self.err.seek(0)
        return out, err


class DontReadFromInput:
    """Temporary stub class.  Ideally when stdin is accessed, the
    capturing should be turned off, with possibly all data captured
    so far sent to the screen.  This should be configurable, though,
    because in automated test runs it is better to crash than
    hang indefinitely.
    """
    def read(self, *args):
        raise IOError("reading from stdin while output is captured")
    readline = read
    readlines = read
    __iter__ = read

    def fileno(self):
        raise ValueError("redirected Stdin is pseudofile, has no fileno()")

    def isatty(self):
        return False

    def close(self):
        pass
