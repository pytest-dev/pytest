import py

class TestPOSIXLocalPath:
    disabled = py.std.sys.platform == 'win32'

    def setup_class(cls):
        cls.root = py.test.ensuretemp(cls.__name__) 

    def setup_method(self, method): 
        name = method.im_func.func_name
        self.tmpdir = self.root.ensure(name, dir=1) 

    def test_samefile(self):
        assert self.tmpdir.samefile(self.tmpdir)
        p = self.tmpdir.ensure("hello")
        assert p.samefile(p) 

    def test_hardlink(self):
        tmpdir = self.tmpdir 
        linkpath = tmpdir.join('test')
        filepath = tmpdir.join('file')
        filepath.write("Hello")
        nlink = filepath.stat().st_nlink 
        linkpath.mklinkto(filepath)
        assert filepath.stat().st_nlink == nlink + 1 

    def test_symlink_are_identical(self):
        tmpdir = self.tmpdir 
        filepath = tmpdir.join('file')
        filepath.write("Hello")
        linkpath = tmpdir.join('test')
        linkpath.mksymlinkto(filepath)
        assert linkpath.readlink() == str(filepath) 

    def test_symlink_isfile(self):
        tmpdir = self.tmpdir 
        linkpath = tmpdir.join('test')
        filepath = tmpdir.join('file')
        filepath.write("")
        linkpath.mksymlinkto(filepath)
        assert linkpath.check(file=1)
        assert not linkpath.check(link=0, file=1)

    def test_symlink_relative(self):
        tmpdir = self.tmpdir 
        linkpath = tmpdir.join('test')
        filepath = tmpdir.join('file')
        filepath.write("Hello")
        linkpath.mksymlinkto(filepath, absolute=False)
        assert linkpath.readlink() == "file"
        assert filepath.read() == linkpath.read()

    def test_symlink_not_existing(self):
        tmpdir = self.tmpdir 
        linkpath = tmpdir.join('testnotexisting')
        assert not linkpath.check(link=1)
        assert linkpath.check(link=0)

    def test_relto_with_root(self):
        y = self.root.join('x').relto(py.path.local('/'))
        assert y[0] == str(self.root)[1]

    def test_visit_recursive_symlink(self):
        tmpdir = self.tmpdir 
        linkpath = tmpdir.join('test')
        linkpath.mksymlinkto(tmpdir)
        visitor = tmpdir.visit(None, lambda x: x.check(link=0))
        assert list(visitor) == [linkpath]

    def test_symlink_isdir(self):
        tmpdir = self.tmpdir 
        linkpath = tmpdir.join('test')
        linkpath.mksymlinkto(tmpdir)
        assert linkpath.check(dir=1)
        assert not linkpath.check(link=0, dir=1)

    def test_symlink_remove(self):
        tmpdir = self.tmpdir.realpath() 
        linkpath = tmpdir.join('test')
        linkpath.mksymlinkto(linkpath) # point to itself
        assert linkpath.check(link=1)
        linkpath.remove()
        assert not linkpath.check()

    def test_realpath_file(self):
        tmpdir = self.tmpdir 
        linkpath = tmpdir.join('test')
        filepath = tmpdir.join('file')
        filepath.write("")
        linkpath.mksymlinkto(filepath)
        realpath = linkpath.realpath()
        assert realpath.basename == 'file'

    def test_owner(self):
        from pwd import getpwuid
        from grp import getgrgid
        stat = self.root.stat()
        assert stat.path == self.root 

        uid = stat.st_uid 
        gid = stat.st_gid 
        owner = getpwuid(uid)[0]
        group = getgrgid(gid)[0]

        assert uid == stat.uid 
        assert owner == stat.owner 
        assert gid == stat.gid 
        assert group == stat.group 

    def test_atime(self):
        import time
        path = self.root.ensure('samplefile')
        now = time.time()
        atime1 = path.atime()
        # we could wait here but timer resolution is very
        # system dependent 
        path.read()
        atime2 = path.atime()
        duration = time.time() - now
        assert (atime2-atime1) <= duration

    def test_commondir(self):
        # XXX This is here in local until we find a way to implement this
        #     using the subversion command line api.
        p1 = self.root.join('something')
        p2 = self.root.join('otherthing')
        assert p1.common(p2) == self.root
        assert p2.common(p1) == self.root

    def test_commondir_nocommon(self):
        # XXX This is here in local until we find a way to implement this
        #     using the subversion command line api.
        p1 = self.root.join('something')
        p2 = py.path.local(self.root.sep+'blabla')
        assert p1.common(p2) == '/' 

    def test_join_to_root(self): 
        root = self.root.parts()[0]
        assert len(str(root)) == 1
        assert str(root.join('a')) == '/a'

    def test_join_root_to_root_with_no_abs(self): 
        nroot = self.root.join('/')
        assert str(self.root) == str(nroot) 
        assert self.root == nroot 

    def test_chmod_simple_int(self):
        print "self.root is", self.root
        mode = self.root.mode()
        self.root.chmod(mode/2)
        try:
            assert self.root.mode() != mode
        finally:
            self.root.chmod(mode)
            assert self.root.mode() == mode

    def test_chmod_rec_int(self):
        # XXX fragile test
        print "self.root is", self.root
        recfilter = lambda x: x.check(dotfile=0, link=0)
        oldmodes = {}
        for x in self.root.visit(rec=recfilter):
            oldmodes[x] = x.mode()
        self.root.chmod(0772, rec=recfilter)
        try:
            for x in self.root.visit(rec=recfilter):
                assert x.mode() & 0777 == 0772
        finally:
            for x,y in oldmodes.items():
                x.chmod(y)

    def test_chown_identity(self):
        owner = self.root.owner()
        group = self.root.group()
        self.root.chown(owner, group)

    def test_chown_dangling_link(self):
        owner = self.root.owner()
        group = self.root.group()
        x = self.root.join('hello')
        x.mksymlinkto('qlwkejqwlek')
        try:
            self.root.chown(owner, group, rec=1)
        finally:
            x.remove(rec=0)

    def test_chown_identity_rec_mayfail(self):
        owner = self.root.owner()
        group = self.root.group()
        self.root.chown(owner, group)
