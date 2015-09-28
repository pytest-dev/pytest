""" recording warnings during test function execution. """

import inspect
import py
import sys
import warnings
import pytest


@pytest.yield_fixture
def recwarn(request):
    """Return a WarningsRecorder instance that provides these methods:

    * ``pop(category=None)``: return last warning matching the category.
    * ``clear()``: clear list of warnings

    See http://docs.python.org/library/warnings.html for information
    on warning categories.
    """
    wrec = WarningsRecorder()
    with wrec:
        warnings.simplefilter('default')
        yield wrec


def pytest_namespace():
    return {'deprecated_call': deprecated_call,
            'warns': warns}


def deprecated_call(func, *args, **kwargs):
    """Assert that ``func(*args, **kwargs)`` triggers a DeprecationWarning.
    """
    wrec = WarningsRecorder()
    with wrec:
        warnings.simplefilter('always')  # ensure all warnings are triggered
        ret = func(*args, **kwargs)

    depwarnings = (DeprecationWarning, PendingDeprecationWarning)
    if not any(r.category in depwarnings for r in wrec):
        __tracebackhide__ = True
        raise AssertionError("%r did not produce DeprecationWarning" % (func,))

    return ret


def warns(expected_warning, *args, **kwargs):
    """Assert that code raises a particular class of warning.

    Specifically, the input @expected_warning can be a warning class or
    tuple of warning classes, and the code must return that warning
    (if a single class) or one of those warnings (if a tuple).

    This helper produces a list of ``warnings.WarningMessage`` objects,
    one for each warning raised.

    This function can be used as a context manager, or any of the other ways
    ``pytest.raises`` can be used::

        >>> with warns(RuntimeWarning):
        ...    warnings.warn("my warning", RuntimeWarning)
    """
    wcheck = WarningsChecker(expected_warning)
    if not args:
        return wcheck
    elif isinstance(args[0], str):
        code, = args
        assert isinstance(code, str)
        frame = sys._getframe(1)
        loc = frame.f_locals.copy()
        loc.update(kwargs)

        with wcheck:
            code = py.code.Source(code).compile()
            py.builtin.exec_(code, frame.f_globals, loc)
    else:
        func = args[0]
        with wcheck:
            return func(*args[1:], **kwargs)


class RecordedWarning(object):
    def __init__(self, message, category, filename, lineno, file, line):
        self.message = message
        self.category = category
        self.filename = filename
        self.lineno = lineno
        self.file = file
        self.line = line


class WarningsRecorder(object):
    """A context manager to record raised warnings.

    Adapted from `warnings.catch_warnings`.
    """

    def __init__(self, module=None):
        self._module = sys.modules['warnings'] if module is None else module
        self._entered = False
        self._list = []

    @property
    def list(self):
        """The list of recorded warnings."""
        return self._list

    def __getitem__(self, i):
        """Get a recorded warning by index."""
        return self._list[i]

    def __iter__(self):
        """Iterate through the recorded warnings."""
        return iter(self._list)

    def __len__(self):
        """The number of recorded warnings."""
        return len(self._list)

    def pop(self, cls=Warning):
        """Pop the first recorded warning, raise exception if not exists."""
        for i, w in enumerate(self._list):
            if issubclass(w.category, cls):
                return self._list.pop(i)
        __tracebackhide__ = True
        raise AssertionError("%r not found in warning list" % cls)

    def clear(self):
        """Clear the list of recorded warnings."""
        self._list[:] = []

    def __enter__(self):
        if self._entered:
            __tracebackhide__ = True
            raise RuntimeError("Cannot enter %r twice" % self)
        self._entered = True
        self._filters = self._module.filters
        self._module.filters = self._filters[:]
        self._showwarning = self._module.showwarning

        def showwarning(message, category, filename, lineno,
                        file=None, line=None):
            self._list.append(RecordedWarning(
                message, category, filename, lineno, file, line))

            # still perform old showwarning functionality
            self._showwarning(
                message, category, filename, lineno, file=file, line=line)

        self._module.showwarning = showwarning

        # allow the same warning to be raised more than once
        self._module.simplefilter('always', append=True)

        return self

    def __exit__(self, *exc_info):
        if not self._entered:
            __tracebackhide__ = True
            raise RuntimeError("Cannot exit %r without entering first" % self)
        self._module.filters = self._filters
        self._module.showwarning = self._showwarning


class WarningsChecker(WarningsRecorder):
    def __init__(self, expected_warning=None, module=None):
        super(WarningsChecker, self).__init__(module=module)

        msg = ("exceptions must be old-style classes or "
               "derived from Warning, not %s")
        if isinstance(expected_warning, tuple):
            for exc in expected_warning:
                if not inspect.isclass(exc):
                    raise TypeError(msg % type(exc))
        elif inspect.isclass(expected_warning):
            expected_warning = (expected_warning,)
        elif expected_warning is not None:
            raise TypeError(msg % type(expected_warning))

        self.expected_warning = expected_warning

    def __exit__(self, *exc_info):
        super(WarningsChecker, self).__exit__(*exc_info)

        # only check if we're not currently handling an exception
        if all(a is None for a in exc_info):
            if self.expected_warning is not None:
                if not any(r.category in self.expected_warning for r in self):
                    __tracebackhide__ = True
                    pytest.fail("DID NOT WARN")
