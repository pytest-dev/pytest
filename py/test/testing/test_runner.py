
from py.__.test.config import SetupState

class TestSetupState:
    disabled = True
    def test_setup_ok(self, testdir):
        item = testdir.getitem("""
            def setup_module(mod):
                pass 
            def test_func():
                pass
        """)
        evrec = testdir.geteventrecorder(item.config)
        setup = SetupState()
        res = setup.do_setup(item)
        assert res

    def test_setup_fails(self, testdir):
        item = testdir.getitem("""
            def setup_module(mod):
                print "world"
                raise ValueError(42)
            def test_func():
                pass
        """)
        evrec = testdir.geteventrecorder(item.config)
        setup = SetupState()
        res = setup.do_setup(item)
        assert not res
        rep = evrec.popcall("itemsetupreport").rep
        assert rep.failed
        assert not rep.skipped
        assert rep.excrepr 
        assert "42" in str(rep.excrepr)
        assert rep.outerr[0].find("world") != -1

    def test_teardown_fails(self, testdir):
        item = testdir.getitem("""
            def test_func():
                pass
            def teardown_function(func): 
                print "13"
                raise ValueError(25)
        """)
        evrec = testdir.geteventrecorder(item.config)
        setup = SetupState()
        res = setup.do_setup(item)
        assert res 
        rep = evrec.popcall("itemsetupreport").rep
        assert rep.passed
        setup.do_teardown(item)
        rep = evrec.popcall("itemsetupreport").rep
        assert rep.item == item 
        assert rep.failed 
        assert not rep.passed
        assert "13" in rep.outerr[0]
        assert "25" in str(rep.excrepr)

    def test_setupitem_skips(self, testdir):
        item = testdir.getitem("""
            import py
            def setup_module(mod):
                py.test.skip("17")
            def test_func():
                pass
        """)
        evrec = testdir.geteventrecorder(item.config)
        setup = SetupState()
        setup.do_setup(item)
        rep = evrec.popcall("itemsetupreport").rep
        assert not rep.failed
        assert rep.skipped
        assert rep.excrepr 
        assert "17" in str(rep.excrepr)

    def test_runtest_ok(self, testdir):
        item = testdir.getitem("def test_func(): pass")
        evrec = testdir.geteventrecorder(item.config)
        setup = SetupState()
        setup.do_fixture_and_runtest(item)
        rep = evrec.popcall("itemtestreport").rep 
        assert rep.passed 

    def test_runtest_fails(self, testdir):
        item = testdir.getitem("def test_func(): assert 0")
        evrec = testdir.geteventrecorder(item.config)
        setup = SetupState()
        setup.do_fixture_and_runtest(item)
        event = evrec.popcall("item_runtest_finished")
        assert event.excinfo 
        
    
