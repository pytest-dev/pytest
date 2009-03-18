import py
from py.__.code.excinfo import FormattedExcinfo, ReprExceptionInfo

class TWMock: 
    def __init__(self):
        self.lines = []
    def sep(self, sep, line=None):
        self.lines.append((sep, line))
    def line(self, line, **kw):
        self.lines.append(line)
    def markup(self, text, **kw):
        return text

    fullwidth = 80

def test_excinfo_simple():
    try:
        raise ValueError
    except ValueError:
        info = py.code.ExceptionInfo()
    assert info.type == ValueError

def test_excinfo_getstatement():
    def g():
        raise ValueError
    def f():
        g()
    try:
        f()
    except ValueError:
        excinfo = py.code.ExceptionInfo()
    linenumbers = [f.func_code.co_firstlineno-1+3,
                   f.func_code.co_firstlineno-1+1,
                   g.func_code.co_firstlineno-1+1,]
    l = list(excinfo.traceback)
    foundlinenumbers = [x.lineno for x in l]
    print l[0].frame.statement
    assert foundlinenumbers == linenumbers
    #for x in info:
    #    print "%s:%d  %s" %(x.path.relto(root), x.lineno, x.statement)
    #xxx

# testchain for getentries test below
def f():
    #
    raise ValueError
    #
def g():
    #
    __tracebackhide__ = True
    f()
    #
def h():
    #
    g()
    #

class TestTraceback_f_g_h: 
    def setup_method(self, method): 
        try:
            h()
        except ValueError:
            self.excinfo = py.code.ExceptionInfo()

    def test_traceback_entries(self):
        tb = self.excinfo.traceback 
        entries = list(tb) 
        assert len(tb) == 4 # maybe fragile test 
        assert len(entries) == 4 # maybe fragile test 
        names = ['f', 'g', 'h']
        for entry in entries:
            try:
                names.remove(entry.frame.code.name)
            except ValueError:
                pass
        assert not names

    def test_traceback_entry_getsource(self):
        tb = self.excinfo.traceback 
        s = str(tb[-1].getsource() )
        assert s.startswith("def f():")
        assert s.endswith("raise ValueError") 

    def test_traceback_entry_getsource_in_construct(self):
        source = py.code.Source("""\
            def xyz():
                try:
                    raise ValueError
                except somenoname:
                    pass
            xyz()
        """) 
        try: 
            exec source.compile()
        except NameError: 
            tb = py.code.ExceptionInfo().traceback 
            print tb[-1].getsource()
            s = str(tb[-1].getsource())
            assert s.startswith("def xyz():\n    try:")
            assert s.endswith("except somenoname:") 

    def test_traceback_cut(self):
        co = py.code.Code(f)
        path, firstlineno = co.path, co.firstlineno 
        traceback = self.excinfo.traceback 
        newtraceback = traceback.cut(path=path, firstlineno=firstlineno)
        assert len(newtraceback) == 1
        newtraceback = traceback.cut(path=path, lineno=firstlineno+2)
        assert len(newtraceback) == 1

    def test_traceback_cut_excludepath(self, testdir):
        p = testdir.makepyfile("def f(): raise ValueError")
        excinfo = py.test.raises(ValueError, "p.pyimport().f()")
        print excinfo.traceback
        pydir = py.path.local(py.__file__).dirpath()
        newtraceback = excinfo.traceback.cut(excludepath=pydir)
        assert len(newtraceback) == 1
        assert newtraceback[0].frame.code.path == p

    def test_traceback_filter(self):
        traceback = self.excinfo.traceback
        ntraceback = traceback.filter()
        assert len(ntraceback) == len(traceback) - 1

    def test_traceback_recursion_index(self):
        def f(n):
            if n < 10:
                n += 1
            f(n)
        excinfo = py.test.raises(RuntimeError, f, 8)
        traceback = excinfo.traceback 
        recindex = traceback.recursionindex() 
        assert recindex == 3

    def test_traceback_no_recursion_index(self):
        def do_stuff():
            raise RuntimeError
        def reraise_me():
            import sys
            exc, val, tb = sys.exc_info()
            raise exc, val, tb
        def f(n):
            try:
                do_stuff()
            except:
                reraise_me()
        excinfo = py.test.raises(RuntimeError, f, 8)
        traceback = excinfo.traceback 
        recindex = traceback.recursionindex() 
        assert recindex is None

    def test_traceback_getcrashentry(self):
        def i():
            __tracebackhide__ = True
            raise ValueError 
        def h():
            i()
        def g():
            __tracebackhide__ = True
            h()
        def f():
            g()

        excinfo = py.test.raises(ValueError, f)
        tb = excinfo.traceback
        entry = tb.getcrashentry()
        co = py.code.Code(h)
        assert entry.frame.code.path == co.path
        assert entry.lineno == co.firstlineno + 1 
        assert entry.frame.code.name == 'h'

    def test_traceback_getcrashentry_empty(self):
        def g():
            __tracebackhide__ = True
            raise ValueError 
        def f():
            __tracebackhide__ = True
            g()

        excinfo = py.test.raises(ValueError, f)
        tb = excinfo.traceback
        entry = tb.getcrashentry()
        co = py.code.Code(g)
        assert entry.frame.code.path == co.path
        assert entry.lineno == co.firstlineno + 2
        assert entry.frame.code.name == 'g'

