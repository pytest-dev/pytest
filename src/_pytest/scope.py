"""
Scope definition and related utilities.

Those are defined here, instead of in the 'fixtures' module because
their use is spread across many other pytest modules, and centralizing it in 'fixtures'
would cause circular references.

Also this makes the module light to import, as it should.
"""

from __future__ import annotations

from enum import Enum
from functools import total_ordering
from typing import Literal


ScopeName = Literal["session", "package", "module", "class", "definition", "function"]


@total_ordering
class Scope(Enum):
    """
    Represents one of the possible fixture scopes in pytest.

    Scopes are ordered from lower to higher, that is:

              ->>> higher ->>>

    Function < Definition < Class < Module < Package < Session

              <<<- lower  <<<-

    ``Definition`` is the scope of a single test *definition*, shared by all
    the (possibly parametrized) invocations generated from it. It requires the
    definition to be a node in the collection tree -- see
    :confval:`collect_function_definition`.
    """

    # Scopes need to be listed from lower to higher.
    Function = "function"
    Definition = "definition"
    Class = "class"
    Module = "module"
    Package = "package"
    Session = "session"

    def next_lower(self) -> Scope:
        """Return the next lower scope."""
        index = _SCOPE_INDICES[self]
        if index == 0:
            raise ValueError(f"{self} is the lower-most scope")
        return _ALL_SCOPES[index - 1]

    def next_higher(self) -> Scope:
        """Return the next higher scope."""
        index = _SCOPE_INDICES[self]
        if index == len(_SCOPE_INDICES) - 1:
            raise ValueError(f"{self} is the upper-most scope")
        return _ALL_SCOPES[index + 1]

    def __lt__(self, other: Scope) -> bool:
        self_index = _SCOPE_INDICES[self]
        other_index = _SCOPE_INDICES[other]
        return self_index < other_index

    @classmethod
    def from_user(
        cls, scope_name: ScopeName, descr: str, where: str | None = None
    ) -> Scope:
        """
        Given a scope name from the user, return the equivalent Scope enum. Should be used
        whenever we want to convert a user provided scope name to its enum object.

        If the scope name is invalid, construct a user friendly message and call pytest.fail.
        """
        from _pytest.outcomes import fail

        try:
            # Holding this reference is necessary for mypy at the moment.
            scope = Scope(scope_name)
        except ValueError:
            fail(
                "{} {}got an unexpected scope value '{}'".format(
                    descr, f"from {where} " if where else "", scope_name
                ),
                pytrace=False,
            )
        return scope


_ALL_SCOPES = list(Scope)
_SCOPE_INDICES = {scope: index for index, scope in enumerate(_ALL_SCOPES)}


# Ordered list of scopes which can contain many tests (in practice all except Function).
HIGH_SCOPES = [x for x in Scope if x is not Scope.Function]
