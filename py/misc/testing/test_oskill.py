
import py, sys

from py.__.misc.killproc import killproc

def test_win_killsubprocess():
    tmp = py.test.ensuretemp("test_win_killsubprocess")
    t = tmp.join("t.py")
    t.write("import time ; time.sleep(100)")
    proc = py.std.subprocess.Popen([sys.executable, str(t)])
    assert proc.poll() is None # no return value yet
    killproc(proc.pid)
    ret = proc.wait()
    assert ret != 0
        
