import os, sys
import py

needsdup = py.test.mark.skipif("not hasattr(os, 'dup')")

from py.builtin import print_

if sys.version_info >= (3,0):
    def tobytes(obj):
        if isinstance(obj, str): 
            obj = obj.encode('UTF-8')
        assert isinstance(obj, bytes)
        return obj
    def totext(obj):
        if isinstance(obj, bytes): 
            obj = str(obj, 'UTF-8')
        assert isinstance(obj, str)
        return obj
else:
    def tobytes(obj):
        if isinstance(obj, unicode):
            obj = obj.encode('UTF-8')
        assert isinstance(obj, str)
        return obj
    def totext(obj):
        if isinstance(obj, str):
            obj = unicode(obj, 'UTF-8')
        assert isinstance(obj, unicode)
        return obj

def oswritebytes(fd, obj):
    os.write(fd, tobytes(obj))
    
class TestTextIO:
    def test_text(self):
        f = py.io.TextIO()
        f.write("hello") 
        s = f.getvalue()
        assert s == "hello"
        f.close()

    def test_unicode_and_str_mixture(self):
        f = py.io.TextIO()
        if sys.version_info >= (3,0):
            f.write("\u00f6")
            py.test.raises(TypeError, "f.write(bytes('hello', 'UTF-8'))")
        else:
            f.write(unicode("\u00f6", 'UTF-8'))
            f.write("hello") # bytes 
            s = f.getvalue()
            f.close()
            assert isinstance(s, unicode) 

def test_bytes_io():
    f = py.io.BytesIO()
    f.write(tobytes("hello"))
    py.test.raises(TypeError, "f.write(totext('hello'))")
    s = f.getvalue()
    assert s == tobytes("hello")

def test_dontreadfrominput():
    from py._io.capture import  DontReadFromInput
    f = DontReadFromInput()
    assert not f.isatty() 
    py.test.raises(IOError, f.read)
    py.test.raises(IOError, f.readlines)
    py.test.raises(IOError, iter, f) 
    py.test.raises(ValueError, f.fileno)
    f.close() # just for completeness

def pytest_funcarg__tmpfile(request):
    testdir = request.getfuncargvalue("testdir")
    f = testdir.makepyfile("").open('wb+')
    request.addfinalizer(f.close)
    return f

@needsdup
def test_dupfile(tmpfile):
    somefile = tmpfile
    flist = []
    for i in range(5): 
        nf = py.io.dupfile(somefile, encoding="utf-8")
        assert nf != somefile
        assert nf.fileno() != somefile.fileno()
        assert nf not in flist 
        print_(i, end="", file=nf)
        flist.append(nf) 
    for i in range(5): 
        f = flist[i]
        f.close()
    somefile.seek(0)
    s = somefile.read()
    assert "01234" in repr(s)
    somefile.close()

class TestFDCapture: 
    pytestmark = needsdup 

    def test_stdout(self, tmpfile):
        fd = tmpfile.fileno()
        cap = py.io.FDCapture(fd)
        data = tobytes("hello")
        os.write(fd, data)
        f = cap.done()
        s = f.read()
        assert s == "hello"

    def test_stderr(self): 
        cap = py.io.FDCapture(2)
        cap.setasfile('stderr')
        print_("hello", file=sys.stderr)
        f = cap.done()
        s = f.read()
        assert s == "hello\n"

    def test_stdin(self, tmpfile): 
        tmpfile.write(tobytes("3"))
        tmpfile.seek(0)
        cap = py.io.FDCapture(0, tmpfile=tmpfile)
        # check with os.read() directly instead of raw_input(), because
        # sys.stdin itself may be redirected (as py.test now does by default)
        x = os.read(0, 100).strip()
        f = cap.done()
        assert x == tobytes("3")

    def test_writeorg(self, tmpfile):
        data1, data2 = tobytes("foo"), tobytes("bar")
        try:
            cap = py.io.FDCapture(tmpfile.fileno())
            tmpfile.write(data1)
            cap.writeorg(data2)
        finally:
            tmpfile.close()
        f = cap.done()
        scap = f.read()
        assert scap == totext(data1)
        stmp = open(tmpfile.name, 'rb').read()
        assert stmp == data2


