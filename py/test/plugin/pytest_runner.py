import py
from py.__.test.outcome import Skipped
from py.__.test.runner import SetupState

py.test.skip("remove me")

def pytest_configure(config):
    config._setupstate = SetupState()

def pytest_unconfigure(config):
    config._setupstate.teardown_all()

def pytest_item_setup_and_runtest(item):
    setupstate = item.config._setupstate

    # setup (and implied teardown of previous items) 
    call = item.config.guardedcall(lambda: setupstate.prepare(item))
    if call.excinfo:
        rep = ItemTestReport(item, call.excinfo, call.outerr)
        item.config.hook.pytest_itemfixturereport(rep=rep)
        return

    # runtest 
    call = item.config.guardedcall(lambda: item.runtest())
    item.config.hook.pytest_item_runtest_finished(
        item=item, excinfo=call.excinfo, outerr=call.outerr)

    # teardown 
    call = item.config.guardedcall(lambda: setupstate.teardown_exact(item))
    if call.excinfo:
        rep = ItemFixtureReport(item, call.excinfo, call.outerr)
        item.config.hook.pytest_itemfixturereport(rep=rep)

def pytest_collector_collect(collector):
    call = item.config.guardedcall(lambda x: collector._memocollect())
    return CollectReport(collector, res, excinfo, outerr)

class BaseReport(object):
    def __repr__(self):
        l = ["%s=%s" %(key, value)
           for key, value in self.__dict__.items()]
        return "<%s %s>" %(self.__class__.__name__, " ".join(l),)

    def toterminal(self, out):
        longrepr = self.longrepr 
        if hasattr(longrepr, 'toterminal'):
            longrepr.toterminal(out)
        else:
            out.line(str(longrepr))
   
class ItemTestReport(BaseReport):
    failed = passed = skipped = False

    def __init__(self, colitem, excinfo=None, when=None, outerr=None):
        self.colitem = colitem 
        if colitem and when != "setup":
            self.keywords = colitem.readkeywords() 
        else:
            # if we fail during setup it might mean 
            # we are not able to access the underlying object
            # this might e.g. happen if we are unpickled 
            # and our parent collector did not collect us 
            # (because it e.g. skipped for platform reasons)
            self.keywords = {}  
        if not excinfo:
            self.passed = True
            self.shortrepr = "." 
        else:
            self.when = when 
            if not isinstance(excinfo, py.code.ExceptionInfo):
                self.failed = True
                shortrepr = "?"
                longrepr = excinfo 
            elif excinfo.errisinstance(Skipped):
                self.skipped = True 
                shortrepr = "s"
                longrepr = self.colitem._repr_failure_py(excinfo, outerr)
            else:
                self.failed = True
                shortrepr = self.colitem.shortfailurerepr
                if self.when == "execute":
                    longrepr = self.colitem.repr_failure(excinfo, outerr)
                else: # exception in setup or teardown 
                    longrepr = self.colitem._repr_failure_py(excinfo, outerr)
                    shortrepr = shortrepr.lower()
            self.shortrepr = shortrepr 
            self.longrepr = longrepr 
            

class CollectReport(BaseReport):
    skipped = failed = passed = False 

    def __init__(self, colitem, result, excinfo=None, outerr=None):
        # XXX rename to collector 
        self.colitem = colitem 
        if not excinfo:
            self.passed = True
            self.result = result 
        else:
            self.outerr = outerr
            self.longrepr = self.colitem._repr_failure_py(excinfo, outerr)
            if excinfo.errisinstance(Skipped):
                self.skipped = True
                self.reason = str(excinfo.value)
            else:
                self.failed = True

class ItemFixtureReport(BaseReport):
    failed = passed = skipped = False
    def __init__(self, item, excinfo=None, outerr=None):
        self.item = item 
        self.outerr = outerr 
        if not excinfo:
            self.passed = True
        else:
            if excinfo.errisinstance(Skipped):
                self.skipped = True 
            else:
                self.failed = True
            self.excrepr = item._repr_failure_py(excinfo, [])


