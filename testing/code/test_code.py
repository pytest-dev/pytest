import py
import sys

def test_ne():
    code1 = py.code.Code(compile('foo = "bar"', '', 'exec'))
    assert code1 == code1
    code2 = py.code.Code(compile('foo = "baz"', '', 'exec'))
    assert code2 != code1

def test_code_gives_back_name_for_not_existing_file():
    name = 'abc-123'
    co_code = compile("pass\n", name, 'exec')
    assert co_code.co_filename == name
    code = py.code.Code(co_code)
    assert str(code.path) == name
    assert code.fullsource is None

def test_code_with_class():
    class A:
        pass
    py.test.raises(TypeError, "py.code.Code(A)")

if True:
    def x():
        pass

def test_code_fullsource():
    code = py.code.Code(x)
    full = code.fullsource
    assert 'test_code_fullsource()' in str(full)

def test_code_source():
    code = py.code.Code(x)
    src = code.source()
    expected = """def x():
    pass"""
    assert str(src) == expected

def test_frame_getsourcelineno_myself():
    def func():
        return sys._getframe(0)
    f = func()
    f = py.code.Frame(f)
    source, lineno = f.code.fullsource, f.lineno
    assert source[lineno].startswith("        return sys._getframe(0)")

def test_getstatement_empty_fullsource():
    def func():
        return sys._getframe(0)
    f = func()
    f = py.code.Frame(f)
    prop = f.code.__class__.fullsource
    try:
        f.code.__class__.fullsource = None
        assert f.statement == py.code.Source("")
    finally:
        f.code.__class__.fullsource = prop

def test_code_from_func():
    co = py.code.Code(test_frame_getsourcelineno_myself)
    assert co.firstlineno
    assert co.path



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
