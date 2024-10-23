from __future__ import annotations


class UsageError(Exception):
    """Error in pytest usage or invocation."""


class PrintHelp(Exception):
    """Raised when pytest should print its help to skip the rest of the
    argument parsing and validation."""
