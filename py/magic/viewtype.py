"""
The View base class for view-based programming.

A view of an object is an extension of this existing object.
This is useful to *locally* add methods or even attributes to objects
that you have obtained from elsewhere.
"""
from __future__ import generators
import inspect

class View(object):
    """View base class.

    If C is a subclass of View, then C(x) creates a proxy object around
    the object x.  The actual class of the proxy is not C in general,
    but a *subclass* of C determined by the rules below.  To avoid confusion
    we call view class the class of the proxy (a subclass of C, so of View)
    and object class the class of x.

    Attributes and methods not found in the proxy are automatically read on x.
    Other operations like setting attributes are performed on the proxy, as
    determined by its view class.  The object x is available from the proxy
    as its __obj__ attribute.

    The view class selection is determined by the __view__ tuples and the
    optional __viewkey__ method.  By default, the selected view class is the
    most specific subclass of C whose __view__ mentions the class of x.
    If no such subclass is found, the search proceeds with the parent
    object classes.  For example, C(True) will first look for a subclass
    of C with __view__ = (..., bool, ...) and only if it doesn't find any
    look for one with __view__ = (..., int, ...), and then ..., object,...
    If everything fails the class C itself is considered to be the default.

    Alternatively, the view class selection can be driven by another aspect
    of the object x, instead of the class of x, by overriding __viewkey__.
    See last example at the end of this module.
    """

    _viewcache = {}
    __view__ = ()

    def __new__(rootclass, obj, *args, **kwds):
        self = object.__new__(rootclass)
        self.__obj__ = obj
        self.__rootclass__ = rootclass
        key = self.__viewkey__()
        try:
            self.__class__ = self._viewcache[key]
        except KeyError:
            self.__class__ = self._selectsubclass(key)
        return self

    def __getattr__(self, attr):
        # attributes not found in the normal hierarchy rooted on View
        # are looked up in the object's real class
        return getattr(self.__obj__, attr)

    def __viewkey__(self):
        return self.__obj__.__class__

    def __matchkey__(self, key, subclasses):
        if inspect.isclass(key):
            keys = inspect.getmro(key)
        else:
            keys = [key]
        for key in keys:
            result = [C for C in subclasses if key in C.__view__]
            if result:
                return result
        return []

    def _selectsubclass(self, key):
        subclasses = list(enumsubclasses(self.__rootclass__))
        for C in subclasses:
            if not isinstance(C.__view__, tuple):
                C.__view__ = (C.__view__,)
        choices = self.__matchkey__(key, subclasses)
        if not choices:
            return self.__rootclass__
        elif len(choices) == 1:
            return choices[0]
        else:
            # combine the multiple choices
            return type('?', tuple(choices), {})

    def __repr__(self):
        return '%s(%r)' % (self.__rootclass__.__name__, self.__obj__)


def enumsubclasses(cls):
    for subcls in cls.__subclasses__():
        for subsubclass in enumsubclasses(subcls):
            yield subsubclass
    yield cls
