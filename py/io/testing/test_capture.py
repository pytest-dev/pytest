import os, sys
import py

class TestTextIO:
    def test_text(self):
        f = py.io.TextIO()
        f.write("hello") 
        s = f.getvalue()
        assert s == "hello"
        f.close()

    def test_unicode_and_str_mixture(self):
        f = py.io.TextIO()
        f.write(u"\u00f6")
        f.write(str("hello")) 
        s = f.getvalue()
        f.close()
        assert isinstance(s, unicode) 

def test_bytes_io():
    f = py.io.BytesIO()
    f.write("hello") 
    py.test.raises(TypeError, "f.write(u'hello')")
    s = f.getvalue()
    assert s == "hello"

def test_dontreadfrominput():
    from py.__.io.capture import  DontReadFromInput
    f = DontReadFromInput()
    assert not f.isatty() 
    py.test.raises(IOError, f.read)
    py.test.raises(IOError, f.readlines)
    py.test.raises(IOError, iter, f) 
    py.test.raises(ValueError, f.fileno)

def test_dupfile(): 
    somefile = py.std.os.tmpfile() 
    flist = []
    for i in range(5): 
        nf = py.io.dupfile(somefile)
        assert nf != somefile
        assert nf.fileno() != somefile.fileno()
        assert nf not in flist 
        print >>nf, i,
        flist.append(nf) 
    for i in range(5): 
        f = flist[i]
        f.close()
    somefile.seek(0)
    s = somefile.read()
    assert s.startswith("01234")
    somefile.close()

class TestFDCapture: 
    def test_basic(self): 
        tmpfile = py.std.os.tmpfile() 
        fd = tmpfile.fileno()
        cap = py.io.FDCapture(fd)
        os.write(fd, "hello")
        f = cap.done()
        s = f.read()
        assert s == "hello"

    def test_stderr(self): 
        cap = py.io.FDCapture(2)
        cap.setasfile('stderr')
        print >>sys.stderr, "hello"
        f = cap.done()
        s = f.read()
        assert s == "hello\n"

    def test_stdin(self): 
        f = os.tmpfile()
        print >>f, "3"
        f.seek(0)
        cap = py.io.FDCapture(0, tmpfile=f)
        # check with os.read() directly instead of raw_input(), because
        # sys.stdin itself may be redirected (as py.test now does by default)
        x = os.read(0, 100).strip()
        f = cap.done()
        assert x == "3"

    def test_writeorg(self):
        tmppath = py.test.ensuretemp('test_writeorg').ensure('stderr',
                                                             file=True)
        tmpfp = tmppath.open('w+b')
        try:
            cap = py.io.FDCapture(tmpfp.fileno())
            print >>tmpfp, 'foo'
            cap.writeorg('bar\n')
        finally:
            tmpfp.close()
        f = cap.done()
        scap = f.read()
        assert scap == 'foo\n'
        stmp = tmppath.read()
        assert stmp == "bar\n"

    def test_writeorg_wrongtype(self):
        tmppath = py.test.ensuretemp('test_writeorg').ensure('stdout',
                                                             file=True)
        tmpfp = tmppath.open('r')
        try:
            cap = py.io.FDCapture(tmpfp.fileno())
            py.test.raises(IOError, "cap.writeorg('bar\\n')")
        finally:
            tmpfp.close()
        f = cap.done()


