import warnings


def user_warning_b():
    """
    A warning triggered in __this__ module for testing.
    """
    # reset the "once" filters
    # globals()['__warningregistry__'] = {}
    warnings.warn("This is deprecated message_b different from a",
                  UserWarning, stacklevel=1)
