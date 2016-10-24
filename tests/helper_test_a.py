import warnings


def deprecated_a():
    """
    A warning triggered in __this__ module for testing.
    """
    globals()['__warningregistry__'] = {}
    warnings.warn("This is deprecated message_a",
                  DeprecationWarning, stacklevel=0)
