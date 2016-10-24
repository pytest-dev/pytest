def test_warnings():
    import warnings
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)


def test_warnings1():
    import warnings
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", RuntimeWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
