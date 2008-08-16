import py
from py.__.apigen.linker import Linker, TempLinker, getrelfspath, relpath

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

class TestTempLinker(object):
    def test_get_target(self):
        linker = TempLinker()
        temphref = linker.get_lazyhref('py.path.local')
        linker.set_link('py.path.local', 'py/path/local.html')
        relpath = linker.get_target(temphref)
        assert relpath == 'py/path/local.html'

    def test_functional(self):
        temp = py.test.ensuretemp('TestTempLinker.test_functional')
        l = TempLinker()
        bar = temp.ensure('foo/bar.html', file=True)
        baz = temp.ensure('foo/baz.html', file=True)
        l.set_link(baz.strpath, baz.relto(temp))
        bar.write('<a href="%s">baz</a>' % (l.get_lazyhref(baz.strpath),))
        l.replace_dirpath(temp)
        assert bar.read() == '<a href="baz.html">baz</a>'

    def test_with_anchor(self):
        py.test.skip("get_lazyhref needs fixing?")
        linker = TempLinker()
        temphref = linker.get_lazyhref('py.path.local', 'LocalPath.join')
        linker.set_link('py.path.local', 'py/path/local.html')
        relpath = linker.get_target(temphref)
        assert relpath == 'py/path/local.html#LocalPath.join'

def gen_check(frompath, topath, sep, expected):
    result = relpath(frompath, topath, sep=sep)
    assert result == expected

def test_gen_check():
    for line in testspec:
        frompath, topath, expected, sep = line.split()
        yield gen_check, frompath, topath, sep, expected

def test_check_incompatible():
    py.test.raises(ValueError, "relpath('/a', 'b')")
