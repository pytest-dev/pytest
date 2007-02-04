
""" test of local version of py.test distributed
"""

import py
from py.__.test.rsession.rsession import LSession
from py.__.test.rsession import repevent
from py.__.test.rsession.local import box_runner, plain_runner, apigen_runner

def setup_module(mod): 
    mod.tmp = py.test.ensuretemp("lsession_module") 

class TestLSession(object):
    # XXX: Some tests of that should be run as well on RSession, while
    #      some not at all
    def example_distribution(self, runner):
        # XXX find a better way for the below 
        tmpdir = tmp
        dirname = "sub_lsession"+runner.func_name
        tmpdir.ensure(dirname, "__init__.py")
        tmpdir.ensure(dirname, "test_one.py").write(py.code.Source("""
            def test_1(): 
                pass
            def test_2():
                assert 0
            def test_3():
                raise ValueError(23)
            def test_4(someargs):
                pass
            #def test_5():
            #    import os
            #    os.kill(os.getpid(), 11)
        """))
        args = [str(tmpdir.join(dirname))]
        config = py.test.config._reparse(args)
        lsession = LSession(config)
        allevents = []
        lsession.main(reporter=allevents.append, runner=runner)
        testevents = [x for x in allevents 
                        if isinstance(x, repevent.ReceivedItemOutcome)]
        assert len(testevents)
        passevents = [i for i in testevents if i.outcome.passed]
        failevents = [i for i in testevents if i.outcome.excinfo]
        skippedevents = [i for i in testevents if i.outcome.skipped]
        signalevents = [i for i in testevents if i.outcome.signal]
        assert len(passevents) == 1
        assert len(failevents) == 3
        assert len(skippedevents) == 0
        #assert len(signalevents) == 1
        tb = failevents[0].outcome.excinfo.traceback
        assert str(tb[0].path).find("test_one") != -1
        assert str(tb[0].source).find("test_2") != -1
        assert failevents[0].outcome.excinfo.typename == 'AssertionError'
        tb = failevents[1].outcome.excinfo.traceback
        assert str(tb[0].path).find("test_one") != -1
        assert str(tb[0].source).find("test_3") != -1
        assert failevents[1].outcome.excinfo.typename == 'ValueError'
        assert str(failevents[1].outcome.excinfo.value) == '23'
        tb = failevents[2].outcome.excinfo.traceback
        assert failevents[2].outcome.excinfo.typename == 'TypeError'
        assert str(tb[0].path).find("executor") != -1
        assert str(tb[0].source).find("execute") != -1

    def test_normal(self):
        if not hasattr(py.std.os, 'fork'):
            py.test.skip('operating system not supported')
        self.example_distribution(box_runner)
    
    def test_plain(self):
        self.example_distribution(plain_runner)

    def test_pdb_run(self):
        # we make sure that pdb is engaged
        tmpdir = tmp
        subdir = "sub_pdb_run"
        tmpdir.ensure(subdir, "__init__.py")
        tmpdir.ensure(subdir, "test_one.py").write(py.code.Source("""
            def test_1(): 
                assert 0
        """))
        import pdb
        l = []
        def some_fun(*args):
            l.append(args)

        try:
            post_mortem = pdb.post_mortem
            pdb.post_mortem = some_fun
            args = [str(tmpdir.join(subdir)), '--pdb']
            config = py.test.config._reparse(args)
            lsession = LSession(config)
            allevents = []
            try:
                lsession.main(reporter=allevents.append, runner=plain_runner)
            except SystemExit:
                pass
            else:
                py.test.fail("Didn't raise system exit")
            failure_events = [event for event in allevents if isinstance(event,
                                                     repevent.ImmediateFailure)]
            assert len(failure_events) == 1
            assert len(l) == 1
        finally:
            pdb.post_mortem = post_mortem

    def test_minus_x(self):
        if not hasattr(py.std.os, 'fork'):
            py.test.skip('operating system not supported')
        tmpdir = tmp
        subdir = "sub_lsession_minus_x"
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
        """))
        args = [str(tmpdir.join(subdir)), '-x']
        config = py.test.config._reparse(args)
        assert config.option.exitfirst
        lsession = LSession(config)
        allevents = []
        
        lsession.main(reporter=allevents.append, runner=box_runner)
        testevents = [x for x in allevents 
                        if isinstance(x, repevent.ReceivedItemOutcome)]
        assert len(testevents)
        passevents = [i for i in testevents if i.outcome.passed]
        failevents = [i for i in testevents if i.outcome.excinfo]
        assert len(passevents) == 1
        assert len(failevents) == 1
    
    def test_minus_k(self):
        if not hasattr(py.std.os, 'fork'):
            py.test.skip('operating system not supported')
        tmpdir = tmp
        tmpdir.ensure("sub3", "__init__.py")
        tmpdir.ensure("sub3", "test_some.py").write(py.code.Source("""
            def test_one(): 
                pass
            def test_one_one():
                assert 0
            def test_other():
                raise ValueError(23)
            def test_two(someargs):
                pass
        """))
        args = [str(tmpdir.join("sub3")), '-k', 'test_one']
        config = py.test.config._reparse(args)
        lsession = LSession(config)
        allevents = []
        
        lsession.main(reporter=allevents.append, runner=box_runner)
        testevents = [x for x in allevents 
                        if isinstance(x, repevent.ReceivedItemOutcome)]
        assert len(testevents)
        passevents = [i for i in testevents if i.outcome.passed]
        failevents = [i for i in testevents if i.outcome.excinfo]
        assert len(passevents) == 1
        assert len(failevents) == 1

    def test_lsession(self):
        tmpdir = tmp
        tmpdir.ensure("sub4", "__init__.py")
        tmpdir.ensure("sub4", "test_some.py").write(py.code.Source("""
            def test_one(): 
                pass
            def test_one_one():
                assert 0
            def test_other():
                raise ValueError(23)
            def test_two(someargs):
                pass
        """))
        
        args = [str(tmpdir.join("sub4"))]
        config = py.test.config._reparse(args)
        lsession = LSession(config)
        allevents = []
        allruns = []
        def dummy_runner(item, config, reporter):
            allruns.append(item)
            item.passed = True
            return item
        lsession.main(reporter=allevents.append, runner=dummy_runner)
        
        assert len(allruns) == 4
        testevents = [x for x in allevents 
                        if isinstance(x, repevent.ReceivedItemOutcome)]
        assert len(testevents) == 4
        lst = ['test_one', 'test_one_one', 'test_other', 'test_two']
        for num, i in enumerate(testevents):
            assert i.item == i.outcome
            assert i.item.name == lst[num]
        
    def test_module_raising(self):
        tmpdir = tmp
        tmpdir.ensure("sub5", "__init__.py")
        tmpdir.ensure("sub5", "test_some.py").write(py.code.Source("""
            1/0
        """))
        tmpdir.ensure("sub5", "test_other.py").write(py.code.Source("""
            import py
            py.test.skip("reason")
        """))
        
        args = [str(tmpdir.join("sub5"))]
        config = py.test.config._reparse(args)
        lsession = LSession(config)
        allevents = []
        lsession.main(reporter=allevents.append, runner=box_runner)
        testevents = [x for x in allevents 
                        if isinstance(x, repevent.ReceivedItemOutcome)]
        assert len(testevents) == 0
        failedtryiter = [x for x in allevents 
                        if isinstance(x, repevent.FailedTryiter)]
        assert len(failedtryiter) == 1
        skippedtryiter = [x for x in allevents 
                        if isinstance(x, repevent.SkippedTryiter)]
        assert len(skippedtryiter) == 1
        

    def test_assert_reinterpret(self):
        if not hasattr(py.std.os, 'fork'):
            py.test.skip('operating system not supported')
        tmpdir = tmp
        tmpdir.ensure("sub6", "__init__.py")
        tmpdir.ensure("sub6", "test_some.py").write(py.code.Source("""
        def test_one():
            x = [1, 2]
            assert [0] == x
        """))
        args = [str(tmpdir.join("sub6"))]
        config = py.test.config._reparse(args)
        lsession = LSession(config)
        allevents = []
        lsession.main(reporter=allevents.append, runner=box_runner)
        testevents = [x for x in allevents 
                        if isinstance(x, repevent.ReceivedItemOutcome)]
        failevents = [i for i in testevents if i.outcome.excinfo]
        assert len(failevents) == 1
        assert len(testevents) == 1
        assert failevents[0].outcome.excinfo.value == 'assert [0] == [1, 2]'

    def test_nocapture(self):
        tmpdir = tmp
        tmpdir.ensure("sub7", "__init__.py")
        tmpdir.ensure("sub7", "test_nocap.py").write(py.code.Source("""
        def test_one():
            print 1
            print 2
            print 3
        """))
        args = [str(tmpdir.join("sub7"))]
        config = py.test.config._reparse(args)
        lsession = LSession(config)
        allevents = []
        lsession.main(reporter=allevents.append, runner=plain_runner)
        testevents = [x for x in allevents 
                        if isinstance(x, repevent.ReceivedItemOutcome)]
        assert len(testevents) == 1
        assert testevents[0].outcome.passed
        assert testevents[0].outcome.stderr == ""
        assert testevents[0].outcome.stdout == "1\n2\n3\n"

    def test_runner_selection(self):
        tmpdir = py.test.ensuretemp("lsession_runner_selection")
        tmpdir.ensure("apigen.py").write(py.code.Source("""
        def get_documentable_items(*args):
            return 'foo', {}
        """))
        opt_mapping = {
            '': plain_runner,
            '--box': box_runner,
            '--apigen=%s/apigen.py' % str(tmpdir): apigen_runner,
        }
        pkgdir = tmpdir.dirpath()
        for opt in opt_mapping.keys():
            if opt:
                all = opt + " " + str(tmpdir)
            else:
                all = str(tmpdir)
            config = py.test.config._reparse(all.split(" "))
            lsession = LSession(config)
            assert lsession.init_runner() is opt_mapping[opt]
        #tmpdir.dirpath().ensure("conftest.py").write(py.code.Source("""
        #dist_boxing=True
        #"""))
        #config = py.test.config._reparse([str(tmpdir)])
        #lsession = LSession(config)
        #assert lsession.init_runner(pkgdir) is box_runner
        # XXX check why it fails
