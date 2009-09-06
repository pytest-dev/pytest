
import py, sys

def test_kill():
    subprocess = py.test.importorskip("subprocess")
    tmp = py.test.ensuretemp("test_kill")
    t = tmp.join("t.py")
    t.write("import time ; time.sleep(100)")
    proc = py.std.subprocess.Popen([sys.executable, str(t)])
    assert proc.poll() is None # no return value yet
    py.process.kill(proc.pid)
    ret = proc.wait()
    if sys.platform == "win32" and ret == 0:
        py.test.skip("XXX on win32, subprocess.Popen().wait() on a killed "
                     "process does not yield return value != 0")
        
    assert ret != 0
