
import py
import example1

from py.__.test.rsession.executor import RunExecutor, BoxExecutor,\
    AsyncExecutor
from py.__.test.rsession.outcome import ReprOutcome
from py.__.test.rsession.testing.test_slave import funcprint_spec, \
    funcprintfail_spec

def setup_module(mod):
    mod.rootdir = py.path.local(py.__file__).dirpath().dirpath()
    mod.config = py.test.config._reparse([mod.rootdir])
    
def XXXtest_executor_passing_function():
    ex = Executor(example1.f1)
    outcome = ex.execute()
    assert outcome.passed 

def XXXtest_executor_raising_function():
    ex = Executor(example1.g1)
    outcome = ex.execute()
    assert not outcome.passed 
    excinfo = outcome.excinfo
    assert excinfo.type == ValueError

def XXXtest_executor_traceback():
    ex = Executor(example1.g1)
    outcome = ex.execute()
    excinfo = outcome.excinfo
    assert len(excinfo.traceback) == 2
    assert excinfo.traceback[1].frame.code.name == 'g2'
    assert excinfo.traceback[0].frame.code.name == 'g1'

def XXX_test_executor_setup_passing(): 
    ex = Executor(example1.f1, setup=lambda: None)
    outcome = ex.execute()
    assert outcome.passed 
    assert not outcome.setupfailure 

def XXX_test_executor_setup_failing(): 
    def failingsetup():
        raise ValueError
    ex = Executor(example1.f1, setup=failingsetup)
    outcome = ex.execute()
    assert not outcome.passed 
    assert outcome.setupfailure 
    assert outcome.excinfo.traceback[-1].frame.code.name == 'failingsetup'

class ItemTestPassing(py.test.Item):    
    def run(self):
        return None

class ItemTestFailing(py.test.Item):
    def run(self):
        assert 0 == 1

class ItemTestSkipping(py.test.Item):
    def run(self):
        py.test.skip("hello")

def test_run_executor():
    ex = RunExecutor(ItemTestPassing("pass"), config=config)
    outcome = ex.execute()
    assert outcome.passed
    
    ex = RunExecutor(ItemTestFailing("fail"), config=config)
    outcome = ex.execute()
    assert not outcome.passed

    ex = RunExecutor(ItemTestSkipping("skip"), config=config)
    outcome = ex.execute()
    assert outcome.skipped 
    assert not outcome.passed
    assert not outcome.excinfo 

def test_box_executor():
    ex = BoxExecutor(ItemTestPassing("pass"), config=config)
    outcome_repr = ex.execute()
    outcome = ReprOutcome(outcome_repr)
    assert outcome.passed
    
    ex = BoxExecutor(ItemTestFailing("fail"), config=config)
    outcome_repr = ex.execute()
    outcome = ReprOutcome(outcome_repr)
    assert not outcome.passed

    ex = BoxExecutor(ItemTestSkipping("skip"), config=config)
    outcome_repr = ex.execute()
    outcome = ReprOutcome(outcome_repr)
    assert outcome.skipped 
    assert not outcome.passed
    assert not outcome.excinfo 

def test_box_executor_stdout():
    rootcol = py.test.collect.Directory(rootdir)
    item = rootcol.getitembynames(funcprint_spec)
    ex = BoxExecutor(item, config=config)
    outcome_repr = ex.execute()
    outcome = ReprOutcome(outcome_repr)
    assert outcome.passed
    assert outcome.stdout.find("samfing") != -1

def test_box_executor_stdout_error():
    rootcol = py.test.collect.Directory(rootdir)
    item = rootcol.getitembynames(funcprintfail_spec)
    ex = BoxExecutor(item, config=config)
    outcome_repr = ex.execute()
    outcome = ReprOutcome(outcome_repr)
    assert not outcome.passed
    assert outcome.stdout.find("samfing elz") != -1 

def test_cont_executor():
    rootcol = py.test.collect.Directory(rootdir)
    item = rootcol.getitembynames(funcprintfail_spec)
    ex = AsyncExecutor(item, config=config)
    cont, pid = ex.execute()
    assert pid
    outcome_repr = cont()
    outcome = ReprOutcome(outcome_repr)
    assert not outcome.passed
    assert outcome.stdout.find("samfing elz") != -1
