from __future__ import generators
from py.__.test.tkinter import util 
from py.__.test.tkinter.util import Status, TestReport, OutBuffer
import py
Item = py.test.Item

class TestStatus:

    def test_init_with_None(self):
        status = Status(None)
        assert status == status.NotExecuted()

    def test_str(self):
        status = Status(Item.Passed())
        assert status == status.Passed()

        status = Status(Item.Failed())
        assert status == status.Failed()

        status = Status(Item.Skipped())
        assert status == status.Skipped()


    def test_init_with_bad_name(self):
        status = Status('nothing')
        assert status == Status.NotExecuted()

    def test_init_with_good_name(self):
        def check_str(obj, expected):
            assert str(obj) == expected
            
        for name in Status.ordered_list:
            yield check_str, Status(name), name

    def test_update(self):
        failed = Status.Failed()
        passed = Status.Passed()
        failed.update(passed)
        assert failed == Status.Failed()

        passed.update(failed)
        assert passed == Status.Failed()
        assert passed == failed

    def test_eq_(self):
        passed = Status.Passed()
        assert passed == passed
        assert passed == Status.Passed()

        failed = Status.Failed()
        assert failed != passed


class TestTestReport:

    def setup_method(self, method):
        self.path = py.path.local()
        self.collector = py.test.collect.Directory(self.path)
        self.testresult = TestReport()
        
    def test_start(self):
        self.testresult.start(self.collector)

        assert self.testresult.full_id == tuple(self.collector.listnames())
        assert self.testresult.time != 0
        assert self.testresult.status == Status.NotExecuted()

    def test_finish(self):
        self.testresult.start(self.collector)

        py.std.time.sleep(1.1)

        self.testresult.finish(self.collector, None)
        assert self.testresult.time > 1
        assert self.testresult.status == Status.NotExecuted()
        
        
    def test_toChannel_fromChannel(self):
        assert isinstance(self.testresult.to_channel()['status'], str)
        result = TestReport.fromChannel(self.testresult.to_channel())
        assert isinstance(result.status, Status)

    def test_copy(self):
        result2 = self.testresult.copy()
        assert self.testresult.status == Status.NotExecuted()
        for key in TestReport.template.keys():
            assert getattr(result2, key) == getattr(self.testresult, key)

        self.testresult.status = Status.Failed()
        assert result2.status != self.testresult.status

    def test_is_item_attribute(self):
        self.testresult.start(py.test.Item('test_is_item_attribute item',
                                           parent = self.collector))
        assert self.testresult.is_item == True
        self.testresult.start(self.collector)
        assert self.testresult.is_item == False
            
class Test_OutBuffer:

    def setup_method(self, method):
        self.out = OutBuffer()

    def test_line(self):
        oneline = 'oneline'
        self.out.line(oneline)
        assert self.out.getoutput() == oneline + '\n'

    def test_write(self):
        item = 'item'
        self.out.write(item)
        assert self.out.getoutput() == item

    
