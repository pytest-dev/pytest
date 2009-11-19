
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

def test_importorskip():
    from py.impl.test.outcome import Skipped, importorskip
    assert importorskip == py.test.importorskip
    try:
        sys = importorskip("sys")
        assert sys == py.std.sys
        #path = py.test.importorskip("os.path")
        #assert path == py.std.os.path
        py.test.raises(Skipped, "py.test.importorskip('alskdj')")
        py.test.raises(SyntaxError, "py.test.importorskip('x y z')")
        py.test.raises(SyntaxError, "py.test.importorskip('x=y')")
        path = importorskip("py", minversion=".".join(py.__version__))
        mod = py.std.types.ModuleType("hello123")
        mod.__version__ = "1.3"
        py.test.raises(Skipped, """
            py.test.importorskip("hello123", minversion="5.0")
        """)
    except Skipped:
        print(py.code.ExceptionInfo())
        py.test.fail("spurious skip")

def test_importorskip_imports_last_module_part():
    import os
    ospath = py.test.importorskip("os.path")
    assert os.path == ospath


def test_pytest_cmdline_main(testdir):
    p = testdir.makepyfile("""
        import sys
        sys.path.insert(0, %r)
        import py
        def test_hello():
            assert 1
        if __name__ == '__main__':
           py.test.cmdline.main([__file__])
    """ % (str(py._dir.dirpath())))
    import subprocess
    subprocess.check_call([sys.executable, str(p)])
