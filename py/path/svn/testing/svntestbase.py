import sys
import py
from py import path, test, process
from py.__.path.testing.fscommon import CommonFSTests, setuptestfs
from py.__.path.svn import cache, svncommon

mypath = py.magic.autopath()
repodump = mypath.dirpath('repotest.dump')

# make a wc directory out of a given root url
# cache previously obtained wcs!
#
def getrepowc(reponame='basetestrepo', wcname='wc'):
    repo = py.test.ensuretemp(reponame)
    wcdir = py.test.ensuretemp(wcname)
    if not repo.listdir():
        #assert not wcdir.check()
        repo.ensure(dir=1)
        py.process.cmdexec('svnadmin create "%s"' %
                svncommon._escape_helper(repo))
        py.process.cmdexec('svnadmin load -q "%s" <"%s"' %
                (svncommon._escape_helper(repo), repodump))
        print "created svn repository", repo
        wcdir.ensure(dir=1)
        wc = py.path.svnwc(wcdir)
        if py.std.sys.platform == 'win32':
            repo = '/' + str(repo).replace('\\', '/')
        wc.checkout(url='file://%s' % repo)
        print "checked out new repo into", wc
    else:
        print "using repository at", repo
        wc = py.path.svnwc(wcdir)
    return ("file://%s" % repo, wc)


def save_repowc(): 
    repo, wc = getrepowc() 
    repo = py.path.local(repo[len("file://"):])
    assert repo.check() 
    savedrepo = repo.dirpath('repo_save')
    savedwc = wc.dirpath('wc_save') 
    repo.copy(savedrepo) 
    wc.localpath.copy(savedwc.localpath)
    return savedrepo, savedwc 

def restore_repowc((savedrepo, savedwc)): 
    repo, wc = getrepowc() 
    print repo
    print repo[len("file://"):]
    repo = py.path.local(repo[len("file://"):])
    print repo
    assert repo.check() 
    # repositories have read only files on windows
    #repo.chmod(0777, rec=True)
    repo.remove() 
    wc.localpath.remove() 
    savedrepo.move(repo) 
    savedwc.localpath.move(wc.localpath) 

# create an empty repository for testing purposes and return the url to it
def make_test_repo(name="test-repository"):
    repo = py.test.ensuretemp(name)
    try:
        py.process.cmdexec('svnadmin create %s' % repo)
    except:
        repo.remove()
        raise
    if sys.platform == 'win32':
        repo = '/' + str(repo).replace('\\', '/')
    return py.path.svnurl("file://%s" % repo)

class CommonSvnTests(CommonFSTests):

    def setup_method(self, meth):
        bn = meth.func_name
        for x in 'test_remove', 'test_move', 'test_status_deleted':
            if bn.startswith(x):
                self._savedrepowc = save_repowc() 

    def teardown_method(self, meth): 
        x = getattr(self, '_savedrepowc', None) 
        if x is not None:
            restore_repowc(x) 
            del self._savedrepowc 

    def test_propget(self):
        url = self.root.join("samplefile")
        value = url.propget('svn:eol-style')
        assert value == 'native'

    def test_proplist(self):
        url = self.root.join("samplefile")
        res = url.proplist()
        assert res['svn:eol-style'] == 'native'

    def test_info(self):
        url = self.root.join("samplefile")
        res = url.info()
        assert res.size > len("samplefile") and res.created_rev >= 0

    def test_log_simple(self):
        url = self.root.join("samplefile")
        logentries = url.log()
        for logentry in logentries:
            assert logentry.rev == 1
            assert hasattr(logentry, 'author')
            assert hasattr(logentry, 'date')

class CommonCommandAndBindingTests(CommonSvnTests):
    def test_trailing_slash_is_stripped(self):
        # XXX we need to test more normalizing properties
        url = self.root.join("/")
        assert self.root == url

    #def test_different_revs_compare_unequal(self):
    #    newpath = self.root.new(rev=1199)
    #    assert newpath != self.root

    def test_exists_svn_root(self):
        assert self.root.check()

    #def test_not_exists_rev(self):
    #    url = self.root.__class__(self.rooturl, rev=500)
    #    assert url.check(exists=0)

    #def test_nonexisting_listdir_rev(self):
    #    url = self.root.__class__(self.rooturl, rev=500)
    #    raises(py.error.ENOENT, url.listdir)

    #def test_newrev(self):
    #    url = self.root.new(rev=None)
    #    assert url.rev == None
    #    assert url.strpath == self.root.strpath
    #    url = self.root.new(rev=10)
    #    assert url.rev == 10

    #def test_info_rev(self):
    #    url = self.root.__class__(self.rooturl, rev=1155)
    #    url = url.join("samplefile")
    #    res = url.info()
    #    assert res.size > len("samplefile") and res.created_rev == 1155

    # the following tests are easier if we have a path class
    def test_repocache_simple(self):
        repocache = cache.RepoCache()
        repocache.put(self.root.strpath, 42)
        url, rev = repocache.get(self.root.join('test').strpath)
        assert rev == 42
        assert url == self.root.strpath

    def test_repocache_notimeout(self):
        repocache = cache.RepoCache()
        repocache.timeout = 0
        repocache.put(self.root.strpath, self.root.rev)
        url, rev = repocache.get(self.root.strpath)
        assert rev == -1
        assert url == self.root.strpath

    def test_repocache_outdated(self):
        repocache = cache.RepoCache()
        repocache.put(self.root.strpath, 42, timestamp=0)
        url, rev = repocache.get(self.root.join('test').strpath)
        assert rev == -1
        assert url == self.root.strpath

    def _test_getreporev(self):
        """ this test runs so slow it's usually disabled """
        old = cache.repositories.repos
        try:
            _repocache.clear()
            root = self.root.new(rev=-1)
            url, rev = cache.repocache.get(root.strpath)
            assert rev>=0
            assert url == svnrepourl
        finally:
            repositories.repos = old

#cache.repositories.put(svnrepourl, 1200, 0)
