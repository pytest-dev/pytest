import os, sys
import py

class TestCapturingOnSys: 

    def getcapture(self): 
        return py.io.StdCapture() 

    def test_capturing_simple(self):
        cap = self.getcapture()
        print "hello world"
        print >>sys.stderr, "hello error"
        out, err = cap.reset()
        assert out == "hello world\n"
        assert err == "hello error\n"

    def test_capturing_twice_error(self):
        cap = self.getcapture() 
        print "hello"
        cap.reset()
        py.test.raises(AttributeError, "cap.reset()")

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
        py.test.raises(AttributeError, "cap2.reset()")
        out1, err1 = cap1.reset() 
        assert out1 == "cap1\n"
        assert out2 == "cap2\n"

    def test_reading_stdin_while_captured_doesnt_hang(self):
        cap = self.getcapture()
        try:
            py.test.raises(IOError, raw_input)
        finally:
            cap.reset()

def test_callcapture_nofd(): 
    def func(x, y): 
        print x
        print >>py.std.sys.stderr, y
        return 42
   
    res, out, err = py.io.StdCapture.call(func, 3, y=4) 
    assert res == 42 
    assert out.startswith("3") 
    assert err.startswith("4") 
        