class TestStdCapture: 
    def getcapture(self, **kw):
        return py.io.StdCapture(**kw)

    def test_capturing_done_simple(self):
        cap = self.getcapture()
        print "hello world"
        print >>sys.stderr, "hello error"
        outfile, errfile = cap.done()
        assert outfile.read() == "hello world\n"
        assert errfile.read() == "hello error\n"

    def test_capturing_reset_simple(self):
        cap = self.getcapture()
        print "hello world"
        print >>sys.stderr, "hello error"
        out, err = cap.reset()
        assert out == "hello world\n"
        assert err == "hello error\n"

    def test_capturing_readouterr(self):
        cap = self.getcapture()
        try:
            print "hello world"
            print >>sys.stderr, "hello error"
            out, err = cap.readouterr()
            assert out == "hello world\n"
            assert err == "hello error\n"
            print >>sys.stderr, "error2"
        finally:
            out, err = cap.reset()
        assert err == "error2\n"

    def test_capturing_mixed(self):
        cap = self.getcapture(mixed=True)
        print "hello",
        print >>sys.stderr, "world",
        print >>sys.stdout, ".",
        out, err = cap.reset()
        assert out.strip() == "hello world ."
        assert not err

    def test_capturing_twice_error(self):
        cap = self.getcapture() 
        print "hello"
        cap.reset()
        py.test.raises(Exception, "cap.reset()")

    def test_capturing_modify_sysouterr_in_between(self):
        oldout = sys.stdout 
        olderr = sys.stderr 
        cap = self.getcapture()
        print "hello",
        print >>sys.stderr, "world",
        sys.stdout = py.io.TextIO() 
        sys.stderr = py.io.TextIO() 
        print "not seen" 
        print >>sys.stderr, "not seen"
        out, err = cap.reset()
        assert out == "hello"
        assert err == "world"
        assert sys.stdout == oldout 
        assert sys.stderr == olderr 

    def test_capturing_error_recursive(self):
        cap1 = self.getcapture() 
        print "cap1"
        cap2 = self.getcapture() 
        print "cap2"
        out2, err2 = cap2.reset()
        py.test.raises(Exception, "cap2.reset()")
        out1, err1 = cap1.reset() 
        assert out1 == "cap1\n"
        assert out2 == "cap2\n"
    
    def test_just_out_capture(self): 
        cap = self.getcapture(out=True, err=False)
        print >>sys.stdout, "hello"
        print >>sys.stderr, "world"
        out, err = cap.reset()
        assert out == "hello\n"
        assert not err 

    def test_just_err_capture(self): 
        cap = self.getcapture(out=False, err=True) 
        print >>sys.stdout, "hello"
        print >>sys.stderr, "world"
        out, err = cap.reset()
        assert err == "world\n"
        assert not out 

    def test_stdin_restored(self):
        old = sys.stdin 
        cap = self.getcapture(in_=True)
        newstdin = sys.stdin 
        out, err = cap.reset()
        assert newstdin != sys.stdin
        assert sys.stdin is old 

    def test_stdin_nulled_by_default(self):
        print "XXX this test may well hang instead of crashing"
        print "XXX which indicates an error in the underlying capturing"
        print "XXX mechanisms" 
        cap = self.getcapture()
        py.test.raises(IOError, "sys.stdin.read()")
        out, err = cap.reset()

    def test_suspend_resume(self):
        cap = self.getcapture(out=True, err=False, in_=False)
        try:
            print "hello"
            sys.stderr.write("error\n")
            out, err = cap.suspend()
            assert out == "hello\n"
            assert not err 
            print "in between"
            sys.stderr.write("in between\n")
            cap.resume()
            print "after"
            sys.stderr.write("error_after\n")
        finally:
            out, err = cap.reset()
        assert out == "after\n"
        assert not err 

class TestStdCaptureFD(TestStdCapture): 
    def getcapture(self, **kw): 
        return py.io.StdCaptureFD(**kw)

    def test_intermingling(self): 
        cap = self.getcapture()
        os.write(1, "1")
        print >>sys.stdout, 2,
        os.write(1, "3")
        os.write(2, "a")
        print >>sys.stderr, "b",
        os.write(2, "c")
        out, err = cap.reset()
        assert out == "123" 
        assert err == "abc" 

    def test_callcapture(self): 
        def func(x, y): 
            print x
            print >>py.std.sys.stderr, y
            return 42
      
        res, out, err = py.io.StdCaptureFD.call(func, 3, y=4) 
        assert res == 42 
        assert out.startswith("3") 
        assert err.startswith("4") 

def test_capture_no_sys(): 
    capsys = py.io.StdCapture()
    try:
        cap = py.io.StdCaptureFD(patchsys=False)
        print >>sys.stdout, "hello"
        print >>sys.stderr, "world"
        os.write(1, "1")
        os.write(2, "2")
        out, err = cap.reset()
        assert out == "1"
        assert err == "2"
    finally:
        capsys.reset()

def test_callcapture_nofd(): 
    def func(x, y): 
        os.write(1, "hello")
        os.write(2, "hello")
        print x
        print >>sys.stderr, y
        return 42
   
    capfd = py.io.StdCaptureFD(patchsys=False)
    try:
        res, out, err = py.io.StdCapture.call(func, 3, y=4) 
    finally:
        capfd.reset()
    assert res == 42 
    assert out.startswith("3") 
    assert err.startswith("4") 
