import pytest
import warnings


def test_warnings():
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)


def test_warnings1():
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)
    warnings.warn("Foo", DeprecationWarning)


def test_warn():
    with pytest.warns(DeprecationWarning):
        warnings.warn("Bar", DeprecationWarning)
