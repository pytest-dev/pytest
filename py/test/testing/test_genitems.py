import py

class Test_genitems: 
    def test_check_collect_hashes(self, testdir):
        p = testdir.makepyfile("""
            def test_1():
                pass

            def test_2():
                pass
        """)
        p.copy(p.dirpath(p.purebasename + "2" + ".py"))
        items, events = testdir.inline_genitems(p.dirpath())
        assert len(items) == 4
        for numi, i in enumerate(items):
            for numj, j in enumerate(items):
                if numj != numi:
                    assert hash(i) != hash(j)
                    assert i != j
       
    def test_root_conftest_syntax_error(self, testdir):
        # do we want to unify behaviour with
        # test_subdir_conftest_error? 
        p = testdir.makepyfile(conftest="raise SyntaxError\n")
        py.test.raises(SyntaxError, testdir.inline_genitems, p.dirpath())
       
    def test_subdir_conftest_error(self, testdir):
        tmp = testdir.tmpdir
        tmp.ensure("sub", "conftest.py").write("raise SyntaxError\n")
        items, events = testdir.inline_genitems(tmp)
        collectionfailures = events.getfailedcollections()
        assert len(collectionfailures) == 1
        ev = collectionfailures[0] 
        assert ev.longrepr.reprcrash.message.startswith("SyntaxError")

    def test_example_items1(self, testdir):
        p = testdir.makepyfile('''
            def testone():
                pass

            class TestX:
                def testmethod_one(self):
                    pass

            class TestY(TestX):
                pass
        ''')
        items, events = testdir.inline_genitems(p)
        assert len(items) == 3
        assert items[0].name == 'testone'
        assert items[1].name == 'testmethod_one'
        assert items[2].name == 'testmethod_one'

        # let's also test getmodpath here
        assert items[0].getmodpath() == "testone"
        assert items[1].getmodpath() == "TestX.testmethod_one"
        assert items[2].getmodpath() == "TestY.testmethod_one"

        s = items[0].getmodpath(stopatmodule=False)
        assert s.endswith("test_example_items1.testone")
        print s


class TestKeywordSelection:
    def test_select_simple(self, testdir):
        file_test = testdir.makepyfile("""
            def test_one(): assert 0
            class TestClass(object): 
                def test_method_one(self): 
                    assert 42 == 43 
        """)
        def check(keyword, name):
            sorter = testdir.inline_run("-s", "-k", keyword, file_test)
            passed, skipped, failed = sorter.listoutcomes()
            assert len(failed) == 1
            assert failed[0].colitem.name == name 
            assert len(sorter.getcalls('deselected')) == 1

        for keyword in ['test_one', 'est_on']:
            #yield check, keyword, 'test_one'
            check(keyword, 'test_one')
        check('TestClass.test', 'test_method_one')

    def test_select_extra_keywords(self, testdir):
        p = testdir.makepyfile(test_select="""
            def test_1():
                pass 
            class TestClass: 
                def test_2(self): 
                    pass
        """)
        testdir.makepyfile(conftest="""
            import py
            class Class(py.test.collect.Class): 
                def _keywords(self):
                    return ['xxx', self.name]
        """)
        for keyword in ('xxx', 'xxx test_2', 'TestClass', 'xxx -test_1', 
                        'TestClass test_2', 'xxx TestClass test_2',): 
            sorter = testdir.inline_run(p.dirpath(), '-s', '-k', keyword)
            print "keyword", repr(keyword)
            passed, skipped, failed = sorter.listoutcomes()
            assert len(passed) == 1
            assert passed[0].colitem.name == "test_2"
            dlist = sorter.getcalls("deselected")
            assert len(dlist) == 1
            assert dlist[0].items[0].name == 'test_1'

    def test_select_starton(self, testdir):
        threepass = testdir.makepyfile(test_threepass="""
            def test_one(): assert 1
            def test_two(): assert 1
            def test_three(): assert 1
        """)
        sorter = testdir.inline_run("-k", "test_two:", threepass)
        passed, skipped, failed = sorter.listoutcomes()
        assert len(passed) == 2
        assert not failed 
        dlist = sorter.getcalls("deselected")
        assert len(dlist) == 1
        item = dlist[0].items[0]
        assert item.name == "test_one" 

