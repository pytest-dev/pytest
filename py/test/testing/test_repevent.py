
from py.__.test import event 
import setupdata, suptest
from py.__.code.testing.test_excinfo import TWMock



class TestItemTestReport(object):

    def test_toterminal(self):
        sorter = suptest.events_run_example("file_test.py")
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
        assert str(filepath).endswith("file_test.py")
        #assert modpath.endswith("file_test.test_one")
        

