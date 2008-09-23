
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
    assert ret != 0
