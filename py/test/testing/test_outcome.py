
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

def test_skip_ifraises():
    excinfo = py.test.raises(Skipped, '''
        py.test.skip(ifraises="""
            import lky
        """)
    ''')
    assert excinfo.traceback[-1].frame.code.name == "skip"
    assert excinfo.traceback[-1].ishidden()
    assert excinfo.value.msg.startswith("ImportError")

def test_skip_ifraises_ns():
    d = {}
    py.test.skip(ns=d, ifraises="import py")
    assert d['py'] == py

def test_skip_ifraises_syntaxerror():
    try:
        excinfo = py.test.raises(SyntaxError, '''
            py.test.skip(ifraises="x y z")''')
    except Skipped:
        py.test.fail("should not skip")
    assert not excinfo.traceback[-1].ishidden()

