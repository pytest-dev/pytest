"""
this is a place where we put datastructures used by legacy apis
we hope to remove
"""
import keyword
from typing import Set

import attr

from _pytest.compat import TYPE_CHECKING
from _pytest.config import UsageError

if TYPE_CHECKING:
    from _pytest.nodes import Item  # noqa: F401 (used in type string)


@attr.s
class MarkMapping:
    """Provides a local mapping for markers where item access
    resolves to True if the marker is present. """

    own_mark_names = attr.ib()

    @classmethod
    def from_item(cls, item):
        mark_names = {mark.name for mark in item.iter_markers()}
        return cls(mark_names)

    def __getitem__(self, name):
        return name in self.own_mark_names


@attr.s
class KeywordMapping:
    """Provides a local mapping for keywords.
    Given a list of names, map any substring of one of these names to True.
    """

    _names = attr.ib(type=Set[str])

    @classmethod
    def from_item(cls, item: "Item") -> "KeywordMapping":
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

    def __getitem__(self, subname: str) -> bool:
        """Return whether subname is included within stored names.

        The string inclusion check is case-insensitive.

        """
        subname = subname.lower()
        names = (name.lower() for name in self._names)

        for name in names:
            if subname in name:
                return True
        return False


python_keywords_allowed_list = ["or", "and", "not"]


def matchmark(colitem, markexpr):
    """Tries to match on any marker names, attached to the given colitem."""
    try:
        return eval(markexpr, {}, MarkMapping.from_item(colitem))
    except SyntaxError as e:
        raise SyntaxError(str(e) + "\nMarker expression must be valid Python!")


def matchkeyword(colitem, keywordexpr):
    """Tries to match given keyword expression to given collector item.

    Will match on the name of colitem, including the names of its parents.
    Only matches names of items which are either a :class:`Class` or a
    :class:`Function`.
    Additionally, matches on names in the 'extra_keyword_matches' set of
    any item, as well as names directly assigned to test functions.
    """
    mapping = KeywordMapping.from_item(colitem)
    if " " not in keywordexpr:
        # special case to allow for simple "-k pass" and "-k 1.3"
        return mapping[keywordexpr]
    elif keywordexpr.startswith("not ") and " " not in keywordexpr[4:]:
        return not mapping[keywordexpr[4:]]
    for kwd in keywordexpr.split():
        if keyword.iskeyword(kwd) and kwd not in python_keywords_allowed_list:
            raise UsageError(
                "Python keyword '{}' not accepted in expressions passed to '-k'".format(
                    kwd
                )
            )
    try:
        return eval(keywordexpr, {}, mapping)
    except SyntaxError:
        raise UsageError("Wrong expression passed to '-k': {}".format(keywordexpr))
