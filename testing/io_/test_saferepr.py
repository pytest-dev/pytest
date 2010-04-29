from __future__ import generators
import py
import sys

saferepr = py.io.saferepr

class TestSafeRepr:
    def test_simple_repr(self):
        assert saferepr(1) == '1'
        assert saferepr(None) == 'None'

    def test_maxsize(self):
        s = saferepr('x'*50, maxsize=25)
        assert len(s) == 25
        expected = repr('x'*10 + '...' + 'x'*10)
        assert s == expected

    def test_maxsize_error_on_instance(self):
        class A:
            def __repr__(self):
                raise ValueError('...')

        s = saferepr(('*'*50, A()), maxsize=25)
        assert len(s) == 25
        assert s[0] == '(' and s[-1] == ')'
    
    def test_exceptions(self):
        class BrokenRepr:
            def __init__(self, ex):
                self.ex = ex
                foo = 0
            def __repr__(self):
                raise self.ex
        class BrokenReprException(Exception):
            __str__ = None 
            __repr__ = None
        assert 'Exception' in saferepr(BrokenRepr(Exception("broken")))
        s = saferepr(BrokenReprException("really broken"))
        assert 'TypeError' in s
        if py.std.sys.version_info < (2,6):
            assert 'unknown' in saferepr(BrokenRepr("string"))
        else:
            assert 'TypeError' in saferepr(BrokenRepr("string"))

    def test_big_repr(self):
        from py._io.saferepr import SafeRepr
        assert len(saferepr(range(1000))) <= \
               len('[' + SafeRepr().maxlist * "1000" + ']')

    def test_repr_on_newstyle(self):
        class Function(object):
            def __repr__(self):
                return "<%s>" %(self.name)
        try:
            s = saferepr(Function())
        except Exception:
            py.test.fail("saferepr failed for newstyle class")
  
def test_builtin_patch_unpatch(monkeypatch):
    cpy_builtin = py.builtin.builtins
    comp = cpy_builtin.compile 
    def mycompile(*args, **kwargs):
        return comp(*args, **kwargs)
    class Sub(AssertionError):
        pass
    monkeypatch.setattr(cpy_builtin, 'AssertionError', Sub)
    monkeypatch.setattr(cpy_builtin, 'compile', mycompile)
    py.code.patch_builtins()
    assert cpy_builtin.AssertionError != Sub
    assert cpy_builtin.compile != mycompile
    py.code.unpatch_builtins()
    assert cpy_builtin.AssertionError is Sub 
    assert cpy_builtin.compile == mycompile 


def test_unicode_handling():
    value = py.builtin._totext('\xc4\x85\xc4\x87\n', 'utf-8').encode('utf8')
    def f():
        raise Exception(value)
    excinfo = py.test.raises(Exception, f)
    s = str(excinfo)
    if sys.version_info[0] < 3:
        u = unicode(excinfo)

def test_unicode_or_repr():
    from py._code.code import unicode_or_repr 
    assert unicode_or_repr('hello') == "hello"
    if sys.version_info[0] < 3:
        s = unicode_or_repr('\xf6\xc4\x85')
    else:
        s = eval("unicode_or_repr(b'\\f6\\xc4\\x85')")
    assert 'print-error' in s
    assert 'c4' in s
    class A:
        def __repr__(self):
            raise ValueError()
    s = unicode_or_repr(A())
    assert 'print-error' in s
    assert 'ValueError' in s
