import py
import sys
from py.path import local
from py.__.path.testing.fscommon import CommonFSTests, setuptestfs

class LocalSetup:
    def setup_class(cls):
        cls.root = py.test.ensuretemp(cls.__name__)
        cls.root.ensure(dir=1)
        setuptestfs(cls.root)

    def setup_method(self, method):
        self.tmpdir = self.root.mkdir(method.__name__)

class TestLocalPath(LocalSetup, CommonFSTests):

    def test_join_normpath(self):
        assert self.tmpdir.join(".") == self.tmpdir
        p = self.tmpdir.join("../%s" % self.tmpdir.basename)
        assert p == self.tmpdir
        p = self.tmpdir.join("..//%s/" % self.tmpdir.basename)
        assert p == self.tmpdir

    def test_gethash(self):
        import md5
        import sha
        fn = self.tmpdir.join("testhashfile")
        fn.write("hello")
        assert fn.computehash("md5") == md5.md5("hello").hexdigest()
        assert fn.computehash("sha") == sha.sha("hello").hexdigest()
        py.test.raises(ValueError, fn.computehash, "asdasd")

    def test_remove_removes_readonly_file(self):
        readonly_file = self.tmpdir.join('readonly').ensure()
        readonly_file.chmod(0)
        readonly_file.remove()
        assert not readonly_file.check(exists=1)

    def test_remove_removes_readonly_dir(self):
        readonly_dir = self.tmpdir.join('readonlydir').ensure(dir=1)
        readonly_dir.chmod(0500)
        readonly_dir.remove()
        assert not readonly_dir.check(exists=1)

    def test_remove_removes_dir_and_readonly_file(self):
        readonly_dir = self.tmpdir.join('readonlydir').ensure(dir=1)
        readonly_file = readonly_dir.join('readonlyfile').ensure()
        readonly_file.chmod(0)
        readonly_dir.remove()
        assert not readonly_dir.check(exists=1)

    def test_initialize_curdir(self):
        assert str(local()) == py.std.os.getcwd()

    def test_initialize_reldir(self):
        old = self.root.chdir()
        try:
            p = local('samplefile')
            assert p.check()
        finally:
            old.chdir()

    def test_eq_with_strings(self):
        path1 = self.root.join('sampledir')
        path2 = str(path1)
        assert path1 == path2
        assert path2 == path1
        path3 = self.root.join('samplefile')
        assert path3 != path2
        assert path2 != path3

    def test_dump(self):
        import tempfile
        for bin in 0, 1: 
            try:
                fd, name = tempfile.mkstemp()
                f = py.std.os.fdopen(fd)
            except AttributeError:
                name = tempfile.mktemp()
                f = open(name, 'w+')
            try:
                d = {'answer' : 42}
                path = local(name)
                path.dump(d, bin=bin)
                from cPickle import load
                dnew = load(f)
                assert d == dnew
            finally:
                f.close()
                py.std.os.remove(name)

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

    def test_normpath(self):
        new1 = self.root.join("/otherdir")
        new2 = self.root.join("otherdir")
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

    def test_chdir(self):
        tmpdir = self.tmpdir.realpath()
        old = local()
        try:
            res = tmpdir.chdir()
            assert str(res) == str(old)
            assert py.std.os.getcwd() == str(tmpdir)
        finally:
            old.chdir()

    def test_ensure_filepath_withdir(self):
        tmpdir = self.tmpdir
        newfile = tmpdir.join('test1','test')
        newfile.ensure()
        assert newfile.check(file=1)
        newfile.write("42")
        newfile.ensure()
        assert newfile.read() == "42"

    def test_ensure_filepath_withoutdir(self):
        tmpdir = self.tmpdir
        newfile = tmpdir.join('test1file')
        t = newfile.ensure()
        assert t == newfile
        assert newfile.check(file=1)

    def test_ensure_dirpath(self):
        tmpdir = self.tmpdir
        newfile = tmpdir.join('test1','testfile')
        t = newfile.ensure(dir=1)
        assert t == newfile
        assert newfile.check(dir=1)

    def test_init_from_path(self):
        l = local()
        l2 = local(l)
        assert l2 is l

        wc = py.path.svnwc('.')
        l3 = local(wc)
        assert l3 is not wc
        assert l3.strpath == wc.strpath
        assert not hasattr(l3, 'commit')

    def test_long_filenames(self):
        if sys.platform == "win32":
            py.test.skip("win32: work around needed for path length limit")
        # see http://codespeak.net/pipermail/py-dev/2008q2/000922.html
        
        tmpdir = self.tmpdir
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

class TestExecutionOnWindows(LocalSetup):
    disabled = py.std.sys.platform != 'win32'

    def test_sysfind(self):
        x = py.path.local.sysfind('cmd')
        assert x.check(file=1)
        assert py.path.local.sysfind('jaksdkasldqwe') is None

