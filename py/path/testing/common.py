from py.__.path.common import checker
import py

class CommonPathTests(object):
    root = None  # subclasses have to setup a 'root' attribute

    def test_constructor_equality(self):
        p = self.root.__class__(self.root)
        assert p == self.root

    def test_eq_nonstring(self):
        path1 = self.root.join('sampledir')
        path2 = self.root.join('sampledir')
        assert path1 == path2

    def test_new_identical(self):
        assert self.root == self.root.new()

    def test_join(self):
        p = self.root.join('sampledir')
        strp = str(p) 
        assert strp.endswith('sampledir') 
        assert strp.startswith(str(self.root)) 

    def test_join_normalized(self):
        newpath = self.root.join(self.root.sep+'sampledir')
        strp = str(newpath) 
        assert strp.endswith('sampledir') 
        assert strp.startswith(str(self.root)) 
        newpath = self.root.join((self.root.sep*2) + 'sampledir')
        strp = str(newpath) 
        assert strp.endswith('sampledir') 
        assert strp.startswith(str(self.root)) 

    def test_join_noargs(self):
        newpath = self.root.join()
        assert self.root == newpath

    def test_add_something(self):
        p = self.root.join('sample')
        p = p + 'dir'
        assert p.check()

    def test_parts(self):
        newpath = self.root.join('sampledir', 'otherfile')
        par = newpath.parts()[-3:]
        assert par == [self.root, self.root.join('sampledir'), newpath]

        revpar = newpath.parts(reverse=True)[:3]
        assert revpar == [newpath, self.root.join('sampledir'), self.root]

    def test_common(self):
        other = self.root.join('sampledir')
        x = other.common(self.root)
        assert x == self.root


    #def test_parents_nonexisting_file(self):
    #    newpath = self.root / 'dirnoexist' / 'nonexisting file'
    #    par = list(newpath.parents())
    #    assert par[:2] == [self.root / 'dirnoexist', self.root]

    def test_basename_checks(self):
        newpath = self.root.join('sampledir')
        assert newpath.check(basename='sampledir')
        assert newpath.check(notbasename='xyz')
        assert newpath.basename == 'sampledir'

    def test_basename(self):
        newpath = self.root.join('sampledir')
        assert newpath.check(basename='sampledir')
        assert newpath.basename, 'sampledir'

    def test_dirpath(self):
        newpath = self.root.join('sampledir')
        assert newpath.dirpath() == self.root

    def test_dirpath_with_args(self):
        newpath = self.root.join('sampledir')
        assert newpath.dirpath('x') == self.root.join('x')

    def test_newbasename(self):
        newpath = self.root.join('samplefile')
        newbase = newpath.new(basename="samplefile2")
        assert newbase.basename == "samplefile2"
        assert newbase.dirpath() == newpath.dirpath()

    def test_not_exists(self):
        assert not self.root.join('does_not_exist').check()
        assert self.root.join('does_not_exist').check(exists=0)

    def test_exists(self):
        assert self.root.join("samplefile").check()
        assert self.root.join("samplefile").check(exists=1)

    def test_dir(self):
        #print repr(self.root.join("sampledir"))
        assert self.root.join("sampledir").check(dir=1)
        assert self.root.join('samplefile').check(notdir=1)
        assert not self.root.join("samplefile").check(dir=1)

    def test_filter_dir(self):
        assert checker(dir=1)(self.root.join("sampledir"))

    def test_fnmatch_file(self):
        assert self.root.join("samplefile").check(fnmatch='s*e')
        assert self.root.join("samplefile").check(notfnmatch='s*x')
        assert not self.root.join("samplefile").check(fnmatch='s*x')

    #def test_fnmatch_dir(self):

    #    pattern = self.root.sep.join(['s*file'])
    #    sfile = self.root.join("samplefile")
    #    assert sfile.check(fnmatch=pattern)

    def test_relto(self):
        l=self.root.join("sampledir", "otherfile")
        assert l.relto(self.root) == l.sep.join(["sampledir", "otherfile"])
        assert l.check(relto=self.root)
        assert self.root.check(notrelto=l)
        assert not self.root.check(relto=l)

    def test_relto_not_relative(self):
        l1=self.root.join("bcde")
        l2=self.root.join("b")
        assert not l1.relto(l2)
        assert not l2.relto(l1)

    def test_listdir(self):
        l = self.root.listdir()
        assert self.root.join('sampledir') in l
        assert self.root.join('samplefile') in l
        py.test.raises(py.error.ENOTDIR,
                       "self.root.join('samplefile').listdir()")

    def test_listdir_fnmatchstring(self):
        l = self.root.listdir('s*dir')
        assert len(l)
        assert l[0], self.root.join('sampledir')

    def test_listdir_filter(self):
        l = self.root.listdir(checker(dir=1))
        assert self.root.join('sampledir') in l
        assert not self.root.join('samplefile') in l

    def test_listdir_sorted(self):
        l = self.root.listdir(checker(basestarts="sample"), sort=True)
        assert self.root.join('sampledir') == l[0]
        assert self.root.join('samplefile') == l[1]
        assert self.root.join('samplepickle') == l[2]

    def test_visit_nofilter(self):
        l = []
        for i in self.root.visit():
            l.append(i.relto(self.root))
        assert "sampledir" in l
        assert self.root.sep.join(["sampledir", "otherfile"]) in l

    def test_visit_norecurse(self):
        l = []
        for i in self.root.visit(None, lambda x: x.basename != "sampledir"):
            l.append(i.relto(self.root))
        assert "sampledir" in l
        assert not self.root.sep.join(["sampledir", "otherfile"]) in l

    def test_visit_filterfunc_is_string(self):
        l = []
        for i in self.root.visit('*dir'):
            l.append(i.relto(self.root))
        assert len(l), 2
        assert "sampledir" in l
        assert "otherdir" in l

    def test_visit_ignore(self):
        p = self.root.join('nonexisting')
        assert list(p.visit(ignore=py.error.ENOENT)) == []

    def test_visit_endswith(self):
        l = []
        for i in self.root.visit(checker(endswith="file")):
            l.append(i.relto(self.root))
        assert self.root.sep.join(["sampledir", "otherfile"]) in l
        assert "samplefile" in l

    def test_endswith(self):
        assert self.root.check(notendswith='.py')
        x = self.root.join('samplefile')
        assert x.check(endswith='file')

    def test_cmp(self):
        path1 = self.root.join('samplefile')
        path2 = self.root.join('samplefile2')
        assert cmp(path1, path2) == cmp('samplefile', 'samplefile2')
        assert cmp(path1, path1) == 0

    def test_contains_path(self):
        path1 = self.root.join('samplefile')
        assert path1 in self.root
        assert not self.root.join('not existing') in self.root

    def test_contains_path_with_basename(self):
        assert 'samplefile' in self.root
        assert 'not_existing' not in self.root

    def featuretest_check_docstring(self):
        here = self.root.__class__
        assert here.check.__doc__
        doc = here.check.__doc__
        for name in dir(local.Checkers):
            if name[0] != '_':
                assert name in doc

    def test_simple_read(self):
        x = self.root.join('samplefile').read('ru')
        assert x == 'samplefile\n'

