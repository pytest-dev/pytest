
""" boxing - wrapping process with another process so we can run
a process inside and see if it crashes
"""

import py
import os
import sys
import marshal
from py.__.test import config as pytestconfig

PYTESTSTDOUT = "pyteststdout"
PYTESTSTDERR = "pyteststderr"
PYTESTRETVAL = "pytestretval"

import tempfile
import itertools
from StringIO import StringIO

counter = itertools.count().next

class FileBox(object):
    def __init__(self, fun, args=None, kwargs=None, config=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        self.fun = fun
        self.config = config
        assert self.config
        self.args = args
        self.kwargs = kwargs
    
    def run(self, continuation=False):
        # XXX we should not use py.test.ensuretemp here
        count = counter()
        tempdir = py.test.ensuretemp("box%d" % count)
        self.tempdir = tempdir
        self.PYTESTRETVAL = tempdir.join('retval')
        self.PYTESTSTDOUT = tempdir.join('stdout')
        self.PYTESTSTDERR = tempdir.join('stderr')

        nice_level = self.config.getvalue('dist_nicelevel')
        pid = os.fork()
        if pid:
            if not continuation:
                self.parent(pid)
            else:
                return self.parent, pid
        else:
            try:
                outcome = self.children(nice_level)
            except:
                excinfo = py.code.ExceptionInfo()
                x = open("/tmp/traceback", "w")
                print >>x, "Internal box error"
                for i in excinfo.traceback:
                    print >>x, str(i)[2:-1]
                print >>x, excinfo
                x.close()
                os._exit(1)
            os.close(1)
            os.close(2)
            os._exit(0)
        return pid
    
    def children(self, nice_level):
        # right now we need to call a function, but first we need to
        # map all IO that might happen
        # make sure sys.stdout points to file descriptor one
        sys.stdout = stdout = self.PYTESTSTDOUT.open('w')
        sys.stdout.flush()
        fdstdout = stdout.fileno()
        if fdstdout != 1:
            os.dup2(fdstdout, 1)
        sys.stderr = stderr = self.PYTESTSTDERR.open('w')
        fdstderr = stderr.fileno()
        if fdstderr != 2:
            os.dup2(fdstderr, 2)
        retvalf = self.PYTESTRETVAL.open("w")
        try:
            if nice_level:
                os.nice(nice_level)
            # with fork() we have duplicated py.test's basetemp
            # directory so we want to set it manually here. 
            # this may be expensive for some test setups, 
            # but that is what you get with boxing. 
            # XXX but we are called in more than strict boxing
            # mode ("AsyncExecutor") so we can't do the following without
            # inflicting on --dist speed, hum: 
            # pytestconfig.basetemp = self.tempdir.join("childbasetemp")
            retval = self.fun(*self.args, **self.kwargs)
            retvalf.write(marshal.dumps(retval))
        finally:
            stdout.close()
            stderr.close()
            retvalf.close()
        os._exit(0)
    
    def parent(self, pid, waiter=os.waitpid):
        pid, exitstat = waiter(pid, 0)
        self.signal = exitstat & 0x7f
        self.exitstat = exitstat & 0xff00

        
        if not exitstat:
            retval = self.PYTESTRETVAL.open()
            try:
                retval_data = retval.read()
            finally:
                retval.close()
            self.retval = marshal.loads(retval_data)
        else:
            self.retval = None
        
        self.stdoutrepr = self.PYTESTSTDOUT.read()
        self.stderrrepr = self.PYTESTSTDERR.read()
        return self.stdoutrepr, self.stderrrepr

Box = FileBox
