import py
from py.__.path.svn.urlcommand import InfoSvnCommand
from py.__.path.svn.testing.svntestbase import CommonCommandAndBindingTests, \
                                               getrepowc
import datetime
import time

def setup_module(mod):
    if py.path.local.sysfind('svn') is None:
        py.test.skip("cannot test py.path.svn, 'svn' binary not found")

class TestSvnURLCommandPath(CommonCommandAndBindingTests):
    def setup_class(cls): 
        repo, wc = getrepowc()
        cls.root = py.path.svnurl(repo)

    def test_move_file(self):  # overrides base class
        p = self.root.ensure('origfile')
        newp = p.dirpath('newfile')
        p.move(newp)
        assert newp.check(file=1)
        newp.remove()
        assert not p.check()

    def test_move_dir(self):  # overrides base class
        p = self.root.ensure('origdir', dir=1)
        newp = p.dirpath('newdir')
        p.move(newp)
        assert newp.check(dir=1)
        newp.remove()
        assert not p.check()

    def test_svnurl_needs_arg(self):
        py.test.raises(TypeError, "py.path.svnurl()")

    def test_svnurl_does_not_accept_None_either(self):
        py.test.raises(Exception, "py.path.svnurl(None)")

    def test_svnurl_characters_simple(self):
        py.path.svnurl("svn+ssh://hello/world")

    def test_svnurl_characters_at_user(self):
        py.path.svnurl("http://user@host.com/some/dir")

    def test_svnurl_characters_at_path(self):
        py.test.raises(ValueError, 'py.path.svnurl("http://host.com/foo@bar")')

    def test_svnurl_characters_colon_port(self):
        py.path.svnurl("http://host.com:8080/some/dir")

    def test_svnurl_characters_tilde_end(self):
        py.path.svnurl("http://host.com/some/file~")

    def test_svnurl_characters_colon_path(self):
        if py.std.sys.platform == 'win32':
            # colons are allowed on win32, because they're part of the drive
            # part of an absolute path... however, they shouldn't be allowed in
            # other parts, I think
            py.test.skip('XXX fixme win32')
        py.test.raises(ValueError, 'py.path.svnurl("http://host.com/foo:bar")')

    def test_export(self):
        repo, wc = getrepowc('test_export_repo', 'test_export_wc')
        foo = wc.join('foo').ensure(dir=True)
        bar = foo.join('bar').ensure(file=True)
        bar.write('bar\n')
        foo.commit('testing something')
        exportpath = py.test.ensuretemp('test_export_exportdir')
        url = py.path.svnurl(repo + '/foo')
        foo = url.export(exportpath.join('foo'))
        assert foo == exportpath.join('foo')
        assert isinstance(foo, py.path.local)
        assert foo.join('bar').check()
        assert not foo.join('.svn').check()

    def test_export_rev(self):
        repo, wc = getrepowc('test_export_rev_repo', 'test_export_rev_wc')
        foo = wc.join('foo').ensure(dir=True)
        bar = foo.join('bar').ensure(file=True)
        bar.write('bar\n')
        rev1 = foo.commit('testing something')
        print 'rev1:', rev1
        baz = foo.join('baz').ensure(file=True)
        baz.write('baz\n')
        rev2 = foo.commit('testing more')
        
        exportpath = py.test.ensuretemp('test_export_rev_exportdir')
        url = py.path.svnurl(repo + '/foo', rev=rev1)
        foo1 = url.export(exportpath.join('foo1'))
        assert foo1.check()
        assert foo1.join('bar').check()
        assert not foo1.join('baz').check()

        url = py.path.svnurl(repo + '/foo', rev=rev2)
        foo2 = url.export(exportpath.join('foo2'))
        assert foo2.check()
        assert foo2.join('bar').check()
        assert foo2.join('baz').check()

class TestSvnInfoCommand:

    def test_svn_1_2(self):
        line = "   2256      hpk        165 Nov 24 17:55 __init__.py"
        info = InfoSvnCommand(line)
        now = datetime.datetime.now()
        assert info.last_author == 'hpk'
        assert info.created_rev == 2256
        assert info.kind == 'file'
        # we don't check for the year (2006), because that depends
        # on the clock correctly being setup
        assert time.gmtime(info.mtime)[1:6] == (11, 24, 17, 55, 0)
        assert info.size ==  165
        assert info.time == info.mtime * 1000000

    def test_svn_1_3(self):
        line ="    4784 hpk                 2 Jun 01  2004 __init__.py"
        info = InfoSvnCommand(line)
        assert info.last_author == 'hpk'
        assert info.kind == 'file'

    def test_svn_1_3_b(self):
        line ="     74 autoadmi              Oct 06 23:59 plonesolutions.com/"
        info = InfoSvnCommand(line)
        assert info.last_author == 'autoadmi'
        assert info.kind == 'dir'

def test_badchars():
    py.test.raises(ValueError, "py.path.svnurl('file:///tmp/@@@:')")
