import py
import sys
from py.path import local
from testing.path import common

failsonjython = py.test.mark.xfail("sys.platform.startswith('java')")
failsonjywin32 = py.test.mark.xfail("sys.platform.startswith('java') "
        "and getattr(os, '_name', None) == 'nt'")
win32only = py.test.mark.skipif(
        "not (sys.platform == 'win32' or getattr(os, '_name', None) == 'nt')")
skiponwin32 = py.test.mark.skipif(
        "sys.platform == 'win32' or getattr(os, '_name', None) == 'nt'")


def pytest_funcarg__path1(request):
    def setup():
        path1 = request.config.mktemp("path1")
        common.setuptestfs(path1)
        return path1
    def teardown(path1):
        # post check 
        assert path1.join("samplefile").check()
    return request.cached_setup(setup, teardown, scope="session")

class TestLocalPath(common.CommonFSTests):
    def test_join_normpath(self, tmpdir):
        assert tmpdir.join(".") == tmpdir
        p = tmpdir.join("../%s" % tmpdir.basename)
        assert p == tmpdir
        p = tmpdir.join("..//%s/" % tmpdir.basename)
        assert p == tmpdir

    def test_gethash(self, tmpdir):
        md5 = py.builtin._tryimport('md5', 'hashlib').md5
        lib = py.builtin._tryimport('sha', 'hashlib')
        sha = getattr(lib, 'sha1', getattr(lib, 'sha', None))
        fn = tmpdir.join("testhashfile")
        data = 'hello'.encode('ascii')
        fn.write(data, mode="wb")
        assert fn.computehash("md5") == md5(data).hexdigest()
        assert fn.computehash("sha1") == sha(data).hexdigest()
        py.test.raises(ValueError, fn.computehash, "asdasd")

    def test_remove_removes_readonly_file(self, tmpdir):
        readonly_file = tmpdir.join('readonly').ensure()
        readonly_file.chmod(0)
        readonly_file.remove()
        assert not readonly_file.check(exists=1)

    def test_remove_removes_readonly_dir(self, tmpdir):
        readonly_dir = tmpdir.join('readonlydir').ensure(dir=1)
        readonly_dir.chmod(int("500", 8))
        readonly_dir.remove()
        assert not readonly_dir.check(exists=1)

    def test_remove_removes_dir_and_readonly_file(self, tmpdir):
        readonly_dir = tmpdir.join('readonlydir').ensure(dir=1)
        readonly_file = readonly_dir.join('readonlyfile').ensure()
        readonly_file.chmod(0)
        readonly_dir.remove()
        assert not readonly_dir.check(exists=1)

    def test_initialize_curdir(self):
        assert str(local()) == py.std.os.getcwd()

    def test_initialize_reldir(self, path1):
        old = path1.chdir()
        try:
            p = local('samplefile')
            assert p.check()
        finally:
            old.chdir()

    def test_eq_with_strings(self, path1):
        path1 = path1.join('sampledir')
        path2 = str(path1)
        assert path1 == path2
        assert path2 == path1
        path3 = path1.join('samplefile')
        assert path3 != path2
        assert path2 != path3

    @py.test.mark.multi(bin=(False, True))
    def test_dump(self, tmpdir, bin):
        path = tmpdir.join("dumpfile%s" % int(bin))
        try:
            d = {'answer' : 42}
            path.dump(d, bin=bin)
            f = path.open('rb+')
            dnew = py.std.pickle.load(f)
            assert d == dnew
        finally:
            f.close()

    @failsonjywin32
    def test_setmtime(self):
        import tempfile
        import time
        try:
            fd, name = tempfile.mkstemp()
            py.std.os.close(fd)
        except AttributeError:
            name = tempfile.mktemp()
            open(name, 'w').close()
        try:
            mtime = int(time.time())-100
            path = local(name)
            assert path.mtime() != mtime
            path.setmtime(mtime)
            assert path.mtime() == mtime
            path.setmtime()
            assert path.mtime() != mtime
        finally:
            py.std.os.remove(name)

    def test_normpath(self, path1):
        new1 = path1.join("/otherdir")
        new2 = path1.join("otherdir")
        assert str(new1) == str(new2)

    def test_mkdtemp_creation(self):
        d = local.mkdtemp()
        try:
            assert d.check(dir=1)
        finally:
            d.remove(rec=1)

    def test_tmproot(self):
        d = local.mkdtemp()
        tmproot = local.get_temproot()
        try:
            assert d.check(dir=1)
            assert d.dirpath() == tmproot
        finally:
            d.remove(rec=1)

    def test_chdir(self, tmpdir):
        old = local()
        try:
            res = tmpdir.chdir()
            assert str(res) == str(old)
            assert py.std.os.getcwd() == str(tmpdir)
        finally:
            old.chdir()

    def test_ensure_filepath_withdir(self, tmpdir):
        newfile = tmpdir.join('test1','test')
        newfile.ensure()
        assert newfile.check(file=1)
        newfile.write("42")
        newfile.ensure()
        s = newfile.read()
        assert s == "42"

    def test_ensure_filepath_withoutdir(self, tmpdir):
        newfile = tmpdir.join('test1file')
        t = newfile.ensure()
        assert t == newfile
        assert newfile.check(file=1)

    def test_ensure_dirpath(self, tmpdir):
        newfile = tmpdir.join('test1','testfile')
        t = newfile.ensure(dir=1)
        assert t == newfile
        assert newfile.check(dir=1)

    def test_init_from_path(self, tmpdir):
        l = local()
        l2 = local(l)
        assert l2 is l

        wc = py.path.svnwc('.')
        l3 = local(wc)
        assert l3 is not wc
        assert l3.strpath == wc.strpath
        assert not hasattr(l3, 'commit')

    def test_long_filenames(self, tmpdir):
        if sys.platform == "win32":
            py.test.skip("win32: work around needed for path length limit")
        # see http://codespeak.net/pipermail/py-dev/2008q2/000922.html
        
        # testing paths > 260 chars (which is Windows' limitation, but
        # depending on how the paths are used), but > 4096 (which is the
        # Linux' limitation) - the behaviour of paths with names > 4096 chars
        # is undetermined
        newfilename = '/test' * 60
        l = tmpdir.join(newfilename)
        l.ensure(file=True)
        l.write('foo')
        l2 = tmpdir.join(newfilename)
        assert l2.read() == 'foo'

    def test_visit_depth_first(self, tmpdir):
        p1 = tmpdir.ensure("a","1")
        p2 = tmpdir.ensure("b","2")
        p3 = tmpdir.ensure("breadth")
        l = list(tmpdir.visit(lambda x: x.check(file=1)))
        assert len(l) == 3
        # check that breadth comes last
        assert l[2] == p3 

