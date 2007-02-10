
""" Testing the slave side node code (in a local way). """
from py.__.test.rsession.slave import SlaveNode, slave_main, setup
from py.__.test.rsession.outcome import ReprOutcome
import py, sys
from py.__.test.rsession.testing.basetest import BasicRsessionTest

modlevel = []
import os

if sys.platform == 'win32':
    py.test.skip("rsession is unsupported on Windows.")

# ----------------------------------------------------------------------

from py.__.test.rsession.executor import RunExecutor

class TestSlave(BasicRsessionTest):
    def gettestnode(self):
        node = SlaveNode(self.config, executor=RunExecutor) 
        return node

    def test_slave_run_passing(self):
        node = self.gettestnode()
        item = self.getexample("pass")
        outcome = node.execute(item._get_collector_trail())
        assert outcome.passed 
        assert not outcome.setupfailure 

        ser = outcome.make_repr()
        reproutcome = ReprOutcome(ser) 
        assert reproutcome.passed 
        assert not reproutcome.setupfailure 

    def test_slave_run_failing(self):
        node = self.gettestnode()
        item = self.getexample("fail") 
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
    
    def test_slave_run_skipping(self):
        node = self.gettestnode()
        item = self.getexample("skip")
        outcome = node.execute(item._get_collector_trail())
        assert not outcome.passed
        assert outcome.skipped

        ser = outcome.make_repr()
        reproutcome = ReprOutcome(ser) 
        assert not reproutcome.passed 
        assert reproutcome.skipped

    def test_slave_run_failing_wrapped(self):
        node = self.gettestnode()
        item = self.getexample("fail") 
        repr_outcome = node.run(item._get_collector_trail()) 
        outcome = ReprOutcome(repr_outcome)  
        assert not outcome.passed 
        assert not outcome.setupfailure 
        assert outcome.excinfo

    def test_slave_run_different_stuff(self):
        py.test.skip("XXX not this way")
        node = self.gettestnode()
        node.run(self.rootcol._getitembynames("py doc log.txt".split()).
                 _get_collector_trail())
