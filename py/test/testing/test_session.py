import py

class SessionTests:
    def test_initsession(self, tmpdir):
        config = py.test.config._reparse([tmpdir])
        session = config.initsession()
        assert session.config is config 
    
    def test_basic_testitem_events(self, testdir):
        tfile = testdir.makepyfile("""
            def test_one(): 
                pass
            def test_one_one():
                assert 0
            def test_other():
                raise ValueError(23)
            def test_two(someargs):
                pass
        """)
        sorter = testdir.inline_run(tfile)
        passed, skipped, failed = sorter.listoutcomes()
        assert len(skipped) == 0
        assert len(passed) == 1
        assert len(failed) == 3  
        assert failed[0].colitem.name == "test_one_one"
        assert failed[1].colitem.name == "test_other"
        assert failed[2].colitem.name == "test_two"
        itemstarted = sorter.getcalls("itemstart")
        assert len(itemstarted) == 4
        colstarted = sorter.getcalls("collectionstart")
        assert len(colstarted) == 1
        col = colstarted[0].collector
        assert isinstance(col, py.test.collect.Module)

    def test_nested_import_error(self, testdir): 
        tfile = testdir.makepyfile("""
            import import_fails
            def test_this():
                assert import_fails.a == 1
        """, import_fails="""
            import does_not_work 
            a = 1
        """)
        sorter = testdir.inline_run(tfile)
        l = sorter.getfailedcollections()
        assert len(l) == 1 
        out = l[0].longrepr.reprcrash.message
        assert out.find('does_not_work') != -1 

    def test_raises_output(self, testdir): 
        sorter = testdir.inline_runsource("""
            import py
            def test_raises_doesnt():
                py.test.raises(ValueError, int, "3")
        """)
        passed, skipped, failed = sorter.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        if not out.find("DID NOT RAISE") != -1: 
            print out
            py.test.fail("incorrect raises() output") 

    def test_generator_yields_None(self, testdir): 
        sorter = testdir.inline_runsource("""
            def test_1():
                yield None 
        """)
        failures = sorter.getfailedcollections()
        out = failures[0].longrepr.reprcrash.message
        i = out.find('TypeError') 
        assert i != -1 

    def test_syntax_error_module(self, testdir): 
        sorter = testdir.inline_runsource("this is really not python")
        l = sorter.getfailedcollections()
        assert len(l) == 1
        out = l[0].longrepr.reprcrash.message
        assert out.find(str('not python')) != -1

    def test_exit_first_problem(self, testdir): 
        sorter = testdir.inline_runsource("""
            def test_one(): assert 0
            def test_two(): assert 0
        """, '--exitfirst')
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 1
        assert passed == skipped == 0

    def test_broken_repr(self, testdir):
        p = testdir.makepyfile("""
            import py
            class BrokenRepr1:
                foo=0
                def __repr__(self):
                    raise Exception("Ha Ha fooled you, I'm a broken repr().")
            class BrokenRepr2:
                foo=0
                def __repr__(self):
                    raise "Ha Ha fooled you, I'm a broken repr()."
            
            class TestBrokenClass:
                def test_explicit_bad_repr(self):
                    t = BrokenRepr1()
                    py.test.raises(Exception, 'repr(t)')
                    
                def test_implicit_bad_repr1(self):
                    t = BrokenRepr1()
                    assert t.foo == 1

                def test_implicit_bad_repr2(self):
                    t = BrokenRepr2()
                    assert t.foo == 1
        """)
        sorter = testdir.inline_run(p)
        passed, skipped, failed = sorter.listoutcomes()
        assert len(failed) == 2
        out = failed[0].longrepr.reprcrash.message
        assert out.find("""[Exception("Ha Ha fooled you, I'm a broken repr().") raised in repr()]""") != -1 #'
        out = failed[1].longrepr.reprcrash.message
        assert (out.find("[unknown exception raised in repr()]") != -1  or
                out.find("TypeError") != -1)

    def test_skip_by_conftest_directory(self, testdir):
        testdir.makepyfile(conftest="""
            import py
            class Directory(py.test.collect.Directory):
                def collect(self):
                    py.test.skip("intentional")
        """, test_file="""
            def test_one(): pass
        """)
        sorter = testdir.inline_run(testdir.tmpdir)
        reports = sorter.getreports("collectreport")
        assert len(reports) == 1
        assert reports[0].skipped 

class TestNewSession(SessionTests):
    def test_pdb_run(self, testdir, monkeypatch):
        import py.__.test.custompdb
        tfile = testdir.makepyfile("""
            def test_usepdb(): 
                assert 0
        """)
        l = []
        def mypdb(*args):
            l.append(args)
        monkeypatch.setattr(py.__.test.custompdb, 'post_mortem', mypdb)
        sorter = testdir.inline_run('--pdb', tfile)
        rep = sorter.matchreport("test_usepdb")
        assert rep.failed
        assert len(l) == 1
        tb = py.code.Traceback(l[0][0])
        assert tb[-1].name == "test_usepdb" 

    def test_order_of_execution(self, testdir): 
        sorter = testdir.inline_runsource("""
            l = []
            def test_1():
                l.append(1)
            def test_2():
                l.append(2)
            def test_3():
                assert l == [1,2]
            class Testmygroup:
                reslist = l
                def test_1(self):
                    self.reslist.append(1)
                def test_2(self):
                    self.reslist.append(2)
                def test_3(self):
                    self.reslist.append(3)
                def test_4(self):
                    assert self.reslist == [1,2,1,2,3]
        """)
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == skipped == 0
        assert passed == 7
        # also test listnames() here ... 

    def test_collect_only_with_various_situations(self, testdir):
        p = testdir.makepyfile(
            test_one="""
                def test_one():
                    raise ValueError()

                class TestX:
                    def test_method_one(self):
                        pass

                class TestY(TestX):
                    pass
            """, 
            test_two="""
                import py
                py.test.skip('xxx')
            """, 
            test_three="xxxdsadsadsadsa",
            __init__=""
        )
        sorter = testdir.inline_run('--collectonly', p.dirpath())
       
        itemstarted = sorter.getcalls("itemstart")
        assert len(itemstarted) == 3
        assert not sorter.getreports("itemtestreport") 
        started = sorter.getcalls("collectionstart")
        finished = sorter.getreports("collectreport")
        assert len(started) == len(finished) 
        assert len(started) == 8 
        colfail = [x for x in finished if x.failed]
        colskipped = [x for x in finished if x.skipped]
        assert len(colfail) == 1
        assert len(colskipped) == 1

    def test_minus_x_import_error(self, testdir):
        testdir.makepyfile(__init__="")
        testdir.makepyfile(test_one="xxxx", test_two="yyyy")
        sorter = testdir.inline_run("-x", testdir.tmpdir)
        finished = sorter.getreports("collectreport")
        colfail = [x for x in finished if x.failed]
        assert len(colfail) == 1

class TestNewSessionDSession(SessionTests):
    def parseconfig(self, *args):
        args = ('-n1',) + args
        return SessionTests.parseconfig(self, *args)
    
