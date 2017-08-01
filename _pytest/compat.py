"""
python version compatibility code
"""
from __future__ import absolute_import, division, print_function
import sys
import inspect
import types
import re
import functools

import py

import _pytest


try:
    import enum
except ImportError:  # pragma: no cover
    # Only available in Python 3.4+ or as a backport
    enum = None


_PY3 = sys.version_info > (3, 0)
_PY2 = not _PY3


NoneType = type(None)
NOTSET = object()

PY35 = sys.version_info[:2] >= (3, 5)
PY36 = sys.version_info[:2] >= (3, 6)
MODULE_NOT_FOUND_ERROR = 'ModuleNotFoundError' if PY36 else 'ImportError'

if hasattr(inspect, 'signature'):
    def _format_args(func):
        return str(inspect.signature(func))
else:
    def _format_args(func):
        return inspect.formatargspec(*inspect.getargspec(func))

isfunction = inspect.isfunction
isclass = inspect.isclass
# used to work around a python2 exception info leak
exc_clear = getattr(sys, 'exc_clear', lambda: None)
# The type of re.compile objects is not exposed in Python.
REGEX_TYPE = type(re.compile(''))


def is_generator(func):
    genfunc = inspect.isgeneratorfunction(func)
    return genfunc and not iscoroutinefunction(func)


def iscoroutinefunction(func):
    """Return True if func is a decorated coroutine function.

    Note: copied and modified from Python 3.5's builtin couroutines.py to avoid import asyncio directly,
    which in turns also initializes the "logging" module as side-effect (see issue #8).
    """
    return (getattr(func, '_is_coroutine', False) or
            (hasattr(inspect, 'iscoroutinefunction') and inspect.iscoroutinefunction(func)))


def getlocation(function, curdir):
    import inspect
    fn = py.path.local(inspect.getfile(function))
    lineno = py.builtin._getcode(function).co_firstlineno
    if fn.relto(curdir):
        fn = fn.relto(curdir)
    return "%s:%d" % (fn, lineno + 1)


def num_mock_patch_args(function):
    """ return number of arguments used up by mock arguments (if any) """
    patchings = getattr(function, "patchings", None)
    if not patchings:
        return 0
    mock = sys.modules.get("mock", sys.modules.get("unittest.mock", None))
    if mock is not None:
        return len([p for p in patchings
                    if not p.attribute_name and p.new is mock.DEFAULT])
    return len(patchings)


def getfuncargnames(function, startindex=None):
    # XXX merge with main.py's varnames
    # assert not isclass(function)
    realfunction = function
    while hasattr(realfunction, "__wrapped__"):
        realfunction = realfunction.__wrapped__
    if startindex is None:
        startindex = inspect.ismethod(function) and 1 or 0
    if realfunction != function:
        startindex += num_mock_patch_args(function)
        function = realfunction
    if isinstance(function, functools.partial):
        argnames = inspect.getargs(_pytest._code.getrawcode(function.func))[0]
        partial = function
        argnames = argnames[len(partial.args):]
        if partial.keywords:
            for kw in partial.keywords:
                argnames.remove(kw)
    else:
        argnames = inspect.getargs(_pytest._code.getrawcode(function))[0]
    defaults = getattr(function, 'func_defaults',
                       getattr(function, '__defaults__', None)) or ()
    numdefaults = len(defaults)
    if numdefaults:
        return tuple(argnames[startindex:-numdefaults])
    return tuple(argnames[startindex:])


if sys.version_info[:2] == (2, 6):
    def isclass(object):
        """ Return true if the object is a class. Overrides inspect.isclass for
        python 2.6 because it will return True for objects which always return
        something on __getattr__ calls (see #1035).
        Backport of https://hg.python.org/cpython/rev/35bf8f7a8edc
        """
        return isinstance(object, (type, types.ClassType))


