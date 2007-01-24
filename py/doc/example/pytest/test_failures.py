
import py
failure_demo = py.magic.autopath().dirpath('failure_demo.py')

def test_failure_demo_fails_properly(): 
    config = py.test.config._reparse([failure_demo]) 
    session = config.initsession()
    session.main()
    l = session.getitemoutcomepairs(py.test.Item.Failed)
    assert len(l) == 21 
    l = session.getitemoutcomepairs(py.test.Item.Passed)
    assert not l 
