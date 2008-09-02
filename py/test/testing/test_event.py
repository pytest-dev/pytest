import py
from py.__.test.event import EventBus
from py.__.test import event 
import suptest
from py.__.code.testing.test_excinfo import TWMock

class TestEventBus:
    def test_simple(self):
        bus = EventBus()
        l = []
        bus.subscribe(l.append) 
        bus.notify(1)
        bus.notify(2)
        bus.notify(3)
        assert l == [1,2,3]

    def test_multi_sub(self):
        bus = EventBus()
        l1 = []
        l2 = []
        bus.subscribe(l1.append) 
        bus.subscribe(l2.append) 
        bus.notify(1)
        bus.notify(2)
        bus.notify(3)
        assert l1 == [1,2,3]
        assert l2 == [1,2,3]

    def test_remove(self):
        bus = EventBus()
        l = []
        bus.subscribe(l.append) 
        bus.notify(1)
        bus.unsubscribe(l.append) 
        bus.notify(2)
        assert l == [1]


class TestItemTestReport(suptest.InlineCollection):
    def test_toterminal(self):
        sorter = suptest.events_from_runsource("""
            def test_one(): 
                assert 42 == 43
        """)
        reports = sorter.get(event.ItemTestReport)
        ev = reports[0] 
        assert ev.failed 
        twmock = TWMock()
        ev.toterminal(twmock)
        assert twmock.lines
        twmock = TWMock()
        ev.outcome.longrepr = "hello"
        ev.toterminal(twmock)
        assert twmock.lines[0] == "hello"
        assert not twmock.lines[1:]

        ##assert ev.repr_run.find("AssertionError") != -1
        filepath = ev.colitem.fspath
        #filepath , modpath = ev.itemrepr_path
        assert str(filepath).endswith(".py")
        #assert modpath.endswith("file_test.test_one")
