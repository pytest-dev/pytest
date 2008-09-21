
import py
import marshal
from py.__.test.outcome import Skipped

class TestRaises:
    def test_raises(self):
        py.test.raises(ValueError, "int('qwe')")

    def test_raises_exec(self):
        py.test.raises(ValueError, "a,x = []") 

    def test_raises_syntax_error(self):
        py.test.raises(SyntaxError, "qwe qwe qwe")

    def test_raises_function(self):
        py.test.raises(ValueError, int, 'hello')

#
# ============ test py.test.deprecated_call() ==============
#

def dep(i):
    if i == 0:
        py.std.warnings.warn("is deprecated", DeprecationWarning)
    return 42

reg = {}
def dep_explicit(i):
    if i == 0:
        py.std.warnings.warn_explicit("dep_explicit", category=DeprecationWarning, 
                                      filename="hello", lineno=3)

def test_deprecated_call_raises():
    excinfo = py.test.raises(AssertionError, 
                   "py.test.deprecated_call(dep, 3)")
    assert str(excinfo).find("did not produce") != -1 

def test_deprecated_call():
    py.test.deprecated_call(dep, 0)

def test_deprecated_call_ret():
    ret = py.test.deprecated_call(dep, 0)
    assert ret == 42

def test_deprecated_call_preserves():
    r = py.std.warnings.onceregistry.copy()
    f = py.std.warnings.filters[:]
    test_deprecated_call_raises()
    test_deprecated_call()
    assert r == py.std.warnings.onceregistry
    assert f == py.std.warnings.filters

def test_deprecated_explicit_call_raises():
    py.test.raises(AssertionError, 
                   "py.test.deprecated_call(dep_explicit, 3)")

def test_deprecated_explicit_call():
    py.test.deprecated_call(dep_explicit, 0)
    py.test.deprecated_call(dep_explicit, 0)

def test_skip_simple():
    excinfo = py.test.raises(Skipped, 'py.test.skip("xxx")')
    assert excinfo.traceback[-1].frame.code.name == "skip"
    assert excinfo.traceback[-1].ishidden()

def test_importorskip():
    try:
        sys = py.test.importorskip("sys")
        assert sys == py.std.sys
        #path = py.test.importorskip("os.path")
        #assert path == py.std.os.path
        py.test.raises(Skipped, "py.test.importorskip('alskdj')")
        py.test.raises(SyntaxError, "py.test.importorskip('x y z')")
        py.test.raises(SyntaxError, "py.test.importorskip('x=y')")
        path = py.test.importorskip("py", minversion=".".join(py.__version__))
        py.test.raises(Skipped, """
            py.test.importorskip("py", minversion="5.0")
        """)
    except Skipped:
        print py.code.ExceptionInfo()
        py.test.fail("spurious skip")

