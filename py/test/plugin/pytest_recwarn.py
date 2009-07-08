"""
helpers for asserting deprecation and other warnings. 

    recwarn: function argument where one can call recwarn.pop() to get
             the last warning that would have been shown. 

    py.test.deprecated_call(func, *args, **kwargs): 
            assert that a function call triggers a deprecation warning. 
"""

import py
import os

def pytest_funcarg__recwarn(request):
    """ check that warnings have been raised. """ 
    warnings = WarningsRecorder()
    request.addfinalizer(warnings.finalize)
    return warnings

def pytest_namespace(config):
    return {'deprecated_call': deprecated_call}

def deprecated_call(func, *args, **kwargs):
    """ assert that calling func(*args, **kwargs)
        triggers a DeprecationWarning. 
    """ 
    warningmodule = py.std.warnings
    l = []
    oldwarn_explicit = getattr(warningmodule, 'warn_explicit')
    def warn_explicit(*args, **kwargs): 
        l.append(args) 
        oldwarn_explicit(*args, **kwargs)
    oldwarn = getattr(warningmodule, 'warn')
    def warn(*args, **kwargs): 
        l.append(args) 
        oldwarn(*args, **kwargs)
        
    warningmodule.warn_explicit = warn_explicit
    warningmodule.warn = warn
    try:
        ret = func(*args, **kwargs)
    finally:
        warningmodule.warn_explicit = warn_explicit
        warningmodule.warn = warn
    if not l:
        #print warningmodule
        raise AssertionError("%r did not produce DeprecationWarning" %(func,))
    return ret


class RecordedWarning:
    def __init__(self, message, category, filename, lineno, line):
        self.message = message
        self.category = category
        self.filename = filename
        self.lineno = lineno
        self.line = line

class WarningsRecorder:
    def __init__(self):
        warningmodule = py.std.warnings
        self.list = []
        def showwarning(message, category, filename, lineno, line=0):
            self.list.append(RecordedWarning(
                message, category, filename, lineno, line))
            try:
                self.old_showwarning(message, category, 
                    filename, lineno, line=line)
            except TypeError:
                # < python2.6 
                self.old_showwarning(message, category, filename, lineno)
        self.old_showwarning = warningmodule.showwarning
        warningmodule.showwarning = showwarning

    def pop(self, cls=Warning):
        """ pop the first recorded warning, raise exception if not exists."""
        for i, w in py.builtin.enumerate(self.list):
            if issubclass(w.category, cls):
                return self.list.pop(i)
        __tracebackhide__ = True
        assert 0, "%r not found in %r" %(cls, self.list)

    #def resetregistry(self):
    #    import warnings
    #    warnings.onceregistry.clear()
    #    warnings.__warningregistry__.clear()

    def clear(self): 
        self.list[:] = []

    def finalize(self):
        py.std.warnings.showwarning = self.old_showwarning

def test_WarningRecorder():
    showwarning = py.std.warnings.showwarning
    rec = WarningsRecorder()
    assert py.std.warnings.showwarning != showwarning
    assert not rec.list
    py.std.warnings.warn_explicit("hello", UserWarning, "xyz", 13)
    assert len(rec.list) == 1
    py.std.warnings.warn(DeprecationWarning("hello"))
    assert len(rec.list) == 2
    warn = rec.pop()
    assert str(warn.message) == "hello"
    l = rec.list
    rec.clear()
    assert len(rec.list) == 0
    assert l is rec.list
    py.test.raises(AssertionError, "rec.pop()")
    rec.finalize()
    assert showwarning == py.std.warnings.showwarning

def test_recwarn_functional(testdir):
    reprec = testdir.inline_runsource("""
        pytest_plugins = 'pytest_recwarn', 
        import warnings
        oldwarn = warnings.showwarning
        def test_method(recwarn):
            assert warnings.showwarning != oldwarn
            warnings.warn("hello")
            warn = recwarn.pop()
            assert isinstance(warn.message, UserWarning)
        def test_finalized():
            assert warnings.showwarning == oldwarn
    """)
    res = reprec.countoutcomes()
    assert tuple(res) == (2, 0, 0), res
        
#
# ============ test py.test.deprecated_call() ==============
#

def dep(i):
    if i == 0:
        py.std.warnings.warn("is deprecated", DeprecationWarning)
    return 42

reg = {}
def dep_explicit(i):
    if i == 0:
        py.std.warnings.warn_explicit("dep_explicit", category=DeprecationWarning, 
                                      filename="hello", lineno=3)

def test_deprecated_call_raises():
    excinfo = py.test.raises(AssertionError, 
                   "py.test.deprecated_call(dep, 3)")
    assert str(excinfo).find("did not produce") != -1 

def test_deprecated_call():
    py.test.deprecated_call(dep, 0)

def test_deprecated_call_ret():
    ret = py.test.deprecated_call(dep, 0)
    assert ret == 42

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

