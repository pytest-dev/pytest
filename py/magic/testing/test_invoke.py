import __builtin__ as bltin
import py
import inspect

def check_assertion():
    excinfo = py.test.raises(AssertionError, "assert 1 == 2")
    assert excinfo.exconly(tryshort=True) == "assert 1 == 2"

def test_invoke_assertion():
    py.magic.invoke(assertion=True)
    try:
        check_assertion()
    finally:
        py.magic.revoke(assertion=True)

def test_invoke_compile():
    py.magic.invoke(compile=True)
    try:
        co = compile("""if 1: 
                    def f(): 
                        return 1
                    \n""", '', 'exec')
        d = {}
        exec co in d
        assert py.code.Source(d['f']) 
    finally:
        py.magic.revoke(compile=True)


