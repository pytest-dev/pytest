
""" Tests various aspects of rsession, like ssh hosts setup/teardown
"""

import py
from py.__.test.rsession import report
from py.__.test.rsession.rsession import RSession 
from py.__.test.rsession.hostmanage import HostManager, HostInfo
from py.__.test.rsession.testing.test_slave import funcfail_spec,\
    funcpass_spec, funcskip_spec, funcprint_spec, funcprintfail_spec, \
    funcoptioncustom_spec

def setup_module(mod):
    mod.pkgdir = py.path.local(py.__file__).dirpath()
    mod.tmpdir = py.test.ensuretemp(mod.__name__)


#def test_make_colitems():
#    one = pkgdir.join("initpkg.py")
#    two = pkgdir.join("path", "__init__.py")#

#    cols = RSession.make_colitems([one, two], baseon=pkgdir) 
#    assert len(cols) == 2
#    col_one, col_two = cols
#    assert col_one.listnames() == ["py", "initpkg.py"]
#    assert col_two.listnames() == ["py", "path", "__init__.py"]#
#
#    cols = RSession.make_colitems([one, two], baseon=pkgdir.dirpath()) 
#    assert len(cols) == 2
#    col_one, col_two = cols
#    assert col_one.listnames() == [pkgdir.dirpath().basename, 
#                                   "py", "initpkg.py"]
#    assert col_two.listnames() == [pkgdir.dirpath().basename, 
#                                   "py", "path", "__init__.py"]

def test_example_tryiter():
    events = []
    tmpdir = py.test.ensuretemp("tryitertest")
    tmpdir.ensure("a", "__init__.py")
    tmpdir.ensure("conftest.py").write(py.code.Source("""
        import py
        py.test.skip("Reason")
    """))
    tmpdir.ensure("a", "test_empty.py").write(py.code.Source("""
        def test_empty():
            pass
    """))
    rootcol = py.test.collect.Directory(tmpdir)
    data = list(rootcol._tryiter(reporterror=events.append))
    assert len(events) == 2
    assert str(events[1][0].value) == "Reason"

