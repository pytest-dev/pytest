"""
python version compatibility code
"""
import functools
import inspect
import io
import re
import sys
from contextlib import contextmanager
from inspect import Parameter
from inspect import signature

import attr
import py

import _pytest
from _pytest._io.saferepr import saferepr
from _pytest.outcomes import fail
from _pytest.outcomes import TEST_OUTCOME


NOTSET = object()

MODULE_NOT_FOUND_ERROR = (
    "ModuleNotFoundError" if sys.version_info[:2] >= (3, 6) else "ImportError"
)


def _format_args(func):
    return str(signature(func))


# The type of re.compile objects is not exposed in Python.
REGEX_TYPE = type(re.compile(""))


def is_generator(func):
    genfunc = inspect.isgeneratorfunction(func)
    return genfunc and not iscoroutinefunction(func)


def iscoroutinefunction(func):
    """Return True if func is a decorated coroutine function.

    Note: copied and modified from Python 3.5's builtin couroutines.py to avoid import asyncio directly,
    which in turns also initializes the "logging" module as side-effect (see issue #8).
    """
    return getattr(func, "_is_coroutine", False) or (
        hasattr(inspect, "iscoroutinefunction") and inspect.iscoroutinefunction(func)
    )


def getlocation(function, curdir):
    function = get_real_func(function)
    fn = py.path.local(inspect.getfile(function))
    lineno = function.__code__.co_firstlineno
    if fn.relto(curdir):
        fn = fn.relto(curdir)
    return "%s:%d" % (fn, lineno + 1)


def num_mock_patch_args(function):
    """ return number of arguments used up by mock arguments (if any) """
    patchings = getattr(function, "patchings", None)
    if not patchings:
        return 0
    mock_modules = [sys.modules.get("mock"), sys.modules.get("unittest.mock")]
    if any(mock_modules):
        sentinels = [m.DEFAULT for m in mock_modules if m is not None]
        return len(
            [p for p in patchings if not p.attribute_name and p.new in sentinels]
        )
    return len(patchings)


def getfuncargnames(function, is_method=False, cls=None):
    """Returns the names of a function's mandatory arguments.

    This should return the names of all function arguments that:
        * Aren't bound to an instance or type as in instance or class methods.
        * Don't have default values.
        * Aren't bound with functools.partial.
        * Aren't replaced with mocks.

    The is_method and cls arguments indicate that the function should
    be treated as a bound method even though it's not unless, only in
    the case of cls, the function is a static method.

    @RonnyPfannschmidt: This function should be refactored when we
    revisit fixtures. The fixture mechanism should ask the node for
    the fixture names, and not try to obtain directly from the
    function object well after collection has occurred.

    """
    # The parameters attribute of a Signature object contains an
    # ordered mapping of parameter names to Parameter instances.  This
    # creates a tuple of the names of the parameters that don't have
    # defaults.
    try:
        parameters = signature(function).parameters
    except (ValueError, TypeError) as e:
        fail(
            "Could not determine arguments of {!r}: {}".format(function, e),
            pytrace=False,
        )

    arg_names = tuple(
        p.name
        for p in parameters.values()
        if (
            p.kind is Parameter.POSITIONAL_OR_KEYWORD
            or p.kind is Parameter.KEYWORD_ONLY
        )
        and p.default is Parameter.empty
    )
    # If this function should be treated as a bound method even though
    # it's passed as an unbound method or function, remove the first
    # parameter name.
    if is_method or (
        cls and not isinstance(cls.__dict__.get(function.__name__, None), staticmethod)
    ):
        arg_names = arg_names[1:]
    # Remove any names that will be replaced with mocks.
    if hasattr(function, "__wrapped__"):
        arg_names = arg_names[num_mock_patch_args(function) :]
    return arg_names


if sys.version_info < (3, 7):

    @contextmanager
    def nullcontext():
        yield


else:
    from contextlib import nullcontext  # noqa


def get_default_arg_names(function):
    # Note: this code intentionally mirrors the code at the beginning of getfuncargnames,
    # to get the arguments which were excluded from its result because they had default values
    return tuple(
        p.name
        for p in signature(function).parameters.values()
        if p.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
        and p.default is not Parameter.empty
    )


_non_printable_ascii_translate_table = {
    i: "\\x{:02x}".format(i) for i in range(128) if i not in range(32, 127)
}
_non_printable_ascii_translate_table.update(
    {ord("\t"): "\\t", ord("\r"): "\\r", ord("\n"): "\\n"}
)


def _translate_non_printable(s):
    return s.translate(_non_printable_ascii_translate_table)


STRING_TYPES = bytes, str


def _bytes_to_ascii(val):
    return val.decode("ascii", "backslashreplace")