# ===============================================================================
#
# plugin tests 
#
# ===============================================================================

def test_generic(plugintester):
    plugintester.hookcheck()

class TestSetupState:
    def test_setup_prepare(self, testdir):
        modcol = testdir.getmodulecol("""
            def setup_function(function):
                function.myfunc = function
            def test_func1():
                pass
            def test_func2():
                pass
            def teardown_function(function):
                del function.myfunc 
        """)
        item1, item2 = modcol.collect()
        setup = SetupState()
        setup.prepare(item1)
        assert item1.obj.myfunc == item1.obj 
        assert not hasattr(item2, 'myfunc')

        setup.prepare(item2)
        assert item2.obj.myfunc == item2.obj 
        assert not hasattr(item1, 'myfunc')

    def test_setup_teardown_exact(self, testdir):
        item = testdir.getitem("""
            def test_func():
                pass
            def teardown_function(function):
                function.tear = "down"
        """)
        setup = SetupState()
        setup.prepare(item)
        setup.teardown_exact(item)
        assert item.obj.tear == "down"

    def test_setup_teardown_exact(self, testdir):
        item = testdir.getitem("""
            def setup_module(mod):
                mod.x = 1
            def setup_function(function):
                function.y = 2
            def test_func():
                pass
            def teardown_function(function):
                del function.y
            def teardown_module(mod):
                del mod.x
        """)
        setup = SetupState()
        setup.prepare(item)
        assert item.obj.y == 2
        assert item.parent.obj.x == 1
        setup.teardown_all()
        assert not hasattr(item.obj, 'y')
        assert not hasattr(item.parent.obj, 'x')

class TestRunnerPlugin:
    def test_pytest_item_setup_and_runtest(self, testdir):
        item = testdir.getitem("""def test_func(): pass""")
        pytest_configure(item.config)
        reprec = testdir.getreportrecorder(item)
        pytest_item_setup_and_runtest(item)
        rep = reprec.getcall("pytest_itemtestreport").rep
        assert rep.passed 
       
class TestSetupEvents:
    def pytest_funcarg__runfunc(self, request):
        testdir = request.getfuncargvalue("testdir")
        def runfunc(source):
            item = testdir.getitem(source)
            reprec = testdir.getreportrecorder(item)
            pytest_item_setup_and_runtest(item)
            return reprec 
        return runfunc
        
    def test_setup_runtest_ok(self, runfunc):
        reprec = runfunc("""
            def setup_module(mod):
                pass 
            def test_func():
                pass
        """)
        assert not reprec.getcalls("pytest_itemfixturereport")

    def test_setup_fails(self, runfunc):
        reprec = runfunc(""" 
            def setup_module(mod):
                print "world"
                raise ValueError(42)
            def test_func():
                pass
        """)
        rep = reprec.popcall("pytest_itemfixturereport").rep
        assert rep.failed
        assert not rep.skipped
        assert rep.excrepr 
        assert "42" in str(rep.excrepr)
        assert rep.outerr[0].find("world") != -1

    def test_teardown_fails(self, runfunc):
        reprec = runfunc(""" 
            def test_func():
                pass
            def teardown_function(func): 
                print "13"
                raise ValueError(25)
        """)
        rep = reprec.popcall("pytest_itemfixturereport").rep 
        assert rep.failed 
        assert rep.item.name == "test_func" 
        assert not rep.passed
        assert "13" in rep.outerr[0]
        assert "25" in str(rep.excrepr)

    def test_setup_skips(self, runfunc):
        reprec = runfunc(""" 
            import py
            def setup_module(mod):
                py.test.skip("17")
            def test_func():
                pass
        """)
        rep = reprec.popcall("pytest_itemfixturereport").rep
        assert not rep.failed
        assert rep.skipped
        assert rep.excrepr 
        assert "17" in str(rep.excrepr)
