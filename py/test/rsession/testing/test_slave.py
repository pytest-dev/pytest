
""" Testing the slave side node code (in a local way). """
from py.__.test.rsession.slave import SlaveNode, slave_main, setup, PidInfo
from py.__.test.rsession.outcome import ReprOutcome
import py, sys

modlevel = []
import os

if sys.platform == 'win32':
    py.test.skip("rsession is unsupported on Windows.")

def setup_module(module):
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
    item = rootcol.getitembynames(funcpass_spec)
    outcome = node.execute(item._get_collector_trail())
    assert outcome.passed 
    assert not outcome.setupfailure 

    ser = outcome.make_repr()
    reproutcome = ReprOutcome(ser) 
    assert reproutcome.passed 
    assert not reproutcome.setupfailure 

def test_slave_run_failing():
    node = gettestnode()
    item = rootcol.getitembynames(funcfail_spec)
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
    item = rootcol.getitembynames(funcskip_spec)    
    outcome = node.execute(item._get_collector_trail())
    assert not outcome.passed
    assert outcome.skipped

    ser = outcome.make_repr()
    reproutcome = ReprOutcome(ser) 
    assert not reproutcome.passed 
    assert reproutcome.skipped

def test_slave_run_failing_wrapped():
    node = gettestnode()
    item = rootcol.getitembynames(funcfail_spec)
    repr_outcome = node.run(item._get_collector_trail()) 
    outcome = ReprOutcome(repr_outcome)  
    assert not outcome.passed 
    assert not outcome.setupfailure 
    assert outcome.excinfo

def test_slave_main_simple(): 
    res = []
    failitem = rootcol.getitembynames(funcfail_spec)
    passitem = rootcol.getitembynames(funcpass_spec)
    q = [None, 
         passitem._get_collector_trail(),
         failitem._get_collector_trail()
        ]
    config = py.test.config._reparse([])
    pidinfo = PidInfo()
    slave_main(q.pop, res.append, str(rootdir), config, pidinfo)
    assert len(res) == 2
    res_repr = [ReprOutcome(r) for r in res]
    assert not res_repr[0].passed and res_repr[1].passed

def test_slave_run_different_stuff():
    node = gettestnode()
    node.run(rootcol.getitembynames("py doc log.txt".split()).
             _get_collector_trail())

def test_slave_setup_exit():
    tmp = py.test.ensuretemp("slaveexit")
    tmp.ensure("__init__.py")
    q = py.std.Queue.Queue()
    config = py.test.config._reparse([tmp])
    
    class C:
        res = []
        def __init__(self):
            self.q = [str(tmp),
                config.make_repr(conftestnames=['dist_nicelevel']),
                funchang_spec,
                42,
                funcpass_spec]
            self.q.reverse()
    
        def receive(self):
            return self.q.pop()
        
        def setcallback(self, callback):
            import thread
            def f():
                while 1:
                    callback(self.q.pop())
            f()
            #thread.start_new_thread(f, ())

        def close(self):
            pass
        
        send = res.append
    try:
        exec py.code.Source(setup, "setup()").compile() in {'channel':C()}
    except SystemExit:
        pass
    else:
        py.test.fail("Did not exit")

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
