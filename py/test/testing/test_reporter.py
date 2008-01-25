
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
from py.__.test.session import AbstractSession, itemgen
from py.__.test.reporter import RemoteReporter, LocalReporter, choose_reporter 
from py.__.test import repevent
from py.__.test.outcome import ReprOutcome, SerializableOutcome
from py.__.test.rsession.hostmanage import HostInfo
from py.__.test.box import Box
from py.__.test.rsession.testing.basetest import BasicRsessionTest
import sys
from StringIO import StringIO

class MockSession(object):
    def __init__(self, reporter):
        self.reporter = reporter
    
    def start(self, item):
        self.reporter(repevent.ItemStart(item))

    def finish(self, item):
        pass

class DummyGateway(object):
    def __init__(self, host):
        self.host = host

class DummyChannel(object):
    def __init__(self, host):
        self.gateway = DummyGateway(host)

class AbstractTestReporter(BasicRsessionTest):
    def prepare_outcomes(self):
        # possible outcomes
        try:
            1/0
        except:
            exc = py.code.ExceptionInfo()

        try:
            py.test.skip("xxx")
        except:
            skipexc = py.code.ExceptionInfo()
        
        outcomes = [SerializableOutcome(()), 
            SerializableOutcome(skipped=skipexc),
            SerializableOutcome(excinfo=exc),
            SerializableOutcome()]
        
        outcomes = [ReprOutcome(outcome.make_repr()) for outcome in outcomes]
        outcomes[3].signal = 11
        outcomes[0].passed = False
        
        return outcomes
    
    def report_received_item_outcome(self):
        item = self.getexample("pass")
        outcomes = self.prepare_outcomes()
        
        def boxfun(config, item, outcomes):
            hosts = self.get_hosts()
            r = self.reporter(config, hosts)
            if hosts:
                ch = DummyChannel(hosts[0])
            else:
                ch = None
            for outcome in outcomes:
                r.report(repevent.ReceivedItemOutcome(ch, item, outcome))
        
        cap = py.io.StdCaptureFD()
        boxfun(self.config, item, outcomes)
        out, err = cap.reset()
        assert not err
        return out

    def _test_module(self):
        funcitem = self.getexample("pass")
        moditem = self.getmod()
        outcomes = self.prepare_outcomes()
        
        def boxfun(config, item, funcitem, outcomes):
            hosts = self.get_hosts()
            r = self.reporter(config, hosts)
            r.report(repevent.ItemStart(item))
            if hosts:
                ch = DummyChannel(hosts[0])
            else:
                ch = None
            for outcome in outcomes:
                r.report(repevent.ReceivedItemOutcome(ch, funcitem, outcome))
        
        cap = py.io.StdCaptureFD()
        boxfun(self.config, moditem, funcitem, outcomes)
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
            hosts = self.get_hosts()
            r = self.reporter(config, hosts)
            list(itemgen(MockSession(r), [rootcol], r.report))

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
            hosts = self.get_hosts()
            r = self.reporter(config, hosts)
            r.report(repevent.TestStarted(hosts, config, ["a"]))
            r.report(repevent.RsyncFinished())
            list(itemgen(MockSession(r), [rootcol], r.report))
            r.report(repevent.TestFinished())
            return r
        
        cap = py.io.StdCaptureFD()
        r = boxfun()
        out, err = cap.reset()
        assert not err
        assert out.find("1 failed in") != -1
        assert out.find("NameError: name 'sadsadsa' is not defined") != -1

    def _test_verbose(self):
        tmpdir = py.test.ensuretemp("reporterverbose")
        tmpdir.ensure("__init__.py")
        tmpdir.ensure("test_one.py").write("def test_x(): pass")
        cap = py.io.StdCaptureFD()
        config = py.test.config._reparse([str(tmpdir), '-v'])
        hosts = self.get_hosts()
        r = self.reporter(config, hosts)
        r.report(repevent.TestStarted(hosts, config, []))
        r.report(repevent.RsyncFinished())
        rootcol = py.test.collect.Directory(tmpdir)
        list(itemgen(MockSession(r), [rootcol], r.report))
        r.report(repevent.TestFinished())
        out, err = cap.reset()
        assert not err
        for i in ['+ testmodule:', 'test_one.py[1]']: # XXX finish
            assert i in out
        
    def _test_still_to_go(self):
        tmpdir = py.test.ensuretemp("stilltogo")
        tmpdir.ensure("__init__.py")
        cap = py.io.StdCaptureFD()
        config = py.test.config._reparse([str(tmpdir)])
        hosts = [HostInfo(i) for i in ["host1", "host2", "host3"]]
        for host in hosts:
            host.gw_remotepath = ''
        r = self.reporter(config, hosts)
        r.report(repevent.TestStarted(hosts, config, ["a", "b", "c"]))
        for host in hosts:
            r.report(repevent.HostGatewayReady(host, ["a", "b", "c"]))
        for host in hosts:
            for root in ["a", "b", "c"]:
                r.report(repevent.HostRSyncRootReady(host, root))
        out, err = cap.reset()
        assert not err
        expected1 = "Test started, hosts: host1[0], host2[0], host3[0]"
        assert out.find(expected1) != -1
        for expected in py.code.Source("""
            host1[0]: READY (still 2 to go)
            host2[0]: READY (still 1 to go)
            host3[0]: READY
        """).lines:
            expected = expected.strip()
            assert out.find(expected) != -1

class TestLocalReporter(AbstractTestReporter):
    reporter = LocalReporter

    def get_hosts(self):
        return None
    
    def test_report_received_item_outcome(self):
        assert self.report_received_item_outcome() == 'FsF.'

    def test_verbose(self):
        self._test_verbose()

    def test_module(self):
        output = self._test_module()
        assert output.find("test_one") != -1
        assert output.endswith("FsF."), output
    
    def test_full_module(self):
        received = self._test_full_module()
        expected_lst = ["repmod/test_one.py", "FAILED TO LOAD MODULE",
                        "skipped", "reason"]
        for i in expected_lst:
            assert received.find(i) != -1

class TestRemoteReporter(AbstractTestReporter):
    reporter = RemoteReporter

    def get_hosts(self):
        return [HostInfo("host")]

    def test_still_to_go(self):
        self._test_still_to_go()

    def test_report_received_item_outcome(self):
        val = self.report_received_item_outcome()
        expected_lst = ["host", "FAILED",
                        "funcpass", "test_one",
                        "SKIPPED",
                        "PASSED"]
        for expected in expected_lst:
            assert val.find(expected) != -1
    
    def test_module(self):
        val = self._test_module()
        expected_lst = ["host", "FAILED",
                        "funcpass", "test_one",
                        "SKIPPED",
                        "PASSED"]
        for expected in expected_lst:
            assert val.find(expected) != -1
    
    def test_full_module(self):
        val = self._test_full_module()
        assert val.find("FAILED TO LOAD MODULE: repmod/test_three.py\n"\
        "\nSkipped ('reason') repmod/test_two.py") != -1

def test_reporter_choice():
    from py.__.test.rsession.web import WebReporter
    from py.__.test.rsession.rest import RestReporter
    choices = [
        (['-d', '--rest'], RestReporter),
        (['-w'], WebReporter),
        (['-r'], WebReporter)]
    for opts, reporter in choices:
        config = py.test.config._reparse(['xxx'] + opts)
        assert choose_reporter(None, config) is reporter

