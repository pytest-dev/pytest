from typing import Any
from typing import Generic
from typing import TypeVar

import attr


if False:  # TYPE_CHECKING
    from typing import Type  # noqa: F401 (used in type string)


class PytestWarning(UserWarning):
    """
    Bases: :class:`UserWarning`.

    Base class for all warnings emitted by pytest.
    """

    __module__ = "pytest"


class PytestAssertRewriteWarning(PytestWarning):
    """
    Bases: :class:`PytestWarning`.

    Warning emitted by the pytest assert rewrite module.
    """

    __module__ = "pytest"


class PytestCacheWarning(PytestWarning):
    """
    Bases: :class:`PytestWarning`.

    Warning emitted by the cache plugin in various situations.
    """

    __module__ = "pytest"


class PytestConfigWarning(PytestWarning):
    """
    Bases: :class:`PytestWarning`.

    Warning emitted for configuration issues.
    """

    __module__ = "pytest"


class PytestCollectionWarning(PytestWarning):
    """
    Bases: :class:`PytestWarning`.

    Warning emitted when pytest is not able to collect a file or symbol in a module.
    """

    __module__ = "pytest"


class PytestDeprecationWarning(PytestWarning, DeprecationWarning):
    """
    Bases: :class:`pytest.PytestWarning`, :class:`DeprecationWarning`.

    Warning class for features that will be removed in a future version.
    """

    __module__ = "pytest"


class PytestExperimentalApiWarning(PytestWarning, FutureWarning):
    """
    Bases: :class:`pytest.PytestWarning`, :class:`FutureWarning`.

    Warning category used to denote experiments in pytest. Use sparingly as the API might change or even be
    removed completely in future version
    """

    __module__ = "pytest"

    @classmethod
    def simple(cls, apiname: str) -> "PytestExperimentalApiWarning":
        return cls(
            "{apiname} is an experimental api that may change over time".format(
                apiname=apiname
            )
        )


class PytestUnhandledCoroutineWarning(PytestWarning):
    """
    Bases: :class:`PytestWarning`.

    Warning emitted when pytest encounters a test function which is a coroutine,
    but it was not handled by any async-aware plugin. Coroutine test functions
    are not natively supported.
    """

    __module__ = "pytest"


class PytestUnknownMarkWarning(PytestWarning):
    """
    Bases: :class:`PytestWarning`.

    Warning emitted on use of unknown markers.
    See https://docs.pytest.org/en/latest/mark.html for details.
    """

    __module__ = "pytest"


_W = TypeVar("_W", bound=PytestWarning)


@attr.s
class UnformattedWarning(Generic[_W]):
    """Used to hold warnings that need to format their message at runtime, as opposed to a direct message.

    Using this class avoids to keep all the warning types and messages in this module, avoiding misuse.
    """

    category = attr.ib(type="Type[_W]")
    template = attr.ib(type=str)

    def format(self, **kwargs: Any) -> _W:
        """Returns an instance of the warning category, formatted with given kwargs"""
        return self.category(self.template.format(**kwargs))


PYTESTER_COPY_EXAMPLE = PytestExperimentalApiWarning.simple("testdir.copy_example")
