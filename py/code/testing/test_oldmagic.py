import py

def check_assertion():
    excinfo = py.test.raises(AssertionError, "assert 1 == 2")
    s = excinfo.exconly(tryshort=True)
    if not s == "assert 1 == 2":
        raise ValueError("assertion not enabled: got %s" % s)

def test_invoke_assertion(recwarn, monkeypatch):
    monkeypatch.setattr(py.std.__builtin__, 'AssertionError', None)
    py.magic.invoke(assertion=True)
    try:
        check_assertion()
    finally:
        py.magic.revoke(assertion=True)
    recwarn.pop(DeprecationWarning)

def test_invoke_compile(recwarn, monkeypatch):
    monkeypatch.setattr(py.std.__builtin__, 'compile', None)
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
    recwarn.pop(DeprecationWarning)

def test_patch_revert(recwarn):
    class a:
        pass
    py.test.raises(AttributeError, "py.magic.patch(a, 'i', 42)")

    a.i = 42
    py.magic.patch(a, 'i', 23)
    assert a.i == 23
    recwarn.pop(DeprecationWarning)
    py.magic.revert(a, 'i')
    assert a.i == 42
    recwarn.pop(DeprecationWarning)

def test_double_patch(recwarn):
    class a:
        i = 42
    assert py.magic.patch(a, 'i', 2) == 42
    recwarn.pop(DeprecationWarning)
    assert py.magic.patch(a, 'i', 3) == 2
    assert a.i == 3
    assert py.magic.revert(a, 'i') == 3
    recwarn.pop(DeprecationWarning)
    assert a.i == 2
    assert py.magic.revert(a, 'i') == 2
    assert a.i == 42

def test_valueerror(recwarn):
    class a:
        i = 2
        pass
    py.test.raises(ValueError, "py.magic.revert(a, 'i')")
    recwarn.pop(DeprecationWarning)
