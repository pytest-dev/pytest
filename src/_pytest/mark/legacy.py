"""
this is a place where we put datastructures used by legacy apis
we hope to remove
"""
from typing import Set

import attr

from _pytest.compat import TYPE_CHECKING
from _pytest.config import UsageError
from _pytest.mark.expression import Expression
from _pytest.mark.expression import ParseError

if TYPE_CHECKING:
    from _pytest.nodes import Item


@attr.s
class MarkMatcher:
    """A matcher for markers which are present."""

    own_mark_names = attr.ib()

    @classmethod
    def from_item(cls, item) -> "MarkMatcher":
        mark_names = {mark.name for mark in item.iter_markers()}
        return cls(mark_names)

    def __call__(self, name: str) -> bool:
        return name in self.own_mark_names


@attr.s
class KeywordMatcher:
    """A matcher for keywords.

    Given a list of names, matches any substring of one of these names. The
    string inclusion check is case-insensitive.
    """

    _names = attr.ib(type=Set[str])

    @classmethod
    def from_item(cls, item: "Item") -> "KeywordMatcher":
        mapped_names = set()

        # Add the names of the current item and any parent items
        import pytest

        for item in item.listchain():
            if not isinstance(item, pytest.Instance):
                mapped_names.add(item.name)

        # Add the names added as extra keywords to current or parent items
        mapped_names.update(item.listextrakeywords())

        # Add the names attached to the current function through direct assignment
        function_obj = getattr(item, "function", None)
        if function_obj:
            mapped_names.update(function_obj.__dict__)

        # add the markers to the keywords as we no longer handle them correctly
        mapped_names.update(mark.name for mark in item.iter_markers())

        return cls(mapped_names)

    def __call__(self, subname: str) -> bool:
        subname = subname.lower()
        names = (name.lower() for name in self._names)

        for name in names:
            if subname in name:
                return True
        return False


def matchmark(colitem, markexpr: str) -> bool:
    """Tries to match on any marker names, attached to the given colitem."""
    try:
        expression = Expression.compile(markexpr)
    except ParseError as e:
        raise UsageError(
            "Wrong expression passed to '-m': {}: {}".format(markexpr, e)
        ) from None
    return expression.evaluate(MarkMatcher.from_item(colitem))


def matchkeyword(colitem, keywordexpr: str) -> bool:
    """Tries to match given keyword expression to given collector item.

    Will match on the name of colitem, including the names of its parents.
    Only matches names of items which are either a :class:`Class` or a
    :class:`Function`.
    Additionally, matches on names in the 'extra_keyword_matches' set of
    any item, as well as names directly assigned to test functions.
    """
    try:
        expression = Expression.compile(keywordexpr)
    except ParseError as e:
        raise UsageError(
            "Wrong expression passed to '-k': {}: {}".format(keywordexpr, e)
        ) from None
    return expression.evaluate(KeywordMatcher.from_item(colitem))
