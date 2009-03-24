"""

module defining basic hook for executing commands
in a - as much as possible - platform independent way.

Current list:

    exec_cmd(cmd)       executes the given command and returns output
                        or ExecutionFailed exception (if exit status!=0)

"""

import os, sys
import py

#-----------------------------------------------------------
# posix external command execution
#-----------------------------------------------------------
def posix_exec_cmd(cmd):
    """ return output of executing 'cmd'.

    raise ExecutionFailed exeception if the command failed.
    the exception will provide an 'err' attribute containing
    the error-output from the command.
    """
    __tracebackhide__ = True
    try:
        from subprocess import Popen, PIPE
    except ImportError:
        from py.__.compat.subprocess import Popen, PIPE

    import errno

    #print "execing", cmd
    child = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE,
                                                                close_fds=True)
    stdin, stdout, stderr = child.stdin, child.stdout, child.stderr

    # XXX sometimes we get a blocked r.read() call (see below)
    #     although select told us there is something to read.
    #     only the next three lines appear to prevent
    #     the read call from blocking infinitely.
    import fcntl
    def set_non_block(fd):
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        flags = flags | os.O_NONBLOCK
        fcntl.fcntl(fd, fcntl.F_SETFL, flags)
    set_non_block(stdout.fileno())
    set_non_block(stderr.fileno())
    #fcntl.fcntl(stdout, fcntl.F_SETFL, os.O_NONBLOCK)
    #fcntl.fcntl(stderr, fcntl.F_SETFL, os.O_NONBLOCK)

    import select
    out, err = [], []
    while 1:
        r_list = filter(lambda x: x and not x.closed, [stdout, stderr])
        if not r_list:
            break
        try:
            r_list = select.select(r_list, [], [])[0]
        except (select.error, IOError), se:
            if se.args[0] == errno.EINTR:
                continue
            else:
                raise
        for r  in r_list:
            try:
                data = r.read()   # XXX see XXX above
            except IOError, io:
                if io.args[0] == errno.EAGAIN:
                    continue
                # Connection Lost
                raise
            except OSError, ose:
                if ose.errno == errno.EPIPE:
                    # Connection Lost
                    raise
                if ose.errno == errno.EAGAIN: # MacOS-X does this
                    continue
                raise

            if not data:
                r.close()
                continue
            if r is stdout:
                out.append(data)
            else:
                err.append(data)
    pid, systemstatus = os.waitpid(child.pid, 0)
    if pid != child.pid:
        raise ExecutionFailed, "child process disappeared during: "+ cmd
    if systemstatus:
        if os.WIFSIGNALED(systemstatus):
            status = os.WTERMSIG(systemstatus) + 128
        else:
            status = os.WEXITSTATUS(systemstatus)
        raise ExecutionFailed(status, systemstatus, cmd,
                              ''.join(out), ''.join(err))
    return "".join(out)

#-----------------------------------------------------------
# simple win32 external command execution
#-----------------------------------------------------------
def win32_exec_cmd(cmd):
    """ return output of executing 'cmd'.

    raise ExecutionFailed exeception if the command failed.
    the exception will provide an 'err' attribute containing
    the error-output from the command.

    Note that this method can currently deadlock because
    we don't have WaitForMultipleObjects in the std-python api.

    Further note that the rules for quoting are very special
    under Windows. Do a HELP CMD in a shell, and tell me if
    you understand this. For now, I try to do a fix.
    """
    #print "*****", cmd

    # the following quoting is only valid for CMD.EXE, not COMMAND.COM
    cmd_quoting = True
    try:
        if os.environ['COMSPEC'].upper().endswith('COMMAND.COM'):
            cmd_quoting = False
    except KeyError:
        pass
    if cmd_quoting:
        if '"' in cmd and not cmd.startswith('""'):
            cmd = '"%s"' % cmd

    return popen3_exec_cmd(cmd)

def popen3_exec_cmd(cmd):
    stdin, stdout, stderr = os.popen3(cmd)
    out = stdout.read()
    err = stderr.read()
    stdout.close()
    stderr.close()
    status = stdin.close()
    if status:
        raise ExecutionFailed(status, status, cmd, out, err)
    return out

def pypy_exec_cmd(cmd):
    return popen3_exec_cmd(cmd)

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
#
# choose correct platform-version
#

if sys.platform == 'win32':
    cmdexec = win32_exec_cmd
elif hasattr(sys, 'pypy') or hasattr(sys, 'pypy_objspaceclass'):
    cmdexec = popen3_exec_cmd
else:
    cmdexec = posix_exec_cmd

# export the exception under the name 'py.process.cmdexec.Error'
cmdexec.Error = ExecutionFailed
try:
    ExecutionFailed.__module__ = 'py.process.cmdexec'
    ExecutionFailed.__name__ = 'Error'
except (AttributeError, TypeError):
    pass
