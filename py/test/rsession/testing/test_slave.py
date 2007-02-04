
""" Testing the slave side node code (in a local way). """
from py.__.test.rsession.slave import SlaveNode, slave_main, setup, PidInfo
from py.__.test.rsession.outcome import ReprOutcome
import py, sys

modlevel = []
import os

if sys.platform == 'win32':
    py.test.skip("rsession is unsupported on Windows.")

def setup_module(module):
    module.tmpdir = py.test.ensuretemp(module.__name__)
    module.rootdir = py.path.local(py.__file__).dirpath().dirpath()
    module.rootcol = py.test.collect.Directory(rootdir)

# ----------------------------------------------------------------------
# inlined testing functions used below
def funcpass(): 
    pass

def funcfail():
    raise AssertionError("hello world")

def funcskip():
    py.test.skip("skipped")

def funcprint():
    print "samfing"

def funcprintfail():
    print "samfing elz"
    asddsa

def funcoptioncustom():
    assert py.test.config.getvalue("custom")

def funchang():
    import time
    time.sleep(1000)

BASE = "py/test/rsession/testing/test_slave.py/"
funcpass_spec = (BASE + "funcpass").split("/")
funcfail_spec = (BASE + "funcfail").split("/")
funcskip_spec = (BASE + "funcskip").split("/")
funcprint_spec = (BASE + "funcprint").split("/")
funcprintfail_spec = (BASE + "funcprintfail").split("/")
funcoptioncustom_spec = (BASE + "funcoptioncustom").split("/")
funchang_spec = (BASE + "funchang").split("/")
mod_spec = BASE[:-1].split("/")

# ----------------------------------------------------------------------

from py.__.test.rsession.executor import RunExecutor

def gettestnode():
    config = py.test.config._reparse([rootdir])
    pidinfo = PidInfo()
    node = SlaveNode(config, pidinfo, executor=RunExecutor) 
    return node

def test_slave_run_passing():
    node = gettestnode()
    item = rootcol._getitembynames(funcpass_spec)
    outcome = node.execute(item._get_collector_trail())
    assert outcome.passed 
    assert not outcome.setupfailure 

    ser = outcome.make_repr()
    reproutcome = ReprOutcome(ser) 
    assert reproutcome.passed 
    assert not reproutcome.setupfailure 

def test_slave_run_failing():
    node = gettestnode()
    item = rootcol._getitembynames(funcfail_spec)
    outcome = node.execute(item._get_collector_trail())
    assert not outcome.passed 
    assert not outcome.setupfailure 
    assert len(outcome.excinfo.traceback) == 1
    assert outcome.excinfo.traceback[-1].frame.code.name == 'funcfail'

    ser = outcome.make_repr()
    reproutcome = ReprOutcome(ser) 
    assert not reproutcome.passed 
    assert not reproutcome.setupfailure 
    assert reproutcome.excinfo
    
def test_slave_run_skipping():
    node = gettestnode()
    item = rootcol._getitembynames(funcskip_spec)    
    outcome = node.execute(item._get_collector_trail())
    assert not outcome.passed
    assert outcome.skipped

    ser = outcome.make_repr()
    reproutcome = ReprOutcome(ser) 
    assert not reproutcome.passed 
    assert reproutcome.skipped

def test_slave_run_failing_wrapped():
    node = gettestnode()
    item = rootcol._getitembynames(funcfail_spec)
    repr_outcome = node.run(item._get_collector_trail()) 
    outcome = ReprOutcome(repr_outcome)  
    assert not outcome.passed 
    assert not outcome.setupfailure 
    assert outcome.excinfo

def test_slave_run_different_stuff():
    node = gettestnode()
    node.run(rootcol._getitembynames("py doc log.txt".split()).
             _get_collector_trail())

def test_pidinfo():
    if not hasattr(os, 'fork') or not hasattr(os, 'waitpid'):
        py.test.skip("Platform does not support fork")
    pidinfo = PidInfo()
    pid = os.fork()
    if pid:
        pidinfo.set_pid(pid)
        pidinfo.waitandclear(pid, 0)
    else:
        import time, sys
        time.sleep(.3)
        os._exit(0)
    # check if this really exits
    py.test.raises(OSError, "os.waitpid(pid, 0)")
