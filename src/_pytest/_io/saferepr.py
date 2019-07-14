import pprint
import reprlib


def _format_repr_exception(exc, obj):
    exc_name = type(exc).__name__
    try:
        exc_info = str(exc)
    except Exception:
        exc_info = "unknown"
    return '<[{}("{}") raised in repr()] {} object at 0x{:x}>'.format(
        exc_name, exc_info, obj.__class__.__name__, id(obj)
    )


def _ellipsize(s, maxsize):
    if len(s) > maxsize:
        i = max(0, (maxsize - 3) // 2)
        j = max(0, maxsize - 3 - i)
        return s[:i] + "..." + s[len(s) - j :]
    return s


class SafeRepr(reprlib.Repr):
    """subclass of repr.Repr that limits the resulting size of repr()
    and includes information on exceptions raised during the call.
    """

    def __init__(self, maxsize):
        super().__init__()
        self.maxstring = maxsize
        self.maxsize = maxsize

    def repr(self, x):
        try:
            s = super().repr(x)
        except Exception as exc:
            s = _format_repr_exception(exc, x)
        return _ellipsize(s, self.maxsize)

    def repr_instance(self, x, level):
        try:
            s = repr(x)
        except Exception as exc:
            s = _format_repr_exception(exc, x)
        return _ellipsize(s, self.maxsize)


def safeformat(obj):
    """return a pretty printed string for the given object.
    Failing __repr__ functions of user instances will be represented
    with a short exception info.
    """
    try:
        return pprint.pformat(obj)
    except Exception as exc:
        return _format_repr_exception(exc, obj)


def saferepr(obj, maxsize=240):
    """return a size-limited safe repr-string for the given object.
    Failing __repr__ functions of user instances will be represented
    with a short exception info and 'saferepr' generally takes
    care to never raise exceptions itself.  This function is a wrapper
    around the Repr/reprlib functionality of the standard 2.6 lib.
    """
    return SafeRepr(maxsize).repr(obj)
