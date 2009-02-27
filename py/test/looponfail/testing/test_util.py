import py
from py.__.test.looponfail.util import StatRecorder

def test_filechange(tmpdir):
    tmp = tmpdir
    hello = tmp.ensure("hello.py")
    sd = StatRecorder([tmp])
    changed = sd.check()
    assert not changed

    hello.write("world")
    changed = sd.check()
    assert changed

    tmp.ensure("new.py")
    changed = sd.check()
    assert changed
    
    tmp.join("new.py").remove()
    changed = sd.check()
    assert changed

    tmp.join("a", "b", "c.py").ensure()
    changed = sd.check()
    assert changed

    tmp.join("a", "c.txt").ensure()
    changed = sd.check()
    assert changed
    changed = sd.check()
    assert not changed

    tmp.join("a").remove()
    changed = sd.check()
    assert changed

def test_pycremoval(tmpdir):
    tmp = tmpdir
    hello = tmp.ensure("hello.py")
    sd = StatRecorder([tmp])
    changed = sd.check()
    assert not changed

    pycfile = hello + "c"
    pycfile.ensure()
    changed = sd.check()
    assert not changed 

    hello.write("world")
    changed = sd.check()
    assert not pycfile.check()
    

def test_waitonchange(tmpdir):
    tmp = tmpdir
    sd = StatRecorder([tmp])

    wp = py._thread.WorkerPool(1)
    reply = wp.dispatch(sd.waitonchange, checkinterval=0.2)
    py.std.time.sleep(0.05)
    tmp.ensure("newfile.py")
    reply.get(timeout=0.5)
    wp.shutdown()
   
