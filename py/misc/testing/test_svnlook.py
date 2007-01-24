
import py
from py.__.misc import svnlook
data = py.magic.autopath().dirpath('data')

if py.path.local.sysfind('svnlook') is None or \
       py.path.local.sysfind('svnadmin') is None:
    py.test.skip("cannot test py.misc.svnlook, svn binaries not found")

def test_svnlook():
    tempdir = py.test.ensuretemp("svnlook")
    repo = tempdir.join("repo")
    py.process.cmdexec('svnadmin create --fs-type fsfs "%s"' % repo)
    py.process.cmdexec('svnadmin load "%s" < "%s"' %(repo, 
                       data.join("svnlookrepo.dump")))

    author = svnlook.author(repo, 1) 
    assert author == "hpk"
    
    for item in svnlook.changed(repo, 1): 
        svnurl = item.svnurl()
        assert item.revision == 1
        assert (svnurl.strpath + "/") == "file://%s/%s" %(repo, item.path)
        assert item.added
        assert not item.modified 
        assert not item.propchanged
        assert not item.deleted 
        assert item.path == "testdir/" 

    for item in svnlook.changed(repo, 2): 
        assert item.revision == 2
        assert not item.added
        assert not item.modified 
        assert item.propchanged 
        assert not item.deleted 
        assert item.path == "testdir/" 

    for item in svnlook.changed(repo, 3): 
        assert item.revision == 3
        assert item.added
        assert not item.modified 
        assert not item.propchanged 
        assert not item.deleted 
        assert item.path == "testdir2/" 

    for item in svnlook.changed(repo, 4): 
        assert item.revision == 4
        assert not item.added
        assert not item.modified 
        assert not item.propchanged 
        assert item.deleted 
        assert item.path == "testdir2/" 

    for item in svnlook.changed(repo, 5): 
        assert item.revision == 5
        assert not item.added
        assert not item.modified 
        assert item.propchanged 
        assert not item.deleted 
        assert item.path == "testdir/" 