class TestExecution(LocalSetup):
    disabled = py.std.sys.platform == 'win32'

    def test_sysfind(self):
        x = py.path.local.sysfind('test')
        assert x.check(file=1)
        assert py.path.local.sysfind('jaksdkasldqwe') is None

    def test_sysfind_no_permisson(self):
        dir = py.test.ensuretemp('sysfind') 
        env = py.std.os.environ
        oldpath = env['PATH']
        try:
            noperm = dir.ensure('noperm', dir=True)
            env['PATH'] += ":%s" % (noperm)
            noperm.chmod(0)
            assert py.path.local.sysfind('a') is None
            
        finally:
            env['PATH'] = oldpath
            noperm.chmod(0644)
            noperm.remove()
            
    def test_sysfind_absolute(self):
        x = py.path.local.sysfind('test')
        assert x.check(file=1)
        y = py.path.local.sysfind(str(x)) 
        assert y.check(file=1) 
        assert y == x 

    def test_sysfind_multiple(self):
        dir = py.test.ensuretemp('sysfind') 
        env = py.std.os.environ
        oldpath = env['PATH']
        try:
            env['PATH'] += ":%s:%s" % (dir.ensure('a'),
                                       dir.join('b'))
            dir.ensure('b', 'a')
            checker = lambda x: x.dirpath().basename == 'b'
            x = py.path.local.sysfind('a', checker=checker)
            assert x.basename == 'a'
            assert x.dirpath().basename == 'b'
            checker = lambda x: None
            assert py.path.local.sysfind('a', checker=checker) is None
        finally:
            env['PATH'] = oldpath
            #dir.remove()

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

    def test_make_numbered_dir(self):
        root = self.tmpdir
        root.ensure('base.not_an_int', dir=1)
        for i in range(10):
            numdir = local.make_numbered_dir(prefix='base.', rootdir=root,
                                             keep=2, lock_timeout=0)
            assert numdir.check()
            assert numdir.basename == 'base.%d' %i
            if i>=1:
                assert numdir.new(ext=str(i-1)).check()
            if i>=2:
                assert numdir.new(ext=str(i-2)).check()
            if i>=3:
                assert not numdir.new(ext=str(i-3)).check()

    def test_locked_make_numbered_dir(self):
        if py.test.config.option.boxed: 
            py.test.skip("Fails when run as boxed tests")
        root = self.tmpdir
        for i in range(10):
            numdir = local.make_numbered_dir(prefix='base2.', rootdir=root,
                                             keep=2)
            assert numdir.check()
            assert numdir.basename == 'base2.%d' %i
            for j in range(i):
                assert numdir.new(ext=str(j)).check()

    def test_error_preservation(self):
        py.test.raises (EnvironmentError, self.root.join('qwoeqiwe').mtime)
        py.test.raises (EnvironmentError, self.root.join('qwoeqiwe').read)

    #def test_parentdirmatch(self):
    #    local.parentdirmatch('std', startmodule=__name__)
    #

    # importing tests 
    def test_pyimport(self):
        obj = self.root.join('execfile.py').pyimport()
        assert obj.x == 42
        assert obj.__name__ == 'execfile' 

    def test_pyimport_execfile_different_name(self):
        obj = self.root.join('execfile.py').pyimport(modname="0x.y.z")
        assert obj.x == 42
        assert obj.__name__ == '0x.y.z' 

    def test_pyimport_a(self):
        otherdir = self.root.join('otherdir')
        mod = otherdir.join('a.py').pyimport()
        assert mod.result == "got it"
        assert mod.__name__ == 'otherdir.a' 

    def test_pyimport_b(self):
        otherdir = self.root.join('otherdir')
        mod = otherdir.join('b.py').pyimport()
        assert mod.stuff == "got it"
        assert mod.__name__ == 'otherdir.b' 

    def test_pyimport_c(self):
        otherdir = self.root.join('otherdir')
        mod = otherdir.join('c.py').pyimport()
        assert mod.value == "got it"

    def test_pyimport_d(self):
        otherdir = self.root.join('otherdir')
        mod = otherdir.join('d.py').pyimport()
        assert mod.value2 == "got it"

    def test_pyimport_and_import(self):
        # XXX maybe a bit of a fragile test ...
        p = py.test.ensuretemp("pyimport") 
        p.ensure('xxxpackage', '__init__.py') 
        mod1path = p.ensure('xxxpackage', 'module1.py')
        mod1 = mod1path.pyimport() 
        assert mod1.__name__ == 'xxxpackage.module1' 
        from xxxpackage import module1 
        assert module1 is mod1

def test_pypkgdir():
    datadir = py.test.ensuretemp("pypkgdir")
    pkg = datadir.ensure('pkg1', dir=1)
    pkg.ensure("__init__.py")
    pkg.ensure("subdir/__init__.py")
    assert pkg.pypkgpath() == pkg
    assert pkg.join('subdir', '__init__.py').pypkgpath() == pkg

def test_homedir():
    homedir = py.path.local._gethomedir()
    assert homedir.check(dir=1)

