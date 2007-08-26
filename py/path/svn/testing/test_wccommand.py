import py
from py.__.path.svn.testing.svntestbase import CommonSvnTests, getrepowc
from py.__.path.svn.wccommand import InfoSvnWCCommand
from py.__.path.svn.wccommand import parse_wcinfotime
from py.__.path.svn import svncommon


if py.path.local.sysfind('svn') is None:
    py.test.skip("cannot test py.path.svn, 'svn' binary not found")


class TestWCSvnCommandPath(CommonSvnTests):

    def setup_class(cls): 
        repo, cls.root = getrepowc()

    def test_move_file(self):  # overrides base class
        try:
            super(TestWCSvnCommandPath, self).test_move_file()
        finally:
            self.root.revert(rec=1)

    def test_move_directory(self): # overrides base class
        try:
            super(TestWCSvnCommandPath, self).test_move_directory()
        finally:
            self.root.revert(rec=1)

    def test_status_attributes_simple(self):
        def assert_nochange(p):
            s = p.status()
            assert not s.modified
            assert not s.prop_modified
            assert not s.added
            assert not s.deleted

        dpath = self.root.join('sampledir')
        assert_nochange(self.root.join('sampledir'))
        assert_nochange(self.root.join('samplefile'))

    def test_status_added(self):
        nf = self.root.join('newfile')
        nf.write('hello')
        nf.add()
        try:
            s = nf.status()
            assert s.added
            assert not s.modified
            assert not s.prop_modified
        finally:
            nf.revert()

    def test_status_change(self):
        nf = self.root.join('samplefile')
        try:
            nf.write(nf.read() + 'change')
            s = nf.status()
            assert not s.added
            assert s.modified
            assert not s.prop_modified
        finally:
            nf.revert()

    def test_status_added_ondirectory(self):
        sampledir = self.root.join('sampledir')
        try:
            t2 = sampledir.mkdir('t2')
            t1 = t2.join('t1')
            t1.write('test')
            t1.add()
            s = sampledir.status(rec=1)
            # Comparing just the file names, because paths are unpredictable
            # on Windows. (long vs. 8.3 paths)
            assert t1.basename in [item.basename for item in s.added]
            assert t2.basename in [item.basename for item in s.added]
        finally:
            t2.revert(rec=1)
            t2.localpath.remove(rec=1)

    def test_status_unknown(self):
        t1 = self.root.join('un1')
        try:
            t1.write('test')
            s = self.root.status()
            # Comparing just the file names, because paths are unpredictable
            # on Windows. (long vs. 8.3 paths)
            assert t1.basename in [item.basename for item in s.unknown]
        finally:
            t1.localpath.remove()

    def test_status_unchanged(self):
        r = self.root
        s = self.root.status(rec=1)
        # Comparing just the file names, because paths are unpredictable
        # on Windows. (long vs. 8.3 paths)
        assert r.join('samplefile').basename in [item.basename 
                                                    for item in s.unchanged]
        assert r.join('sampledir').basename in [item.basename 
                                                    for item in s.unchanged]
        assert r.join('sampledir/otherfile').basename in [item.basename 
                                                    for item in s.unchanged]

    def test_status_update(self):
        r = self.root
        try:
            r.update(rev=1)
            s = r.status(updates=1, rec=1)
            # Comparing just the file names, because paths are unpredictable
            # on Windows. (long vs. 8.3 paths)
            assert r.join('anotherfile').basename in [item.basename for 
                                                    item in s.update_available]
            #assert len(s.update_available) == 1
        finally:
            r.update()

    def test_diff(self):
        p = self.root / 'anotherfile'
        out = p.diff(rev=2)
        assert out.find('hello') != -1

    def test_blame(self):
        p = self.root.join('samplepickle')
        lines = p.blame()
        assert sum([l[0] for l in lines]) == len(lines)
        for l1, l2 in zip(p.readlines(), [l[2] for l in lines]):
            assert l1 == l2
        assert [l[1] for l in lines] == ['hpk'] * len(lines)
        p = self.root.join('samplefile')
        lines = p.blame()
        assert sum([l[0] for l in lines]) == len(lines)
        for l1, l2 in zip(p.readlines(), [l[2] for l in lines]):
            assert l1 == l2
        assert [l[1] for l in lines] == ['hpk'] * len(lines)

    def test_join_abs(self):
        s = str(self.root.localpath)
        n = self.root.join(s, abs=1)
        assert self.root == n

    def test_join_abs2(self):
        assert self.root.join('samplefile', abs=1) == self.root.join('samplefile')

    def test_str_gives_localpath(self):
        assert str(self.root) == str(self.root.localpath)

    def test_versioned(self):
        assert self.root.check(versioned=1)
        # TODO: Why does my copy of svn think .svn is versioned?
        #assert self.root.join('.svn').check(versioned=0) 
        assert self.root.join('samplefile').check(versioned=1)
        assert not self.root.join('notexisting').check(versioned=1)
        notexisting = self.root.join('hello').localpath
        try:
            notexisting.write("")
            assert self.root.join('hello').check(versioned=0)
        finally:
            notexisting.remove()

    def test_nonversioned_remove(self):
        assert self.root.check(versioned=1)
        somefile = self.root.join('nonversioned/somefile')
        nonwc = py.path.local(somefile)
        nonwc.ensure()
        assert somefile.check()
        assert not somefile.check(versioned=True)
        somefile.remove() # this used to fail because it tried to 'svn rm'

    def test_properties(self):
        try:
            self.root.propset('gaga', 'this')
            assert self.root.propget('gaga') == 'this'
            # Comparing just the file names, because paths are unpredictable
            # on Windows. (long vs. 8.3 paths)
            assert self.root.basename in [item.basename for item in 
                                        self.root.status().prop_modified]
            assert 'gaga' in self.root.proplist()
            assert self.root.proplist()['gaga'] == 'this'

        finally:
            self.root.propdel('gaga')

    def test_proplist_recursive(self):
        s = self.root.join('samplefile')
        s.propset('gugu', 'that')
        try:
            p = self.root.proplist(rec=1)
            # Comparing just the file names, because paths are unpredictable
            # on Windows. (long vs. 8.3 paths)
            assert (self.root / 'samplefile').basename in [item.basename 
                                                                for item in p]
        finally:
            s.propdel('gugu')

    def test_long_properties(self):
        value = """
        vadm:posix : root root 0100755
        Properties on 'chroot/dns/var/bind/db.net.xots':
                """
        try:
            self.root.propset('gaga', value)
            backvalue = self.root.propget('gaga')
            assert backvalue == value
            #assert len(backvalue.split('\n')) == 1
        finally:
            self.root.propdel('gaga')


    def test_ensure(self):
        newpath = self.root.ensure('a', 'b', 'c')
        try:
            assert newpath.check(exists=1, versioned=1)
            newpath.write("hello")
            newpath.ensure()
            assert newpath.read() == "hello"
        finally:
            self.root.join('a').remove(force=1)

    def test_not_versioned(self):
        p = self.root.localpath.mkdir('whatever')
        f = self.root.localpath.ensure('testcreatedfile')
        try:
            assert self.root.join('whatever').check(versioned=0)
            assert self.root.join('testcreatedfile').check(versioned=0)
            assert not self.root.join('testcreatedfile').check(versioned=1)
        finally:
            p.remove(rec=1)
            f.remove()

    def test_lock_unlock(self):
        root = self.root
        somefile = root.join('somefile')
        somefile.ensure(file=True)
        # not yet added to repo
        py.test.raises(py.process.cmdexec.Error, 'somefile.lock()')
        somefile.write('foo')
        somefile.commit('test')
        assert somefile.check(versioned=True)
        somefile.lock()
        try:
            locked = root.status().locked
            assert len(locked) == 1
            assert str(locked[0]) == str(somefile)
            #assert somefile.locked()
            py.test.raises(Exception, 'somefile.lock()')
        finally:
            somefile.unlock()
        #assert not somefile.locked()
        locked = root.status().locked
        assert locked == []
        py.test.raises(Exception, 'somefile,unlock()')
        somefile.remove()

    def test_commit_nonrecursive(self):
        root = self.root
        somedir = root.join('sampledir')
        somefile = somedir.join('otherfile')
        somefile.write('foo')
        somedir.propset('foo', 'bar')
        status = somedir.status()
        assert len(status.prop_modified) == 1
        assert len(status.modified) == 1

        somedir.commit('non-recursive commit', rec=0)
        status = somedir.status()
        assert len(status.prop_modified) == 0
        assert len(status.modified) == 1

        somedir.commit('recursive commit')
        status = somedir.status()
        assert len(status.prop_modified) == 0
        assert len(status.modified) == 0

    #def test_log(self):
    #   l = self.root.log()
    #   assert len(l) == 3  # might need to be upped if more tests are added

