import py
from py.__.test.dist.dsession import DSession
from test_txnode import EventQueue

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
        config = testdir.parseconfig('-d', p1, '--tx=popen')
        dsession = DSession(config)
        eq = EventQueue(config.bus)
        dsession.main([config.getfsnode(p1)])
        ev, = eq.geteventargs("itemtestreport")
        assert ev.passed
        ev, = eq.geteventargs("itemtestreport")
        assert ev.skipped
        ev, = eq.geteventargs("itemtestreport")
        assert ev.failed
        # see that the node is really down 
        node, error = eq.geteventargs("testnodedown")
        assert node.gateway.spec.popen
        eq.geteventargs("testrunfinish")

    def test_distribution_rsyncdirs_example(self, testdir):
        source = testdir.mkdir("source")
        dest = testdir.mkdir("dest")
        subdir = source.mkdir("example_pkg")
        subdir.ensure("__init__.py")
        p = subdir.join("test_one.py")
        p.write("def test_5(): assert not __file__.startswith(%r)" % str(p))
        result = testdir.runpytest("-d", "--rsyncdir=%(subdir)s" % locals(), 
            "--tx=popen//chdir=%(dest)s" % locals(), p)
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            "*1* *popen*platform*",
            #"RSyncStart: [G1]",
            #"RSyncFinished: [G1]",
            "*1 passed*"
        ])
        assert dest.join(subdir.basename).check(dir=1)

    def test_nice_level(self, testdir):
        """ Tests if nice level behaviour is ok """
        import os
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
        evrec = testdir.inline_run('-d', p1, '--tx=popen')
        ev = evrec.getfirstnamed('itemtestreport')
        assert ev.passed