def hello(x): 
    x + 5 

def test_tbentry_reinterpret(): 
    try: 
        hello("hello") 
    except TypeError: 
        excinfo = py.code.ExceptionInfo() 
    tbentry = excinfo.traceback[-1]
    msg = tbentry.reinterpret() 
    assert msg.startswith("TypeError: ('hello' + 5)") 

def test_excinfo_exconly():
    excinfo = py.test.raises(ValueError, h)
    assert excinfo.exconly().startswith('ValueError')

def test_excinfo_repr():
    excinfo = py.test.raises(ValueError, h)
    s = repr(excinfo)
    assert s == "<ExceptionInfo ValueError tblen=4>"

def test_excinfo_str():
    excinfo = py.test.raises(ValueError, h)
    s = str(excinfo)
    print s
    assert s.startswith(__file__[:-1]) # pyc file 
    assert s.endswith("ValueError")
    assert len(s.split(":")) >= 3 # on windows it's 4

def test_excinfo_errisinstance():
    excinfo = py.test.raises(ValueError, h)
    assert excinfo.errisinstance(ValueError) 

def test_excinfo_no_sourcecode():
    try:
        exec "raise ValueError()"
    except ValueError: 
        excinfo = py.code.ExceptionInfo()
    s = str(excinfo.traceback[-1])
    if py.std.sys.version_info < (2,5):
        assert s == "  File '<string>':1 in ?\n  ???\n"
    else:
        assert s == "  File '<string>':1 in <module>\n  ???\n"
    
def test_entrysource_Queue_example():
    import Queue
    try:
        Queue.Queue().get(timeout=0.001)
    except Queue.Empty:
        excinfo = py.code.ExceptionInfo()
    entry = excinfo.traceback[-1]
    source = entry.getsource()
    assert source is not None
    s = str(source).strip()
    assert s.startswith("def get")

def test_codepath_Queue_example():
    py.test.skip("try harder to get at the paths of code objects.")
    import Queue
    try:
        Queue.Queue().get(timeout=0.001)
    except Queue.Empty:
        excinfo = py.code.ExceptionInfo()
    entry = excinfo.traceback[-1]
    path = entry.path
    assert isinstance(path, py.path.local)
    assert path.basename == "Queue.py"
    assert path.check()

