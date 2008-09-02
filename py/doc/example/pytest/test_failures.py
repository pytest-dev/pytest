
import py
failure_demo = py.magic.autopath().dirpath('failure_demo.py')

from py.__.test.testing import suptest
from py.__.test import event

def test_failure_demo_fails_properly(): 
    sorter = suptest.events_from_cmdline([failure_demo]) 
    passed, skipped, failed = sorter.countoutcomes() 
    assert passed == 0 
    assert failed == 20, failed
    colreports = sorter.get(event.CollectionReport)
    failed = len([x.failed for x in colreports])
    assert failed == 5
