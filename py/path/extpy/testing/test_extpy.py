import os
import py

from py.__.path.testing import common

mypath = py.magic.autopath().dirpath('inc_test_extpy.py')

class TestExtPyCommonTests(common.CommonPathTests):
    def setup_class(cls):
        cls.root = py.path.extpy(
                      py.magic.autopath().dirpath('inc_pseudofs.py'))

    def test_file(self):
        assert self.root.join('samplefile').check(file=1)
        assert self.root.join('otherdir').check(file=0)

class TestExtPy:
    def setup_class(cls):
        cls.root = py.path.extpy(mypath)

    def test_join(self):
        p = self.root.join('A')
        obj = p.resolve()
        assert hasattr(obj, '__bases__')
        assert obj.x1 == 42

    def test_listdir_module(self):
        l = self.root.listdir()
        basenames = [x.basename for x in l]
        dlist = dir(self.root.resolve())
        for name in dlist:
            assert name in basenames
        for name in basenames:
            assert name in dlist

    def test_listdir_class(self):
        l = self.root.join('A').listdir()
        basenames = [x.basename for x in l]
        dlist = dir(self.root.resolve().A)
        for name in dlist:
            assert name in basenames
        for name in basenames:
            assert name in dlist

    def listobj(self):
        l = self.root.listobj(basestarts='path')
        assert len(l) == 1
        assert l[0] == path

    def test_visit(self):
        l = list(self.root.visit(lambda x: x.basename == 'borgfunc'))
        assert len(l) == 1
        obj = l[0]
        assert str(obj).endswith('Nested.Class.borgfunc')
        assert obj.resolve() == self.root.resolve().Nested.Class.borgfunc

    def test_visit_fnmatch(self):
        l = list(self.root.visit('borg*'))
        assert len(l) == 1
        obj = l[0]
        assert str(obj).endswith('Nested.Class.borgfunc')
        assert obj.resolve() == self.root.resolve().Nested.Class.borgfunc

    #def test_join_from_empty(self):
    #    p = path.py('')
    #    n = p.join('tokenize')
    #    assert str(n) == 'tokenize'
    #
    #    p = path.py('', ns=os)
    #    n = p.join('getlogin')
    #    assert str(n) == 'getlogin'

    #def test_unspecifiedpypath_lists_modules(self):
    #    p = path.py('')
    #    l = p.listdir()
    #    for i in l:
    #        assert '.' not in str(i)
    #
    #    for j in sys.modules:
    #        for i in l:
    #            if j.startswith(str(i)):
    #                break
    #        else:
    #            self.fail("%s is not in sys.modules")

    #def test_main_works(self):
    #    m = path.py('__main__')
    #    import __main__
    #    assert m.resolve() is __main__

    def test_relto(self):
        m1 = self.root.new(modpath='a.b.c.d')
        m2 = self.root.new(modpath='a.b')
        m3 = self.root.new(modpath='')
        res = m1.relto(m2)
        assert str(res) == 'c.d'
        assert m2.relto(m3) == 'a.b'

    def test_basename(self):
        m1 = self.root.new(modpath='a.b.hello')
        assert m1.basename == 'hello'
        assert m1.check(basename='hello')
        assert not m1.check(basename='nono')
        assert m1.check(basestarts='he')
        assert not m1.check(basestarts='42')

    def test_dirpath(self):
        m1 = self.root.new(modpath='a.b.hello')
        m2 = self.root.new(modpath='a.b')
        m3 = self.root.new(modpath='a')
        m4 = self.root.new(modpath='')
        assert m1.dirpath() == m2
        assert m2.dirpath() == m3
        assert m3.dirpath() == m4

    def test_function(self):
        p = self.root.join('A.func')
        assert p.check(func=1)
        p = self.root.join('A.x1')
        assert p.check(func=0)

    def test_generatorfunction(self):
        p = self.root.join('A.genfunc')
        assert p.check(genfunc=1)
        p = self.root.join('A.func')
        assert p.check(genfunc=0)
        p = self.root.join('A')
        assert p.check(genfunc=0)

    def test_class(self):
        p = self.root.join('A')
        assert p.check(class_=1)

    def test_hashing_equality(self):
        x = self.root
        y = self.root.new()
        assert x == y
        assert hash(x) == hash(y)

    def test_parts2(self):
        x = self.root.new(modpath='os.path.abspath')
        l = x.parts()
        assert len(l) == 4
        assert self.root.join('') == l[0]
        assert self.root.join('os') == l[1]
        assert self.root.join('os.path') == l[2]
        assert self.root.join('os.path.abspath') == l[3]

#class TestExtPyWithModule:
#    def test_module(self):
#        import os
#        x = py.path.extpy(os, 'path.abspath')
#        assert x.check()
#        assert x.resolve() is os.path.abspath
#    #def setup_class(cls):
    #    cls.root = py.path.extpy(mypath)

class TestEval:
    disabled = True
    def test_funccall(self):
        p = path.py('os.path.join("a", "b")')
        s = p.resolve()
        assert s == os.path.join("a", "b")

    def test_invalid1(self):
        p = path.py('os.path.qwe("a", "b")')
        s = test.raises(py.error.ENOENT, "p.resolve()")

    def test_syntaxerror(self):
        p = path.py('os.path.qwe("a", ')
        s = test.raises(ValueError, "p.resolve()")

class TestErrors:
    def test_ENOENT(self):
        p = py.path.extpy(mypath, 'somesuch')
        py.test.raises(py.error.ENOENT, p.resolve)

    def test_ENOENT_really(self):
        p = py.path.extpy(mypath.new(basename='notexist'), 'somesuch')
        py.test.raises(py.error.ENOENT, p.resolve)

    #def test_ImportError():
    #    p = path.py('__std.utest.test.data.failingimport.someattr')
    #    utest.raises(ImportError, p.resolve)

class ExampleClass:
    testattr = 1

def test_no_newline():
    filepath = mypath.dirpath() / 'test_data' / 'no_trailing_newline.py'
    pyc = filepath.dirpath() / 'no_trailing_newline.pyc'
    if pyc.check(exists=1):
        pyc.remove()
    data = filepath.read()
    assert not data.endswith('\n') and not data.endswith('\r'), (
        "The file must not end with a newline (that's the point of "
        "this test")
    #print repr(data)
    mod_extpy = py.path.extpy(filepath)
    #print mod_extpy.resolve()
    assert mod_extpy.resolve().test
