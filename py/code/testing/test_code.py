from __future__ import generators
import py
import sys, new
from py.__.code.code import safe_repr

def test_newcode(): 
    source = "i = 3"
    co = compile(source, '', 'exec') 
    code = py.code.Code(co) 
    newco = code.new() 
    assert co == newco 

def test_ne():
    code1 = py.code.Code(compile('foo = "bar"', '', 'exec'))
    assert code1 == code1
    code2 = py.code.Code(compile('foo = "baz"', '', 'exec'))
    assert code2 != code1

def test_newcode_unknown_args(): 
    code = py.code.Code(compile("", '', 'exec'))
    py.test.raises(TypeError, 'code.new(filename="hello")')

def test_newcode_withfilename():
    source = py.code.Source("""
        def f():
            def g():
                pass
    """)
    co = compile(str(source)+'\n', 'nada', 'exec')
    obj = 'hello'
    newco = py.code.Code(co).new(rec=True, co_filename=obj)
    def walkcode(co):
        for x in co.co_consts:
            if isinstance(x, type(co)):
                for y in walkcode(x):
                    yield y
        yield co

    names = []
    for code in walkcode(newco):
        assert newco.co_filename == obj
        assert newco.co_filename is obj
        names.append(code.co_name)
    assert 'f' in names
    assert 'g' in names

def test_newcode_with_filename(): 
    source = "i = 3"
    co = compile(source, '', 'exec') 
    code = py.code.Code(co) 
    class MyStr(str): 
        pass 
    filename = MyStr("hello") 
    filename.__source__ = py.code.Source(source) 
    newco = code.new(rec=True, co_filename=filename) 
    assert newco.co_filename is filename 
    s = py.code.Source(newco) 
    assert str(s) == source 


def test_new_code_object_carries_filename_through():
    class mystr(str):
        pass
    filename = mystr("dummy")
    co = compile("hello\n", filename, 'exec')
    assert not isinstance(co.co_filename, mystr)
    c2 = new.code(co.co_argcount, co.co_nlocals, co.co_stacksize,
             co.co_flags, co.co_code, co.co_consts,
             co.co_names, co.co_varnames,
             filename,
             co.co_name, co.co_firstlineno, co.co_lnotab,
             co.co_freevars, co.co_cellvars)
    assert c2.co_filename is filename

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



class TestSafeRepr:
    def test_simple_repr(self):
        assert safe_repr(1) == '1'
        assert safe_repr(None) == 'None'
    
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
        assert 'Exception' in safe_repr(BrokenRepr(Exception("broken")))
        s = safe_repr(BrokenReprException("really broken"))
        assert 'TypeError' in s
        if py.std.sys.version_info < (2,6):
            assert 'unknown' in safe_repr(BrokenRepr("string"))
        else:
            assert 'TypeError' in safe_repr(BrokenRepr("string"))

    def test_big_repr(self):
        from py.__.code.code import SafeRepr
        assert len(safe_repr(range(1000))) <= \
               len('[' + SafeRepr().maxlist * "1000" + ']')

    def test_repr_on_newstyle(self):
        class Function(object):
            def __repr__(self):
                return "<%s>" %(self.name)
        try:
            s = safe_repr(Function())
        except Exception, e:
            py.test.fail("saferepr failed for newstyle class")
  
def test_builtin_patch_unpatch(monkeypatch):
    import __builtin__ as cpy_builtin
    comp = cpy_builtin.compile 
    def mycompile(*args, **kwargs):
        return comp(*args, **kwargs)
    monkeypatch.setattr(cpy_builtin, 'AssertionError', None)
    monkeypatch.setattr(cpy_builtin, 'compile', mycompile)
    py.code.patch_builtins()
    assert cpy_builtin.AssertionError
    assert cpy_builtin.compile != mycompile
    py.code.unpatch_builtins()
    assert cpy_builtin.AssertionError is None
    assert cpy_builtin.compile == mycompile 

