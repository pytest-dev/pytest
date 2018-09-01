class PytestWarning(UserWarning):
    """Base class for all warnings emitted by pytest"""


class PytestUsageWarning(PytestWarning):
    """Warnings related to pytest usage: either command line or testing code."""


class RemovedInPytest4Warning(PytestWarning, DeprecationWarning):
    """warning class for features that will be removed in pytest 4.0"""
