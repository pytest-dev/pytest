import os, StringIO

import py

from py.__.test import resultlog
from py.__.test.collect import Node, Item, FSCollector
from py.__.test.event import EventBus
from py.__.test.event import ItemTestReport, CollectionReport
from py.__.test.event import InternalException
from py.__.test.runner import OutcomeRepr


class Fake(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


def test_generic_path():
    p1 = Node('a', config='dummy')
    assert p1.fspath is None
    p2 = Node('B', parent=p1)
    p3 = Node('()', parent = p2)
    item = Item('c', parent = p3)

    res = resultlog.generic_path(item)
    assert res == 'a.B().c'

    p0 = FSCollector('proj/test', config='dummy')
    p1 = FSCollector('proj/test/a', parent=p0)
    p2 = Node('B', parent=p1)
    p3 = Node('()', parent = p2)
    p4 = Node('c', parent=p3)
    item = Item('[1]', parent = p4)

    res = resultlog.generic_path(item)
    assert res == 'test/a:B().c[1]'


def make_item(*names):
    node = None
    config = "dummy"
    for name in names[:-1]:
        if '/' in name:
            node = FSCollector(name, parent=node, config=config)
        else:
            node = Node(name, parent=node, config=config)
    if names[-1] is None:
        return node
    return Item(names[-1], parent=node)

class TestResultLog(object):

    def test_create(self):
        bus = EventBus()
        logfile = object()
        
        reslog = resultlog.ResultLog(bus, logfile)
        assert len(bus._subscribers) == 1
        assert reslog.logfile is logfile

    def test_write_log_entry(self):
        reslog = resultlog.ResultLog(EventBus(), None)

        reslog.logfile = StringIO.StringIO()
        reslog.write_log_entry('.', 'name', '')  
        entry = reslog.logfile.getvalue()
        assert entry[-1] == '\n'        
        entry_lines = entry.splitlines()
        assert len(entry_lines) == 1
        assert entry_lines[0] == '. name'

        reslog.logfile = StringIO.StringIO()
        reslog.write_log_entry('s', 'name', 'Skipped')  
        entry = reslog.logfile.getvalue()
        assert entry[-1] == '\n'        
        entry_lines = entry.splitlines()
        assert len(entry_lines) == 2
        assert entry_lines[0] == 's name'
        assert entry_lines[1] == ' Skipped'

        reslog.logfile = StringIO.StringIO()
        reslog.write_log_entry('s', 'name', 'Skipped\n')  
        entry = reslog.logfile.getvalue()
        assert entry[-1] == '\n'        
        entry_lines = entry.splitlines()
        assert len(entry_lines) == 2
        assert entry_lines[0] == 's name'
        assert entry_lines[1] == ' Skipped'

        reslog.logfile = StringIO.StringIO()
        longrepr = ' tb1\n tb 2\nE tb3\nSome Error'
        reslog.write_log_entry('F', 'name', longrepr)
        entry = reslog.logfile.getvalue()
        assert entry[-1] == '\n'        
        entry_lines = entry.splitlines()
        assert len(entry_lines) == 5
        assert entry_lines[0] == 'F name'
        assert entry_lines[1:] == [' '+line for line in longrepr.splitlines()]
    
    def test_log_outcome(self):
        reslog = resultlog.ResultLog(EventBus(), StringIO.StringIO())

        colitem = make_item('some', 'path', 'a', 'b')

        try:
            raise ValueError
        except ValueError:
            the_repr = py.code.ExceptionInfo().getrepr()

        outcome=OutcomeRepr('execute', 'F', the_repr)
        ev = Fake(colitem=colitem, outcome=outcome)

        reslog.log_outcome(ev)

        entry = reslog.logfile.getvalue()
        entry_lines = entry.splitlines()

        assert entry_lines[0] == 'F some.path.a.b'
        assert entry_lines[-1][0] == ' '
        assert 'ValueError' in entry

    def test_item_test_passed(self):
        bus = EventBus()
        reslog = resultlog.ResultLog(bus, StringIO.StringIO())

        colitem = make_item('proj/test', 'proj/test/mod', 'a', 'b')

        outcome=OutcomeRepr('execute', '.', '')
        rep_ev = ItemTestReport(colitem, passed=outcome)

        bus.notify(rep_ev)

        lines = reslog.logfile.getvalue().splitlines()
        assert len(lines) == 1
        line = lines[0]
        assert line.startswith(". ")
        assert line[2:] == 'test/mod:a.b'

    def test_collection_report(self):
        bus = EventBus()        
        reslog = resultlog.ResultLog(bus, None)

        reslog.logfile = StringIO.StringIO()
        colitem = make_item('proj/test', 'proj/test/mod', 'A', None)
        outcome=OutcomeRepr('execute', '', '')
        rep_ev = CollectionReport(colitem, object(), passed=outcome)

        bus.notify(rep_ev)

        entry = reslog.logfile.getvalue()
        assert not entry

        reslog.logfile = StringIO.StringIO()
        outcome=OutcomeRepr('execute', 'F', 'Some Error')
        rep_ev = CollectionReport(colitem, object(), failed=outcome)        

        bus.notify(rep_ev)

        lines = reslog.logfile.getvalue().splitlines()        
        assert len(lines) == 2
        assert lines[0] == 'F test/mod:A'

    def test_internal_exception(self):
        # they are produced for example by a teardown failing
        # at the end of the run
        bus = EventBus()
        reslog = resultlog.ResultLog(bus, StringIO.StringIO())        

        try:
            raise ValueError
        except ValueError:
            excinfo = py.code.ExceptionInfo()

        internal = InternalException(excinfo)

        bus.notify(internal)

        entry = reslog.logfile.getvalue()
        entry_lines = entry.splitlines()

        assert entry_lines[0].startswith('! ')
        assert os.path.basename(__file__)[:-1] in entry_lines[0] #.py/.pyc
        assert entry_lines[-1][0] == ' '
        assert 'ValueError' in entry  
