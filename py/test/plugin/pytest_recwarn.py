"""

provides "recwarn" funcarg for asserting warnings to be shown 
to a user.  See the test at the bottom for an example. 

"""
import py
import os

class RecwarnPlugin:
    def pytest_funcarg__recwarn(self, request):
        """ check that warnings have been raised. """ 
        warnings = WarningsRecorder()
        request.addfinalizer(warnings.finalize)
        return warnings

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
    sorter = testdir.inline_runsource("""
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
    res = sorter.countoutcomes()
    assert tuple(res) == (2, 0, 0), res
        
