import os, sys
import py

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
        py.test.raises(EnvironmentError, "cap.reset()")

    def test_capturing_modify_sysouterr_in_between(self):
        oldout = sys.stdout 
        olderr = sys.stderr 
        cap = self.getcapture()
        print "hello",
        print >>sys.stderr, "world",
        sys.stdout = py.std.StringIO.StringIO() 
        sys.stderr = py.std.StringIO.StringIO() 
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
        py.test.raises(EnvironmentError, "cap2.reset()")
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
    cap = py.io.StdCaptureFD(patchsys=False)
    print >>sys.stdout, "hello"
    print >>sys.stderr, "world"
    os.write(1, "1")
    os.write(2, "2")
    out, err = cap.reset()
    assert out == "1"
    assert err == "2"

def test_callcapture_nofd(): 
    def func(x, y): 
        os.write(1, "hello")
        os.write(2, "hello")
        print x
        print >>py.std.sys.stderr, y
        return 42
   
    res, out, err = py.io.StdCapture.call(func, 3, y=4) 
    assert res == 42 
    assert out.startswith("3") 
    assert err.startswith("4") 