class TestExecutionOnWindows:
    pytestmark = win32only

    def test_sysfind(self):
        x = py.path.local.sysfind('cmd')
        assert x.check(file=1)
        assert py.path.local.sysfind('jaksdkasldqwe') is None

class TestExecution:
    pytestmark = skiponwin32

    def test_sysfind(self):
        x = py.path.local.sysfind('test')
        assert x.check(file=1)
        assert py.path.local.sysfind('jaksdkasldqwe') is None

    def test_sysfind_no_permisson_ignored(self, monkeypatch, tmpdir):
        noperm = tmpdir.ensure('noperm', dir=True)
        monkeypatch.setenv("PATH", noperm, prepend=":")
        noperm.chmod(0)
        assert py.path.local.sysfind('jaksdkasldqwe') is None
            
    def test_sysfind_absolute(self):
        x = py.path.local.sysfind('test')
        assert x.check(file=1)
        y = py.path.local.sysfind(str(x)) 
        assert y.check(file=1) 
        assert y == x 

    def test_sysfind_multiple(self, tmpdir, monkeypatch):
        monkeypatch.setenv('PATH', 
                          "%s:%s" % (tmpdir.ensure('a'),
                                       tmpdir.join('b')),
                          prepend=":")
        tmpdir.ensure('b', 'a')
        checker = lambda x: x.dirpath().basename == 'b'
        x = py.path.local.sysfind('a', checker=checker)
        assert x.basename == 'a'
        assert x.dirpath().basename == 'b'
        checker = lambda x: None
        assert py.path.local.sysfind('a', checker=checker) is None

    def test_sysexec(self):
        x = py.path.local.sysfind('ls') 
        out = x.sysexec('-a')
        for x in py.path.local().listdir(): 
            assert out.find(x.basename) != -1

    def test_sysexec_failing(self):
        x = py.path.local.sysfind('false')
        py.test.raises(py.process.cmdexec.Error, """
            x.sysexec('aksjdkasjd')
        """)

    def test_make_numbered_dir(self, tmpdir):
        tmpdir.ensure('base.not_an_int', dir=1)
        for i in range(10):
            numdir = local.make_numbered_dir(prefix='base.', rootdir=tmpdir,
                                             keep=2, lock_timeout=0)
            assert numdir.check()
            assert numdir.basename == 'base.%d' %i
            if i>=1:
                assert numdir.new(ext=str(i-1)).check()
            if i>=2:
                assert numdir.new(ext=str(i-2)).check()
            if i>=3:
                assert not numdir.new(ext=str(i-3)).check()

    def test_locked_make_numbered_dir(self, tmpdir):
        for i in range(10):
            numdir = local.make_numbered_dir(prefix='base2.', rootdir=tmpdir,
                                             keep=2)
            assert numdir.check()
            assert numdir.basename == 'base2.%d' %i
            for j in range(i):
                assert numdir.new(ext=str(j)).check()

    def test_error_preservation(self, path1):
        py.test.raises (EnvironmentError, path1.join('qwoeqiwe').mtime)
        py.test.raises (EnvironmentError, path1.join('qwoeqiwe').read)

    #def test_parentdirmatch(self):
    #    local.parentdirmatch('std', startmodule=__name__)
    #


