""" test reporting functionality. """

import py
from py.__.test.rsession import repevent 

def test_wrapcall_ok():
    l = []
    def ok(x):
        return x+1
    i = repevent.wrapcall(l.append, ok, 1)
    assert i == 2
    assert len(l) == 2
    assert isinstance(l[0], repevent.CallStart) 
    assert isinstance(l[1], repevent.CallFinish) 
    assert repr(l[0]) 
    assert repr(l[1]) 

def test_wrapcall_exception():
    l = []
    def fail(x):
        raise ValueError
    py.test.raises(ValueError, "repevent.wrapcall(l.append, fail, 1)")
    assert len(l) == 2
    assert isinstance(l[0], repevent.CallStart) 
    assert isinstance(l[1], repevent.CallException) 

def test_reporter_methods_sanity():
    """ Checks if all the methods of reporter are sane
    """
    from py.__.test.rsession.rsession import RemoteReporter
    from py.__.test.rsession import repevent
    
    for method in dir(RemoteReporter):
        
        if method.startswith("report_") and method != "report_unknown":
            assert method[len('report_'):] in repevent.__dict__
