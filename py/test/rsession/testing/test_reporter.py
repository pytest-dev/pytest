
""" reporter tests.

XXX there are a few disabled reporting tests because
they test for exact formatting as far as i can see.
I think it's rather better to directly invoke a
reporter and pass it some hand-prepared events to see
that running the reporter doesn't break shallowly. 

Otherwise, i suppose that some "visual" testing can usually be driven 
manually by user-input.  And when passing particular events
to a reporter it's also easier to check for one line
instead of having to know the order in which things are printed
etc. 


"""


import py, os
#py.test.skip("in progress")
from py.__.test.rsession.rsession import LocalReporter, AbstractSession,\
    RemoteReporter
from py.__.test.rsession import report
from py.__.test.rsession.outcome import ReprOutcome, Outcome
from py.__.test.rsession.testing.test_slave import funcpass_spec, mod_spec
from py.__.test.rsession.hostmanage import HostInfo
from py.__.test.rsession.box import Box
#from py.__.test.
import sys
from StringIO import StringIO

class DummyGateway(object):
    def __init__(self, host):
        self.host = host

class DummyChannel(object):
    def __init__(self, host):
        self.gateway = DummyGateway(host)

class AbstractTestReporter(object):
    def setup_class(cls):
        cls.pkgdir = py.path.local(py.__file__).dirpath()
    
    def prepare_outcomes(self):
        # possible outcomes
        try:
            1/0
        except:
            exc = py.code.ExceptionInfo()
        
        outcomes = [Outcome(()), 
            Outcome(skipped=True),
            Outcome(excinfo=exc),
            Outcome()]
        
        outcomes = [ReprOutcome(outcome.make_repr()) for outcome in outcomes]
        outcomes[3].signal = 11
        outcomes[0].passed = False
        
        return outcomes
    
    def report_received_item_outcome(self):
        config = py.test.config._reparse(["some_sub"])
        # we just go...
        rootcol = py.test.collect.Directory(self.pkgdir.dirpath())
        item = rootcol.getitembynames(funcpass_spec)
        outcomes = self.prepare_outcomes()
        
        def boxfun(config, item, outcomes):
            hosts = [HostInfo("localhost")]
            r = self.reporter(config, hosts)
            ch = DummyChannel(hosts[0])
            for outcome in outcomes:
                r.report(report.ReceivedItemOutcome(ch, item, outcome))
        
        cap = py.io.StdCaptureFD()
        boxfun(config, item, outcomes)
        out, err = cap.reset()
        assert not err
        return out

    def _test_module(self):
        config = py.test.config._reparse(["some_sub"])
        # we just go...
        rootcol = py.test.collect.Directory(self.pkgdir.dirpath())
        funcitem = rootcol.getitembynames(funcpass_spec)
        moditem = rootcol.getitembynames(mod_spec)
        outcomes = self.prepare_outcomes()
        
        def boxfun(pkgdir, config, item, funcitem, outcomes):
            hosts = [HostInfo('localhost')]
            r = self.reporter(config, hosts)
            #r.pkgdir = pkdgir
            r.report(report.ItemStart(item))
            ch = DummyChannel(hosts[0])
            for outcome in outcomes:
                r.report(report.ReceivedItemOutcome(ch, funcitem, outcome))
        
        cap = py.io.StdCaptureFD()
        boxfun(self.pkgdir, config, moditem, funcitem, outcomes)
        out, err = cap.reset()
        assert not err
        return out

    def _test_full_module(self):
        tmpdir = py.test.ensuretemp("repmod")
        tmpdir.ensure("__init__.py")
        tmpdir.ensure("test_one.py").write(py.code.Source("""
        def test_x():
            pass
        """))
        tmpdir.ensure("test_two.py").write(py.code.Source("""
        import py
        py.test.skip("reason")
        """))
        tmpdir.ensure("test_three.py").write(py.code.Source("""
        sadsadsa
        """))
        
        def boxfun():
            config = py.test.config._reparse([str(tmpdir)])
            rootcol = py.test.collect.Directory(tmpdir)
            hosts = [HostInfo('localhost')]
            r = self.reporter(config, hosts)
            list(rootcol.tryiter(reporterror=lambda x : AbstractSession.reporterror(r.report, x)))

        cap = py.io.StdCaptureFD()
        boxfun()
        out, err = cap.reset()
        assert not err
        return out

    def test_failed_to_load(self):
        tmpdir = py.test.ensuretemp("failedtoload")
        tmpdir.ensure("__init__.py")
        tmpdir.ensure("test_three.py").write(py.code.Source("""
        sadsadsa
        """))
        def boxfun():
            config = py.test.config._reparse([str(tmpdir)])
            rootcol = py.test.collect.Directory(tmpdir)
            host = HostInfo('localhost')
            r = self.reporter(config, [host])
            r.report(report.TestStarted([host]))
            r.report(report.RsyncFinished())
            list(rootcol.tryiter(reporterror=lambda x : AbstractSession.reporterror(r.report, x)))
            r.report(report.TestFinished())
        
        cap = py.io.StdCaptureFD()
        boxfun()
        out, err = cap.reset()
        assert not err
        assert out.find("NameError: name 'sadsadsa' is not defined") != -1

    def _test_still_to_go(self):
        tmpdir = py.test.ensuretemp("stilltogo")
        tmpdir.ensure("__init__.py")
        cap = py.io.StdCaptureFD()
        config = py.test.config._reparse([str(tmpdir)])
        hosts = [HostInfo(i) for i in ["host1", "host2", "host3"]]
        r = self.reporter(config, hosts)
        r.report(report.TestStarted(hosts))
        r.report(report.HostReady(hosts[0]))
        r.report(report.HostReady(hosts[1]))
        r.report(report.HostReady(hosts[2]))
        out, err = cap.reset()
        assert not err
        expected1 = "Test started, hosts: host1, host2, host3"
        expected2 = """host1: READY (still 2 to go)
     host2: READY (still 1 to go)
     host3: READY"""
        assert out.find(expected1) != -1
        assert out.find(expected2) != -1

