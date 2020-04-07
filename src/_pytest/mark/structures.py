import inspect
import warnings
from collections import namedtuple
from collections.abc import MutableMapping
from typing import Any
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Union

import attr

from .._code.source import getfslineno
from ..compat import ascii_escaped
from ..compat import NOTSET
from _pytest.outcomes import fail
from _pytest.warning_types import PytestUnknownMarkWarning

EMPTY_PARAMETERSET_OPTION = "empty_parameter_set_mark"


def istestfunc(func):
    return (
        hasattr(func, "__call__")
        and getattr(func, "__name__", "<lambda>") != "<lambda>"
    )


def get_empty_parameterset_mark(config, argnames, func):
    from ..nodes import Collector

    requested_mark = config.getini(EMPTY_PARAMETERSET_OPTION)
    if requested_mark in ("", None, "skip"):
        mark = MARK_GEN.skip
    elif requested_mark == "xfail":
        mark = MARK_GEN.xfail(run=False)
    elif requested_mark == "fail_at_collect":
        f_name = func.__name__
        _, lineno = getfslineno(func)
        raise Collector.CollectError(
            "Empty parameter set in '%s' at line %d" % (f_name, lineno + 1)
        )
    else:
        raise LookupError(requested_mark)
    fs, lineno = getfslineno(func)
    reason = "got empty parameter set %r, function %s at %s:%d" % (
        argnames,
        func.__name__,
        fs,
        lineno,
    )
    return mark(reason=reason)


class ParameterSet(namedtuple("ParameterSet", "values, marks, id")):
    @classmethod
    def param(cls, *values, marks=(), id=None):
        if isinstance(marks, MarkDecorator):
            marks = (marks,)
        else:
            assert isinstance(marks, (tuple, list, set))

        if id is not None:
            if not isinstance(id, str):
                raise TypeError(
                    "Expected id to be a string, got {}: {!r}".format(type(id), id)
                )
            id = ascii_escaped(id)
        return cls(values, marks, id)

    @classmethod
    def extract_from(cls, parameterset, force_tuple=False):
        """
        :param parameterset:
            a legacy style parameterset that may or may not be a tuple,
            and may or may not be wrapped into a mess of mark objects

        :param force_tuple:
            enforce tuple wrapping so single argument tuple values
            don't get decomposed and break tests
        """

        if isinstance(parameterset, cls):
            return parameterset
        if force_tuple:
            return cls.param(parameterset)
        else:
            return cls(parameterset, marks=[], id=None)

    @staticmethod
    def _parse_parametrize_args(argnames, argvalues, *args, **kwargs):
        if not isinstance(argnames, (tuple, list)):
            argnames = [x.strip() for x in argnames.split(",") if x.strip()]
            force_tuple = len(argnames) == 1
        else:
            force_tuple = False
        return argnames, force_tuple

    @staticmethod
    def _parse_parametrize_parameters(argvalues, force_tuple):
        return [
            ParameterSet.extract_from(x, force_tuple=force_tuple) for x in argvalues
        ]

    @classmethod
    def _for_parametrize(cls, argnames, argvalues, func, config, function_definition):
        argnames, force_tuple = cls._parse_parametrize_args(argnames, argvalues)
        parameters = cls._parse_parametrize_parameters(argvalues, force_tuple)
        del argvalues

        if parameters:
            # check all parameter sets have the correct number of values
            for param in parameters:
                if len(param.values) != len(argnames):
                    msg = (
                        '{nodeid}: in "parametrize" the number of names ({names_len}):\n'
                        "  {names}\n"
                        "must be equal to the number of values ({values_len}):\n"
                        "  {values}"
                    )
                    fail(
                        msg.format(
                            nodeid=function_definition.nodeid,
                            values=param.values,
                            names=argnames,
                            names_len=len(argnames),
                            values_len=len(param.values),
                        ),
                        pytrace=False,
                    )
        else:
            # empty parameter set (likely computed at runtime): create a single
            # parameter set with NOTSET values, with the "empty parameter set" mark applied to it
            mark = get_empty_parameterset_mark(config, argnames, func)
            parameters.append(
                ParameterSet(values=(NOTSET,) * len(argnames), marks=[mark], id=None)
            )
        return argnames, parameters