class XTestWCSvnCommandPathSpecial:

    rooturl = 'http://codespeak.net/svn/py.path/trunk/dist/py.path/test/data'
    #def test_update_none_rev(self):
    #    path = tmpdir.join('checkouttest')
    #    wcpath = newpath(xsvnwc=str(path), url=self.rooturl)
    #    try:
    #        wcpath.checkout(rev=2100)
    #        wcpath.update()
    #        assert wcpath.info().rev > 2100
    #    finally:
    #        wcpath.localpath.remove(rec=1)

def test_parse_wcinfotime():
    assert (parse_wcinfotime('2006-05-30 20:45:26 +0200 (Tue, 30 May 2006)') ==
            1149021926)
    assert (parse_wcinfotime('2003-10-27 20:43:14 +0100 (Mon, 27 Oct 2003)') ==
            1067287394)

class TestInfoSvnWCCommand:

    def test_svn_1_2(self):
        output = """
        Path: test_wccommand.py
        Name: test_wccommand.py
        URL: http://codespeak.net/svn/py/dist/py/path/svn/wccommand.py
        Repository UUID: fd0d7bf2-dfb6-0310-8d31-b7ecfe96aada
        Revision: 28137
        Node Kind: file
        Schedule: normal
        Last Changed Author: jan
        Last Changed Rev: 27939
        Last Changed Date: 2006-05-30 20:45:26 +0200 (Tue, 30 May 2006)
        Text Last Updated: 2006-06-01 00:42:53 +0200 (Thu, 01 Jun 2006)
        Properties Last Updated: 2006-05-23 11:54:59 +0200 (Tue, 23 May 2006)
        Checksum: 357e44880e5d80157cc5fbc3ce9822e3
        """
        path = py.magic.autopath().dirpath().chdir()
        info = InfoSvnWCCommand(output)
        path.chdir()
        assert info.last_author == 'jan'
        assert info.kind == 'file'
        assert info.mtime == 1149021926.0
        assert info.url == 'http://codespeak.net/svn/py/dist/py/path/svn/wccommand.py'
        assert info.time == 1149021926000000.0
        assert info.rev == 28137


    def test_svn_1_3(self):
        output = """
        Path: test_wccommand.py
        Name: test_wccommand.py
        URL: http://codespeak.net/svn/py/dist/py/path/svn/wccommand.py
        Repository Root: http://codespeak.net/svn
        Repository UUID: fd0d7bf2-dfb6-0310-8d31-b7ecfe96aada
        Revision: 28124
        Node Kind: file
        Schedule: normal
        Last Changed Author: jan
        Last Changed Rev: 27939
        Last Changed Date: 2006-05-30 20:45:26 +0200 (Tue, 30 May 2006)
        Text Last Updated: 2006-06-02 23:46:11 +0200 (Fri, 02 Jun 2006)
        Properties Last Updated: 2006-06-02 23:45:28 +0200 (Fri, 02 Jun 2006)
        Checksum: 357e44880e5d80157cc5fbc3ce9822e3
        """
        path = py.magic.autopath().dirpath().chdir()
        info = InfoSvnWCCommand(output)
        path.chdir()
        assert info.last_author == 'jan'
        assert info.kind == 'file'
        assert info.mtime == 1149021926.0
        assert info.url == 'http://codespeak.net/svn/py/dist/py/path/svn/wccommand.py'
        assert info.rev == 28124
        assert info.time == 1149021926000000.0

class TestWCSvnCommandPathEmptyRepo(object):

    def setup_class(cls):
        repo = py.test.ensuretemp("emptyrepo")
        wcdir = py.test.ensuretemp("emptywc")
        py.process.cmdexec('svnadmin create "%s"' %
                svncommon._escape_helper(repo))
        wc = py.path.svnwc(wcdir)
        repopath = repo.strpath
        if py.std.sys.platform.startswith('win32'):
            # strange win problem, paths become something like file:///c:\\foo
            repourl = 'file:///%s' % (repopath.replace('\\', '/'),)
        else:
            repourl = 'file://%s' % (repopath,)
        wc.checkout(url=repourl)
        cls.wc = wc

    def test_info(self):
        self.wc.info().rev = 0

def test_characters_at():
    py.test.raises(ValueError, "py.path.svnwc('/tmp/@@@:')")

def test_characters_tilde():
    py.path.svnwc('/tmp/test~')
