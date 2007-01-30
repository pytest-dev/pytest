from py import path, test
import py
from py.__.path.svn.testing.test_wccommand import getrepowc

class TestAPI:

    def setup_class(cls): 
        cls.root = py.test.ensuretemp(cls.__name__) 

    def repr_eval_test(self, p):
        r = repr(p)
        from py.path import local,svnurl, svnwc
        y = eval(r)
        assert y == p

    def test_defaultlocal(self):
        p = path.local()
        assert hasattr(p, 'atime')
        #assert hasattr(p, 'group') # XXX win32? 
        assert hasattr(p, 'setmtime')
        assert p.check()
        assert p.check(local=1)
        assert p.check(svnwc=0)
        assert not p.check(svnwc=1)
        self.repr_eval_test(p)

        #assert p.std.path()

    def test_local(self):
        p = path.local()
        assert hasattr(p, 'atime')
        assert hasattr(p, 'setmtime')
        assert p.check()
        assert p.check(local=1)
        self.repr_eval_test(p)

    def test_svnurl(self):
        p = path.svnurl('http://codespeak.net/svn/py')
        assert p.check(svnurl=1)
        self.repr_eval_test(p)

    def test_svnwc(self):
        p = path.svnwc(self.root)
        assert p.check(svnwc=1)
        self.repr_eval_test(p)

    #def test_fspy(self):
    #    p = path.py('smtplib.SMTP')
    #    self.repr_eval_test(p)


if __name__ == '__main__':
    test.main()

