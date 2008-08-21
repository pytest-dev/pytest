
import py
from py.__.code import safe_repr

def test_simple_repr():
    assert safe_repr._repr(1) == '1'
    assert safe_repr._repr(None) == 'None'
    
class BrokenRepr:
    def __init__(self, ex):
        self.ex = ex
        foo = 0
    def __repr__(self):
        raise self.ex
        
def test_exception():
    assert 'Exception' in safe_repr._repr(BrokenRepr(Exception("broken")))

class BrokenReprException(Exception):
    __str__ = None 
    __repr__ = None
    
def test_broken_exception():
    assert 'Exception' in safe_repr._repr(BrokenRepr(BrokenReprException("really broken")))

def test_string_exception():
    if py.std.sys.version_info < (2,6):
        assert 'unknown' in safe_repr._repr(BrokenRepr("string"))
    else:
        assert 'TypeError' in safe_repr._repr(BrokenRepr("string"))
        


def test_big_repr():
    assert len(safe_repr._repr(range(1000))) <= \
           len('[' + safe_repr.SafeRepr().maxlist * "1000" + ']')

def test_repr_on_newstyle():
    class Function(object):
        def __repr__(self):
            return "<%s>" %(self.name)
    try:
        s = safe_repr._repr(Function())
    except Exception, e:
        py.test.fail("saferepr failed for newstyle class")
    
        
    
