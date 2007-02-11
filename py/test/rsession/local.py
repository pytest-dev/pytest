
""" local-only operations
"""

import py
from py.__.test.rsession.executor import BoxExecutor, RunExecutor,\
     ApigenExecutor
from py.__.test.rsession import repevent
from py.__.test.rsession.outcome import ReprOutcome

# XXX copied from session.py
def startcapture(session):
    if not session.config.option.nocapture:
        session._capture = py.io.StdCapture()

def finishcapture(session): 
    if hasattr(session, '_capture'): 
        capture = session._capture 
        del session._capture
        return capture.reset()
    return "", ""

def box_runner(item, session, reporter):
    r = BoxExecutor(item, config=session.config)
    return ReprOutcome(r.execute())

def plain_runner(item, session, reporter):
    r = RunExecutor(item, usepdb=session.config.option.usepdb, reporter=reporter, config=session.config)
    outcome = r.execute()
    outcome = ReprOutcome(outcome.make_repr(session.config.option.tbstyle))
    return outcome

def benchmark_runner(item, session, reporter):
    raise NotImplementedError()

def apigen_runner(item, session, reporter):
    #retval = plain_runner(item, session, reporter)
    startcapture(session)
    r = ApigenExecutor(item, reporter=reporter, config=session.config)
    outcome = r.execute(session.tracer)
    outcome = ReprOutcome(outcome.make_repr(session.config.option.tbstyle))
    outcome.stdout, outcome.stderr = finishcapture(session)
    return outcome

def exec_runner(item, session, reporter):
    raise NotImplementedError()

# runner interface is here to perform several different types of run
#+1. box_runner - for running normal boxed tests
#+2. plain_runner - for performing running without boxing (necessary for pdb)
#    XXX: really?
#-3. exec_runner - for running under different interpreter
#-4. benchmark_runner - for running with benchmarking
#-5. apigen_runner - for running under apigen to generate api out of it.
def local_loop(session, reporter, itemgenerator, shouldstop, config, runner=None):
    assert runner is not None
    #if runner is None:
    #    if session.config.option.apigen:
    #        runner = apigen_runner
    #    else:
    #    runner = box_runner
    while 1:
        try:
            item = itemgenerator.next()
            if shouldstop():
                return
            outcome = runner(item, session, reporter)
            reporter(repevent.ReceivedItemOutcome(None, item, outcome))
        except StopIteration:
            break
