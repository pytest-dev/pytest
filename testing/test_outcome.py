
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

    def test_raises_callable_no_exception(self):
        class A:
            def __call__(self):
                pass
        try:
            py.test.raises(ValueError, A())
        except py.test.exc.ExceptionFailure:
            pass

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
    importorskip = py.test.importorskip
    try:
        sys = importorskip("sys")
        assert sys == py.std.sys
        #path = py.test.importorskip("os.path")
        #assert path == py.std.os.path
        py.test.raises(py.test.exc.Skipped, 
            "py.test.importorskip('alskdj')")
        py.test.raises(SyntaxError, "py.test.importorskip('x y z')")
        py.test.raises(SyntaxError, "py.test.importorskip('x=y')")
        path = importorskip("py", minversion=".".join(py.__version__))
        mod = py.std.types.ModuleType("hello123")
        mod.__version__ = "1.3"
        py.test.raises(py.test.exc.Skipped, """
            py.test.importorskip("hello123", minversion="5.0")
        """)
    except py.test.exc.Skipped:
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
    """ % (str(py._pydir.dirpath())))
    import subprocess
    popen = subprocess.Popen([sys.executable, str(p)], stdout=subprocess.PIPE)
    s = popen.stdout.read()
    ret = popen.wait()
    assert ret == 0
