import sys
import py

def test_frame_getsourcelineno_myself():
    def func():
        return sys._getframe(0)
    f = func()
    f = py.code.Frame(f)
    source, lineno = f.code.fullsource, f.lineno
    assert source[lineno].startswith("        return sys._getframe(0)")

def test_code_from_func(): 
    co = py.code.Code(test_frame_getsourcelineno_myself) 
    assert co.firstlineno
    assert co.path
