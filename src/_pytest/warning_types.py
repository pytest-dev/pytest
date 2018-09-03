class PytestWarning(UserWarning):
    """
    Bases: :class:`UserWarning`.

    Base class for all warnings emitted by pytest.
    """


class PytestDeprecationWarning(PytestWarning, DeprecationWarning):
    """
    Bases: :class:`pytest.PytestWarning`, :class:`DeprecationWarning`.

    Warning class for features that will be removed in a future version.
    """


class RemovedInPytest4Warning(PytestDeprecationWarning):
    """
    Bases: :class:`pytest.PytestDeprecationWarning`.

    Warning class for features scheduled to be removed in pytest 4.0.
    """