def ascii_escaped(val):
    """If val is pure ascii, returns it as a str().  Otherwise, escapes
    bytes objects into a sequence of escaped bytes:

    b'\xc3\xb4\xc5\xd6' -> '\\xc3\\xb4\\xc5\\xd6'

    and escapes unicode objects into a sequence of escaped unicode
    ids, e.g.:

    '4\\nV\\U00043efa\\x0eMXWB\\x1e\\u3028\\u15fd\\xcd\\U0007d944'

    note:
       the obvious "v.decode('unicode-escape')" will return
       valid utf-8 unicode if it finds them in bytes, but we
       want to return escaped bytes for any byte, even if they match
       a utf-8 string.

    """
    if isinstance(val, bytes):
        ret = _bytes_to_ascii(val)
    else:
        ret = val.encode("unicode_escape").decode("ascii")
    return _translate_non_printable(ret)


@attr.s
class _PytestWrapper:
    """Dummy wrapper around a function object for internal use only.

    Used to correctly unwrap the underlying function object
    when we are creating fixtures, because we wrap the function object ourselves with a decorator
    to issue warnings when the fixture function is called directly.
    """

    obj = attr.ib()


def get_real_func(obj):
    """ gets the real function object of the (possibly) wrapped object by
    functools.wraps or functools.partial.
    """
    start_obj = obj
    for i in range(100):
        # __pytest_wrapped__ is set by @pytest.fixture when wrapping the fixture function
        # to trigger a warning if it gets called directly instead of by pytest: we don't
        # want to unwrap further than this otherwise we lose useful wrappings like @mock.patch (#3774)
        new_obj = getattr(obj, "__pytest_wrapped__", None)
        if isinstance(new_obj, _PytestWrapper):
            obj = new_obj.obj
            break
        new_obj = getattr(obj, "__wrapped__", None)
        if new_obj is None:
            break
        obj = new_obj
    else:
        raise ValueError(
            ("could not find real function of {start}\nstopped at {current}").format(
                start=saferepr(start_obj), current=saferepr(obj)
            )
        )
    if isinstance(obj, functools.partial):
        obj = obj.func
    return obj


def get_real_method(obj, holder):
    """
    Attempts to obtain the real function object that might be wrapping ``obj``, while at the same time
    returning a bound method to ``holder`` if the original object was a bound method.
    """
    try:
        is_method = hasattr(obj, "__func__")
        obj = get_real_func(obj)
    except Exception:
        return obj
    if is_method and hasattr(obj, "__get__") and callable(obj.__get__):
        obj = obj.__get__(holder)
    return obj


def getfslineno(obj):
    # xxx let decorators etc specify a sane ordering
    obj = get_real_func(obj)
    if hasattr(obj, "place_as"):
        obj = obj.place_as
    fslineno = _pytest._code.getfslineno(obj)
    assert isinstance(fslineno[1], int), obj
    return fslineno


def getimfunc(func):
    try:
        return func.__func__
    except AttributeError:
        return func


def safe_getattr(object, name, default):
    """ Like getattr but return default upon any Exception or any OutcomeException.

    Attribute access can potentially fail for 'evil' Python objects.
    See issue #214.
    It catches OutcomeException because of #2490 (issue #580), new outcomes are derived from BaseException
    instead of Exception (for more details check #2707)
    """
    try:
        return getattr(object, name, default)
    except TEST_OUTCOME:
        return default


def safe_isclass(obj):
    """Ignore any exception via isinstance on Python 3."""
    try:
        return inspect.isclass(obj)
    except Exception:
        return False


COLLECT_FAKEMODULE_ATTRIBUTES = (
    "Collector",
    "Module",
    "Function",
    "Instance",
    "Session",
    "Item",
    "Class",
    "File",
    "_fillfuncargs",
)


def _setup_collect_fakemodule():
    from types import ModuleType
    import pytest

    pytest.collect = ModuleType("pytest.collect")
    pytest.collect.__all__ = []  # used for setns
    for attr_name in COLLECT_FAKEMODULE_ATTRIBUTES:
        setattr(pytest.collect, attr_name, getattr(pytest, attr_name))


class CaptureIO(io.TextIOWrapper):
    def __init__(self):
        super().__init__(io.BytesIO(), encoding="UTF-8", newline="", write_through=True)

    def getvalue(self):
        return self.buffer.getvalue().decode("UTF-8")


class FuncargnamesCompatAttr:
    """ helper class so that Metafunc, Function and FixtureRequest
    don't need to each define the "funcargnames" compatibility attribute.
    """

    @property
    def funcargnames(self):
        """ alias attribute for ``fixturenames`` for pre-2.3 compatibility"""
        import warnings
        from _pytest.deprecated import FUNCARGNAMES

        warnings.warn(FUNCARGNAMES, stacklevel=2)
        return self.fixturenames
