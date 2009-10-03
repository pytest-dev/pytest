import py
from _py.test.looponfail.util import StatRecorder

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
    

def test_waitonchange(tmpdir, monkeypatch):
    tmp = tmpdir
    sd = StatRecorder([tmp])

    l = [True, False]
    monkeypatch.setattr(StatRecorder, 'check', lambda self: l.pop())
    sd.waitonchange(checkinterval=0.2)
    assert not l