if _PY3:
    import codecs
    imap = map
    izip = zip
    STRING_TYPES = bytes, str
    UNICODE_TYPES = str,

    def _ascii_escaped(val):
        """If val is pure ascii, returns it as a str().  Otherwise, escapes
        bytes objects into a sequence of escaped bytes:

        b'\xc3\xb4\xc5\xd6' -> u'\\xc3\\xb4\\xc5\\xd6'

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
            if val:
                # source: http://goo.gl/bGsnwC
                encoded_bytes, _ = codecs.escape_encode(val)
                return encoded_bytes.decode('ascii')
            else:
                # empty bytes crashes codecs.escape_encode (#1087)
                return ''
        else:
            return val.encode('unicode_escape').decode('ascii')
else:
    STRING_TYPES = bytes, str, unicode
    UNICODE_TYPES = unicode,

    from itertools import imap, izip  # NOQA

    def _ascii_escaped(val):
        """In py2 bytes and str are the same type, so return if it's a bytes
        object, return it unchanged if it is a full ascii string,
        otherwise escape it into its binary form.

        If it's a unicode string, change the unicode characters into
        unicode escapes.

        """
        if isinstance(val, bytes):
            try:
                return val.encode('ascii')
            except UnicodeDecodeError:
                return val.encode('string-escape')
        else:
            return val.encode('unicode-escape')


def get_real_func(obj):
    """ gets the real function object of the (possibly) wrapped object by
    functools.wraps or functools.partial.
    """
    start_obj = obj
    for i in range(100):
        new_obj = getattr(obj, '__wrapped__', None)
        if new_obj is None:
            break
        obj = new_obj
    else:
        raise ValueError(
            ("could not find real function of {start}"
             "\nstopped at {current}").format(
                start=py.io.saferepr(start_obj),
                current=py.io.saferepr(obj)))
    if isinstance(obj, functools.partial):
        obj = obj.func
    return obj


def getfslineno(obj):
    # xxx let decorators etc specify a sane ordering
    obj = get_real_func(obj)
    if hasattr(obj, 'place_as'):
        obj = obj.place_as
    fslineno = _pytest._code.getfslineno(obj)
    assert isinstance(fslineno[1], int), obj
    return fslineno


def getimfunc(func):
    try:
        return func.__func__
    except AttributeError:
        try:
            return func.im_func
        except AttributeError:
            return func


def safe_getattr(object, name, default):
    """ Like getattr but return default upon any Exception.

    Attribute access can potentially fail for 'evil' Python objects.
    See issue #214.
    """
    try:
        return getattr(object, name, default)
    except Exception:
        return default


def _is_unittest_unexpected_success_a_failure():
    """Return if the test suite should fail if a @expectedFailure unittest test PASSES.

    From https://docs.python.org/3/library/unittest.html?highlight=unittest#unittest.TestResult.wasSuccessful:
        Changed in version 3.4: Returns False if there were any
        unexpectedSuccesses from tests marked with the expectedFailure() decorator.
    """
    return sys.version_info >= (3, 4)


if _PY3:
    def safe_str(v):
        """returns v as string"""
        return str(v)
else:
    def safe_str(v):
        """returns v as string, converting to ascii if necessary"""
        try:
            return str(v)
        except UnicodeError:
            if not isinstance(v, unicode):
                v = unicode(v)
            errors = 'replace'
            return v.encode('utf-8', errors)


COLLECT_FAKEMODULE_ATTRIBUTES = (
    'Collector',
    'Module',
    'Generator',
    'Function',
    'Instance',
    'Session',
    'Item',
    'Class',
    'File',
    '_fillfuncargs',
)


def _setup_collect_fakemodule():
    from types import ModuleType
    import pytest
    pytest.collect = ModuleType('pytest.collect')
    pytest.collect.__all__ = []  # used for setns
    for attr in COLLECT_FAKEMODULE_ATTRIBUTES:
        setattr(pytest.collect, attr, getattr(pytest, attr))


if _PY2:
    # Without this the test_dupfile_on_textio will fail, otherwise CaptureIO could directly inherit from StringIO.
    from py.io import TextIO

    class CaptureIO(TextIO):

        @property
        def encoding(self):
            return getattr(self, '_encoding', 'UTF-8')

else:
    import io

    class CaptureIO(io.TextIOWrapper):
        def __init__(self):
            super(CaptureIO, self).__init__(
                io.BytesIO(),
                encoding='UTF-8', newline='', write_through=True,
            )

        def getvalue(self):
            return self.buffer.getvalue().decode('UTF-8')


class FuncargnamesCompatAttr(object):
    """ helper class so that Metafunc, Function and FixtureRequest
    don't need to each define the "funcargnames" compatibility attribute.
    """
    @property
    def funcargnames(self):
        """ alias attribute for ``fixturenames`` for pre-2.3 compatibility"""
        return self.fixturenames
