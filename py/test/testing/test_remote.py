import py
from py.__.test.testing.setupdata import setup_module

class TestRemote: 
    def test_exec(self): 
        o = tmpdir.ensure('remote', dir=1) 
        tfile = o.join('test_exec.py')
        tfile.write(py.code.Source("""
            def test_1():
                assert 1 == 0 
        """))
        print py.std.sys.executable
        config = py.test.config._reparse(
                        ['--exec=' + py.std.sys.executable, 
                         o])
        cls = config._getsessionclass() 
        out = []  # out = py.std.Queue.Queue() 
        session = cls(config, out.append) 
        session.main()
        for s in out: 
            if s.find('1 failed') != -1: 
                break 
        else: 
            py.test.fail("did not see test_1 failure") 

    def test_looponfailing(self): 
        o = tmpdir.ensure('looponfailing', dir=1) 
        tfile = o.join('test_looponfailing.py')
        tfile.write(py.code.Source("""
            def test_1():
                assert 1 == 0 
        """))
        print py.std.sys.executable
        config = py.test.config._reparse(['--looponfailing', str(o)])
        cls = config._getsessionclass() 
        out = py.std.Queue.Queue() 
        session = cls(config, out.put) 
        pool = py._thread.WorkerPool() 
        reply = pool.dispatch(session.main)
        while 1: 
            s = out.get(timeout=5.0)
            if s.find('1 failed') != -1: 
                break 
            print s
        else: 
            py.test.fail("did not see test_1 failure") 
        # XXX we would like to have a cleaner way to finish 
        try: 
            reply.get(timeout=5.0) 
        except IOError, e: 
            assert str(e).lower().find('timeout') != -1 

        
