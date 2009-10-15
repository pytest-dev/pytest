
import py
import sys

class TestRaises:
    def test_raises(self):
        py.test.raises(ValueError, "int('qwe')")

    def test_raises_exec(self):
        py.test.raises(ValueError, "a,x = []") 

    def test_raises_syntax_error(self):
        py.test.raises(SyntaxError, "qwe qwe qwe")

    def test_raises_function(self):
        py.test.raises(ValueError, int, 'hello')

def test_pytest_exit():
    try:
        py.test.exit("hello")
    except:
        excinfo = py.code.ExceptionInfo()
        assert excinfo.errisinstance(KeyboardInterrupt)

def test_exception_printing_skip():
    try:
        py.test.skip("hello")
    except Exception:
        excinfo = py.code.ExceptionInfo()
        s = excinfo.exconly(tryshort=True)
        assert s.startswith("Skipped")