class TestLocalReporter(AbstractTestReporter):
    reporter = LocalReporter
    
    def test_report_received_item_outcome(self):
        #py.test.skip("XXX rewrite test to not rely on exact formatting")
        assert self.report_received_item_outcome() == 'FsF.'

    def test_module(self):
        #py.test.skip("XXX rewrite test to not rely on exact formatting")
        output = self._test_module()
        assert output.find("test_slave") != -1
        assert output.endswith("FsF."), output
    
    def test_full_module(self):
        #py.test.skip("XXX rewrite test to not rely on exact formatting")
        received = self._test_full_module()
        expected = """
repmod/test_one.py[1] 
repmod/test_three.py[0] - FAILED TO LOAD MODULE
repmod/test_two.py[0] - skipped (reason)"""
        assert received.find(expected) != -1 

class TestRemoteReporter(AbstractTestReporter):
    reporter = RemoteReporter

    def test_still_to_go(self):
        self._test_still_to_go()

    def test_report_received_item_outcome(self):
        py.test.skip("XXX rewrite test to not rely on exact formatting")
        val = self.report_received_item_outcome()
        expected = """ localhost: FAILED  py.test.rsession.testing.test_slave.py funcpass
 localhost: SKIPPED py.test.rsession.testing.test_slave.py funcpass
 localhost: FAILED  py.test.rsession.testing.test_slave.py funcpass
 localhost: PASSED  py.test.rsession.testing.test_slave.py funcpass
"""
        assert val.find(expected) != -1
    
    def test_module(self):
        py.test.skip("XXX rewrite test to not rely on exact formatting")
        val = self._test_module()
        print val
        expected = """ localhost: FAILED  py.test.rsession.testing.test_slave.py funcpass
 localhost: SKIPPED py.test.rsession.testing.test_slave.py funcpass
 localhost: FAILED  py.test.rsession.testing.test_slave.py funcpass
 localhost: PASSED  py.test.rsession.testing.test_slave.py funcpass
"""
        assert val.find(expected) != -1
    
    def test_full_module(self):
        #py.test.skip("XXX rewrite test to not rely on exact formatting")
        val = self._test_full_module()
        assert val.find('FAILED TO LOAD MODULE: repmod/test_three.py\n'\
        '\nSkipped (reason) repmod/test_two.py') != -1
