import py

class SessionTests:
    def test_initsession(self, testdir, tmpdir):
        config = testdir.reparseconfig()
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
        reprec = testdir.inline_run(tfile)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(skipped) == 0
        assert len(passed) == 1
        assert len(failed) == 3  
        assert failed[0].item.name == "test_one_one"
        assert failed[1].item.name == "test_other"
        assert failed[2].item.name == "test_two"
        itemstarted = reprec.getcalls("pytest_itemstart")
        assert len(itemstarted) == 4
        colstarted = reprec.getcalls("pytest_collectstart")
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
        reprec = testdir.inline_run(tfile)
        l = reprec.getfailedcollections()
        assert len(l) == 1 
        out = l[0].longrepr.reprcrash.message
        assert out.find('does_not_work') != -1 

    def test_raises_output(self, testdir): 
        reprec = testdir.inline_runsource("""
            import py
            def test_raises_doesnt():
                py.test.raises(ValueError, int, "3")
        """)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        if not out.find("DID NOT RAISE") != -1: 
            print(out)
            py.test.fail("incorrect raises() output") 

    def test_generator_yields_None(self, testdir): 
        reprec = testdir.inline_runsource("""
            def test_1():
                yield None 
        """)
        failures = reprec.getfailedcollections()
        out = failures[0].longrepr.reprcrash.message
        i = out.find('TypeError') 
        assert i != -1 

    def test_syntax_error_module(self, testdir): 
        reprec = testdir.inline_runsource("this is really not python")
        l = reprec.getfailedcollections()
        assert len(l) == 1
        out = l[0].longrepr.reprcrash.message
        assert out.find(str('not python')) != -1

    def test_exit_first_problem(self, testdir): 
        reprec = testdir.inline_runsource("""
            def test_one(): assert 0
            def test_two(): assert 0
        """, '--exitfirst')
        passed, skipped, failed = reprec.countoutcomes()
        assert failed == 1
        assert passed == skipped == 0

    def test_broken_repr(self, testdir):
        p = testdir.makepyfile("""
            import py
            class BrokenRepr1:
                foo=0
                def __repr__(self):
                    raise Exception("Ha Ha fooled you, I'm a broken repr().")
            
            class TestBrokenClass:
                def test_explicit_bad_repr(self):
                    t = BrokenRepr1()
                    py.test.raises(Exception, 'repr(t)')
                    
                def test_implicit_bad_repr1(self):
                    t = BrokenRepr1()
                    assert t.foo == 1

        """)
        reprec = testdir.inline_run(p)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out.find("""[Exception("Ha Ha fooled you, I'm a broken repr().") raised in repr()]""") != -1 #'

    def test_skip_by_conftest_directory(self, testdir):
        testdir.makepyfile(conftest="""
            import py
            class Directory(py.test.collect.Directory):
                def collect(self):
                    py.test.skip("intentional")
        """, test_file="""
            def test_one(): pass
        """)
        reprec = testdir.inline_run(testdir.tmpdir)
        reports = reprec.getreports("pytest_collectreport")
        assert len(reports) == 1
        assert reports[0].skipped 

class TestNewSession(SessionTests):

    def test_order_of_execution(self, testdir): 
        reprec = testdir.inline_runsource("""
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
        passed, skipped, failed = reprec.countoutcomes()
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
        reprec = testdir.inline_run('--collectonly', p.dirpath())
       
        itemstarted = reprec.getcalls("pytest_itemstart")
        assert len(itemstarted) == 3
        assert not reprec.getreports("pytest_runtest_logreport") 
        started = reprec.getcalls("pytest_collectstart")
        finished = reprec.getreports("pytest_collectreport")
        assert len(started) == len(finished) 
        assert len(started) == 8 
        colfail = [x for x in finished if x.failed]
        colskipped = [x for x in finished if x.skipped]
        assert len(colfail) == 1
        assert len(colskipped) == 1

    def test_minus_x_import_error(self, testdir):
        testdir.makepyfile(__init__="")
        testdir.makepyfile(test_one="xxxx", test_two="yyyy")
        reprec = testdir.inline_run("-x", testdir.tmpdir)
        finished = reprec.getreports("pytest_collectreport")
        colfail = [x for x in finished if x.failed]
        assert len(colfail) == 1

