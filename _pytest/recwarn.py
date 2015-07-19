""" recording warnings during test function execution. """

import sys
import warnings


def pytest_funcarg__recwarn(request):
    """Return a WarningsRecorder instance that provides these methods:

    * ``pop(category=None)``: return last warning matching the category.
    * ``clear()``: clear list of warnings

    See http://docs.python.org/library/warnings.html for information
    on warning categories.
    """
    if sys.version_info >= (2,7):
        oldfilters = warnings.filters[:]
        warnings.simplefilter('default')
        def reset_filters():
            warnings.filters[:] = oldfilters
        request.addfinalizer(reset_filters)
    wrec = WarningsRecorder()
    request.addfinalizer(wrec.finalize)
    return wrec

def pytest_namespace():
    return {'deprecated_call': deprecated_call}

def deprecated_call(func, *args, **kwargs):
    """ assert that calling ``func(*args, **kwargs)``
    triggers a DeprecationWarning.
    """
    l = []
    oldwarn_explicit = getattr(warnings, 'warn_explicit')
    def warn_explicit(*args, **kwargs):
        l.append(args)
        oldwarn_explicit(*args, **kwargs)
    oldwarn = getattr(warnings, 'warn')
    def warn(*args, **kwargs):
        l.append(args)
        oldwarn(*args, **kwargs)

    warnings.warn_explicit = warn_explicit
    warnings.warn = warn
    try:
        ret = func(*args, **kwargs)
    finally:
        warnings.warn_explicit = oldwarn_explicit
        warnings.warn = oldwarn
    if not l:
        __tracebackhide__ = True
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
        self.old_showwarning = warnings.showwarning
        warnings.showwarning = showwarning

    def pop(self, cls=Warning):
        """ pop the first recorded warning, raise exception if not exists."""
        for i, w in enumerate(self.list):
            if issubclass(w.category, cls):
                return self.list.pop(i)
        __tracebackhide__ = True
        assert 0, "%r not found in %r" %(cls, self.list)

    #def resetregistry(self):
    #    warnings.onceregistry.clear()
    #    warnings.__warningregistry__.clear()

    def clear(self):
        self.list[:] = []

    def finalize(self):
        warnings.showwarning = self.old_showwarning