@attr.s(frozen=True)
class Mark:
    #: Name of the mark.
    name = attr.ib(type=str)
    #: Positional arguments of the mark decorator.
    args = attr.ib(type=Tuple[Any, ...])
    #: Keyword arguments of the mark decorator.
    kwargs = attr.ib(type=Mapping[str, Any])

    #: Source Mark for ids with parametrize Marks.
    _param_ids_from = attr.ib(type=Optional["Mark"], default=None, repr=False)
    #: Resolved/generated ids with parametrize Marks.
    _param_ids_generated = attr.ib(
        type=Optional[Sequence[str]], default=None, repr=False
    )

    def _has_param_ids(self) -> bool:
        return "ids" in self.kwargs or len(self.args) >= 4

    def combined_with(self, other: "Mark") -> "Mark":
        """Return a new Mark which is a combination of this
        Mark and another Mark.

        Combines by appending args and merging kwargs.

        :param other: The mark to combine with.
        :type other: Mark
        :rtype: Mark
        """
        assert self.name == other.name

        # Remember source of ids with parametrize Marks.
        param_ids_from = None  # type: Optional[Mark]
        if self.name == "parametrize":
            if other._has_param_ids():
                param_ids_from = other
            elif self._has_param_ids():
                param_ids_from = self

        return Mark(
            self.name,
            self.args + other.args,
            dict(self.kwargs, **other.kwargs),
            param_ids_from=param_ids_from,
        )


@attr.s
class MarkDecorator:
    """A decorator for applying a mark on test functions and classes.

    MarkDecorators are created with ``pytest.mark``::

        mark1 = pytest.mark.NAME              # Simple MarkDecorator
        mark2 = pytest.mark.NAME(name1=value) # Parametrized MarkDecorator

    and can then be applied as decorators to test functions::

        @mark2
        def test_function():
            pass

    When a MarkDecorator is called it does the following:

    1. If called with a single class as its only positional argument and no
       additional keyword arguments, it attaches the mark to the class so it
       gets applied automatically to all test cases found in that class.

    2. If called with a single function as its only positional argument and
       no additional keyword arguments, it attaches the mark to the function,
       containing all the arguments already stored internally in the
       MarkDecorator.

    3. When called in any other case, it returns a new MarkDecorator instance
       with the original MarkDecorator's content updated with the arguments
       passed to this call.

    Note: The rules above prevent MarkDecorators from storing only a single
    function or class reference as their positional argument with no
    additional keyword or positional arguments. You can work around this by
    using `with_args()`.
    """

    mark = attr.ib(type=Mark, validator=attr.validators.instance_of(Mark))

    @property
    def name(self) -> str:
        """Alias for mark.name."""
        return self.mark.name

    @property
    def args(self) -> Tuple[Any, ...]:
        """Alias for mark.args."""
        return self.mark.args

    @property
    def kwargs(self) -> Mapping[str, Any]:
        """Alias for mark.kwargs."""
        return self.mark.kwargs

    @property
    def markname(self) -> str:
        return self.name  # for backward-compat (2.4.1 had this attr)

    def __repr__(self) -> str:
        return "<MarkDecorator {!r}>".format(self.mark)

    def with_args(self, *args: object, **kwargs: object) -> "MarkDecorator":
        """Return a MarkDecorator with extra arguments added.

        Unlike calling the MarkDecorator, with_args() can be used even
        if the sole argument is a callable/class.

        :return: MarkDecorator
        """
        mark = Mark(self.name, args, kwargs)
        return self.__class__(self.mark.combined_with(mark))

    def __call__(self, *args: object, **kwargs: object):
        """Call the MarkDecorator."""
        if args and not kwargs:
            func = args[0]
            is_class = inspect.isclass(func)
            if len(args) == 1 and (istestfunc(func) or is_class):
                store_mark(func, self.mark)
                return func
        return self.with_args(*args, **kwargs)


