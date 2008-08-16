import py
from py.__.test.looponfail.util import StatRecorder, EventRecorder
from py.__.test import event

def test_filechange():
    tmp = py.test.ensuretemp("test_filechange")
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

def test_pycremoval():
    tmp = py.test.ensuretemp("test_pycremoval")
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
    

def test_waitonchange():
    tmp = py.test.ensuretemp("test_waitonchange")
    sd = StatRecorder([tmp])

    wp = py._thread.WorkerPool(1)
    reply = wp.dispatch(sd.waitonchange, checkinterval=0.2)
    py.std.time.sleep(0.05)
    tmp.ensure("newfile.py")
    reply.get(timeout=0.5)
    wp.shutdown()
    
def test_eventrecorder():
    bus = event.EventBus()
    recorder = EventRecorder(bus)
    bus.notify(event.NOP())
    assert recorder.events 
    assert not recorder.getfailures()
    rep = event.ItemTestReport(None, failed=True)
    bus.notify(rep)
    failures = recorder.getfailures()
    assert failures == [rep]
    recorder.clear() 
    assert not recorder.events
    assert not recorder.getfailures()
    recorder.unsubscribe()
    bus.notify(rep)
    assert not recorder.events 
    assert not recorder.getfailures()
    
    
        
    
    
    
    

