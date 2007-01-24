
import py
from py.__.test.rsession.outcome import Outcome, ReprOutcome, ExcInfoRepr

import marshal

def test_critical_debugging_flag():
    outcome = Outcome(is_critical=True)
    r = ReprOutcome(outcome.make_repr())
    assert r.is_critical 
    
def f1():
    1
    2
    3
    4
    raise ValueError(42)

def f2():
    f1()

def f3():
    f2()

def test_exception_info_repr():
    try:
        f3()
    except:
        outcome = Outcome(excinfo=py.code.ExceptionInfo())
        
    repr = outcome.make_excinfo_repr("long")
    assert marshal.dumps(repr)
    excinfo = ExcInfoRepr(repr)
    
    assert str(excinfo.typename) == "ValueError"
    assert str(excinfo.value) == "42"
    assert len(excinfo.traceback) == 4
    myfile = py.magic.autopath()
    assert excinfo.traceback[3].path == myfile
    assert excinfo.traceback[3].lineno == f1.func_code.co_firstlineno + 4
    assert excinfo.traceback[3].relline == 5
    assert excinfo.traceback[2].path == myfile
    assert excinfo.traceback[2].lineno == f2.func_code.co_firstlineno
    assert excinfo.traceback[2].relline == 1
    assert excinfo.traceback[1].path == myfile
    assert excinfo.traceback[1].lineno == f3.func_code.co_firstlineno
    assert excinfo.traceback[1].relline == 1

#def test_f3():
#    f3()
