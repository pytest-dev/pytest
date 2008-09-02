import py
from py.__.test import event 
from py.__.test.testing import suptest

def setup_module(mod):
    mod.tmpdir = py.test.ensuretemp(mod.__name__) 

class TestKeywordSelection(suptest.InlineSession):
    def test_select_simple(self):
        file_test = self.makepyfile(file_test="""
            def test_one(): assert 0
            class TestClass(object): 
                def test_method_one(self): 
                    assert 42 == 43 
        """)
        def check(keyword, name):
            sorter = self.parse_and_run("-s", "-k", keyword, file_test)
            passed, skipped, failed = sorter.listoutcomes()
            assert len(failed) == 1
            assert failed[0].colitem.name == name 
            assert len(sorter.get(event.Deselected)) == 1

        for keyword in ['test_one', 'est_on']:
            yield check, keyword, 'test_one'
        yield check, 'TestClass.test', 'test_method_one'

    def test_select_extra_keywords(self):
        o = self.tmpdir
        tfile = o.join('test_select.py').write(py.code.Source("""
            def test_1():
                pass 
            class TestClass: 
                def test_2(self): 
                    pass
        """))
        conftest = o.join('conftest.py').write(py.code.Source("""
            import py
            class Class(py.test.collect.Class): 
                def _keywords(self):
                    return ['xxx', self.name]
        """))
        for keyword in ('xxx', 'xxx test_2', 'TestClass', 'xxx -test_1', 
                        'TestClass test_2', 'xxx TestClass test_2',): 
            sorter = suptest.events_from_cmdline([o, '-s', '-k', keyword])
            print "keyword", repr(keyword)
            passed, skipped, failed = sorter.listoutcomes()
            assert len(passed) == 1
            assert passed[0].colitem.name == "test_2"
            dlist = sorter.get(event.Deselected)
            assert len(dlist) == 1
            assert dlist[0].items[0].name == 'test_1'

    def test_select_starton(self):
        threepass = self.makepyfile(test_threepass="""
            def test_one(): assert 1
            def test_two(): assert 1
            def test_three(): assert 1
        """)
        sorter = self.parse_and_run("-k", "test_two:", threepass)
        passed, skipped, failed = sorter.listoutcomes()
        assert len(passed) == 2
        assert not failed 
        dlist = sorter.get(event.Deselected)
        assert len(dlist) == 1
        item = dlist[0].items[0]
        assert item.name == "test_one" 

