import py

def dep(i):
    if i == 0:
        py.std.warnings.warn("is deprecated", DeprecationWarning)

reg = {}
def dep_explicit(i):
    if i == 0:
        py.std.warnings.warn_explicit("dep_explicit", category=DeprecationWarning, 
                                      filename="hello", lineno=3)

def test_deprecated_call_raises():
    py.test.raises(AssertionError, 
                   "py.test.deprecated_call(dep, 3)")

def test_deprecated_call():
    py.test.deprecated_call(dep, 0)

def test_deprecated_call_preserves():
    r = py.std.warnings.onceregistry.copy()
    f = py.std.warnings.filters[:]
    test_deprecated_call_raises()
    test_deprecated_call()
    assert r == py.std.warnings.onceregistry
    assert f == py.std.warnings.filters

def test_deprecated_explicit_call_raises():
    py.test.raises(AssertionError, 
                   "py.test.deprecated_call(dep_explicit, 3)")

def test_deprecated_explicit_call():
    py.test.deprecated_call(dep_explicit, 0)
    py.test.deprecated_call(dep_explicit, 0)