class TestImport: 
    def test_pyimport(self, path1):
        obj = path1.join('execfile.py').pyimport()
        assert obj.x == 42
        assert obj.__name__ == 'execfile' 

    def test_pyimport_execfile_different_name(self, path1):
        obj = path1.join('execfile.py').pyimport(modname="0x.y.z")
        assert obj.x == 42
        assert obj.__name__ == '0x.y.z' 

    def test_pyimport_a(self, path1):
        otherdir = path1.join('otherdir')
        mod = otherdir.join('a.py').pyimport()
        assert mod.result == "got it"
        assert mod.__name__ == 'otherdir.a' 

    def test_pyimport_b(self, path1):
        otherdir = path1.join('otherdir')
        mod = otherdir.join('b.py').pyimport()
        assert mod.stuff == "got it"
        assert mod.__name__ == 'otherdir.b' 

    def test_pyimport_c(self, path1):
        otherdir = path1.join('otherdir')
        mod = otherdir.join('c.py').pyimport()
        assert mod.value == "got it"

    def test_pyimport_d(self, path1):
        otherdir = path1.join('otherdir')
        mod = otherdir.join('d.py').pyimport()
        assert mod.value2 == "got it"

    def test_pyimport_and_import(self, tmpdir):
        tmpdir.ensure('xxxpackage', '__init__.py') 
        mod1path = tmpdir.ensure('xxxpackage', 'module1.py')
        mod1 = mod1path.pyimport() 
        assert mod1.__name__ == 'xxxpackage.module1' 
        from xxxpackage import module1 
        assert module1 is mod1

    def test_pyimport_check_filepath_consistency(self, monkeypatch, tmpdir):
        name = 'pointsback123'
        ModuleType = type(py.std.os)
        p = tmpdir.ensure(name + '.py')
        for ending in ('.pyc', '$py.class', '.pyo'):
            mod = ModuleType(name)
            pseudopath = tmpdir.ensure(name+ending)
            mod.__file__ = str(pseudopath)
            monkeypatch.setitem(sys.modules, name, mod)
            newmod = p.pyimport()
            assert mod == newmod
        monkeypatch.undo()
        mod = ModuleType(name)
        pseudopath = tmpdir.ensure(name+"123.py")
        mod.__file__ = str(pseudopath)
        monkeypatch.setitem(sys.modules, name, mod)
        excinfo = py.test.raises(EnvironmentError, "p.pyimport()")
        s = str(excinfo.value)
        assert "mismatch" in s 
        assert name+"123" in s 

def test_pypkgdir(tmpdir):
    pkg = tmpdir.ensure('pkg1', dir=1)
    pkg.ensure("__init__.py")
    pkg.ensure("subdir/__init__.py")
    assert pkg.pypkgpath() == pkg
    assert pkg.join('subdir', '__init__.py').pypkgpath() == pkg