class SessionTests(suptest.InlineCollection):
    def events_from_cmdline(self, *args):
        paths = [p for p in args if isinstance(p, py.path.local)]
        if not paths:
            args = (self.tmpdir,) + args
        config = self.parseconfig(*args)
        self.session = config.initsession()
        self.sorter = suptest.EventSorter(config, self.session)
        self.session.main()
        return self.sorter

    def events_from_runsource(self, source, *args):
        p = self.makepyfile(test_source=source)
        return self.events_from_cmdline(p, *args)

    def makepyfile(self, *args, **kw):
        self.tmpdir.ensure('__init__.py')
        return super(SessionTests, self).makepyfile(*args, **kw)

    def test_basic_testitem_events(self):
        tfile = self.makepyfile(test_one="""
            def test_one(): 
                pass
            def test_one_one():
                assert 0
            def test_other():
                raise ValueError(23)
            def test_two(someargs):
                pass
        """)
        sorter = self.events_from_cmdline(tfile)
        passed, skipped, failed = sorter.listoutcomes()
        assert len(skipped) == 0
        assert len(passed) == 1
        assert len(failed) == 3  
        assert failed[0].colitem.name == "test_one_one"
        assert failed[1].colitem.name == "test_other"
        assert failed[2].colitem.name == "test_two"
        itemstarted = sorter.get(event.ItemStart)
        assert len(itemstarted) == 4
        colstarted = sorter.get(event.CollectionStart)
        assert len(colstarted) == 1
        col = colstarted[0].collector
        assert isinstance(col, py.test.collect.Module)

    def test_nested_import_error(self): 
        tfile = self.makepyfile(test_one="""
            import import_fails
            def test_this():
                assert import_fails.a == 1
        """, import_fails="""
            import does_not_work 
            a = 1
        """)
        sorter = self.events_from_cmdline()
        l = sorter.getfailedcollections()
        assert len(l) == 1 
        out = l[0].outcome.longrepr.reprcrash.message
        assert out.find('does_not_work') != -1 

    def test_raises_output(self): 
        self.makepyfile(test_one="""
            import py
            def test_raises_doesnt():
                py.test.raises(ValueError, int, "3")
        """)
        sorter = self.events_from_cmdline()
        passed, skipped, failed = sorter.listoutcomes()
        assert len(failed) == 1
        out = failed[0].outcome.longrepr.reprcrash.message
        if not out.find("DID NOT RAISE") != -1: 
            print out
            py.test.fail("incorrect raises() output") 

    def test_generator_yields_None(self): 
        sorter = self.events_from_runsource("""
            def test_1():
                yield None 
        """)
        failures = sorter.getfailedcollections()
        out = failures[0].outcome.longrepr.reprcrash.message
        i = out.find('TypeError') 
        assert i != -1 

    def test_syntax_error_module(self): 
        sorter = self.events_from_runsource("this is really not python")
        l = sorter.getfailedcollections()
        assert len(l) == 1
        out = l[0].outcome.longrepr.reprcrash.message
        assert out.find(str('not python')) != -1

    def test_exit_first_problem(self): 
        sorter = self.events_from_runsource("""
            def test_one(): assert 0
            def test_two(): assert 0
        """, '--exitfirst')
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 1
        assert passed == skipped == 0

    def test_broken_repr(self):
        self.makepyfile(test_broken="""
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
        sorter = self.events_from_cmdline()
        passed, skipped, failed = sorter.listoutcomes()
        assert len(failed) == 2
        out = failed[0].outcome.longrepr.reprcrash.message
        assert out.find("""[Exception("Ha Ha fooled you, I'm a broken repr().") raised in repr()]""") != -1 #'
        out = failed[1].outcome.longrepr.reprcrash.message
        assert (out.find("[unknown exception raised in repr()]") != -1  or
                out.find("TypeError") != -1)

    def test_skip_by_conftest_directory(self):
        from py.__.test import outcome
        self.makepyfile(conftest="""
            import py
            class Directory(py.test.collect.Directory):
                def collect(self):
                    py.test.skip("intentional")
        """, test_file="""
            def test_one(): pass
        """)
        sorter = self.events_from_cmdline()
        skips = sorter.get(event.CollectionReport)
        assert len(skips) == 1
        assert skips[0].skipped 

class TestNewSession(SessionTests):
    def test_pdb_run(self):
        tfile = self.makepyfile(test_one="""
            def test_usepdb(): 
                assert 0
        """)
        l = []
        def mypdb(*args):
            l.append(args)
        py.magic.patch(py.__.test.custompdb, 'post_mortem', mypdb)
        try:
            sorter = self.events_from_cmdline('--pdb')
        finally:
            py.magic.revert(py.__.test.custompdb, 'post_mortem')
        rep = sorter.getreport("test_usepdb")
        assert rep.failed
        assert len(l) == 1
        tb = py.code.Traceback(l[0][0])
        assert tb[-1].name == "test_usepdb" 

    def test_order_of_execution(self): 
        sorter = self.events_from_runsource("""
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

    def test_collect_only_with_various_situations(self):
        p = self.makepyfile(
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
            test_three="xxxdsadsadsadsa"
        )
        sorter = self.events_from_cmdline('--collectonly')
       
        itemstarted = sorter.get(event.ItemStart)
        assert len(itemstarted) == 3
        assert not sorter.get(event.ItemTestReport) 
        started = sorter.get(event.CollectionStart)
        finished = sorter.get(event.CollectionReport)
        assert len(started) == len(finished) 
        assert len(started) == 8 
        colfail = [x for x in finished if x.failed]
        colskipped = [x for x in finished if x.skipped]
        assert len(colfail) == 1
        assert len(colskipped) == 1

class TestNewSessionDSession(SessionTests):
    def parseconfig(self, *args):
        args = ('-n1',) + args
        return SessionTests.parseconfig(self, *args)
    
