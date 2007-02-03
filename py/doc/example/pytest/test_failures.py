
import py
failure_demo = py.magic.autopath().dirpath('failure_demo.py')
from py.__.test.outcome import Failed, Passed

def test_failure_demo_fails_properly(): 
    config = py.test.config._reparse([failure_demo]) 
    session = config.initsession()
    session.main()
    l = session.getitemoutcomepairs(Failed)
    assert len(l) == 21 
    l = session.getitemoutcomepairs(Passed)
    assert not l 
