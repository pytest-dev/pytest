"""

"""

import os, sys
import subprocess
import py
from subprocess import Popen, PIPE

def cmdexec(cmd):
    """ return output of executing 'cmd' in a separate process.

    raise cmdexec.ExecutionFailed exeception if the command failed.
    the exception will provide an 'err' attribute containing
    the error-output from the command.
    """
    process = subprocess.Popen(cmd, shell=True, 
            universal_newlines=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    out = py.builtin._totext(out, sys.getdefaultencoding())
    err = py.builtin._totext(err, sys.getdefaultencoding())
    status = process.poll()
    if status:
        raise ExecutionFailed(status, status, cmd, out, err)
    return out

class ExecutionFailed(py.error.Error):
    def __init__(self, status, systemstatus, cmd, out, err):
        Exception.__init__(self)
        self.status = status
        self.systemstatus = systemstatus
        self.cmd = cmd
        self.err = err
        self.out = out

    def __str__(self):
        return "ExecutionFailed: %d  %s\n%s" %(self.status, self.cmd, self.err)

# export the exception under the name 'py.process.cmdexec.Error'
cmdexec.Error = ExecutionFailed
try:
    ExecutionFailed.__module__ = 'py.process.cmdexec'
    ExecutionFailed.__name__ = 'Error'
except (AttributeError, TypeError):
    pass
