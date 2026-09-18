from __future__ import annotations

import sys
import types
from typing import Any
from typing import Generic
from typing import NamedTuple
from typing import TYPE_CHECKING
from typing import TypeVar


if TYPE_CHECKING:
    from _pytest.fixtures import FixtureDef


FixtureValue = TypeVar("FixtureValue")

# NamedTuples cannot take generic arguments before Python 3.11
if TYPE_CHECKING and sys.version_info >= (3, 11):

    class _FixtureResult(NamedTuple, Generic[FixtureValue]):
        value: FixtureValue
        param: object
        exception_and_traceback: None
else:

    class _FixtureResult(NamedTuple):
        value: Any
        param: object
        exception_and_traceback: None


class _FixtureException(NamedTuple):
    value: None
    param: object
    exception_and_traceback: tuple[BaseException, types.TracebackType | None]


_FixtureCachedResult = _FixtureResult[FixtureValue] | _FixtureException  # type: ignore[type-arg]


class FixtureCache:
    """
    Temporarily stores the results of FixtureDefs.

    Conceptually, the entries of this cache should be indexed by a tuple of FixtureDef and param. However,
    the param used by the previous test may no longer be known when retrieving the value of a FixtureDef.
    Therefore, we store the param as part of the result to detect a cache miss.
    """

    def __init__(self) -> None:
        self._cache: dict[FixtureDef[Any], Any] = {}

    def get(
        self, fixturedef: FixtureDef[FixtureValue]
    ) -> _FixtureCachedResult[FixtureValue] | None:
        """Retrieve the result for the specified fixture definition or ``None``."""
        return self._cache.get(fixturedef)

    def set_value(
        self,
        fixturedef: FixtureDef[FixtureValue],
        param: object,
        value: FixtureValue,
    ) -> None:
        """Write a value into the cache for a fixture definition and the specified fixture parameter."""
        self._cache[fixturedef] = _FixtureResult(value, param, None)

    def set_exception(
        self,
        fixturedef: FixtureDef[FixtureValue],
        param: object,
        exception: BaseException,
    ) -> None:
        """Write an exception result into the cache for a fixture definition and the specified fixture parameter."""
        self._cache[fixturedef] = _FixtureException(
            None, param, (exception, exception.__traceback__)
        )

    def invalidate(self, fixturedef: FixtureDef[FixtureValue]) -> None:
        """Remove the entry for the specified fixture definition."""
        del self._cache[fixturedef]