def test_pypkgdir_unimportable(tmpdir):
    pkg = tmpdir.ensure('pkg1-1', dir=1) # unimportable
    pkg.ensure("__init__.py")
    subdir = pkg.ensure("subdir/__init__.py").dirpath()
    assert subdir.pypkgpath() == subdir
    assert subdir.ensure("xyz.py").pypkgpath() == subdir
    assert not pkg.pypkgpath() 

def test_isimportable():
    from py._path.local import isimportable
    assert not isimportable("")
    assert isimportable("x")
    assert isimportable("x1")
    assert isimportable("x_1")
    assert isimportable("_")
    assert isimportable("_1")
    assert not isimportable("x-1")
    assert not isimportable("x:1")

def test_homedir():
    homedir = py.path.local._gethomedir()
    assert homedir.check(dir=1)

def test_samefile(tmpdir):
    assert tmpdir.samefile(tmpdir)
    p = tmpdir.ensure("hello")
    assert p.samefile(p) 

class TestWINLocalPath:
    pytestmark = win32only

    def test_owner_group_not_implemented(self, path1):
        py.test.raises(NotImplementedError, "path1.stat().owner")
        py.test.raises(NotImplementedError, "path1.stat().group")

    def test_chmod_simple_int(self, path1):
        py.builtin.print_("path1 is", path1)
        mode = path1.stat().mode
        # Ensure that we actually change the mode to something different.
        path1.chmod(mode == 0 and 1 or 0)
        try:
            print(path1.stat().mode)
            print(mode)
            assert path1.stat().mode != mode
        finally:
            path1.chmod(mode)
            assert path1.stat().mode == mode

    def test_path_comparison_lowercase_mixed(self, path1):
        t1 = path1.join("a_path")
        t2 = path1.join("A_path")
        assert t1 == t1
        assert t1 == t2
        
    def test_relto_with_mixed_case(self, path1):
        t1 = path1.join("a_path", "fiLe")
        t2 = path1.join("A_path")
        assert t1.relto(t2) == "fiLe"

    def test_allow_unix_style_paths(self, path1):
        t1 = path1.join('a_path')
        assert t1 == str(path1) + '\\a_path'
        t1 = path1.join('a_path/')
        assert t1 == str(path1) + '\\a_path'
        t1 = path1.join('dir/a_path')
        assert t1 == str(path1) + '\\dir\\a_path'

    def test_sysfind_in_currentdir(self, path1):
        cmd = py.path.local.sysfind('cmd')
        root = cmd.new(dirname='', basename='') # c:\ in most installations
        old = root.chdir()
        try:
            x = py.path.local.sysfind(cmd.relto(root))
            assert x.check(file=1)
        finally:
            old.chdir()    

