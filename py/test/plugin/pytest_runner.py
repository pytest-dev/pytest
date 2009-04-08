import py
from py.__.test.outcome import Skipped

class RunnerPlugin:
    def pytest_configure(self, config):
        config._setupstate = SetupState()

    def pytest_unconfigure(self, config):
        config._setupstate.teardown_all()

    def pytest_item_setup_and_runtest(self, item):
        setupstate = item.config._setupstate
        call = item.config.guardedcall(lambda: setupstate.prepare(item))
        rep = ItemSetupReport(item, call.excinfo, call.outerr)
        if call.excinfo:
            item.config.pytestplugins.notify("itemsetupreport", rep)
        else:
            call = item.config.guardedcall(lambda: item.runtest())
            item.config.api.pytest_item_runtest_finished(
                item=item, excinfo=call.excinfo, outerr=call.outerr)
            call = item.config.guardedcall(lambda: self.teardown_exact(item))
            if call.excinfo:
                rep = ItemSetupReport(item, call.excinfo, call.outerr)
                item.config.pytestplugins.notify("itemsetupreport", rep)

    def pytest_collector_collect(self, collector):
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

class ItemSetupReport(BaseReport):
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

class SetupState(object):
    """ shared state for setting up/tearing down test items or collectors. """
    def __init__(self):
        self.stack = []

    def teardown_all(self): 
        while self.stack: 
            col = self.stack.pop() 
            col.teardown() 

    def teardown_exact(self, item):
        if self.stack and self.stack[-1] == item:
            col = self.stack.pop()
            col.teardown()
     
    def prepare(self, colitem): 
        """ setup objects along the collector chain to the test-method
            Teardown any unneccessary previously setup objects."""
        needed_collectors = colitem.listchain() 
        while self.stack: 
            if self.stack == needed_collectors[:len(self.stack)]: 
                break 
            col = self.stack.pop() 
            col.teardown()
        for col in needed_collectors[len(self.stack):]: 
            col.setup() 
            self.stack.append(col) 

# ===============================================================================
#
# plugin tests 
#
# ===============================================================================

def test_generic(plugintester):
    plugintester.apicheck(RunnerPlugin())

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
        plugin = RunnerPlugin()
        plugin.pytest_configure(item.config)
        sorter = testdir.geteventrecorder(item.config)
        plugin.pytest_item_setup_and_runtest(item)
        rep = sorter.getcall("itemtestreport").rep
        assert rep.passed 
        
class TestSetupEvents:
    disabled = True

    def test_setup_runtest_ok(self, testdir):
        sorter = testdir.inline_runsource("""
            def setup_module(mod):
                pass 
            def test_func():
                pass
        """)
        assert not sorter.getcalls("itemsetupreport")

    def test_setup_fails(self, testdir):
        sorter = testdir.inline_runsource("""
            def setup_module(mod):
                print "world"
                raise ValueError(42)
            def test_func():
                pass
        """)
        rep = sorter.popcall("itemsetupreport").rep
        assert rep.failed
        assert not rep.skipped
        assert rep.excrepr 
        assert "42" in str(rep.excrepr)
        assert rep.outerr[0].find("world") != -1

    def test_teardown_fails(self, testdir):
        sorter = testdir.inline_runsource("""
            def test_func():
                pass
            def teardown_function(func): 
                print "13"
                raise ValueError(25)
        """)
        rep = evrec.popcall("itemsetupreport").rep 
        assert rep.failed 
        assert rep.item == item 
        assert not rep.passed
        assert "13" in rep.outerr[0]
        assert "25" in str(rep.excrepr)

    def test_setup_skips(self, testdir):
        sorter = testdir.inline_runsource("""
            import py
            def setup_module(mod):
                py.test.skip("17")
            def test_func():
                pass
        """)
        rep = sorter.popcall("itemsetupreport")
        assert not rep.failed
        assert rep.skipped
        assert rep.excrepr 
        assert "17" in str(rep.excrepr)
    

