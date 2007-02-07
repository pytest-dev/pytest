import py
from py.__.path.svn.testing.svntestbase import make_test_repo


if py.path.local.sysfind('svn') is None:
    py.test.skip("cannot test py.path.svn, 'svn' binary not found")

class TestMakeRepo(object):
    def setup_class(cls):
        cls.repo = make_test_repo()
        cls.wc = py.path.svnwc(py.test.ensuretemp("test-wc").join("wc"))

    def test_empty_checkout(self):
        self.wc.checkout(self.repo)
        assert len(self.wc.listdir()) == 0

    def test_commit(self):
        self.wc.checkout(self.repo)
        p = self.wc.join("a_file")
        p.write("test file")
        p.add()
        rev = self.wc.commit("some test")
        assert p.info().rev == 1
        assert rev == 1
        rev = self.wc.commit()
        assert rev is None
        
