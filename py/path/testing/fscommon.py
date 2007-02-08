import py
from py.__.path.testing import common 

def setuptestfs(path):
    if path.join('samplefile').check():
        return
    #print "setting up test fs for", repr(path)
    samplefile = path.ensure('samplefile')
    samplefile.write('samplefile\n')

    execfile = path.ensure('execfile')
    execfile.write('x=42')

    execfilepy = path.ensure('execfile.py')
    execfilepy.write('x=42')

    d = {1:2, 'hello': 'world', 'answer': 42}
    path.ensure('samplepickle').dump(d)

    sampledir = path.ensure('sampledir', dir=1)
    sampledir.ensure('otherfile')

    otherdir = path.ensure('otherdir', dir=1)
    otherdir.ensure('__init__.py')

    module_a = otherdir.ensure('a.py')
    module_a.write('from b import stuff as result\n')
    module_b = otherdir.ensure('b.py')
    module_b.write('stuff="got it"\n')
    module_c = otherdir.ensure('c.py')
    module_c.write('''import py; py.magic.autopath()
import otherdir.a
value = otherdir.a.result
''')
    module_d = otherdir.ensure('d.py')
    module_d.write('''import py; py.magic.autopath()
from otherdir import a
value2 = a.result
''')

class CommonFSTests(common.CommonPathTests):
    root = None  # subclasses have to provide a current 'root' attribute

    def test_join_div_operator(self):
        newpath = self.root / '/sampledir' / '/test//'
        newpath2 = self.root.join('sampledir', 'test')
        assert newpath == newpath2

    def test_ext(self):
        newpath = self.root.join('sampledir.ext')
        assert newpath.ext == '.ext'
        newpath = self.root.join('sampledir')
        assert not newpath.ext

    def test_purebasename(self):
        newpath = self.root.join('samplefile.py')
        assert newpath.purebasename == 'samplefile'

    def test_multiple_parts(self):
        newpath = self.root.join('samplefile.py')
        dirname, purebasename, basename, ext = newpath._getbyspec(
            'dirname,purebasename,basename,ext')
        assert str(self.root).endswith(dirname) # be careful with win32 'drive' 
        assert purebasename == 'samplefile'
        assert basename == 'samplefile.py'
        assert ext == '.py'

    def test_dotted_name_ext(self):
        newpath = self.root.join('a.b.c')
        ext = newpath.ext
        assert ext == '.c'
        assert newpath.ext == '.c'

    def test_newext(self):
        newpath = self.root.join('samplefile.py')
        newext = newpath.new(ext='.txt')
        assert newext.basename == "samplefile.txt"
        assert newext.purebasename == "samplefile"

    def test_readlines(self):
        fn = self.root.join('samplefile')
        contents = fn.readlines()
        assert contents == ['samplefile\n']

    def test_readlines_nocr(self):
        fn = self.root.join('samplefile')
        contents = fn.readlines(cr=0)
        assert contents == ['samplefile', '']

    def test_file(self):
        assert self.root.join('samplefile').check(file=1)

    def test_not_file(self):
        assert not self.root.join("sampledir").check(file=1)
        assert self.root.join("sampledir").check(file=0)

    #def test_fnmatch_dir(self):

    def test_non_existent(self):
        assert self.root.join("sampledir.nothere").check(dir=0)
        assert self.root.join("sampledir.nothere").check(file=0)
        assert self.root.join("sampledir.nothere").check(notfile=1)
        assert self.root.join("sampledir.nothere").check(notdir=1)
        assert self.root.join("sampledir.nothere").check(notexists=1)
        assert not self.root.join("sampledir.nothere").check(notfile=0)

    #    pattern = self.root.sep.join(['s*file'])
    #    sfile = self.root.join("samplefile")
    #    assert sfile.check(fnmatch=pattern)

    def test_size(self):
        url = self.root.join("samplefile")
        assert url.size() > len("samplefile")

    def test_mtime(self):
        url = self.root.join("samplefile")
        assert url.mtime() > 0

    def test_relto_wrong_type(self): 
        py.test.raises(TypeError, "self.root.relto(42)")

    def test_visit_filesonly(self):
        l = []
        for i in self.root.visit(lambda x: x.check(file=1)): 
            l.append(i.relto(self.root))
        assert not "sampledir" in l
        assert self.root.sep.join(["sampledir", "otherfile"]) in l

    def test_load(self):
        p = self.root.join('samplepickle')
        obj = p.load()
        assert type(obj) is dict
        assert obj.get('answer',None) == 42

    def test_visit_nodotfiles(self):
        l = []
        for i in self.root.visit(lambda x: x.check(dotfile=0)): 
            l.append(i.relto(self.root))
        assert "sampledir" in l
        assert self.root.sep.join(["sampledir", "otherfile"]) in l
        assert not ".dotfile" in l

    def test_endswith(self):
        def chk(p):
            return p.check(endswith="pickle")
        assert not chk(self.root)
        assert not chk(self.root.join('samplefile'))
        assert chk(self.root.join('somepickle'))

    def test_copy_file(self):
        otherdir = self.root.join('otherdir')
        initpy = otherdir.join('__init__.py')
        copied = otherdir.join('copied')
        initpy.copy(copied)
        try:
            assert copied.check()
            s1 = initpy.read()
            s2 = copied.read()
            assert s1 == s2
        finally:
            if copied.check():
                copied.remove()

    def test_copy_dir(self):
        otherdir = self.root.join('otherdir')
        copied = self.root.join('newdir')
        try:
            otherdir.copy(copied)
            assert copied.check(dir=1)
            assert copied.join('__init__.py').check(file=1)
            s1 = otherdir.join('__init__.py').read()
            s2 = copied.join('__init__.py').read()
            assert s1 == s2
        finally:
            if copied.check(dir=1):
                copied.remove(rec=1)

    def test_remove_file(self):
        d = self.root.ensure('todeleted')
        assert d.check()
        d.remove()
        assert not d.check()

    def test_remove_dir_recursive_by_default(self):
        d = self.root.ensure('to', 'be', 'deleted')
        assert d.check()
        p = self.root.join('to')
        p.remove()
        assert not p.check()

    def test_mkdir_and_remove(self):
        tmpdir = self.root
        py.test.raises(py.error.EEXIST, tmpdir.mkdir, 'sampledir')
        new = tmpdir.join('mktest1')
        new.mkdir()
        assert new.check(dir=1)
        new.remove()

        new = tmpdir.mkdir('mktest')
        assert new.check(dir=1)
        new.remove()
        assert tmpdir.join('mktest') == new

    def test_move_file(self):
        p = self.root.join('samplefile')
        newp = p.dirpath('moved_samplefile')
        p.move(newp)
        assert newp.check(file=1)
        assert not p.check()

    def test_move_directory(self):
        source = self.root.join('sampledir') 
        dest = self.root.join('moveddir') 
        source.move(dest)
        assert dest.check(dir=1)
        assert dest.join('otherfile').check(file=1) 
        assert not source.join('sampledir').check()

    def test__getpymodule(self):
        obj = self.root.join('execfile')._getpymodule()
        assert obj.x == 42

    def test_not_has_resolve(self):
        # because this would mean confusion with respect to
        # py.path.extpy
        assert not hasattr(self.root, 'resolve')

    def test__getpymodule_a(self):
        otherdir = self.root.join('otherdir')
        mod = otherdir.join('a.py')._getpymodule()
        assert mod.result == "got it"

    def test__getpymodule_b(self):
        otherdir = self.root.join('otherdir')
        mod = otherdir.join('b.py')._getpymodule()
        assert mod.stuff == "got it"

    def test__getpymodule_c(self):
        otherdir = self.root.join('otherdir')
        mod = otherdir.join('c.py')._getpymodule()
        assert mod.value == "got it"

    def test__getpymodule_d(self):
        otherdir = self.root.join('otherdir')
        mod = otherdir.join('d.py')._getpymodule()
        assert mod.value2 == "got it"
