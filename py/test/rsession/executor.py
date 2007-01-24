""" Remote executor
"""

import py, os

from py.__.test.rsession.outcome import Outcome, ReprOutcome
from py.__.test.rsession.box import Box
from py.__.test.rsession import report

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
    
    def execute(self):
        try:
            self.item.run()
            outcome = Outcome()
        except py.test.Item.Skipped, e: 
            outcome = Outcome(skipped=str(e))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            excinfo = py.code.ExceptionInfo()
            if isinstance(self.item, py.test.Function): 
                fun = self.item.obj # hope this is stable 
                code = py.code.Code(fun)
                excinfo.traceback = excinfo.traceback.cut(
                        path=code.path, firstlineno=code.firstlineno)
            outcome = Outcome(excinfo=excinfo, setupfailure=False)
            if self.usepdb:
                if self.reporter is not None:
                    self.reporter(report.ImmediateFailure(self.item,
                        ReprOutcome(outcome.make_repr
                                    (self.config.option.tbstyle))))
                import pdb
                pdb.post_mortem(excinfo._excinfo[2])
                # XXX hmm, we probably will not like to continue from that
                #     point
                raise SystemExit()
        outcome.stdout = ""
        outcome.stderr = ""
        return outcome

class BoxExecutor(RunExecutor):
    """ Same as run executor, but boxes test instead
    """
    wraps = True
    
    def execute(self):
        def fun():
            outcome = RunExecutor.execute(self)
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
            outcome = RunExecutor.execute(self)
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
