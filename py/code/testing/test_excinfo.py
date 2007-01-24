import py
mypath = py.magic.autopath()

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
        
    #def test_traceback_display_func(self):
    #    tb = self.excinfo.traceback 
    #    for x in tb: 
    #        x.setdisplay(lambda entry: entry.frame.code.name + '\n')
    ##    l = tb.display().rstrip().split('\n')
    #    assert l == ['setup_method', 'h', 'g', 'f']


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

#def test_excinfo_getentries_type_error():
#    excinfo = py.test.raises(ValueError, h)
#    entries = excinfo.getentries(
#            lambda x: x.frame.code.name != 'raises',
#            lambda x: x.frame.code.name != 'f')
#    names = [x.frame.code.name for x in entries]
#    assert names == ['h','g']

def test_excinfo_exconly():
    excinfo = py.test.raises(ValueError, h)
    assert excinfo.exconly().startswith('ValueError')

def test_excinfo_errisinstance():
    excinfo = py.test.raises(ValueError, h)
    assert excinfo.errisinstance(ValueError) 

def test_excinfo_no_sourcecode():
    try:
        exec "raise ValueError()"
    except ValueError: 
        excinfo = py.code.ExceptionInfo()
    s = str(excinfo.traceback[-1])
