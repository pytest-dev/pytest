
""" Testing the slave side node code (in a local way). """
from py.__.test.rsession.slave import SlaveNode, slave_main
from py.__.test.rsession.outcome import ReprOutcome
import py, sys

modlevel = []
import os

if sys.platform == 'win32':
    py.test.skip("rsession is unsupported on Windows.")

def setup_module(module):
    from py.__.test.rsession.rsession import session_options
    module.rootdir = py.path.local(py.__file__).dirpath().dirpath()
    config = py.test.config._reparse([])
    session_options.bind_config(config)

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

def funcoption():
    from py.__.test.rsession.rsession import remote_options
    assert remote_options.we_are_remote

def funcoptioncustom():
    from py.__.test.rsession.rsession import remote_options
    assert remote_options.custom == "custom"

def funchang():
    import time
    time.sleep(1000)

BASE = "py/test/rsession/testing/test_slave.py/"
funcpass_spec = (BASE + "funcpass").split("/")
funcfail_spec = (BASE + "funcfail").split("/")
funcskip_spec = (BASE + "funcskip").split("/")
funcprint_spec = (BASE + "funcprint").split("/")
funcprintfail_spec = (BASE + "funcprintfail").split("/")
funcoption_spec = (BASE + "funcoption").split("/")
funcoptioncustom_spec = (BASE + "funcoptioncustom").split("/")
funchang_spec = (BASE + "funchang").split("/")
mod_spec = BASE[:-1].split("/")

# ----------------------------------------------------------------------

from py.__.test.rsession.executor import RunExecutor

def gettestnode():
    rootcol = py.test.collect.Directory(rootdir)
    node = SlaveNode(rootcol, executor=RunExecutor) 
    return node

def test_slave_run_passing():
    node = gettestnode()
    outcome = node.execute(funcpass_spec)
    assert outcome.passed 
    assert not outcome.setupfailure 

    ser = outcome.make_repr()
    reproutcome = ReprOutcome(ser) 
    assert reproutcome.passed 
    assert not reproutcome.setupfailure 

def test_slave_run_failing():
    node = gettestnode()
    outcome = node.execute(funcfail_spec) 
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
    outcome = node.execute(funcskip_spec) 
    assert not outcome.passed
    assert outcome.skipped

    ser = outcome.make_repr()
    reproutcome = ReprOutcome(ser) 
    assert not reproutcome.passed 
    assert reproutcome.skipped

def test_slave_run_failing_wrapped():
    node = gettestnode()
    repr_outcome = node.run(funcfail_spec) 
    outcome = ReprOutcome(repr_outcome)  
    assert not outcome.passed 
    assert not outcome.setupfailure 
    assert outcome.excinfo

def test_slave_main_simple(): 
    res = []
    q = [None, 
         funcpass_spec, 
         funcfail_spec
        ]
    slave_main(q.pop, res.append, str(rootdir))
    assert len(res) == 2
    res_repr = [ReprOutcome(r) for r in res]
    assert not res_repr[0].passed and res_repr[1].passed

def test_slave_run_different_stuff():
    node = gettestnode()
    node.run("py doc log.txt".split())

def test_slave_setup_fails_on_import_error():
    from py.__.test.rsession.slave import setup 
    tmp = py.test.ensuretemp("slavesetup")
    class C:
        def __init__(self):
            self.count = 0
        
        def receive(self):
            if self.count == 0:
                retval = str(tmp)
            elif self.count == 1:
                from py.__.test.rsession.rsession import remote_options
                retval = remote_options.d
            else:
                raise NotImplementedError("more data")
            self.count += 1
            return retval
    try:
        exec py.code.Source(setup, "setup()").compile() in {
            'channel': C()}
    except ImportError: 
        pass # expected 
    else:
        py.test.fail("missing exception") 
    
def test_slave_setup_exit():
    tmp = py.test.ensuretemp("slaveexit")
    tmp.ensure("__init__.py")
    from py.__.test.rsession.slave import setup
    from Queue import Queue
    q = Queue()
    
    class C:
        res = []
        def __init__(self):
            from py.__.test.rsession.rsession import remote_options
            self.q = [str(tmp),
                remote_options.d,
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
        
        send = res.append
    try:
        exec py.code.Source(setup, "setup()").compile() in {'channel':C()}
    except SystemExit:
        pass
    else:
        py.test.fail("Did not exit")

def test_slave_setup_fails_on_missing_pkg():
    from py.__.test.rsession.slave import setup 
    tmp = py.test.ensuretemp("slavesetup2")
    x = tmp.ensure("sometestpackage", "__init__.py")
    class C: 
        def __init__(self):
            self.count = 0

        def receive(self):
            if self.count == 0:
                retval = str(x.dirpath())
            elif self.count == 1:
                from py.__.test.rsession.rsession import remote_options
                retval = remote_options.d
            else:
                raise NotImplementedError("more data")
            self.count += 1
            return retval
    try:
        exec py.code.Source(setup, "setup()").compile() in {'channel': C()}
    except AttributeError: # channel.send 
        pass
    else:
        py.test.fail("missing exception") 

    # now create a parallel structure 
    tmp = py.test.ensuretemp("slavesetup3")
    x = tmp.ensure("sometestpackage", "__init__.py")
    try:
        exec py.code.Source(setup, "setup()").compile() in {
            'channel': C()}
    except AssertionError: 
        pass # expected 
    else:
        py.test.fail("missing exception") 
    