class TestFormattedExcinfo: 
    def setup_method(self, method):
        self.tmpdir = py.test.ensuretemp("%s_%s" %(
            self.__class__.__name__, method.__name__))

    def importasmod(self, source):
        source = py.code.Source(source)
        modpath = self.tmpdir.join("mod.py")
        self.tmpdir.ensure("__init__.py")
        modpath.write(source)
        return modpath.pyimport()

    def excinfo_from_exec(self, source):
        source = py.code.Source(source).strip()
        try:
            exec source.compile()
        except KeyboardInterrupt:
            raise
        except:
            return py.code.ExceptionInfo()
        assert 0, "did not raise"

    def test_repr_source(self):
        pr = FormattedExcinfo()
        source = py.code.Source("""
            def f(x):
                pass
        """).strip()
        pr.flow_marker = "|"
        lines = pr.get_source(source, 0)
        assert len(lines) == 2
        assert lines[0] == "|   def f(x):"
        assert lines[1] == "        pass"

    def test_repr_source_excinfo(self):
        """ check if indentation is right """
        pr = FormattedExcinfo()
        excinfo = self.excinfo_from_exec("""
            def f():
                assert 0
            f()
        """)
        pr = FormattedExcinfo()
        source = pr._getentrysource(excinfo.traceback[-1])
        lines = pr.get_source(source, 1, excinfo)
        print lines
        assert lines == [
            '    def f():', 
            '>       assert 0', 
            'E       assert 0'
        ]


    def test_repr_source_not_existing(self):
        pr = FormattedExcinfo()
        co = compile("raise ValueError()", "", "exec")
        try:
            exec co 
        except ValueError:
            excinfo = py.code.ExceptionInfo()
        repr = pr.repr_excinfo(excinfo)
        assert repr.reprtraceback.reprentries[1].lines[0] == ">   ???"

    def test_repr_many_line_source_not_existing(self):
        pr = FormattedExcinfo()
        co = compile("""
a = 1        
raise ValueError()
""", "", "exec")
        try:
            exec co 
        except ValueError:
            excinfo = py.code.ExceptionInfo()
        repr = pr.repr_excinfo(excinfo)
        assert repr.reprtraceback.reprentries[1].lines[0] == ">   ???"

    def test_repr_source_failing_fullsource(self):
        pr = FormattedExcinfo()

        class FakeCode(object):
            path = '?'
            firstlineno = 5

            def fullsource(self):
                return None
            fullsource = property(fullsource)

        class FakeFrame(object):
            code = FakeCode()
            f_locals = {}

        class FakeTracebackEntry(py.code.Traceback.Entry):
            def __init__(self, tb):
                self.frame = FakeFrame()
                self.lineno = 5+3

        class Traceback(py.code.Traceback):
            Entry = FakeTracebackEntry

        class FakeExcinfo(py.code.ExceptionInfo):
            typename = "Foo"
            def __init__(self):
                pass
            
            def exconly(self, tryshort):
                return "EXC"
            def errisinstance(self, cls):
                return False 

        excinfo = FakeExcinfo()
        class FakeRawTB(object):
            tb_next = None
        tb = FakeRawTB()
        excinfo.traceback = Traceback(tb)

        fail = IOError()
        repr = pr.repr_excinfo(excinfo)
        assert repr.reprtraceback.reprentries[0].lines[0] == ">   ???"

        fail = py.error.ENOENT
        repr = pr.repr_excinfo(excinfo)
        assert repr.reprtraceback.reprentries[0].lines[0] == ">   ???"        
        

    def test_repr_local(self):
        p = FormattedExcinfo(showlocals=True)
        loc = {'y': 5, 'z': 7, 'x': 3, '__builtins__': __builtins__}
        reprlocals = p.repr_locals(loc) 
        assert reprlocals.lines 
        print reprlocals.lines
        assert reprlocals.lines[0] == '__builtins__ = <builtins>'
        assert reprlocals.lines[1] == 'x          = 3'
        assert reprlocals.lines[2] == 'y          = 5'
        assert reprlocals.lines[3] == 'z          = 7'

    def test_repr_tracebackentry_lines(self):
        mod = self.importasmod("""
            def func1():
                raise ValueError("hello\\nworld")
        """)
        excinfo = py.test.raises(ValueError, mod.func1)
        excinfo.traceback = excinfo.traceback.filter()
        p = FormattedExcinfo()
        reprtb = p.repr_traceback_entry(excinfo.traceback[-1])
        print reprtb
        
        # test as intermittent entry
        lines = reprtb.lines
        assert lines[0] == '    def func1():'
        assert lines[1] == '>       raise ValueError("hello\\nworld")'

        # test as last entry 
        p = FormattedExcinfo(showlocals=True)
        repr_entry = p.repr_traceback_entry(excinfo.traceback[-1], excinfo)
        lines = repr_entry.lines
        assert lines[0] == '    def func1():'
        assert lines[1] == '>       raise ValueError("hello\\nworld")'
        assert lines[2] == 'E       ValueError: hello'
        assert lines[3] == 'E       world'
        assert not lines[4:]

        loc = repr_entry.reprlocals is not None
        loc = repr_entry.reprfileloc 
        assert loc.path == mod.__file__
        assert loc.lineno == 3
        #assert loc.message == "ValueError: hello"

    def test_repr_tracebackentry_lines(self):
        mod = self.importasmod("""
            def func1(m, x, y, z):
                raise ValueError("hello\\nworld")
        """)
        excinfo = py.test.raises(ValueError, mod.func1, "m"*90, 5, 13, "z"*120)
        excinfo.traceback = excinfo.traceback.filter()
        entry = excinfo.traceback[-1]
        p = FormattedExcinfo(funcargs=True)
        reprfuncargs = p.repr_args(entry)
        assert reprfuncargs.args[0] == ('m', repr("m"*90))
        assert reprfuncargs.args[1] == ('x', '5')
        assert reprfuncargs.args[2] == ('y', '13')
        assert reprfuncargs.args[3] == ('z', repr("z" * 120))

        p = FormattedExcinfo(funcargs=True)
        repr_entry = p.repr_traceback_entry(entry)
        assert repr_entry.reprfuncargs.args == reprfuncargs.args
        tw = TWMock()
        repr_entry.toterminal(tw)
        assert tw.lines[0] == "m = " + repr('m' * 90)
        assert tw.lines[1] == "x = 5, y = 13"
        assert tw.lines[2] == "z = " + repr('z' * 120)

    def test_repr_tracebackentry_short(self):
        mod = self.importasmod("""
            def func1():
                raise ValueError("hello")
            def entry():
                func1()
        """)
        excinfo = py.test.raises(ValueError, mod.entry)
        p = FormattedExcinfo(style="short")
        reprtb = p.repr_traceback_entry(excinfo.traceback[-2])
        lines = reprtb.lines
        basename = py.path.local(mod.__file__).basename
        assert lines[0] == '  File "%s", line 5, in entry' % basename 
        assert lines[1] == '    func1()' 

        # test last entry 
        p = FormattedExcinfo(style="short")
        reprtb = p.repr_traceback_entry(excinfo.traceback[-1], excinfo)
        lines = reprtb.lines
        assert lines[0] == '  File "%s", line 3, in func1' % basename 
        assert lines[1] == '    raise ValueError("hello")'
        assert lines[2] == 'E   ValueError: hello'

    def test_repr_tracebackentry_no(self):
        mod = self.importasmod("""
            def func1():
                raise ValueError("hello")
            def entry():
                func1()
        """)
        excinfo = py.test.raises(ValueError, mod.entry)
        p = FormattedExcinfo(style="no")
        p.repr_traceback_entry(excinfo.traceback[-2])

        p = FormattedExcinfo(style="no")
        reprentry = p.repr_traceback_entry(excinfo.traceback[-1], excinfo)
        lines = reprentry.lines
        assert lines[0] == 'E   ValueError: hello'
        assert not lines[1:] 

    def test_repr_traceback_tbfilter(self):
        mod = self.importasmod("""
            def f(x):
                raise ValueError(x)
            def entry():
                f(0)
        """)
        excinfo = py.test.raises(ValueError, mod.entry)
        p = FormattedExcinfo(tbfilter=True)
        reprtb = p.repr_traceback(excinfo)
        assert len(reprtb.reprentries) == 2
        p = FormattedExcinfo(tbfilter=False)
        reprtb = p.repr_traceback(excinfo)
        assert len(reprtb.reprentries) == 3

    def test_repr_traceback_and_excinfo(self):
        mod = self.importasmod("""
            def f(x):
                raise ValueError(x)
            def entry():
                f(0)
        """)
        excinfo = py.test.raises(ValueError, mod.entry)
      
        for style in ("long", "short"):
            p = FormattedExcinfo(style=style)
            reprtb = p.repr_traceback(excinfo)
            assert len(reprtb.reprentries) == 2
            assert reprtb.style == style
            assert not reprtb.extraline
            repr = p.repr_excinfo(excinfo)
            assert repr.reprtraceback 
            assert len(repr.reprtraceback.reprentries) == len(reprtb.reprentries)
            assert repr.reprcrash.path.endswith("mod.py")
            assert repr.reprcrash.message == "ValueError: 0"

    def test_repr_excinfo_addouterr(self):
        mod = self.importasmod("""
            def entry():
                raise ValueError()
        """)
        excinfo = py.test.raises(ValueError, mod.entry)
        repr = excinfo.getrepr()
        repr.addsection("title", "content")
        twmock = TWMock()
        repr.toterminal(twmock)
        assert twmock.lines[-1] == "content"
        assert twmock.lines[-2] == ("-", "title")

    def test_repr_excinfo_reprcrash(self):
        mod = self.importasmod("""
            def entry():
                raise ValueError()
        """)
        excinfo = py.test.raises(ValueError, mod.entry)
        repr = excinfo.getrepr()
        assert repr.reprcrash.path.endswith("mod.py")
        assert repr.reprcrash.lineno == 3
        assert repr.reprcrash.message == "ValueError"
        assert str(repr.reprcrash).endswith("mod.py:3: ValueError")

    def test_repr_traceback_recursion(self):
        mod = self.importasmod("""
            def rec2(x):
                return rec1(x+1)
            def rec1(x):
                return rec2(x-1)
            def entry():
                rec1(42)
        """)
        excinfo = py.test.raises(RuntimeError, mod.entry)

        for style in ("short", "long", "no"):
            p = FormattedExcinfo(style="short")
            reprtb = p.repr_traceback(excinfo)
            assert reprtb.extraline == "!!! Recursion detected (same locals & position)"
            assert str(reprtb)

    def test_tb_entry_AssertionError(self):
        # probably this test is a bit redundant 
        # as py/magic/testing/test_assertion.py
        # already tests correctness of
        # assertion-reinterpretation  logic 
        mod = self.importasmod("""
            def somefunc():
                x = 1
                assert x == 2
        """)
        py.magic.invoke(assertion=True)
        try:
            excinfo = py.test.raises(AssertionError, mod.somefunc)
        finally:
            py.magic.revoke(assertion=True)
            
        p = FormattedExcinfo()
        reprentry = p.repr_traceback_entry(excinfo.traceback[-1], excinfo)
        lines = reprentry.lines
        assert lines[-1] == "E       assert 1 == 2"

    def test_reprexcinfo_getrepr(self):
        mod = self.importasmod("""
            def f(x):
                raise ValueError(x)
            def entry():
                f(0)
        """)
        excinfo = py.test.raises(ValueError, mod.entry)

        for style in ("short", "long", "no"):
            for showlocals in (True, False):
                repr = excinfo.getrepr(style=style, showlocals=showlocals)
                assert isinstance(repr, ReprExceptionInfo)
                assert repr.reprtraceback.style == style 
         
    def test_toterminal_long(self):
        mod = self.importasmod("""
            def g(x):
                raise ValueError(x)
            def f():
                g(3)
        """)
        excinfo = py.test.raises(ValueError, mod.f)
        excinfo.traceback = excinfo.traceback.filter()
        repr = excinfo.getrepr()
        tw = TWMock()
        repr.toterminal(tw)
        assert tw.lines[0] == ""
        tw.lines.pop(0)
        assert tw.lines[0] == "    def f():" 
        assert tw.lines[1] == ">       g(3)"
        assert tw.lines[2] == ""
        assert tw.lines[3].endswith("mod.py:5: ")
        assert tw.lines[4] == ("_ ", None)
        assert tw.lines[5] == ""
        assert tw.lines[6] == "    def g(x):"
        assert tw.lines[7] == ">       raise ValueError(x)"
        assert tw.lines[8] == "E       ValueError: 3"
        assert tw.lines[9] == ""
        assert tw.lines[10].endswith("mod.py:3: ValueError")


    def test_format_excinfo(self):
        mod = self.importasmod("""
            def g(x):
                raise ValueError(x)
            def f():
                g(3)
        """)
        excinfo = py.test.raises(ValueError, mod.f)
        def format_and_str(kw):
            tw = py.io.TerminalWriter(stringio=True)
            repr = excinfo.getrepr(**kw)
            repr.toterminal(tw)
            assert tw.stringio.getvalue()
           
        for combo in self.allcombos():
            yield format_and_str, combo

    def allcombos(self): 
        for style in ("long", "short", "no"):
            for showlocals in (True, False):
                for tbfilter in (True, False):
                    for funcargs in (True, False):
                        kw = {'style': style, 
                              'showlocals': showlocals, 
                              'funcargs': funcargs, 
                              'tbfilter': tbfilter
                        }
                        yield kw
