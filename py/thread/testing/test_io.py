
import py
import sys

WorkerPool = py._thread.WorkerPool
ThreadOut = py._thread.ThreadOut

def test_threadout_install_deinstall():
    old = sys.stdout
    out = ThreadOut(sys, 'stdout')
    out.deinstall()
    assert old == sys.stdout

class TestThreadOut:
    def setup_method(self, method):
        self.out = ThreadOut(sys, 'stdout')
    def teardown_method(self, method):
        self.out.deinstall()

    def test_threadout_one(self):
        l = []
        self.out.setwritefunc(l.append)
        print 42,13,
        x = l.pop(0)
        assert x == '42'
        x = l.pop(0)
        assert x == ' '
        x = l.pop(0)
        assert x == '13'


    def test_threadout_multi_and_default(self):
        num = 3
        defaults = []
        def f(l):
            self.out.setwritefunc(l.append)
            print id(l),
            self.out.delwritefunc()
            print 1
        self.out.setdefaultwriter(defaults.append)
        pool = WorkerPool()
        listlist = []
        for x in range(num):
            l = []
            listlist.append(l)
            pool.dispatch(f, l)
        pool.shutdown()
        for name, value in self.out.__dict__.items():
            print >>sys.stderr, "%s: %s" %(name, value)
        pool.join(2.0)
        for i in range(num):
            item = listlist[i]
            assert item ==[str(id(item))]
        assert not self.out._tid2out
        assert defaults
        expect = ['1' for x in range(num)]
        defaults = [x for x in defaults if x.strip()]
        assert defaults == expect

    def test_threadout_nested(self):
        # we want ThreadOuts to coexist
        last = sys.stdout
        out = ThreadOut(sys, 'stdout')
        assert last == sys.stdout
        out.deinstall()
        assert last == sys.stdout
