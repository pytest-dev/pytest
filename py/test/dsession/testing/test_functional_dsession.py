
""" Tests various aspects of dist, like ssh hosts setup/teardown
"""

import py
from py.__.test.dsession.dsession import DSession
from test_masterslave import EventQueue
import os


class TestAsyncFunctional:
    def test_conftest_options(self, testdir):
        p1 = testdir.tmpdir.ensure("dir", 'p1.py')
        p1.dirpath("__init__.py").write("")
        p1.dirpath("conftest.py").write(py.code.Source("""
            print "importing conftest", __file__
            import py
            Option = py.test.config.Option 
            option = py.test.config.addoptions("someopt", 
                Option('--someopt', action="store_true", dest="someopt", default=False))
            dist_rsync_roots = ['../dir']
            print "added options", option
            print "config file seen from conftest", py.test.config
        """))
        p1.write(py.code.Source("""
            import py, conftest
            def test_1(): 
                print "config from test_1", py.test.config
                print "conftest from test_1", conftest.__file__
                print "test_1: py.test.config.option.someopt", py.test.config.option.someopt
                print "test_1: conftest", conftest
                print "test_1: conftest.option.someopt", conftest.option.someopt
                assert conftest.option.someopt 
        """))
        result = testdir.runpytest('-n1', p1, '--someopt')
        assert result.ret == 0
        extra = result.stdout.fnmatch_lines([
            "*1 passed*", 
        ])

    def test_dist_some_tests(self, testdir):
        p1 = testdir.makepyfile(test_one="""
            def test_1(): 
                pass
            def test_x():
                import py
                py.test.skip("aaa")
            def test_fail():
                assert 0
        """)
        config = testdir.parseconfig('-d', p1, '--hosts=popen')
        dsession = DSession(config)
        eq = EventQueue(config.bus)
        dsession.main([config.getfsnode(p1)])
        ev, = eq.geteventargs("itemtestreport")
        assert ev.passed
        ev, = eq.geteventargs("itemtestreport")
        assert ev.skipped
        ev, = eq.geteventargs("itemtestreport")
        assert ev.failed
        # see that the host is really down 
        ev, = eq.geteventargs("hostdown")
        assert ev.host.address == "popen"
        ev, = eq.geteventargs("testrunfinish")

    def test_distribution_rsync_roots_example(self, testdir):
        py.test.skip("testing for root rsync needs rework")
        destdir = py.test.ensuretemp("example_dist_destdir")
        subdir = "sub_example_dist"
        sourcedir = self.tmpdir.mkdir("source")
        sourcedir.ensure(subdir, "conftest.py").write(py.code.Source("""
            hosts = ["popen:%s"]
            rsyncdirs = ["%s", "../py"]
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

        sorter = testdir.inline_run(tmpdir.join(subdir))
        testevents = sorter.getnamed('itemtestreport')
        assert len([x for x in testevents if x.passed]) == 2
        assert len([x for x in testevents if x.failed]) == 3
        assert len([x for x in testevents if x.skipped]) == 0

    def test_nice_level(self, testdir):
        """ Tests if nice level behaviour is ok """
        if not hasattr(os, 'nice'):
            py.test.skip("no os.nice() available")
        testdir.makepyfile(conftest="""
                dist_nicelevel = 10
        """)
        p1 = testdir.makepyfile("""
            def test_nice():
                import os
                assert os.nice(0) == 10
        """)
        evrec = testdir.inline_run('-d', p1, '--hosts=popen')
        ev = evrec.getreport('test_nice')
        assert ev.passed