class TestPOSIXLocalPath:
    pytestmark = skiponwin32

    def test_hardlink(self, tmpdir):
        linkpath = tmpdir.join('test')
        filepath = tmpdir.join('file')
        filepath.write("Hello")
        nlink = filepath.stat().nlink
        linkpath.mklinkto(filepath)
        assert filepath.stat().nlink == nlink + 1 

    def test_symlink_are_identical(self, tmpdir):
        filepath = tmpdir.join('file')
        filepath.write("Hello")
        linkpath = tmpdir.join('test')
        linkpath.mksymlinkto(filepath)
        assert linkpath.readlink() == str(filepath) 

    def test_symlink_isfile(self, tmpdir):
        linkpath = tmpdir.join('test')
        filepath = tmpdir.join('file')
        filepath.write("")
        linkpath.mksymlinkto(filepath)
        assert linkpath.check(file=1)
        assert not linkpath.check(link=0, file=1)

    def test_symlink_relative(self, tmpdir):
        linkpath = tmpdir.join('test')
        filepath = tmpdir.join('file')
        filepath.write("Hello")
        linkpath.mksymlinkto(filepath, absolute=False)
        assert linkpath.readlink() == "file"
        assert filepath.read() == linkpath.read()

    def test_symlink_not_existing(self, tmpdir):
        linkpath = tmpdir.join('testnotexisting')
        assert not linkpath.check(link=1)
        assert linkpath.check(link=0)

    def test_relto_with_root(self, path1, tmpdir):
        y = path1.join('x').relto(py.path.local('/'))
        assert y[0] == str(path1)[1]

    def test_visit_recursive_symlink(self, tmpdir):
        linkpath = tmpdir.join('test')
        linkpath.mksymlinkto(tmpdir)
        visitor = tmpdir.visit(None, lambda x: x.check(link=0))
        assert list(visitor) == [linkpath]

    def test_symlink_isdir(self, tmpdir):
        linkpath = tmpdir.join('test')
        linkpath.mksymlinkto(tmpdir)
        assert linkpath.check(dir=1)
        assert not linkpath.check(link=0, dir=1)

    def test_symlink_remove(self, tmpdir):
        linkpath = tmpdir.join('test')
        linkpath.mksymlinkto(linkpath) # point to itself
        assert linkpath.check(link=1)
        linkpath.remove()
        assert not linkpath.check()

    def test_realpath_file(self, tmpdir):
        linkpath = tmpdir.join('test')
        filepath = tmpdir.join('file')
        filepath.write("")
        linkpath.mksymlinkto(filepath)
        realpath = linkpath.realpath()
        assert realpath.basename == 'file'

    def test_owner(self, path1, tmpdir):
        from pwd import getpwuid
        from grp import getgrgid
        stat = path1.stat()
        assert stat.path == path1 

        uid = stat.uid
        gid = stat.gid
        owner = getpwuid(uid)[0]
        group = getgrgid(gid)[0]

        assert uid == stat.uid 
        assert owner == stat.owner 
        assert gid == stat.gid 
        assert group == stat.group 

    def test_atime(self, tmpdir):
        import time
        path = tmpdir.ensure('samplefile')
        now = time.time()
        atime1 = path.atime()
        # we could wait here but timer resolution is very
        # system dependent 
        path.read()
        time.sleep(0.01) 
        atime2 = path.atime()
        time.sleep(0.01)
        duration = time.time() - now
        assert (atime2-atime1) <= duration

    def test_commondir(self, path1):
        # XXX This is here in local until we find a way to implement this
        #     using the subversion command line api.
        p1 = path1.join('something')
        p2 = path1.join('otherthing')
        assert p1.common(p2) == path1
        assert p2.common(p1) == path1

    def test_commondir_nocommon(self, path1):
        # XXX This is here in local until we find a way to implement this
        #     using the subversion command line api.
        p1 = path1.join('something')
        p2 = py.path.local(path1.sep+'blabla')
        assert p1.common(p2) == '/' 

    def test_join_to_root(self, path1): 
        root = path1.parts()[0]
        assert len(str(root)) == 1
        assert str(root.join('a')) == '/a'

    def test_join_root_to_root_with_no_abs(self, path1): 
        nroot = path1.join('/')
        assert str(path1) == str(nroot) 
        assert path1 == nroot 

    def test_chmod_simple_int(self, path1):
        mode = path1.stat().mode
        path1.chmod(int(mode/2))
        try:
            assert path1.stat().mode != mode
        finally:
            path1.chmod(mode)
            assert path1.stat().mode == mode

    def test_chmod_rec_int(self, path1):
        # XXX fragile test
        recfilter = lambda x: x.check(dotfile=0, link=0)
        oldmodes = {}
        for x in path1.visit(rec=recfilter):
            oldmodes[x] = x.stat().mode
        path1.chmod(int("772", 8), rec=recfilter)
        try:
            for x in path1.visit(rec=recfilter):
                assert x.stat().mode & int("777", 8) == int("772", 8)
        finally:
            for x,y in oldmodes.items():
                x.chmod(y)

    @failsonjython
    def test_chown_identity(self, path1):
        owner = path1.stat().owner
        group = path1.stat().group
        path1.chown(owner, group)

    @failsonjython
    def test_chown_dangling_link(self, path1):
        owner = path1.stat().owner
        group = path1.stat().group
        x = path1.join('hello')
        x.mksymlinkto('qlwkejqwlek')
        try:
            path1.chown(owner, group, rec=1)
        finally:
            x.remove(rec=0)

    @failsonjython
    def test_chown_identity_rec_mayfail(self, path1):
        owner = path1.stat().owner
        group = path1.stat().group
        path1.chown(owner, group)
