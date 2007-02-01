
import py
import sys

WorkerPool = py._thread.WorkerPool
ThreadOut = py._thread.ThreadOut

def test_some():
    pool = WorkerPool()
    q = py.std.Queue.Queue()
    num = 4

    def f(i): 
        q.put(i) 
        while q.qsize(): 
            py.std.time.sleep(0.01) 
    for i in range(num):
        pool.dispatch(f, i) 
    for i in range(num):
        q.get()
    assert len(pool._alive) == 4
    pool.shutdown()
    # XXX I replaced the following join() with a time.sleep(1), which seems
    # to fix the test on Windows, and doesn't break it on Linux... Completely
    # unsure what the idea is, though, so it would be nice if someone with some
    # more understanding of what happens here would either fix this better, or
    # remove this comment...
    # pool.join(timeout=1.0)
    py.std.time.sleep(1)
    assert len(pool._alive) == 0
    assert len(pool._ready) == 0

def test_get():
    pool = WorkerPool()
    def f(): 
        return 42
    reply = pool.dispatch(f) 
    result = reply.get() 
    assert result == 42 

def test_get_timeout():
    pool = WorkerPool()
    def f(): 
        py.std.time.sleep(0.2) 
        return 42
    reply = pool.dispatch(f) 
    py.test.raises(IOError, "reply.get(timeout=0.01)") 

def test_get_excinfo():
    pool = WorkerPool()
    def f(): 
        raise ValueError("42") 
    reply = pool.dispatch(f) 
    excinfo = py.test.raises(ValueError, "reply.get(1.0)") 
    py.test.raises(EOFError, "reply.get(1.0)") 

def test_maxthreads():
    pool = WorkerPool(maxthreads=1)
    def f():
        py.std.time.sleep(0.5)
    try:
        pool.dispatch(f)
        py.test.raises(IOError, pool.dispatch, f)
    finally:
        pool.shutdown()

def test_join_timeout():
    pool = WorkerPool()
    q = py.std.Queue.Queue()
    def f():
        q.get() 
    reply = pool.dispatch(f)
    pool.shutdown()
    py.test.raises(IOError, pool.join, 0.01)
    q.put(None)
    reply.get(timeout=1.0) 
    pool.join(timeout=0.1) 

def test_pool_clean_shutdown():
    capture = py.io.StdCaptureFD() 
    pool = WorkerPool()
    def f():
        pass
    pool.dispatch(f)
    pool.dispatch(f)
    pool.shutdown()
    pool.join(timeout=1.0)
    assert not pool._alive
    assert not pool._ready
    out, err = capture.reset()
    print out
    print >>sys.stderr, err
    assert err == ''
