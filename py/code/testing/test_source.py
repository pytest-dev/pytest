from py.code import Source
import py
import sys

def test_source_str_function():
    x = Source("3")
    assert str(x) == "3"

    x = Source("   3")
    assert str(x) == "3"

    x = Source("""
        3
    """, rstrip=False)
    assert str(x) == "\n3\n    "

    x = Source("""
        3
    """, rstrip=True)
    assert str(x) == "\n3"

def test_unicode(): 
    x = Source(unicode("4"))
    assert str(x) == "4"


def test_source_from_function():
    source = py.code.Source(test_source_str_function)
    assert str(source).startswith('def test_source_str_function():')

def test_source_from_inner_function():
    def f():
        pass
    source = py.code.Source(f, deindent=False)
    assert str(source).startswith('    def f():')
    source = py.code.Source(f)
    assert str(source).startswith('def f():')

def test_source_putaround_simple():
    source = Source("raise ValueError")
    source = source.putaround(
        "try:", """\
        except ValueError:
            x = 42
        else:
            x = 23""")
    assert str(source)=="""\
try:
    raise ValueError
except ValueError:
    x = 42
else:
    x = 23"""

def test_source_putaround(): 
    source = Source() 
    source = source.putaround("""
        if 1:
            x=1
    """)
    assert str(source).strip() == "if 1:\n    x=1"

def test_source_strips(): 
    source = Source("")
    assert source == Source()
    assert str(source) == ''
    assert source.strip() == source 

def test_source_strip_multiline(): 
    source = Source()
    source.lines = ["", " hello", "  "]
    source2 = source.strip() 
    assert source2.lines == [" hello"]

def test_syntaxerror_rerepresentation():
    ex = py.test.raises(SyntaxError, py.code.compile, 'x x')
    assert ex.value.lineno == 1
    assert ex.value.offset == 3
    assert ex.value.text.strip(), 'x x'

def test_isparseable():
    assert Source("hello").isparseable()
    assert Source("if 1:\n  pass").isparseable()
    assert Source(" \nif 1:\n  pass").isparseable()
    assert not Source("if 1:\n").isparseable() 
    assert not Source(" \nif 1:\npass").isparseable()

class TestAccesses:
    source = Source("""\
        def f(x):
            pass
        def g(x):
            pass
    """)
    def test_getrange(self):
        x = self.source[0:2]
        assert x.isparseable()
        assert len(x.lines) == 2
        assert str(x) == "def f(x):\n    pass"

    def test_getline(self):
        x = self.source[0]
        assert x == "def f(x):"

    def test_len(self):
        assert len(self.source) == 4 

    def test_iter(self):
        l = [x for x in self.source] 
        assert len(l) == 4 
            
class TestSourceParsingAndCompiling:
    source = Source("""\
        def f(x):
            assert (x ==
                    3 +
                    4)
    """).strip()

    def test_compile(self):
        co = py.code.compile("x=3")
        exec co
        assert x == 3

    def test_compile_unicode(self): 
        co = py.code.compile(unicode('u"\xc3\xa5"', 'utf8'), mode='eval')
        val = eval(co) 
        assert isinstance(val, unicode)

    def test_compile_and_getsource_simple(self):
        co = py.code.compile("x=3")
        exec co
        source = py.code.Source(co)
        assert str(source) == "x=3"

    def test_getstatement(self):
        #print str(self.source)
        ass = str(self.source[1:])
        for i in range(1, 4):
            #print "trying start in line %r" % self.source[i]
            s = self.source.getstatement(i)
            #x = s.deindent()
            assert str(s) == ass

    def test_getstatementrange_within_constructs(self):
        source = Source("""\
            try:
                try: 
                    raise ValueError
                except SomeThing: 
                    pass 
            finally:
                42
        """)
        assert len(source) == 7
        assert source.getstatementrange(0) == (0, 7) 
        assert source.getstatementrange(1) == (1, 5) 
        assert source.getstatementrange(2) == (2, 3)
        assert source.getstatementrange(3) == (1, 5)
        assert source.getstatementrange(4) == (4, 5) 
        assert source.getstatementrange(5) == (0, 7)
        assert source.getstatementrange(6) == (6, 7) 

    def test_getstatementrange_bug(self):
        source = Source("""\
            try:
                x = (
                   y +
                   z)
            except:
                pass
        """)
        assert len(source) == 6
        assert source.getstatementrange(2) == (1, 4)

    def test_getstatementrange_bug2(self):
        py.test.skip("fix me (issue19)")
        source = Source("""\
            assert (
                33
                ==
                [
                  X(3,
                      b=1, c=2
                   ),
                ]
              )
        """)
        assert len(source) == 9
        assert source.getstatementrange(5) == (0, 9)

    def test_compile_and_getsource(self):
        co = self.source.compile()
        exec co
        f(7)
        excinfo = py.test.raises(AssertionError, "f(6)")
        frame = excinfo.traceback[-1].frame 
        stmt = frame.code.fullsource.getstatement(frame.lineno)
        #print "block", str(block)
        assert str(stmt).strip().startswith('assert')

    def test_compilefuncs_and_path_sanity(self):
        def check(comp, name):
            co = comp(self.source, name)
            if not name:
                expected = "<codegen %s:%d>" %(mypath, mylineno+2+1)
            else:
                expected = "<codegen %r %s:%d>" % (name, mypath, mylineno+2+1)
            fn = co.co_filename
            assert fn == expected 

        mycode = py.code.Code(self.test_compilefuncs_and_path_sanity)
        mylineno = mycode.firstlineno
        mypath = mycode.path 
            
        for comp in py.code.compile, py.code.Source.compile:
            for name in '', None, 'my':
                yield check, comp, name

    def test_offsetless_synerr(self):
        py.test.raises(SyntaxError, py.code.compile, "lambda a,a: 0", mode='eval')

