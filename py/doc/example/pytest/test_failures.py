
import py
failure_demo = py.magic.autopath().dirpath('failure_demo.py')
from py.__.doc.test_conftest import countoutcomes 

def test_failure_demo_fails_properly(): 
    config = py.test.config._reparse([failure_demo]) 
    session = config.initsession()
    failed, passed, skipped = countoutcomes(session) 
    assert failed == 21 
    assert passed == 0 
