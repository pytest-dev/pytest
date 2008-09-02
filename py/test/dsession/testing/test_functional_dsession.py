
""" Tests various aspects of dist, like ssh hosts setup/teardown
"""

import py
from py.__.test import event
from py.__.test.dsession.dsession import DSession
from py.__.test.dsession.hostmanage import HostManager, Host
from py.__.test.testing import suptest
import os

def eventreader(session):
    queue = py.std.Queue.Queue()
    session.bus.subscribe(queue.put)
    def readevent(eventtype=event.ItemTestReport, timeout=2.0):
        events = []
        while 1:
            try:
                ev = queue.get(timeout=timeout)
            except py.std.Queue.Empty:
                print "seen events", events
                raise IOError("did not see %r events" % (eventtype))
            else:
                if isinstance(ev, eventtype):
                    #print "other events seen", events
                    return ev
                events.append(ev)
    return readevent

class TestAsyncFunctional(suptest.InlineCollection):
    def test_dist_no_disthost(self):
        config = self.parseconfig(self.tmpdir, '-d')
        py.test.raises(SystemExit, "config.initsession()")

    def test_session_eventlog_dist(self):
        self.makepyfile(conftest="dist_hosts=['localhost']\n")
        eventlog = self.tmpdir.join("mylog")
        config = self.parseconfig(self.tmpdir, '-d', '--eventlog=%s' % eventlog)
        session = config.initsession()
        session.bus.notify(event.TestrunStart())
        s = eventlog.read()
        assert s.find("TestrunStart") != -1

    def test_conftest_options(self):
        self.makepyfile(conftest="""
            print "importing conftest"
            import py
            Option = py.test.config.Option 
            option = py.test.config.addoptions("someopt", 
                Option('', '--forcegen', action="store_true", dest="forcegen", default=False))
        """)
        self.makepyfile(__init__="#")
        p1 = self.makepyfile(test_one="""
            def test_1(): 
                import py, conftest
                print "test_1: py.test.config.option.forcegen", py.test.config.option.forcegen
                print "test_1: conftest", conftest
                print "test_1: conftest.option.forcegen", conftest.option.forcegen
                assert conftest.option.forcegen 
        """)
        print p1
        config = self.parseconfig('-n1', p1, '--forcegen')
        dsession = DSession(config)
        readevent = eventreader(dsession)
        dsession.main()
        ev = readevent(event.ItemTestReport)
        if not ev.passed:
            print ev.outcome.longrepr
            assert 0

    def test_dist_some_tests(self):
        self.makepyfile(conftest="dist_hosts=['localhost']\n")
        p1 = self.makepyfile(test_one="""
            def test_1(): 
                pass
            def test_x():
                import py
                py.test.skip("aaa")
            def test_fail():
                assert 0
        """)
        config = self.parseconfig('-d', p1)
        dsession = DSession(config)
        readevent = eventreader(dsession)
        dsession.main([config.getfsnode(p1)])
        ev = readevent(event.ItemTestReport)
        assert ev.passed
        ev = readevent(event.ItemTestReport)
        assert ev.skipped
        ev = readevent(event.ItemTestReport)
        assert ev.failed
        # see that the host is really down 
        ev = readevent(event.HostDown)
        assert ev.host.hostname == "localhost"
        ev = readevent(event.TestrunFinish)

    def test_distribution_rsync_roots_example(self):
        py.test.skip("testing for root rsync needs rework")
        destdir = py.test.ensuretemp("example_dist_destdir")
        subdir = "sub_example_dist"
        sourcedir = self.tmpdir.mkdir("source")
        sourcedir.ensure(subdir, "conftest.py").write(py.code.Source("""
            dist_hosts = ["localhost:%s"]
            dist_rsync_roots = ["%s", "../py"]
        """ % (destdir, tmpdir.join(subdir), )))
        tmpdir.ensure(subdir, "__init__.py")
        tmpdir.ensure(subdir, "test_one.py").write(py.code.Source("""
            def test_1(): 
                pass
            def test_2():
                assert 0
            def test_3():
                raise ValueError(23)
            def test_4(someargs):
                pass
            def test_5():
                assert __file__ != '%s'
            #def test_6():
            #    import py
            #    assert py.__file__ != '%s'
        """ % (tmpdir.join(subdir), py.__file__)))
        destdir.join("py").mksymlinkto(py.path.local(py.__file__).dirpath())
        config = py.test.config._reparse([tmpdir.join(subdir)])
        assert config.topdir == tmpdir
        assert not tmpdir.join("__init__.py").check()
        dist = DSession(config)
        sorter = suptest.events_from_session(dist)
        testevents = sorter.get(event.ItemTestReport)
        assert len([x for x in testevents if x.passed]) == 2
        assert len([x for x in testevents if x.failed]) == 3
        assert len([x for x in testevents if x.skipped]) == 0

    def test_nice_level(self):
        """ Tests if nice level behaviour is ok """
        if not hasattr(os, 'nice'):
            py.test.skip("no os.nice() available")
        self.makepyfile(conftest="""
                dist_hosts=['localhost']
                dist_nicelevel = 10
        """)
        p1 = self.makepyfile(test_nice="""
            def test_nice():
                import os
                assert os.nice(0) == 10
        """)
        config = self.parseconfig('-d', p1)
        session = config.initsession()
        events = suptest.events_from_session(session)
        ev = events.getreport('test_nice')
        assert ev.passed