def test_getstartingblock_singleline():
    class A:
        def __init__(self, *args):
            frame = sys._getframe(1)
            self.source = py.code.Frame(frame).statement

    x = A('x', 'y')

    l = [i for i in x.source.lines if i.strip()]
    assert len(l) == 1

def test_getstartingblock_multiline():
    class A:
        def __init__(self, *args):
            frame = sys._getframe(1)
            self.source = py.code.Frame(frame).statement

    x = A('x',
          'y' \
          ,
          'z')

    l = [i for i in x.source.lines if i.strip()]
    assert len(l) == 4

def test_getline_finally():
    #py.test.skip("inner statements cannot be located yet.")
    def c(): pass
    excinfo = py.test.raises(TypeError, """
           teardown = None
           try:
                c(1)
           finally:
                if teardown:
                    teardown()
    """)
    source = excinfo.traceback[-1].statement
    assert str(source).strip() == 'c(1)'

def test_getfuncsource_dynamic():
    source = """
        def f():
            raise ValueError

        def g(): pass
    """
    co = py.code.compile(source)
    exec co
    assert str(py.code.Source(f)).strip() == 'def f():\n    raise ValueError'
    assert str(py.code.Source(g)).strip() == 'def g(): pass'


def test_getfuncsource_with_multine_string():
    def f():
        c = '''while True:
    pass
'''
    assert str(py.code.Source(f)).strip() == "def f():\n    c = '''while True:\n    pass\n'''"
    

def test_deindent():
    from py.__.code.source import deindent as deindent
    assert deindent(['\tfoo', '\tbar', ]) == ['foo', 'bar']

    def f():
        c = '''while True:
    pass
'''
    import inspect
    lines = deindent(inspect.getsource(f).splitlines())
    assert lines == ["def f():", "    c = '''while True:", "    pass", "'''"]

    source = """
        def f():
            def g():
                pass
    """
    lines = deindent(source.splitlines())
    assert lines == ['', 'def f():', '    def g():', '        pass', '    ']

def test_source_of_class_at_eof_without_newline():
    py.test.skip("CPython's inspect.getsource is buggy")
    # this test fails because the implicit inspect.getsource(A) below 
    # does not return the "x = 1" last line. 
    tmpdir = py.test.ensuretemp("source_write_read")
    source = py.code.Source('''
        class A(object):
            def method(self):
                x = 1
    ''')
    path = tmpdir.join("a.py")
    path.write(source)
    s2 = py.code.Source(tmpdir.join("a.py").pyimport().A)
    assert str(source).strip() == str(s2).strip()

if True:
    def x():
        pass

def test_getsource_fallback():
    from py.__.code.source import getsource
    expected = """def x():
    pass"""
    src = getsource(x)
    assert src == expected

def test_idem_compile_and_getsource():
    from py.__.code.source import getsource
    expected = "def x(): pass"
    co = py.code.compile(expected)
    src = getsource(co)
    assert src == expected

def test_findsource_fallback():
    from py.__.code.source import findsource
    src, lineno = findsource(x)
    assert 'test_findsource_simple' in str(src)
    assert src[lineno] == '    def x():'

def test_findsource___source__():
    from py.__.code.source import findsource
    co = py.code.compile("""if 1:
    def x():
        pass
""")
        
    src, lineno = findsource(co)
    assert 'if 1:' in str(src)

    d = {}
    eval(co, d)
    src, lineno = findsource(d['x'])
    assert 'if 1:' in str(src)
    assert src[lineno] == "    def x():"
    