class TestStdCapture: 
    def getcapture(self, **kw):
        return py.io.StdCapture(**kw)

    def test_capturing_done_simple(self):
        cap = self.getcapture()
        sys.stdout.write("hello")
        sys.stderr.write("world")
        outfile, errfile = cap.done()
        s = outfile.read()
        assert s == "hello"
        s = errfile.read()
        assert s == "world"

    def test_capturing_reset_simple(self):
        cap = self.getcapture()
        print("hello world")
        sys.stderr.write("hello error\n")
        out, err = cap.reset()
        assert out == "hello world\n"
        assert err == "hello error\n"

    def test_capturing_readouterr(self):
        cap = self.getcapture()
        try:
            print ("hello world")
            sys.stderr.write("hello error\n")
            out, err = cap.readouterr()
            assert out == "hello world\n"
            assert err == "hello error\n"
            sys.stderr.write("error2")
        finally:
            out, err = cap.reset()
        assert err == "error2"

    def test_capturing_mixed(self):
        cap = self.getcapture(mixed=True)
        sys.stdout.write("hello ")
        sys.stderr.write("world")
        sys.stdout.write(".")
        out, err = cap.reset()
        assert out.strip() == "hello world."
        assert not err

    def test_capturing_twice_error(self):
        cap = self.getcapture() 
        print ("hello")
        cap.reset()
        py.test.raises(Exception, "cap.reset()")

    def test_capturing_modify_sysouterr_in_between(self):
        oldout = sys.stdout 
        olderr = sys.stderr 
        cap = self.getcapture()
        sys.stdout.write("hello")
        sys.stderr.write("world")
        sys.stdout = py.io.TextIO() 
        sys.stderr = py.io.TextIO() 
        print ("not seen" )
        sys.stderr.write("not seen\n")
        out, err = cap.reset()
        assert out == "hello"
        assert err == "world"
        assert sys.stdout == oldout 
        assert sys.stderr == olderr 

    def test_capturing_error_recursive(self):
        cap1 = self.getcapture() 
        print ("cap1")
        cap2 = self.getcapture() 
        print ("cap2")
        out2, err2 = cap2.reset()
        py.test.raises(Exception, "cap2.reset()")
        out1, err1 = cap1.reset() 
        assert out1 == "cap1\n"
        assert out2 == "cap2\n"
    
    def test_just_out_capture(self): 
        cap = self.getcapture(out=True, err=False)
        sys.stdout.write("hello")
        sys.stderr.write("world")
        out, err = cap.reset()
        assert out == "hello"
        assert not err 

    def test_just_err_capture(self): 
        cap = self.getcapture(out=False, err=True) 
        sys.stdout.write("hello")
        sys.stderr.write("world")
        out, err = cap.reset()
        assert err == "world"
        assert not out 

    def test_stdin_restored(self):
        old = sys.stdin 
        cap = self.getcapture(in_=True)
        newstdin = sys.stdin 
        out, err = cap.reset()
        assert newstdin != sys.stdin
        assert sys.stdin is old 

    def test_stdin_nulled_by_default(self):
        print ("XXX this test may well hang instead of crashing")
        print ("XXX which indicates an error in the underlying capturing")
        print ("XXX mechanisms" )
        cap = self.getcapture()
        py.test.raises(IOError, "sys.stdin.read()")
        out, err = cap.reset()

    def test_suspend_resume(self):
        cap = self.getcapture(out=True, err=False, in_=False)
        try:
            print ("hello")
            sys.stderr.write("error\n")
            out, err = cap.suspend()
            assert out == "hello\n"
            assert not err 
            print ("in between")
            sys.stderr.write("in between\n")
            cap.resume()
            print ("after")
            sys.stderr.write("error_after\n")
        finally:
            out, err = cap.reset()
        assert out == "after\n"
        assert not err 

class TestStdCaptureFD(TestStdCapture): 
    pytestmark = needsdup

    def getcapture(self, **kw): 
        return py.io.StdCaptureFD(**kw)

    def test_intermingling(self): 
        cap = self.getcapture()
        oswritebytes(1, "1")
        sys.stdout.write(str(2))
        sys.stdout.flush()
        oswritebytes(1, "3")
        oswritebytes(2, "a")
        sys.stderr.write("b")
        sys.stderr.flush()
        oswritebytes(2, "c")
        out, err = cap.reset()
        assert out == "123" 
        assert err == "abc" 

    def test_callcapture(self): 
        def func(x, y): 
            print (x)
            py.std.sys.stderr.write(str(y))
            return 42
      
        res, out, err = py.io.StdCaptureFD.call(func, 3, y=4) 
        assert res == 42 
        assert out.startswith("3") 
        assert err.startswith("4") 

@needsdup
def test_capture_no_sys(): 
    capsys = py.io.StdCapture()
    try:
        cap = py.io.StdCaptureFD(patchsys=False)
        sys.stdout.write("hello")
        sys.stderr.write("world")
        oswritebytes(1, "1")
        oswritebytes(2, "2")
        out, err = cap.reset()
        assert out == "1"
        assert err == "2"
    finally:
        capsys.reset()

@needsdup
def test_callcapture_nofd(): 
    def func(x, y): 
        oswritebytes(1, "hello")
        oswritebytes(2, "hello")
        print (x)
        sys.stderr.write(str(y))
        return 42
   
    capfd = py.io.StdCaptureFD(patchsys=False)
    try:
        res, out, err = py.io.StdCapture.call(func, 3, y=4) 
    finally:
        capfd.reset()
    assert res == 42 
    assert out.startswith("3") 
    assert err.startswith("4") 