class TestRSessionRemote: 
    def test_example_distribution_minus_x(self):
        destdir = py.test.ensuretemp("example_dist_dest_x")
        tmpdir = py.test.ensuretemp("example_distribution_minus_x")
        tmpdir.ensure("sub", "conftest.py").write(py.code.Source("""
            dist_hosts = ['localhost:%s']
        """ % destdir))
        tmpdir.ensure("sub", "__init__.py")
        tmpdir.ensure("sub", "test_one.py").write(py.code.Source("""
            def test_1(): 
                pass
            def test_x():
                import py
                py.test.skip("aaa")
            def test_2():
                assert 0
            def test_3():
                raise ValueError(23)
            def test_4(someargs):
                pass
        """))
        config = py.test.config._reparse([tmpdir.join("sub"), '-x'])
        rsession = RSession(config)
        allevents = []
        rsession.main(reporter=allevents.append)
        testevents = [x for x in allevents 
                        if isinstance(x, report.ReceivedItemOutcome)]
        assert len(testevents) == 3
        assert rsession.checkfun()

    def test_distribution_rsync_roots_example(self):
        destdir = py.test.ensuretemp("example_dist_destdir")
        subdir = "sub_example_dist"
        tmpdir = py.test.ensuretemp("example_distribution")
        tmpdir.ensure(subdir, "conftest.py").write(py.code.Source("""
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
            def test_6():
                import py
                assert py.__file__ != '%s'
        """ % (tmpdir.join(subdir), py.__file__)))
        destdir.join("py").mksymlinkto(py.path.local(py.__file__).dirpath())
        config = py.test.config._reparse([tmpdir.join(subdir)])
        assert config.topdir == tmpdir
        assert not tmpdir.join("__init__.py").check()
        rsession = RSession(config)
        allevents = []
        rsession.main(reporter=allevents.append) 
        testevents = [x for x in allevents 
                        if isinstance(x, report.ReceivedItemOutcome)]
        assert len(testevents)
        print testevents
        passevents = [i for i in testevents if i.outcome.passed]
        failevents = [i for i in testevents if i.outcome.excinfo]
        skippedevents = [i for i in testevents if i.outcome.skipped]
        assert len(testevents) == 6
        assert len(passevents) == 3
        assert len(failevents) == 3
        tb = failevents[0].outcome.excinfo.traceback
        assert str(tb[0].path).find("test_one") != -1
        assert tb[0].source.find("test_2") != -1
        assert failevents[0].outcome.excinfo.typename == 'AssertionError'
        tb = failevents[1].outcome.excinfo.traceback
        assert str(tb[0].path).find("test_one") != -1
        assert tb[0].source.find("test_3") != -1
        assert failevents[1].outcome.excinfo.typename == 'ValueError'
        assert failevents[1].outcome.excinfo.value == '23'
        tb = failevents[2].outcome.excinfo.traceback
        assert failevents[2].outcome.excinfo.typename == 'TypeError'
        assert str(tb[0].path).find("executor") != -1
        assert tb[0].source.find("execute") != -1
        
    def test_setup_teardown_ssh(self):
        hosts = [HostInfo('localhost')]
        setup_events = []
        teardown_events = []
        
        config = py.test.config._reparse([tmpdir])
        hm = HostManager(hosts, config)
        nodes = hm.init_hosts(setup_events.append)
        hm.teardown_hosts(teardown_events.append, 
                       [node.channel for node in nodes], nodes)
        
        count_rsyn_calls = [i for i in setup_events 
                if isinstance(i, report.HostRSyncing)]
        assert len(count_rsyn_calls) == len([i for i in hosts])
        count_ready_calls = [i for i in setup_events 
                if isinstance(i, report.HostReady)]
        assert len(count_ready_calls) == len([i for i in hosts])
        
        # same for teardown events
        teardown_wait_starts = [i for i in teardown_events 
                                    if isinstance(i, report.CallStart)]
        teardown_wait_ends = [i for i in teardown_events 
                                    if isinstance(i, report.CallFinish)]
        assert len(teardown_wait_starts) == len(hosts)
        assert len(teardown_wait_ends) == len(hosts)

    def test_setup_teardown_run_ssh(self):
        hosts = [HostInfo('localhost')]
        allevents = []
        
        config = py.test.config._reparse([])
        hm = HostManager(hosts, config)
        nodes = hm.init_hosts(allevents.append)
        
        from py.__.test.rsession.testing.test_executor \
            import ItemTestPassing, ItemTestFailing, ItemTestSkipping
        
        rootcol = py.test.collect.Directory(pkgdir.dirpath())
        itempass = rootcol._getitembynames(funcpass_spec)
        itemfail = rootcol._getitembynames(funcfail_spec)
        itemskip = rootcol._getitembynames(funcskip_spec)
        itemprint = rootcol._getitembynames(funcprint_spec)

        # actually run some tests
        for node in nodes:
            node.send(itempass)
            node.send(itemfail)
            node.send(itemskip)
            node.send(itemprint)

        hm.teardown_hosts(allevents.append, [node.channel for node in nodes], nodes)

        events = [i for i in allevents 
                        if isinstance(i, report.ReceivedItemOutcome)]
        passed = [i for i in events 
                        if i.outcome.passed]
        skipped = [i for i in events 
                        if i.outcome.skipped]
        assert len(passed) == 2 * len(nodes)
        assert len(skipped) == len(nodes)
        assert len(events) == 4 * len(nodes)
        # one of passed for each node has non-empty stdout
        passed_stdout = [i for i in passed if i.outcome.stdout.find('samfing') != -1]
        assert len(passed_stdout) == len(nodes), passed

    def test_nice_level(self):
        """ Tests if nice level behaviour is ok
        """
        allevents = []
        hosts = [HostInfo('localhost')]
        tmpdir = py.test.ensuretemp("nice")
        tmpdir.ensure("__init__.py")
        tmpdir.ensure("conftest.py").write(py.code.Source("""
        dist_hosts = ['localhost']
        dist_nicelevel = 10
        """))
        tmpdir.ensure("test_one.py").write("""def test_nice():
            import os
            assert os.nice(0) == 10
        """)
        
        config = py.test.config._reparse([tmpdir])
        rsession = RSession(config)
        allevents = []
        rsession.main(reporter=allevents.append) 
        testevents = [x for x in allevents 
                        if isinstance(x, report.ReceivedItemOutcome)]
        passevents = [x for x in testevents if x.outcome.passed]
        assert len(passevents) == 1
        
def test_rsession_no_disthost():
    tmpdir = py.test.ensuretemp("rsession_no_disthost")
    tmpdir.ensure("conftest.py")
    config = py.test.config._reparse([str(tmpdir), '-d'])
    py.test.raises(SystemExit, "config.initsession()")
