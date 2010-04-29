import py
import os, sys
from py._io import terminalwriter 

def test_get_terminal_width():
    x = py.io.get_terminal_width
    assert x == terminalwriter.get_terminal_width

def test_terminal_width_COLUMNS(monkeypatch):
    """ Dummy test for get_terminal_width
    """
    fcntl = py.test.importorskip("fcntl") 
    monkeypatch.setattr(fcntl, 'ioctl', lambda *args: int('x'))
    monkeypatch.setenv('COLUMNS', '42')
    assert terminalwriter.get_terminal_width() == 42
    monkeypatch.delenv('COLUMNS', raising=False)

def test_terminalwriter_defaultwidth_80(monkeypatch):
    monkeypatch.setattr(terminalwriter, '_getdimensions', lambda: 0/0)
    monkeypatch.delenv('COLUMNS', raising=False)
    tw = py.io.TerminalWriter()  
    assert tw.fullwidth == 80

def test_terminalwriter_getdimensions_bogus(monkeypatch):
    monkeypatch.setattr(terminalwriter, '_getdimensions', lambda: (10,10))
    monkeypatch.delenv('COLUMNS', raising=False)
    tw = py.io.TerminalWriter()  
    assert tw.fullwidth == 80

def test_terminalwriter_computes_width(monkeypatch):
    monkeypatch.setattr(terminalwriter, 'get_terminal_width', lambda: 42)
    tw = py.io.TerminalWriter()  
    assert tw.fullwidth == 42
    
def test_terminalwriter_default_instantiation():
    tw = py.io.TerminalWriter(stringio=True)
    assert hasattr(tw, 'stringio')

def test_terminalwriter_dumb_term_no_markup(monkeypatch):
    monkeypatch.setattr(os, 'environ', {'TERM': 'dumb', 'PATH': ''})
    class MyFile:
        def isatty(self):
            return True
    monkeypatch.setattr(sys, 'stdout', MyFile())
    try:
        assert sys.stdout.isatty()
        tw = py.io.TerminalWriter()
        assert not tw.hasmarkup
    finally:
        monkeypatch.undo()

def test_unicode_encoding():
    msg = py.builtin._totext('b\u00f6y', 'utf8')
    for encoding in 'utf8', 'latin1':
        l = []
        tw = py.io.TerminalWriter(l.append, encoding=encoding)
        tw.line(msg)
        assert l[0].strip() == msg.encode(encoding)

class TestTerminalWriter:
    def pytest_generate_tests(self, metafunc):
        if "tw" in metafunc.funcargnames:
            metafunc.addcall(id="path", param="path")
            metafunc.addcall(id="stringio", param="stringio")
            metafunc.addcall(id="callable", param="callable")
    def pytest_funcarg__tw(self, request):
        if request.param == "path":
            tmpdir = request.getfuncargvalue("tmpdir")
            p = tmpdir.join("tmpfile")
            tw = py.io.TerminalWriter(p.open('w+'))
            def getlines():
                tw._file.flush()
                return p.open('r').readlines()
        elif request.param == "stringio":
            tw = py.io.TerminalWriter(stringio=True)
            def getlines():
                tw.stringio.seek(0)
                return tw.stringio.readlines()
        elif request.param == "callable":
            writes = []
            tw = py.io.TerminalWriter(writes.append)
            def getlines():
                io = py.io.TextIO()
                io.write("".join(writes))
                io.seek(0)
                return io.readlines()
        tw.getlines = getlines
        return tw

    def test_line(self, tw):    
        tw.line("hello")
        l = tw.getlines()
        assert len(l) == 1
        assert l[0] == "hello\n"

    def test_line_unicode(self, tw):    
        for encoding in 'utf8', 'latin1':
            tw._encoding = encoding 
            msg = py.builtin._totext('b\u00f6y', 'utf8')
            tw.line(msg)
            l = tw.getlines()
            assert l[0] == msg + "\n"

    def test_sep_no_title(self, tw):
        tw.sep("-", fullwidth=60) 
        l = tw.getlines()
        assert len(l) == 1
        assert l[0] == "-" * 60 + "\n"

    def test_sep_with_title(self, tw):
        tw.sep("-", "hello", fullwidth=60) 
        l = tw.getlines()
        assert len(l) == 1
        assert l[0] == "-" * 26 + " hello " + "-" * 27 + "\n"

    @py.test.mark.skipif("sys.platform == 'win32'")
    def test__escaped(self, tw):
        text2 = tw._escaped("hello", (31))
        assert text2.find("hello") != -1

    @py.test.mark.skipif("sys.platform == 'win32'")
    def test_markup(self, tw):
        for bold in (True, False):
            for color in ("red", "green"):
                text2 = tw.markup("hello", **{color: True, 'bold': bold})
                assert text2.find("hello") != -1
        py.test.raises(ValueError, "tw.markup('x', wronkw=3)")
        py.test.raises(ValueError, "tw.markup('x', wronkw=0)")

    def test_line_write_markup(self, tw):
        tw.hasmarkup = True
        tw.line("x", bold=True)
        tw.write("x\n", red=True)
        l = tw.getlines()
        if sys.platform != "win32":
            assert len(l[0]) >= 2, l
            assert len(l[1]) >= 2, l

    def test_attr_fullwidth(self, tw):
        tw.sep("-", "hello", fullwidth=70)
        tw.fullwidth = 70
        tw.sep("-", "hello")
        l = tw.getlines()
        assert len(l[0]) == len(l[1])


def test_attr_hasmarkup():
    tw = py.io.TerminalWriter(stringio=True)
    assert not tw.hasmarkup
    tw.hasmarkup = True
    tw.line("hello", bold=True)
    s = tw.stringio.getvalue()
    assert len(s) > len("hello")

def test_ansi_print():
    # we have no easy way to construct a file that
    # represents a terminal 
    f = py.io.TextIO()
    f.isatty = lambda: True
    py.io.ansi_print("hello", 0x32, file=f)
    text2 = f.getvalue()
    assert text2.find("hello") != -1
    assert len(text2) >= len("hello")
