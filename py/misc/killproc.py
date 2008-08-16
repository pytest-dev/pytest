
import py
import os, sys

def killproc(pid):
    if sys.platform == "win32":
        py.process.cmdexec("taskkill /F /PID %d" %(pid,))
    else:
        os.kill(pid, 15)
        
