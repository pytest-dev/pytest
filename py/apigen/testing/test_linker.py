import py
from py.__.apigen.linker import Linker, getrelfspath, relpath

class TestLinker(object):
    def test_get_target(self):
        linker = Linker()
        lazyhref = linker.get_lazyhref('py.path.local')
        linker.set_link('py.path.local', 'py/path/local.html')
        relpath = linker.get_target('py.path.local')
        assert relpath == 'py/path/local.html'
   
    def test_target_relative(self):
        linker = Linker()
        lazyhref = linker.get_lazyhref('py.path.local')
        linker.set_link('py.path.local', 'py/path/local.html')
        relpath = linker.call_withbase('py/index.html', 
                    linker.get_target, 'py.path.local')
        assert relpath == 'path/local.html'

testspec = [
    'a              a/b         a/b     /',
    '/a             /a/b        a/b     /',
    'a              b           b       /',
    '/a             /b          b       /',
    'a/b            c/d         ../c/d  /',
    '/a/b           /c/d        ../c/d  /',
    'a/b            a           ../a    /',
    '/a/b           /a          ../a    /',
    'c:\\foo\\bar c:\\foo       ../foo  \\',
]

def gen_check(frompath, topath, sep, expected):
    result = relpath(frompath, topath, sep=sep)
    assert result == expected

def test_gen_check():
    for line in testspec:
        frompath, topath, expected, sep = line.split()
        yield gen_check, frompath, topath, sep, expected

def test_check_incompatible():
    py.test.raises(ValueError, "relpath('/a', 'b')")
