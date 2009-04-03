import py
import os, sys
from py.__.io import terminalwriter 

def skip_win32():
    if sys.platform == 'win32':
        py.test.skip('Not relevant on win32')

def test_terminalwriter_computes_width(monkeypatch):
    monkeypatch.setattr(terminalwriter, 'get_terminal_width', lambda: 42)
    tw = py.io.TerminalWriter()  
    assert tw.fullwidth == 42

def test_terminalwriter_defaultwidth_80(monkeypatch):
    monkeypatch.setattr(terminalwriter, '_getdimensions', lambda: 0/0)
    tw = py.io.TerminalWriter()  
    assert tw.fullwidth == int(os.environ.get('COLUMNS', 80)) -1
    
def test_terminalwriter_default_instantiation():
    tw = py.io.TerminalWriter(stringio=True)
    assert hasattr(tw, 'stringio')

class BaseTests:
    def test_line(self):    
        tw = self.getwriter()
        tw.line("hello")
        l = self.getlines()
        assert len(l) == 1
        assert l[0] == "hello\n"

    def test_sep_no_title(self):
        tw = self.getwriter()
        tw.sep("-", fullwidth=60) 
        l = self.getlines()
        assert len(l) == 1
        assert l[0] == "-" * 60 + "\n"

    def test_sep_with_title(self):
        tw = self.getwriter()
        tw.sep("-", "hello", fullwidth=60) 
        l = self.getlines()
        assert len(l) == 1
        assert l[0] == "-" * 26 + " hello " + "-" * 27 + "\n"

    def test__escaped(self):
        skip_win32()
        tw = self.getwriter()
        text2 = tw._escaped("hello", (31))
        assert text2.find("hello") != -1

    def test_markup(self):
        skip_win32()
        tw = self.getwriter()
        for bold in (True, False):
            for color in ("red", "green"):
                text2 = tw.markup("hello", **{color: True, 'bold': bold})
                assert text2.find("hello") != -1
        py.test.raises(ValueError, "tw.markup('x', wronkw=3)")
        py.test.raises(ValueError, "tw.markup('x', wronkw=0)")

    def test_line_write_markup(self):
        tw = self.getwriter()
        tw.hasmarkup = True
        tw.line("x", bold=True)
        tw.write("x\n", red=True)
        l = self.getlines()
        skip_win32()
        assert len(l[0]) > 2, l
        assert len(l[1]) > 2, l

    def test_attr_fullwidth(self):
        tw = self.getwriter()
        tw.sep("-", "hello", fullwidth=70)
        tw.fullwidth = 70
        tw.sep("-", "hello")
        l = self.getlines()
        assert len(l[0]) == len(l[1])

class TestStringIO(BaseTests):
    def getwriter(self):
        self.tw = py.io.TerminalWriter(stringio=True)
        return self.tw
    def getlines(self):
        io = self.tw.stringio
        io.seek(0)
        return io.readlines()

class TestCallableFile(BaseTests):    
    def getwriter(self):
        self.writes = []
        return py.io.TerminalWriter(self.writes.append)

    def getlines(self):
        io = py.std.cStringIO.StringIO()
        io.write("".join(self.writes))
        io.seek(0)
        return io.readlines()

def test_attr_hasmarkup():
    tw = py.io.TerminalWriter(stringio=True)
    assert not tw.hasmarkup
    tw.hasmarkup = True
    tw.line("hello", bold=True)
    s = tw.stringio.getvalue()
    assert len(s) > len("hello")

    

