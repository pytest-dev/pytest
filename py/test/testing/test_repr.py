
import py
from py.__.test.representation import Presenter
from py.__.test.terminal.out import getout
from StringIO import StringIO
import sys

def newconfig(*args):
    tmpdir = py.test.ensuretemp("newconfig")
    args = list(args)
    args.append(tmpdir)
    return py.test.config._reparse(args)
    
def test_repr_source():
    source = py.code.Source("""
    def f(x):
        pass
    """).strip()
    config = newconfig()
    s = StringIO()
    out = getout(s)
    p = Presenter(out, config)
    p.repr_source(source, "|", 0)
    lines = s.getvalue().split("\n")
    assert len(lines) == 3
    assert lines[0].startswith("|")
    assert lines[0].find("def f(x)") != -1
    assert lines[1].find("pass") != -1

def test_repr_failure_explanation():
    """ We check here if indentation is right
    """
    def f():
        def g():
            1/0
        try:
            g()
        except:
            e = py.code.ExceptionInfo()
        return e
    config = newconfig()
    s = StringIO()
    out = getout(s)
    p = Presenter(out, config)
    source = py.code.Source(f)
    e = f()
    p.repr_failure_explanation(e, source)
    assert s.getvalue().startswith(">   ")

def test_repr_local():
    config = newconfig('--showlocals')
    s = StringIO()
    out = getout(s)
    p = Presenter(out, config)
    p.repr_locals(locals())
    for key in locals().keys():
        assert s.getvalue().find(key) != -1

def test_repr_traceback_long():
    py.test.skip("unfinished")
    config = py.test.config._reparse([])
    s = StringIO()
    out = getout(s)
    p = Presenter(out, config)
    # errr... here we should
    # a) prepare an item
    # b) prepare excinfo
    # c) prepare some traceback info, with few different ideas,
    #    like recursion detected etc.
    # test it...
