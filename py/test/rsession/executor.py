""" Remote executor
"""

import py, os, sys

from py.__.test.rsession.outcome import Outcome, ReprOutcome
from py.__.test.rsession.box import Box
from py.__.test.rsession import repevent
from py.__.test.outcome import Skipped, Failed

class RunExecutor(object):
    """ Same as in executor, but just running run
    """
    wraps = False
    
    def __init__(self, item, usepdb=False, reporter=None, config=None):
        self.item = item
        self.usepdb = usepdb
        self.reporter = reporter
        self.config = config
        assert self.config

    def run(self, capture=True):
        if capture:
            self.item.startcapture()
            try:
                self.item.run()
            finally:
                self.item.finishcapture()
        else:
            self.item.run()

    def execute(self, capture=True):
        try:
            self.run(capture)
            outcome = Outcome()
        except Skipped, e: 
            outcome = Outcome(skipped=str(e))
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            e = sys.exc_info()[1]
            if isinstance(e, Failed) and e.excinfo:
                excinfo = e.excinfo
            else:
                excinfo = py.code.ExceptionInfo()
                if isinstance(self.item, py.test.collect.Function): 
                    fun = self.item.obj # hope this is stable 
                    code = py.code.Code(fun)
                    excinfo.traceback = excinfo.traceback.cut(
                        path=code.path, firstlineno=code.firstlineno)
            outcome = Outcome(excinfo=excinfo, setupfailure=False)
            if self.usepdb:
                if self.reporter is not None:
                    self.reporter(repevent.ImmediateFailure(self.item,
                        ReprOutcome(outcome.make_repr
                                    (self.config.option.tbstyle))))
                import pdb
                pdb.post_mortem(excinfo._excinfo[2])
                # XXX hmm, we probably will not like to continue from that
                #     point
                raise SystemExit()
        outcome.stdout, outcome.stderr = self.item._getouterr()
        return outcome

class ApigenExecutor(RunExecutor):
    """ Same as RunExecutor, but takes tracer to trace calls as
    an argument to execute
    """
    def execute(self, tracer):
        self.tracer = tracer
        return super(ApigenExecutor, self).execute()

    def wrap_underlaying(self, target, *args):
        try:
            self.tracer.start_tracing()
            return target(*args)
        finally:
            self.tracer.end_tracing()

    def run(self, capture):
        """ We want to trace *only* function objects here. Unsure
        what to do with custom collectors at all
        """
        if hasattr(self.item, 'obj') and type(self.item) is py.test.collect.Function:
            self.item.execute = self.wrap_underlaying
        self.item.run()

class BoxExecutor(RunExecutor):
    """ Same as RunExecutor, but boxes test instead
    """
    wraps = True

    def execute(self):
        def fun():
            outcome = RunExecutor.execute(self, False)
            return outcome.make_repr(self.config.option.tbstyle)
        b = Box(fun, config=self.config)
        pid = b.run()
        assert pid
        if b.retval is not None:
            passed, setupfailure, excinfo, skipped, critical, _, _, _\
                    = b.retval
            return (passed, setupfailure, excinfo, skipped, critical, 0,
                b.stdoutrepr, b.stderrrepr)
        else:
            return (False, False, None, False, False, b.signal,
                    b.stdoutrepr, b.stderrrepr)

class AsyncExecutor(RunExecutor):
    """ same as box executor, but instead it returns function to continue
    computations (more async mode)
    """
    wraps = True

    def execute(self):
        def fun():
            outcome = RunExecutor.execute(self, False)
            return outcome.make_repr(self.config.option.tbstyle)
        
        b = Box(fun, config=self.config)
        parent, pid = b.run(continuation=True)
        
        def cont(waiter=os.waitpid):
            parent(pid, waiter=waiter)
            if b.retval is not None:
                passed, setupfailure, excinfo, skipped,\
                    critical, _, _, _ = b.retval
                return (passed, setupfailure, excinfo, skipped, critical, 0,
                    b.stdoutrepr, b.stderrrepr)
            else:
                return (False, False, None, False, False,
                        b.signal, b.stdoutrepr, b.stderrrepr)
        
        return cont, pid
