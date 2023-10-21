import collections
import dataclasses
import pprint
import reprlib
import sys
import types
from typing import Any
from typing import Dict
from typing import IO
from typing import Optional


def _try_repr_or_str(obj: object) -> str:
    try:
        return repr(obj)
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        return f'{type(obj).__name__}("{obj}")'


def _format_repr_exception(exc: BaseException, obj: object) -> str:
    try:
        exc_info = _try_repr_or_str(exc)
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as exc:
        exc_info = f"unpresentable exception ({_try_repr_or_str(exc)})"
    return "<[{} raised in repr()] {} object at 0x{:x}>".format(
        exc_info, type(obj).__name__, id(obj)
    )


def _ellipsize(s: str, maxsize: int) -> str:
    if len(s) > maxsize:
        i = max(0, (maxsize - 3) // 2)
        j = max(0, maxsize - 3 - i)
        return s[:i] + "..." + s[len(s) - j :]
    return s


class SafeRepr(reprlib.Repr):
    """
    repr.Repr that limits the resulting size of repr() and includes
    information on exceptions raised during the call.
    """

    def __init__(self, maxsize: Optional[int], use_ascii: bool = False) -> None:
        """
        :param maxsize:
            If not None, will truncate the resulting repr to that specific size, using ellipsis
            somewhere in the middle to hide the extra text.
            If None, will not impose any size limits on the returning repr.
        """
        super().__init__()
        # ``maxstring`` is used by the superclass, and needs to be an int; using a
        # very large number in case maxsize is None, meaning we want to disable
        # truncation.
        self.maxstring = maxsize if maxsize is not None else 1_000_000_000
        self.maxsize = maxsize
        self.use_ascii = use_ascii

    def repr(self, x: object) -> str:
        try:
            if self.use_ascii:
                s = ascii(x)
            else:
                s = super().repr(x)

        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as exc:
            s = _format_repr_exception(exc, x)
        if self.maxsize is not None:
            s = _ellipsize(s, self.maxsize)
        return s

    def repr_instance(self, x: object, level: int) -> str:
        try:
            s = repr(x)
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as exc:
            s = _format_repr_exception(exc, x)
        if self.maxsize is not None:
            s = _ellipsize(s, self.maxsize)
        return s


def safeformat(obj: object) -> str:
    """Return a pretty printed string for the given object.

    Failing __repr__ functions of user instances will be represented
    with a short exception info.
    """
    try:
        return pprint.pformat(obj)
    except Exception as exc:
        return _format_repr_exception(exc, obj)


# Maximum size of overall repr of objects to display during assertion errors.
DEFAULT_REPR_MAX_SIZE = 240


def saferepr(
    obj: object, maxsize: Optional[int] = DEFAULT_REPR_MAX_SIZE, use_ascii: bool = False
) -> str:
    """Return a size-limited safe repr-string for the given object.

    Failing __repr__ functions of user instances will be represented
    with a short exception info and 'saferepr' generally takes
    care to never raise exceptions itself.

    This function is a wrapper around the Repr/reprlib functionality of the
    stdlib.
    """

    return SafeRepr(maxsize, use_ascii).repr(obj)


def saferepr_unlimited(obj: object, use_ascii: bool = True) -> str:
    """Return an unlimited-size safe repr-string for the given object.

    As with saferepr, failing __repr__ functions of user instances
    will be represented with a short exception info.

    This function is a wrapper around simple repr.

    Note: a cleaner solution would be to alter ``saferepr``this way
    when maxsize=None, but that might affect some other code.
    """
    try:
        if use_ascii:
            return ascii(obj)
        return repr(obj)
    except Exception as exc:
        return _format_repr_exception(exc, obj)


class AlwaysDispatchingPrettyPrinter(pprint.PrettyPrinter):
    """PrettyPrinter that always dispatches (regardless of width)."""

    # Type ignored because _dispatch is private.
    _dispatch = pprint.PrettyPrinter._dispatch.copy()  # type: ignore[attr-defined]

    def _format(
        self,
        object: object,
        stream: IO[str],
        indent: int,
        allowance: int,
        context: Dict[int, Any],
        level: int,
    ) -> None:
        p = self._dispatch.get(type(object).__repr__, None)

        objid = id(object)
        if objid not in context:
            # Force the dispatch is an object has a registered dispatched function
            if p is not None:
                context[objid] = 1
                p(self, object, stream, indent, allowance, context, level + 1)
                del context[objid]
                return
            # Force the dispatch for dataclasses
            elif (
                sys.version_info[:2] >= (3, 10)  # only supported upstream from 3.10
                and dataclasses.is_dataclass(object)
                and not isinstance(object, type)
                and object.__dataclass_params__.repr  # type: ignore[attr-defined]
                and
                # Check dataclass has generated repr method.
                hasattr(object.__repr__, "__wrapped__")
                and "__create_fn__" in object.__repr__.__wrapped__.__qualname__
            ):
                context[objid] = 1
                # Type ignored because _pprint_dataclass is private.
                self._pprint_dataclass(  # type: ignore[attr-defined]
                    object, stream, indent, allowance, context, level + 1
                )
                del context[objid]
                return

        # Fallback to the default pretty printer behavior
        # Type ignored because _format is private.
        super()._format(  # type: ignore[misc]
            object,
            stream,
            indent,
            allowance,
            context,
            level,
        )

    def _format_items(self, items, stream, indent, allowance, context, level):
        if not items:
            return
        # The upstream format_items will add indent_per_level -1 to the line, so
        # we need to add the missing indent here
        stream.write("\n" + " " * (indent + 1))
        # Type ignored because _format_items is private.
        super()._format_items(  # type: ignore[misc]
            items, stream, indent, allowance, context, level
        )
        stream.write(",\n" + " " * indent)

    def _format_dict_items(self, items, stream, indent, allowance, context, level):
        if not items:
            return
        write = stream.write
        item_indent = indent + self._indent_per_level  # type: ignore[attr-defined]
        delimnl = "\n" + " " * item_indent
        for key, ent in items:
            write(delimnl)
            write(self._repr(key, context, level))  # type: ignore[attr-defined]
            write(": ")
            self._format(ent, stream, item_indent, allowance + 1, context, level)
            write(",")
        write("\n" + " " * indent)

    def _pprint_dataclass(self, object, stream, indent, allowance, context, level):
        cls_name = object.__class__.__name__
        items = [
            (f.name, getattr(object, f.name))
            for f in dataclasses.fields(object)
            if f.repr
        ]
        if not items:
            # Type ignored because _repr is private.
            stream.write(self._repr(object, context, level))  # type: ignore[attr-defined]
            return

        # Type ignored because _indent_per_level is private.
        stream.write(cls_name + "(\n" + (" " * (indent + self._indent_per_level)))  # type: ignore[attr-defined]
        # Type ignored because _ is private.
        self._format_namespace_items(  # type: ignore[attr-defined]
            items, stream, indent + self._indent_per_level, allowance, context, level  # type: ignore[attr-defined]
        )
        stream.write(",\n" + " " * indent + ")")

    def _pprint_chain_map(self, object, stream, indent, allowance, context, level):
        if not len(object.maps) or (len(object.maps) == 1 and not len(object.maps[0])):
            stream.write(repr(object))
            return
        cls = object.__class__
        stream.write(cls.__name__ + "(")
        # Type ignored because _indent_per_level is private.
        item_indent = indent + self._indent_per_level  # type: ignore[attr-defined]
        for m in object.maps:
            stream.write("\n" + " " * item_indent)
            self._format(m, stream, item_indent, allowance + 1, context, level + 1)
            stream.write(",")
        stream.write("\n%s)" % (" " * indent))

    _dispatch[collections.ChainMap.__repr__] = _pprint_chain_map

    def _pprint_counter(self, object, stream, indent, allowance, context, level):
        if not len(object):
            stream.write(repr(object))
            return

        stream.write(object.__class__.__name__ + "({")
        items = object.most_common()
        self._format_dict_items(items, stream, indent, allowance + 1, context, level)
        stream.write("})")

    _dispatch[collections.Counter.__repr__] = _pprint_counter

    def _pprint_deque(self, object, stream, indent, allowance, context, level):
        if not len(object):
            stream.write(repr(object))
            return

        cls = object.__class__
        stream.write(cls.__name__ + "(")
        if object.maxlen is not None:
            stream.write("maxlen=%d, " % object.maxlen)
        stream.write("[")

        self._format_items(object, stream, indent, allowance + 1, context, level)
        stream.write("])")

    _dispatch[collections.deque.__repr__] = _pprint_deque

    def _pprint_default_dict(self, object, stream, indent, allowance, context, level):
        if not len(object):
            stream.write(repr(object))
            return

        # Type ignored because _repr is private.
        rdf = self._repr(object.default_factory, context, level)  # type: ignore[attr-defined]
        stream.write(object.__class__.__name__ + "(" + rdf + ", ")
        self._pprint_dict(object, stream, indent, allowance + 1, context, level)
        stream.write(")")

    _dispatch[collections.defaultdict.__repr__] = _pprint_default_dict

    def _pprint_dict(self, object, stream, indent, allowance, context, level):
        stream.write("{")
        length = len(object)
        if length:
            # Type ignored because _sort_dicts is private.
            if self._sort_dicts:  # type: ignore[attr-defined]
                # Type ignored because _safe_tuple is private.
                items = sorted(object.items(), key=pprint._safe_tuple)  # type: ignore[attr-defined]
            else:
                items = object.items()
            self._format_dict_items(
                items, stream, indent, allowance + 1, context, level
            )
        stream.write("}")

    _dispatch[dict.__repr__] = _pprint_dict

    def _pprint_mappingproxy(self, object, stream, indent, allowance, context, level):
        stream.write("mappingproxy(")
        self._format(object.copy(), stream, indent, allowance + 1, context, level)
        stream.write(")")

    _dispatch[types.MappingProxyType.__repr__] = _pprint_mappingproxy

    def _pprint_ordered_dict(self, object, stream, indent, allowance, context, level):
        if not len(object):
            stream.write(repr(object))
            return

        stream.write(object.__class__.__name__ + "(")
        self._pprint_dict(object, stream, indent, allowance + 1, context, level)  # type: ignore[attr-defined]
        stream.write(")")

    _dispatch[collections.OrderedDict.__repr__] = _pprint_ordered_dict

    if sys.version_info[:2] > (3, 9):

        def _pprint_simplenamespace(
            self, object, stream, indent, allowance, context, level
        ):
            if not len(object.__dict__):
                stream.write(repr(object))
                return

            if type(object) is types.SimpleNamespace:
                # The SimpleNamespace repr is "namespace" instead of the class
                # name, so we do the same here. For subclasses; use the class name.
                cls_name = "namespace"
            else:
                cls_name = object.__class__.__name__
            items = object.__dict__.items()
            # Type ignored because _indent_per_level is private.
            stream.write(cls_name + "(\n" + " " * (indent + self._indent_per_level))  # type: ignore[attr-defined]
            # Type ignored because _format_namespace_items is private.
            self._format_namespace_items(  # type: ignore[attr-defined]
                items,
                stream,
                # Type ignored because _indent_per_level is private.
                indent + self._indent_per_level,  # type: ignore[attr-defined]
                allowance + 1,
                context,
                level,
            )
            stream.write(",\n" + " " * indent + ")")

        _dispatch[types.SimpleNamespace.__repr__] = _pprint_simplenamespace

    def _pprint_tuple(self, object, stream, indent, allowance, context, level):
        stream.write("(")
        self._format_items(object, stream, indent, allowance + 1, context, level)
        stream.write(")")

    _dispatch[tuple.__repr__] = _pprint_tuple


def _pformat_dispatch(
    object: object,
    indent: int = 4,
    width: int = 80,
    depth: Optional[int] = None,
    *,
    compact: bool = False,
) -> str:
    return AlwaysDispatchingPrettyPrinter(
        indent=indent, width=width, depth=depth, compact=compact
    ).pformat(object)
