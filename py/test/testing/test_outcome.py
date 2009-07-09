
import py
import marshal

class TestRaises:
    def test_raises(self):
        py.test.raises(ValueError, "int('qwe')")

    def test_raises_exec(self):
        py.test.raises(ValueError, "a,x = []") 

    def test_raises_syntax_error(self):
        py.test.raises(SyntaxError, "qwe qwe qwe")

    def test_raises_function(self):
        py.test.raises(ValueError, int, 'hello')

def test_importorskip():
    from py.__.test.outcome import Skipped
    try:
        sys = py.test.importorskip("sys")
        assert sys == py.std.sys
        #path = py.test.importorskip("os.path")
        #assert path == py.std.os.path
        py.test.raises(Skipped, "py.test.importorskip('alskdj')")
        py.test.raises(SyntaxError, "py.test.importorskip('x y z')")
        py.test.raises(SyntaxError, "py.test.importorskip('x=y')")
        path = py.test.importorskip("py", minversion=".".join(py.__version__))
        mod = py.std.new.module("hello123")
        mod.__version__ = "1.3" 
        py.test.raises(Skipped, """
            py.test.importorskip("hello123", minversion="5.0")
        """)
    except Skipped:
        print py.code.ExceptionInfo()
        py.test.fail("spurious skip")

def test_pytest_exit():
    try:
        py.test.exit("hello")
    except:
        excinfo = py.code.ExceptionInfo()
        assert excinfo.errisinstance(KeyboardInterrupt)