def get_unpacked_marks(obj):
    """
    obtain the unpacked marks that are stored on an object
    """
    mark_list = getattr(obj, "pytestmark", [])
    if not isinstance(mark_list, list):
        mark_list = [mark_list]
    return normalize_mark_list(mark_list)


def normalize_mark_list(mark_list: Iterable[Union[Mark, MarkDecorator]]) -> List[Mark]:
    """
    normalizes marker decorating helpers to mark objects

    :type mark_list: List[Union[Mark, Markdecorator]]
    :rtype: List[Mark]
    """
    extracted = [
        getattr(mark, "mark", mark) for mark in mark_list
    ]  # unpack MarkDecorator
    for mark in extracted:
        if not isinstance(mark, Mark):
            raise TypeError("got {!r} instead of Mark".format(mark))
    return [x for x in extracted if isinstance(x, Mark)]


def store_mark(obj, mark: Mark) -> None:
    """Store a Mark on an object.

    This is used to implement the Mark declarations/decorators correctly.
    """
    assert isinstance(mark, Mark), mark
    # Always reassign name to avoid updating pytestmark in a reference that
    # was only borrowed.
    obj.pytestmark = get_unpacked_marks(obj) + [mark]


class MarkGenerator:
    """Factory for :class:`MarkDecorator` objects - exposed as
    a ``pytest.mark`` singleton instance.

    Example::

         import pytest

         @pytest.mark.slowtest
         def test_function():
            pass

    applies a 'slowtest' :class:`Mark` on ``test_function``.
    """

    _config = None
    _markers = set()  # type: Set[str]

    def __getattr__(self, name: str) -> MarkDecorator:
        if name[0] == "_":
            raise AttributeError("Marker name must NOT start with underscore")

        if self._config is not None:
            # We store a set of markers as a performance optimisation - if a mark
            # name is in the set we definitely know it, but a mark may be known and
            # not in the set.  We therefore start by updating the set!
            if name not in self._markers:
                for line in self._config.getini("markers"):
                    # example lines: "skipif(condition): skip the given test if..."
                    # or "hypothesis: tests which use Hypothesis", so to get the
                    # marker name we split on both `:` and `(`.
                    marker = line.split(":")[0].split("(")[0].strip()
                    self._markers.add(marker)

            # If the name is not in the set of known marks after updating,
            # then it really is time to issue a warning or an error.
            if name not in self._markers:
                if self._config.option.strict_markers:
                    fail(
                        "{!r} not found in `markers` configuration option".format(name),
                        pytrace=False,
                    )

                # Raise a specific error for common misspellings of "parametrize".
                if name in ["parameterize", "parametrise", "parameterise"]:
                    __tracebackhide__ = True
                    fail("Unknown '{}' mark, did you mean 'parametrize'?".format(name))

                warnings.warn(
                    "Unknown pytest.mark.%s - is this a typo?  You can register "
                    "custom marks to avoid this warning - for details, see "
                    "https://docs.pytest.org/en/latest/mark.html" % name,
                    PytestUnknownMarkWarning,
                    2,
                )

        return MarkDecorator(Mark(name, (), {}))


MARK_GEN = MarkGenerator()


class NodeKeywords(MutableMapping):
    def __init__(self, node):
        self.node = node
        self.parent = node.parent
        self._markers = {node.name: True}

    def __getitem__(self, key):
        try:
            return self._markers[key]
        except KeyError:
            if self.parent is None:
                raise
            return self.parent.keywords[key]

    def __setitem__(self, key, value):
        self._markers[key] = value

    def __delitem__(self, key):
        raise ValueError("cannot delete key in keywords dict")

    def __iter__(self):
        seen = self._seen()
        return iter(seen)

    def _seen(self):
        seen = set(self._markers)
        if self.parent is not None:
            seen.update(self.parent.keywords)
        return seen

    def __len__(self):
        return len(self._seen())

    def __repr__(self):
        return "<NodeKeywords for node {}>".format(self.node)
