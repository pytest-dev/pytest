import pytest
import warnings

from pytest_warnings import _setoption
from helper_test_a import deprecated_a
from helper_test_b import user_warning_b


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


# This section test the ability to filter selectively warnings using regular
# expressions on messages.

def test_filters_setoption():
    "A alone works"

    with pytest.warns(DeprecationWarning):
        deprecated_a()


def test_filters_setoption_2():
    "B alone works"

    with pytest.warns(UserWarning) as record:
        user_warning_b()

    assert len(record) == 1


def test_filters_setoption_3():
    "A and B works"

    with pytest.warns(None) as record:
        user_warning_b()
        deprecated_a()
    assert len(record) == 2


def test_filters_setoption_4():
    "A works, B is filtered"

    with pytest.warns(None) as record:
        _setoption(warnings, 'ignore:.*message_a.*')
        deprecated_a()
        user_warning_b()

    assert len(record) == 1, "Only `A` should be filtered out"


def test_filters_setoption_4b():
    "A works, B is filtered"

    with pytest.warns(None) as record:
        _setoption(warnings, 'ignore:.*message_b.*')
        _setoption(warnings, 'ignore:.*message_a.*')
        _setoption(warnings, 'always:::.*helper_test_a.*')
        deprecated_a()
        user_warning_b()

    assert len(record) == 1, "`A` and `B` should be visible, second filter reenable A"


def test_filters_setoption_5():
    "B works, A is filtered"

    with pytest.warns(None) as records:
        _setoption(warnings, 'always:::.*helper_test_a.*')
        _setoption(warnings, 'ignore::UserWarning')
        deprecated_a()
        user_warning_b()

    assert len(records) == 1, "Only `B` should be filtered out"
