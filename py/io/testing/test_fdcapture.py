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

